import os
import csv
import pandas as pd

from flask import Flask, Response, render_template, request
from werkzeug.utils import secure_filename

from . import db, read_pdf, saliency_metric, topic

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'saliency.sqlite'),
)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

@app.route('/joke')
def hello_joke():
    return "I only know 25 letters of the alphabet. I don't know y."


@app.route('/')
def upload_file():

    conn = db.get_db()
    curs = conn.cursor()

    curs.execute("INSERT INTO saliency VALUES (?, ?, ?, ?)", ["test", "test", "test", 2.12]) # FIXME: db not saved

    conn.close()

    return render_template('upload.html')

@app.route('/uploader', methods = ['GET', 'POST'])
def parse_file():
    if request.method == 'POST':
        f = request.files['file']
        filepath = os.path.join('.tmp', secure_filename(f.filename))

        f.save(filepath)
        sentences = read_pdf.path_to_sentences(filepath)
        lda, corpus, words = topic.get_topics(sentences)
        saliencies = saliency_metric.saliency_index(lda, corpus, words) 

        filedata = f.filename.replace(".pdf", "").split("-")

        if len(filedata) != 2:
            return "Upload not successful: format of file should be REPORT-COMPANY.pdf"

        report, company = [s.lower() for s in filedata]

        db.add_to_saliency(report, company, saliencies)

        os.remove(filepath)

        return "Done!"


    return "Done nothing, have a good day!"

@app.route('/download', methods = ['GET', 'POST'])
def download():
    tmppath = os.path.join(".tmp", "data.csv")

    conn = db.get_db()

    data = pd.read_sql_query("SELECT * FROM saliency", conn)

    data.to_csv(tmppath, index = False)

    with open(tmppath, 'r') as fp:
        csvraw = fp.read()

    conn.close()
    os.remove(tmppath)

    return Response(
        csvraw,
        mimetype="text/csv",
        headers = { "Content-disposition": "attachment; filename = saliency.csv" }
    )

db.init_app(app)
    