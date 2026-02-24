# lookup: https://info.arxiv.org/help/api/user-manual.html

from __future__ import annotations

import os
import time
import xml.etree.ElementTree as ET
from typing import Generator

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from requests import Session

from services import pdf_scraper

load_dotenv()

ARXIV_PAPERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arxiv_papers", "pdf")
ARXIV_MD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arxiv_papers", "md")
ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_USER_AGENT = os.getenv("ARXIV_USER_AGENT") or "AutoRedBlue/0.1"
ARXIV_MIN_REQUEST_INTERVAL_S = 3.0
_LAST_ARXIV_REQUEST_TS = 0.0


def _throttle_arxiv_requests():
    global _LAST_ARXIV_REQUEST_TS
    now = time.time()
    wait_s = (_LAST_ARXIV_REQUEST_TS + ARXIV_MIN_REQUEST_INTERVAL_S) - now
    if wait_s > 0:
        time.sleep(wait_s)
    _LAST_ARXIV_REQUEST_TS = time.time()



def _request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    max_retries: int = 2,
    base_backoff_s: float = 1.0,
    max_backoff_s: float = 60.0,
    timeout: float | tuple[float, float] = (5.0, 20.0),
    **kwargs,
) -> requests.Response:
    headers = dict(kwargs.pop("headers", {}) or {})
    headers.setdefault("user-agent", ARXIV_USER_AGENT)
    kwargs["headers"] = headers
    kwargs.setdefault("timeout", timeout)

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            _throttle_arxiv_requests()
            response = session.request(method, url, **kwargs)
            if response.status_code not in (429, 500, 502, 503, 504):
                return response

            if attempt >= max_retries:
                return response

            response.close()

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


def _strip(text: str | None) -> str:
    return (text or "").strip()


def _normalize_arxiv_id(arxiv_id: str) -> str:
    arxiv_id = arxiv_id.strip()
    if arxiv_id.startswith("http://") or arxiv_id.startswith("https://"):
        arxiv_id = arxiv_id.rstrip("/")
        arxiv_id = arxiv_id.split("/")[-1]
    if arxiv_id.startswith("arXiv:"):
        arxiv_id = arxiv_id[len("arXiv:") :]
    return arxiv_id


def _parse_arxiv_atom(xml_text: str) -> list[dict]:
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    root = ET.fromstring(xml_text)
    entries: list[dict] = []

    for entry in root.findall("atom:entry", ns):
        entry_id_url = _strip(entry.findtext("atom:id", default="", namespaces=ns))
        arxiv_id = _normalize_arxiv_id(entry_id_url)
        title = " ".join(_strip(entry.findtext("atom:title", default="", namespaces=ns)).split())
        summary = " ".join(_strip(entry.findtext("atom:summary", default="", namespaces=ns)).split())
        updated = _strip(entry.findtext("atom:updated", default="", namespaces=ns))
        published = _strip(entry.findtext("atom:published", default="", namespaces=ns))
        authors = [
            _strip(a.findtext("atom:name", default="", namespaces=ns))
            for a in entry.findall("atom:author", ns)
        ]
        authors = [a for a in authors if a]

        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href", "")
                break
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        entries.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "summary": summary,
                "updated": updated,
                "published": published,
                "authors": authors,
                "abs_url": entry_id_url,
                "pdf_url": pdf_url,
            }
        )

    return entries


def _format_entries(entries: list[dict]) -> str:
    out = ""
    for idx, e in enumerate(entries):
        out += f"idx. {idx} | title:{e.get('title','')} | id:{e.get('arxiv_id','')} | url:{e.get('abs_url','')}\n"
    return out


# @tool
def search_arxiv(query:str, page:int = 1, limit:int = 10) -> str:
    """Search arXiv for papers matching a free-text query.

    Args:
        query: Query string (searched across title/abstract/authors).
        limit: Maximum number of results to return.

    Returns:
        A newline-separated string of results containing title, arXiv id, and abstract URL.
    """

    with Session() as session:
        rsp = _request_with_retries(
            session,
            "GET",
            ARXIV_API_URL,
            params={
                "search_query": f"all:{query}",
                "start": (page-1)*limit,
                "max_results": int(limit),
            },
        )
    rsp.raise_for_status()
    # print(rsp.text)
    entries = _parse_arxiv_atom(rsp.text)
    if not entries:
        return "No matches found. Please try another query."
    return _format_entries(entries)


def _download_pdf(session: Session, url: str, path: str):
    rsp = _request_with_retries(
        session,
        "GET",
        url,
        stream=True,
    )
    rsp.raise_for_status()

    content_type = rsp.headers.get("content-type", "")
    if "pdf" not in content_type.lower():
        raise Exception("The response is not a pdf")

    with open(path, "wb") as f:
        for chunk in rsp.iter_content(chunk_size=8192):
            f.write(chunk)


def _download_papers(arxiv_ids: list[str], directory: str) -> Generator[tuple[str, str | None | Exception], None, None]:
    with Session() as session:
        for arxiv_id in arxiv_ids:
            try:
                norm_id = _normalize_arxiv_id(arxiv_id)
                if not norm_id:
                    yield arxiv_id, Exception("Invalid arXiv id")
                    continue

                pdf_url = f"https://arxiv.org/pdf/{norm_id}.pdf"
                os.makedirs(directory, exist_ok=True)
                pdf_path = os.path.join(directory, f"{norm_id}.pdf")
                if not os.path.exists(pdf_path):
                    _download_pdf(session, pdf_url, pdf_path)
                yield norm_id, pdf_path
            except Exception as e:
                yield arxiv_id, e


# @tool
def download_pdfs(arxiv_ids: list[str]) -> tuple[list[str], str]:
    """Download PDFs for a list of arXiv ids.

    Args:
        arxiv_ids: List of arXiv ids (e.g. "2401.01234") or arXiv URLs.

    Returns:
        A tuple:
            - list[str]: ids successfully downloaded
            - str: status log of successes/failures
    """
    downloaded: list[str] = []
    status = ""

    for arxiv_id, result in _download_papers(arxiv_ids, directory=ARXIV_PAPERS_DIR):
        if isinstance(result, Exception):
            status += f"Failed to download '{arxiv_id}': {type(result).__name__}: {result}\n"
        else:
            status += f"Downloaded '{arxiv_id}'\n"
            downloaded.append(arxiv_id)

    return downloaded, status

# @tool
def read_pdf(arxiv_id:str) -> str:
    """Read PDF for an arXiv id.

    Args:
        arxiv_id: some arXiv id (e.g. "2401.01234") or arXiv URL.

    Returns:
        A text, markdown-encoded readable version of the pdf
    """

    norm_id = _normalize_arxiv_id(arxiv_id)
    return pdf_scraper.read_pdf(input_dir=ARXIV_PAPERS_DIR, input_name=norm_id, store_dir=ARXIV_MD_DIR)

# export tools as an object list
tools = [search_arxiv, download_pdfs, read_pdf]
