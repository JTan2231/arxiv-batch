import hashlib
import logging
import os
import re
import shutil
import unicodedata

import requests
from bs4 import BeautifulSoup
from tika import parser

format_string = (
    "%(asctime)s - %(filename)s.%(funcName)s:"
    + "%(lineno)d [%(levelname)s]: %(message)s"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/yangnet.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(format_string))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

console_handler.setFormatter(logging.Formatter(format_string))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def clean_string(s):
    s = strip_accents(s)
    s = s.strip("\r")

    return s


def parse_pdf(pdf_path):
    parsed = parser.from_file(pdf_path)
    content = parsed["content"]
    logger.info(f"tika parsed {pdf_path}")

    return content


def get_citations(content):
    options = ["References", "REFERENCES"]

    reference_split = ""
    for o in options:
        if o in content:
            reference_split = content.split(o)[-1]

    reference_split = clean_string(reference_split)
    content = clean_string(content)

    authors = "([A-Za-z,\n .\-]+)"
    title = "([A-Za-z–0-9:\- \n]+)"
    journal = "([A-Za-z–0-9:\- .,()&]+)(?=, [A-Za-z]{0,5} ?[0-9]{4}\.)"
    date = "(, [A-Za-z]{0,5} ?[0-9]{4}\.)"
    citation_regex = rf"({authors}\.\s{title}\.\s{journal}{date})"

    citations = []

    citation = re.compile(citation_regex)
    for match in re.findall(citation, content):
        citations.append(match[0])

    return citations


def hash_string(string):
    encoded = string.encode()
    hashed = hashlib.sha256(encoded)
    hex = hashed.hexdigest()

    return hex


def get_papers(limit=10):
    papers = []

    os.makedirs("./pdfs")
    try:
        logger.info("getting new articles from https://arxiv.org/list/cs/new")

        html = requests.get("https://arxiv.org/list/cs/new").text
        soup = BeautifulSoup(html, "html.parser")
        pdfs = soup.find_all("a", title="Download PDF")

        logger.info(f"retrieved links for {len(pdfs)} articles")

        links = []
        for f in pdfs:
            links.append(f.get("href"))

        logger.info(f"retrieving and processing up to {limit} articles")
        for i in range(limit):
            if i < len(links):
                pdf_url = "http://arxiv.org" + links[i] + ".pdf"
                logger.info(f"retrieving {pdf_url}")

                title = links[i].split("/")[2]
                content = requests.get(pdf_url).content

                with open(f"./pdfs/{title}.pdf", "wb") as f:
                    f.write(content)
            else:
                break

        for pdf in os.listdir("./pdfs"):
            content = parse_pdf(os.path.join("./pdfs", pdf))
            papers.append(
                {
                    "title": ".".join(pdf.split(".")[:-1]),
                    "content": content,
                    "abstract": "",  # TODO
                    "citations": get_citations(content),
                    "hash": hash_string(content),
                }
            )

    except Exception as e:
        logger.error(f"error in get_papers: {e}")
        print(f"error in get_papers: {e}")

    shutil.rmtree("./pdfs")

    return papers


try:
    papers = get_papers()
    logger.info(f"parsed {len(papers)} papers, sending to API")

    url = "http://localhost:5000/add-papers"
    response = requests.post(url, json=papers)
    if response.status_code != 200:
        logger.warning(
            f"papers sent to {url} returned "
            + f"status code {response.status_code}, response: {response.text}"
        )
    else:
        logger.info(f"{response.text}")
except BaseException as e:
    logger.exception("Unexpected error occurred: %s", str(e))
