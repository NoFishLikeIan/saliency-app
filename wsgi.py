import os
from flask_sslify import SSLify

from app import app, db

if __name__ == "__main__":
    with app.app_context():
        db.init_db()

    if 'DYNO' is os.environ:
        app = SSLify(app)
        
    app.run()