import os
import json 

from dotenv import load_dotenv, find_dotenv

from math import log
from itertools import chain

from gensim.models.ldamodel import LdaModel
from gensim.corpora.dictionary import Dictionary

from parse_reports import read_sentences
from nlp import topic


def saliency_index(lda: LdaModel, corpus, words: Dictionary):

    full_corpus = list(chain(*corpus))

    N = len(words)
    total = sum(words.cfs[i] for i in range(N))
    frequencies = [words.cfs[i] / total for i in range(N)]

    relative_likelihood = [0. for _ in range(N)]

    for topic_id, topic_prob in lda.get_document_topics(full_corpus, minimum_probability=0.):
        for term, cond_prob in lda.get_topic_terms(topic_id, topn = None):

            relative_likelihood[term] += cond_prob * log(cond_prob / topic_prob)


    saliencies = [f * l for f, l in zip(frequencies, relative_likelihood)]

    return { words[i]: s for i, s in enumerate(saliencies) }

if __name__ == '__main__':

    load_dotenv(find_dotenv())
    VERBOSE = os.environ.get("VERBOSE", "False") == "True"
    SENTENCES = os.environ.get("SENTENCES")

    companies = {}

    for sentences, filename in read_sentences(SENTENCES):

        company, extension = os.path.splitext(filename) 

        VERBOSE and print(f"Working on {company}...")

        if len(sentences[0]) > 0:

            lda, corpus, words = topic.get_topics(sentences)

            saliencies = saliency_index(lda, corpus, words) 

            companies[company] = saliencies

        else:
            VERBOSE and print(f"{company} has empty sentences...")

    VERBOSE and print("Writing results...")

    with open("data/saliency.json", "w") as outfile:

        json.dump(companies, outfile)

    VERBOSE and print("...done!")