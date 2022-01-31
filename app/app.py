import os

from flask import Flask, Response, render_template, request
from flask_basicauth import BasicAuth

from dotenv import load_dotenv
load_dotenv()

from . import db, read_pdf, saliency_metric, topic, utils

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    DATABASE=os.path.join(app.instance_path, 'saliency.sqlite'),
    BASIC_AUTH_USERNAME=os.environ.get("BASIC_AUTH_USERNAME"),
    BASIC_AUTH_PASSWORD=os.environ.get("BASIC_AUTH_PASSWORD")
)

basic_auth = BasicAuth(app)

# ensure the instance and tmp folder exists
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(".tmp", exist_ok=True)

@app.route('/joke')
def hello_joke():
    return "I only know 25 letters of the alphabet. I don't know y."

@app.before_first_request
def initialize_database():
    db.init_db()

@app.route('/')
@basic_auth.required
def upload_file():

    return render_template('upload.html')

@app.route('/uploader', methods = ['GET', 'POST'])
@basic_auth.required
def parse_file():
    if request.method == 'POST':
        f = request.files['file']

        filepath, success = utils.save_pdf(f)

        if not success:
            return filepath

        sentences = read_pdf.path_to_sentences(filepath)
        lda, corpus, words = topic.get_topics(sentences)
        saliencies = saliency_metric.saliency_index(lda, corpus, words) 

        report, company = f.filename.lower().replace(".pdf", "").split("-")

        db.add_to_saliency(report, company, saliencies)

        os.remove(filepath)

        return "Done!"


    return "Done nothing, have a good day!"

@app.route('/download')
@basic_auth.required
def download():
    
    csvraw = db.data_as_csv()

    return Response(
        csvraw,
        mimetype="text/csv",
        headers = { "Content-disposition": "attachment; filename = saliency.csv" }
    )


@app.route('/clear')
@basic_auth.required
def clear_db():
    instance = app.config.get("DATABASE")
    
    if os.path.isfile(instance):
        db.init_db()
        return "Cleared db"
    else:
        return f"DB instance not found at {instance}"

    