# based on the semantic scholar repo: https://github.com/allenai/s2-folks/blob/main/examples/python

import dotenv
from langchain_core.tools import tool
from dotenv import load_dotenv
import requests
import argparse
import os
from requests import Session
from typing import Generator, Union
import urllib3
urllib3.disable_warnings()

load_dotenv()
SCHOLAR_PAPERS_DIR = os.getenv("SCHOLAR_PAPERS_DIR")
# S2_API_KEY = os.getenv('S2_API_KEY') # don't have one yet
RESULT_LIMIT = 10

# ============================================================================
#                     PAPER FETCHING AND RECOMMENDATIONS
# ============================================================================

@tool
def find_basis_paper(query:str="LLM prompt inyection") -> str:
    """
    Looks for realted papers in Semantic Scholar based on the input query string,
    it will return a string with paper titles and id's.
    """
    papers = None
    rsp = requests.get('https://api.semanticscholar.org/graph/v1/paper/search',
                        params={'query': query, 'limit': RESULT_LIMIT, 'fields': 'title,url'})
    rsp.raise_for_status()
    results = rsp.json()
    total = results["total"]
    if not total:
        return 'No matches found. Please try another query.'

    print(f'Found {total} results. Showing up to {RESULT_LIMIT}.')
    papers = results['data']
    return _print_papers(papers)

@tool
def find_recommendations(paperId:str) -> str:
    """
    Looks for realted papers to 'paperId' in Semantic Scholar, it will return a string with paper titles and id's
    from which you can further obtain recommendations.
    """
    rsp = requests.get(f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{paperId}",
                       params={'fields': 'title,url', 'limit': 10})
    rsp.raise_for_status()
    results = rsp.json()
    papers = results['recommendedPapers']

    if len(papers) < 1:
        return 'No matches found. Please verify paperId.'
    return _print_papers(results['recommendedPapers'])


def _print_papers(papers) -> str:
    papers_str = ""
    for idx, paper in enumerate(papers):
        papers_str += f"{paper['title']} id:{paper['paperId']}\n"

    return papers_str

# ============================================================================
#                           PAPER EXTRACTION
# ============================================================================

@tool
def fetch_papers(paper_ids:list(str)) -> tuple(list(str), str):
    """
    Receives a list of Semantic Scholar paper ids, fetches the publicly available PDF files whenever
    they are available. Responds with the list of successfully downloaded paper ids and a status log.
    """
    downloaded_papers = []
    status = ""

    for paper_id, result in _download_papers(paper_ids, directory=SCHOLAR_PAPERS_DIR, user_agent="requests/2.0.0"):
        if isinstance(result, Exception):
            status += f"Failed to download '{paper_id}': {type(result).__name__}: {result}\n"
        elif result is None:
            status += f"'{paper_id}' is not open access\n"
        else:
            status += f"Downloaded '{paper_id}'\n"
            downloaded_papers.append(paper_id)

    return downloaded_papers, status

def _get_paper(session: Session, paper_id: str, fields: str = 'paperId,title', **kwargs) -> dict:
    params = {
        'fields': fields,
        **kwargs,
    }

    with session.get(f'https://api.semanticscholar.org/graph/v1/paper/{paper_id}', params=params) as response:
        response.raise_for_status()
        return response.json()


def _download_pdf(session: Session, url: str, path: str, user_agent: str = 'requests/2.0.0'):
    # send a user-agent to avoid server error
    headers = {
        'user-agent': user_agent,
    }

    # stream the response to avoid downloading the entire file into memory
    with session.get(url, headers=headers, stream=True, verify=False) as response:
        # check if the request was successful
        response.raise_for_status()

        if response.headers['content-type'] != 'application/pdf':
            raise Exception('The response is not a pdf')

        with open(path, 'wb') as f:
            # write the response to the file, chunk_size bytes at a time
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)


def _download_paper(session: Session, paper_id: str, directory: str = 'papers', user_agent: str = 'requests/2.0.0') -> Union[str, None]:
    paper = _get_paper(session, paper_id, fields='paperId,isOpenAccess,openAccessPdf')

    # check if the paper is open access
    if not paper['isOpenAccess']:
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


def _download_papers(paper_ids: list[str], directory: str = 'papers', user_agent: str = 'requests/2.0.0') -> Generator[tuple[str, Union[str, None, Exception]], None, None]:
    # use a session to reuse the same TCP connection
    with Session() as session:
        for paper_id in paper_ids:
            try:
                yield paper_id, _download_paper(session, paper_id, directory=directory, user_agent=user_agent)
            except Exception as e:
                yield paper_id, e

# export toolkit
tools = [find_basis_paper, find_recommendations, fetch_papers]