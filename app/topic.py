import pandas as pd
from gensim.models.ldamodel import LdaModel
from gensim.corpora import Dictionary

from typing import List, Tuple, NewType

Topics = NewType("Topics", Tuple[LdaModel, List[Tuple[int, int]], Dictionary])

def get_topics(sentences:List[str], **kwargs) -> Topics:
    """
    Parses a list of words (assumed to be a sentence) using a
    LdaModel, returns the model and the gensim corpus.
    """
    words = Dictionary(sentences)

    corpus = [words.doc2bow(doc) for doc in sentences]

    lda_model = LdaModel(corpus=corpus, id2word=words, alpha='auto', **kwargs)

    return lda_model, corpus, words

def format_topics_sentences(ldamodel, corpus, sentences) -> pd.DataFrame:
    
    sent_topics_df = pd.DataFrame()

    for row_list in ldamodel[corpus]:
        row = row_list[0] if ldamodel.per_word_topics else row_list            
        row = sorted(row, key=lambda x: (x[1]), reverse=True)

        for j, (topic_num, prop_topic) in enumerate(row):
            if j == 0: 
                wp = ldamodel.show_topic(topic_num)
                topic_keywords = ", ".join([word for word, prop in wp])
                sent_topics_df = sent_topics_df.append(pd.Series([int(topic_num), round(prop_topic,6), topic_keywords]), ignore_index=True)
            else:
                break
                
    sent_topics_df.columns = ['Dominant_Topic', 'Perc_Contribution', 'Topic_Keywords']

    contents = pd.Series(sentences)
    sent_topics_df = pd.concat([sent_topics_df, contents], axis=1)

    return sent_topics_df


def find_keywords(df, keywords = set(["climate", "change", "environment", "sustainable"])):
    
    df = df.sort_values("Dominant_Topic").reset_index(drop = True)
    
    impact_factor = 0.
    contr = 0.
    
    for row, kwds in enumerate(df["Keywords"]):
        
        found = False
        
        for k in kwds.split(', '):
            if k in keywords:
                found = True
                
        if found:
            impact_factor += df["Dominant_Topic"][row]
            contr += df["Topic_Perc_Contrib"][row]

        found = False
        
    return impact_factor / sum(df["Dominant_Topic"]), np.mean(contr)