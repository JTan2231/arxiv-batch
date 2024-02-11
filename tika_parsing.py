import re
import unicodedata
from tika import parser

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def clean_string(s):
    s = strip_accents(s)
    s = s.strip('\r')

    return s

parsed = parser.from_file('./iclr/pdf.pdf')
content = parsed['content']

options = ['References', 'REFERENCES']

reference_split = ''
for o in options:
    if o in content:
        print(f'found {o}')
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

print(reference_split[:1000])

citation = re.compile(citation_regex)
for match in re.findall(citation, reference_split):
    print(f'CITATION: {match[0]}')
    print()
    count += 1

print(f'{count} citations')
print(repr(citation_regex))
