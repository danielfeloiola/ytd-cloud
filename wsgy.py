from app import app
if __name__ == "__main__":
    app.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))