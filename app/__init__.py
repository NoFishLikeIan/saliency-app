import os
import requests

from flask import Flask, Response, flash, url_for
from flask import render_template, request, redirect
from flask_basicauth import BasicAuth

from dotenv import load_dotenv
load_dotenv()

from . import db, read_pdf, saliency_metric, topic, utils

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

        if 'file' not in request.files:
            flash('No file!')
            return redirect(request.url)

        file = request.files['file']
        filepath, success = utils.save_pdf(file)

        if not success:
            return filepath

        sentences = read_pdf.path_to_sentences(filepath)
        lda, corpus, words = topic.get_topics(sentences)
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