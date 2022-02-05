import os
from sqlite3 import connect
import pandas as pd
import psycopg2

from dotenv import load_dotenv

load_dotenv()

def get_db():

    conn = psycopg2.connect(
        host = 'localhost',
        database = os.environ.get('DATABASE'),
        user = os.environ.get('DB_USERNAME'),
        password = os.environ.get('KEY')
    )
    
    return conn


def add_to_saliency(report, company, saliencies, tol = 1e-4):
    with get_db() as connection:
        with connection.cursor() as cur:
            for word, score in saliencies.items():
                if score > tol:
                    cur.execute(
                        'INSERT INTO saliency VALUES (%s, %s, %s, %s)',
                        (report, company, word, score)
                    )



def query_db(query:str) -> pd.DataFrame:
    with get_db() as conn:
        data = pd.read_sql_query(query, conn)

    return data

def data_as_csv(query):
    data = query_db(query)

    csv = data.to_csv(index = False)

    return csv


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur = conn.cursor()

            cur.execute('DROP TABLE IF EXISTS saliency;')
            cur.execute("""
            CREATE TABLE saliency (
                report TEXT NOT NULL,
                company TEXT NOT NULL,
                word TEXT NOT NULL,
                score REAL NOT NULL
            );
            """)