import os
import json

from flask import Flask, render_template, request
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

        with open('.tmp/test.json', 'w') as outfile:
            json.dump(saliencies, outfile)


        os.remove(filepath)

        return "Done!"


    return "Have a good day!"

db.init_app(app)
    