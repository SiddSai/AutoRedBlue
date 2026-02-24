# based on the semantic scholar repo: https://github.com/allenai/s2-folks/blob/main/examples/python

import dotenv
from langchain_core.tools import tool
from dotenv import load_dotenv
import requests
import argparse
import os
import time
from requests import Session
from typing import Generator, Union
import urllib3
urllib3.disable_warnings()

load_dotenv()
SCHOLAR_PAPERS_DIR = os.getenv("SCHOLAR_PAPERS_DIR")
RESULT_LIMIT = 10


def _request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    max_retries: int = 6,
    base_backoff_s: float = 1.0,
    max_backoff_s: float = 60.0,
    timeout: float | tuple[float, float] = (10.0, 60.0),
    **kwargs,
) -> requests.Response:
    headers = dict(kwargs.pop("headers", {}) or {})
    kwargs["headers"] = headers
    kwargs.setdefault("timeout", timeout)

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = session.request(method, url, **kwargs)
            if response.status_code not in (429, 500, 502, 503, 504):
                return response

            if attempt >= max_retries:
                return response

            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    sleep_s = float(retry_after)
                except ValueError:
                    sleep_s = base_backoff_s * (2**attempt)
            else:
                sleep_s = base_backoff_s * (2**attempt)

            sleep_s = min(max_backoff_s, max(0.0, sleep_s))
            time.sleep(sleep_s)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exc = e
            if attempt >= max_retries:
                raise
            sleep_s = min(max_backoff_s, base_backoff_s * (2**attempt))
            time.sleep(sleep_s)

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Request retry loop ended unexpectedly")

# ============================================================================
#                     PAPER FETCHING AND RECOMMENDATIONS
# ============================================================================

# @tool
def find_basis_paper(query:str="LLM prompt inyection") -> str:
    """
    Looks for realted papers in Semantic Scholar based on the input query string,
    it will return a string with paper titles and id's.
    """
    papers = None
    with Session() as session:
        rsp = _request_with_retries(
            session,
            "GET",
            'https://api.semanticscholar.org/graph/v1/paper/search',
            params={'query': query, 'limit': RESULT_LIMIT, 'fields': 'title,url'},
        )
    rsp.raise_for_status()
    results = rsp.json()
    total = results["total"]
    if not total:
        return 'No matches found. Please try another query.'

    print(f'Found {total} results. Showing up to {RESULT_LIMIT}.')
    papers = results['data']
    return _print_papers(papers)

# @tool
def find_recommendations(paperId:str) -> str:
    """
    Looks for realted papers to 'paperId' in Semantic Scholar, it will return a string with paper titles and id's
    from which you can further obtain recommendations.
    """
    with Session() as session:
        rsp = _request_with_retries(
            session,
            "GET",
            f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{paperId}",
            params={'fields': 'title,url', 'limit': 10},
        )
    rsp.raise_for_status()
    results = rsp.json()
    papers = results['recommendedPapers']

    if len(papers) < 1:
        return 'No matches found. Please verify paperId.'
    return _print_papers(results['recommendedPapers'])


def _print_papers(papers) -> str:
    papers_str = ""
    for idx, paper in enumerate(papers):
        papers_str += f"idx. {paper['title']} | id:{paper['paperId']} | url:{paper['url']}\n"

    return papers_str

# ============================================================================
#                           PAPER EXTRACTION
# ============================================================================

# @tool
def fetch_papers(paper_ids: list[str]) -> tuple[list[str], str]:
    """
    Receives a list of Semantic Scholar paper ids, fetches the publicly available PDF files whenever
    they are available. Responds with the list of successfully downloaded paper ids and a status log.
    """
    downloaded_papers = []
    status = ""

    for paper_id, result in _download_papers(paper_ids, directory=SCHOLAR_PAPERS_DIR, user_agent="requests/2.0.0"):
        print("checking paper:", paper_id)
        if isinstance(result, Exception):
            status += f"Failed to download '{paper_id}': {type(result).__name__}: {result}\n"
        elif result is None:
            status += f"'{paper_id}' is not open access\n"
        else:
            status += f"Downloaded '{paper_id}'\n"
            downloaded_papers.append(paper_id)

    return downloaded_papers, status

def _download_papers(paper_ids: list[str], directory: str = 'papers', user_agent: str = 'requests/2.0.0') -> Generator[tuple[str, Union[str, None, Exception]], None, None]:
    # use a session to reuse the same TCP connection
    with Session() as session:
        for paper_id in paper_ids:
            try:
                yield paper_id, _download_paper(session, paper_id, directory=directory, user_agent=user_agent)
            except Exception as e:
                yield paper_id, e


def _download_paper(session: Session, paper_id: str, directory: str = 'papers', user_agent: str = 'requests/2.0.0') -> Union[str, None]:
    paper = _get_paper(session, paper_id, fields='paperId,isOpenAccess,openAccessPdf')
    print(paper)
    print()

    # check if the paper is open access
    if not paper['isOpenAccess']:
        print("Paper is not open acces, from _download_paper")
        return None

    if paper['openAccessPdf'] is None:
        return None

    paperId: str = paper['paperId']
    pdf_url: str = paper['openAccessPdf']['url']
    pdf_path = os.path.join(directory, f'{paperId}.pdf')

    # create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # check if the pdf has already been downloaded
    if not os.path.exists(pdf_path):
       _download_pdf(session, pdf_url, pdf_path, user_agent=user_agent)

    return pdf_path

def _get_paper(session: Session, paper_id: str, fields: str = 'paperId,title', **kwargs) -> dict:
    params = {
        'fields': fields,
        **kwargs,
    }

    response = _request_with_retries(
        session,
        "GET",
        f'https://api.semanticscholar.org/graph/v1/paper/{paper_id}',
        params=params,
    )
    response.raise_for_status()
    return response.json()

def _download_pdf(session: Session, url: str, path: str, user_agent: str = 'requests/2.0.0'):
    # send a user-agent to avoid server error
    headers = {
        'user-agent': user_agent,
    }

    # stream the response to avoid downloading the entire file into memory
    response = _request_with_retries(
        session,
        "GET",
        url,
        headers=headers,
        stream=True,
        verify=False,
    )

    response.raise_for_status()

    content_type = response.headers.get('content-type', '')
    if content_type != 'application/pdf':
        print("The response is not a pdf")
        raise Exception('The response is not a pdf')

    with open(path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

# export toolkit
tools = [find_basis_paper, find_recommendations, fetch_papers]