from app import app, db

if __name__ == "__main__":
    db.init_db()
    app.run()