import os
import pathlib
import requests
import sys

from flask import Flask, Response, flash, url_for
from flask import render_template, request, redirect
from flask_basicauth import BasicAuth

from dotenv import load_dotenv
load_dotenv()

from . import db, read_pdf, saliency_metric, topic, utils

# Logging
import logging
from time import time
from datetime import datetime

log_file = pathlib.Path(os.environ.get("LOG_PATH", "logs")) / "app.log"
if not log_file.parent.is_dir():
    log_file.parent.mkdir(parents = True)

if not log_file.exists():
    log_file.touch()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

logging.basicConfig(filename=log_file, level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    DATABASE=os.path.join("DATABASE_URL"),
    BASIC_AUTH_USERNAME=os.environ.get("BASIC_AUTH_USERNAME"),
    SECRET_KEY=os.environ.get("KEY"),
    BASIC_AUTH_PASSWORD=os.environ.get("BASIC_AUTH_PASSWORD")
)

basic_auth = BasicAuth(app)

# ensure the tmp folder exists
os.makedirs(".tmp", exist_ok=True)

@app.route('/joke')
def hello_joke():

    r = requests.get(
        'https://icanhazdadjoke.com/',
        headers={'Accept': 'text/plain'}
    )

    return r.text

@app.route('/')
def pass_by():
    return redirect(url_for('upload'))

@app.route('/upload', methods = ['GET', 'POST'])
@basic_auth.required
def upload():

    if request.method == 'POST':

        logging.info(f"{str(datetime.now())}: Received POST request.")

        files = request.files.getlist("file[]")
    
        logging.info(f"{str(datetime.now())}: Uploaded {len(files)} files.")

        for (idx, file) in enumerate(files):
            filepath, success = utils.save_pdf(file)

            if not success:
                return filepath

            logging.info(f"{str(datetime.now())}: Processing file {idx + 1} / {len(files)}.")
            logging.info(f"{str(datetime.now())}: Fitting LDA model.")
            sentences = read_pdf.path_to_sentences(filepath)
            lda, corpus, words = topic.get_topics(sentences)

            logging.info(f"{str(datetime.now())}: Computing saliency model.")
            saliencies = saliency_metric.saliency_index(lda, corpus, words) 

            report, company = file.filename.lower().replace(".pdf", "").split("-")

            db.add_to_saliency(report, company, saliencies)

            os.remove(filepath)

        flash("Done")
        redirect(url_for('upload'))

    return render_template('upload.html')


@app.route('/download')
@basic_auth.required
def download():
    
    csvraw = db.data_as_csv('SELECT * FROM saliency')

    return Response(
        csvraw,
        mimetype="text/csv",
        headers = { "Content-disposition": "attachment; filename = saliency.csv" }
    )

@app.route('/preview')
@basic_auth.required
def preview():
    df = db.query_db('SELECT DISTINCT report, company FROM saliency ORDER BY company')

    records = df.to_records(index=False)

    return f"Current uploads: {records}"


@app.route('/clear')
@basic_auth.required
def clear_db():
    db.init_db()

    return 'Done!'

if __name__ == "__main__":
    with app.app_context():
        db.init_db()
        
    app.run()