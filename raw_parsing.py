import re
import zlib

REFERENCE_HEADERS = {
    'ICLR': 'REFERENCES'
}

def text_from_raw_pdf(text):
    c = 0
    def inBounds():
        return c < len(text)

    output = ''
    while inBounds():
        if text[c] == '(':
            c += 1
            while inBounds() and text[c] != ')':
                output += text[c]
                c += 1

            c += 1

            # is there a number?
            if inBounds() and text[c] != ']':
                num = ''
                while inBounds() and text[c] == '-' or text[c].isnumeric():
                    num += text[c]
                    c += 1

                if len(num) > 0:
                    num = abs(int(num))
                    if num > 100:
                        output += ' '

        else:
            c += 1

    return output

def parse_iclr(filename):
    def decode_pdf(filename):
        pdf = open(f'{filename}.pdf', 'rb').read()
        stream = re.compile(rb'.*?FlateDecode.*?stream(.*?)endstream', re.S)

        pdf_decoded = ''
        for s in stream.findall(pdf):
            if '/Image' in s:
                continue

            s = s.strip(b'\n')
            try:
                decoded = zlib.decompress(s).decode()
                pdf_decoded += decoded
            except:
                pass

        with open(f'{filename}.decoded', 'w') as f:
            f.write(pdf_decoded)
        
        exit()

        return pdf_decoded

    def count_alpha(string):
        count = 0
        for c in string:
            count += c.isalpha()

        return count

    # this *should* only capture letters enclosed in parenthesis
    def extract_title(string):
        i = 0
        def bounded():
            return i < len(string)

        title = ''
        while bounded():
            if string[i] == '(':
                i += 1
                while bounded() and string[i] != ')':
                    title += string[i]
                    i += 1
            else:
                i += 1

        return title

    def get_references_raw(pdf_decoded):
        header_regex = re.compile(r'(\[(\(([A-Z])\)?(-[0-9]*)?)*\]TJ)')
        headers = []
        for t in header_regex.finditer(pdf_decoded):
            match = t.group()
            index = t.start()
            if count_alpha(match) > 3:
                headers.append((extract_title(match), index))

        references_start = -1
        header_index = -1
        for i, t in enumerate(headers):
            if t[0] in REFERENCE_HEADERS['ICLR']:
                references_start = t[1]
                header_index = i

        references_raw = ''
        if header_index > -1 and header_index < len(headers):
            references_end = headers[header_index + 1][1]
            references_raw = pdf_decoded[references_start:references_end]
        elif header_index == -1:
            print("error: no references!")
            exit(-1)
        else:
            references_raw = pdf_decoded[references_start:]

        return references_raw

    def references_from_raw(references_raw):
        def trim_journal_in(text):
            keywords = [' In', '.In', '. In']
            for keyword in keywords:
                if keyword in text:
                    text = text[:text.rfind(keyword)]
                    return text

            return text

        delimiter = re.compile(r'\/F[0-9]* [0-9.]* Tf')

        references = []
        for line in references_raw.split('\n'):
            split = re.split(delimiter, line)
            if len(split) > 1:
                text = text_from_raw_pdf(split[0])
                if len(text) > 0:
                    text = trim_journal_in(text)
                    split = [s for s in text.split('.') if len(s) > 0]

                    authors = split[:-1]
                    title = split[-1]
                    references.append({
                        'authors': ' '.join(authors),
                        'title': title
                    })

        return references

    references_raw = get_references_raw(decode_pdf(filename))
    references = references_from_raw(references_raw)
    for ref in references:
        print(f'authors: {ref["authors"]}')
        print(f'title: {ref["title"]}')
        print()

def parse_ieee(filename):
    def decode_pdf(filename):
        pdf = open(f'{filename}.pdf', 'rb').read()
        stream = re.compile(rb'.*?FlateDecode.*?stream(.*?)endstream', re.S)

        pdf_decoded = ''
        for s in stream.findall(pdf):
            s = s.strip(b'\n')
            try:
                decoded = zlib.decompress(s).decode()
                pdf_decoded += decoded
            except:
                pass

        with open(f'{filename}.decoded', 'w') as f:
            f.write(pdf_decoded)

        return pdf_decoded

    def count_alpha(string):
        count = 0
        for c in string:
            count += c.isalpha()

        return count

    # this *should* only capture letters enclosed in parenthesis
    def extract_title(string):
        i = 0
        def bounded():
            return i < len(string)

        title = ''
        while bounded():
            if string[i] == '(':
                i += 1
                while bounded() and string[i] != ')':
                    title += string[i]
                    i += 1
            else:
                i += 1

        return title

    def get_references_raw(pdf_decoded):
        header_regex = re.compile(r'(\[\(REFERENCES\)\]TJ)')
        headers = []
        for t in header_regex.finditer(pdf_decoded):
            match = t.group()
            index = t.start()
            if count_alpha(match) > 3:
                headers.append((extract_title(match), index))

        references_start = -1
        header_index = -1
        for i, t in enumerate(headers):
            if t[0] in REFERENCE_HEADERS['ICLR']:
                references_start = t[1]
                header_index = i

        references_raw = ''
        if header_index > -1 and header_index < len(headers):
            references_end = headers[header_index + 1][1]
            references_raw = pdf_decoded[references_start:references_end]
        elif header_index == -1:
            print("error: no references!")
            exit(-1)
        else:
            references_raw = pdf_decoded[references_start:]

        return references_raw

    def references_from_raw(references_raw):
        def trim_journal_in(text):
            keywords = [' In', '.In', '. In']
            for keyword in keywords:
                if keyword in text:
                    text = text[:text.rfind(keyword)]
                    return text

            return text

        delimiter = re.compile(r'\/F[0-9]* [0-9.]* Tf')

        references = []
        for line in references_raw.split('\n'):
            split = re.split(delimiter, line)
            if len(split) > 1:
                text = text_from_raw_pdf(split[0])
                if len(text) > 0:
                    text = trim_journal_in(text)
                    split = [s for s in text.split('.') if len(s) > 0]

                    authors = split[:-1]
                    title = split[-1]
                    references.append({
                        'authors': ' '.join(authors),
                        'title': title
                    })

        return references

    references_raw = get_references_raw(decode_pdf(filename))
    references = references_from_raw(references_raw)
    for ref in references:
        print(f'authors: {ref["authors"]}')
        print(f'title: {ref["title"]}')
        print()

filename = 'mono'
with open(f'ieee/{filename}.pdf', 'rb') as f:
    with open(f'{filename}.raw', 'wb') as out:
        out.write(f.read())

parse_iclr(f'ieee/{filename}')
