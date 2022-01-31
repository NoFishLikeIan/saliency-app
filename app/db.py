import sqlite3
import os
import pandas as pd

from flask import current_app, g

def get_db():

    db = getattr(g, '_database', None)

    if db is None:
        g._database = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g._database.row_factory = sqlite3.Row

        db = g._database

    return db

def close_connection():
    
    db = getattr(g, '_database', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def add_to_saliency(report, company, saliencies):
    db = get_db()
    cur = db.cursor()

    rows = saliency_to_sql(report, company, saliencies)

    cur.executemany(
        "INSERT INTO saliency VALUES (?, ?, ?, ?)",
        rows
    )

    db.commit()
    close_connection()

def saliency_to_sql(report, company, saliencies):
    """
    Maps to schema
    (
        report TEXT NOT NULL,
        company TEXT NOT NULL,
        word TEXT NOT NULL,
        score REAL NOT NULL
    );
    """

    rows = [
        (report, company, word, score) for
        word, score in saliencies.items()
    ]    

    return rows

def query_db(query:str) -> pd.DataFrame:
    conn = get_db()
    data = pd.read_sql_query(query, conn)
    close_connection()

    return data

def data_as_csv(query):
    data = query_db(query)

    csv = data.to_csv(index = False)

    return csv



