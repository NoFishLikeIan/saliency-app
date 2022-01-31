import PyPDF2
import nltk
import os

import re, io, os, requests
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer,PorterStemmer
from nltk.corpus import stopwords

from typing import List

nltk.download(["punkt", "wordnet", "stopwords", "omw-1.4"])

lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer() 

def preprocess(sentence):
    sentence=str(sentence)
    sentence = sentence.lower()
    sentence = sentence.replace('{html}',"") 
    cleantext = re.sub(re.compile('<.*?>'), '', sentence)
    rem_url=re.sub(r'http\S+', '',cleantext)
    rem_num = re.sub('[0-9]+', '', rem_url)
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(rem_num)  
    filtered_words = [w for w in tokens if len(w) > 2 if not w in stopwords.words('english')]

    stem_words=[stemmer.stem(w) for w in filtered_words]

    lemma_words=[lemmatizer.lemmatize(w) for w in stem_words]

    return " ".join(lemma_words)

def is_url(to_validate):

    url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(url_regex, to_validate) is not None

def extract_statements(text):
    
    return [nltk.word_tokenize(preprocess(sent)) for sent in nltk.sent_tokenize(text)]


def pdf_to_text(pdf):
    text = ""
    n_pages = pdf.getNumPages()

    for i in range(n_pages):
        page = pdf.getPage(i)

        page_text = page.extractText()

        text += f"{page_text}\n"

    return text


def pdfreader_decrypt(filename):
    """
    https://stackoverflow.com/a/48364988
    """    
    with open(filename, "rb") as fp:
        pdfFile  = PyPDF2.PdfFileReader(fp, strict=False)

        if pdfFile.isEncrypted:
            try:
                pdfFile.decrypt('')
                print('File Decrypted (PyPDF2)')

                return pdf_to_text(pdfFile)
            except:
                command = f'cp "{filename}" temp.pdf; qpdf --password="" --decrypt temp.pdf "{filename}"; rm temp.pdf'

                os.system(command)
                print('File Decrypted (qpdf)')

                with open(filename, "rb") as fp:
                    pdfFile = PyPDF2.PdfFileReader(fp, strict=False)
                    return pdf_to_text(pdfFile)

        return pdf_to_text(pdfFile)


def path_to_sentences(filepath: str) -> List[str]:

    text = ""

    if os.path.isfile(filepath):       
        text = pdfreader_decrypt(filepath)

    else:
        response = requests.get(filepath)

        with io.BytesIO(response.content) as file:
            pdf = PyPDF2.PdfFileReader(file, strict=False)
            text = pdf_to_text(pdf)
    
    return extract_statements(text)