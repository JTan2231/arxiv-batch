import re
import unicodedata
import os,shutil
import requests
from tika import parser
from bs4 import BeautifulSoup

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def clean_string(s):
    s = strip_accents(s)
    s = s.strip('\r')

    return s

def get_citations(pdf_path):
    parsed = parser.from_file(pdf_path)
    content = parsed['content']

    options = ['References', 'REFERENCES']

    reference_split = ''
    for o in options:
        if o in content:
            #print(f'found {o}')
            reference_split = content.split(o)[-1]

    if len(reference_split) > 0:
        page_number = re.search(r'[0-9]+\n', reference_split)
        end = page_number.start() if page_number else -1

    reference_split = clean_string(reference_split)
    content = clean_string(content)

    count = 0

    authors = '([A-Za-z,\n .\-]+)'
    title = '([A-Za-z–0-9:\- \n]+)'
    journal = '([A-Za-z–0-9:\- .,()&]+)(?=, [A-Za-z]{0,5} ?[0-9]{4}\.)'
    date = '(, [A-Za-z]{0,5} ?[0-9]{4}\.)'
    citation_regex = rf"({authors}\.\s{title}\.\s{journal}{date})"

    #print(reference_split[:1000])

    out = { "Citations" : [] }

    citation = re.compile(citation_regex)
    for match in re.findall(citation, reference_split):
        #print(f'CITATION: {match[0]}')
        #print()
        out["Citations"].append(match[0])
        count += 1

    #print(f'{count} citations')
    #print(repr(citation_regex))
    
    return out


def get_papers():
    try:
        os.makedirs('./pdfs')
        html = requests.get('https://arxiv.org/list/cs/new').text
        soup = BeautifulSoup(html,'html.parser')
        pdfs = soup.find_all('a',title="Download PDF")
        links = []
        for f in pdfs: links.append(f.get('href'))

        for i in range(10):
            if i < len(links):
                title = links[i].split("/")[2]
                content = requests.get("http://arxiv.org" + links[i] + ".pdf").content
                with open(f'./pdfs/{title}.pdf', "wb") as f:
                    f.write(content)
            else:
                break

        for pdf in os.listdir('./pdfs'):
            file_path = os.path.join('./pdfs',pdf)
            print(file_path)
            print(get_citations(file_path))

    finally:
        print("done")
        shutil.rmtree('./pdfs')


get_papers()
