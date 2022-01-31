import os
import re

from werkzeug import utils

# Typing
from cgi import FieldStorage

valid_pattern = "^[A-Za-z0-9]+-[A-Za-z0-9]+.pdf$"
error = "Upload not successful: format of filename should be REPORT-COMPANY.pdf (e.g. annual-blackrock.pdf)"

def save_pdf(file:FieldStorage, directory = '.tmp'):

    match = re.fullmatch(valid_pattern, file.filename)

    if not match:
        return error, False

    filepath = os.path.join(
        directory, 
        utils.secure_filename(file.filename)
    )

    file.save(filepath)

    return filepath, True
    