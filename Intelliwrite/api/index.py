from aeo_blog_engine.api import app

# Vercel expects one of these
application = app

@app.route("/")
def home():
    return "IntelliWrite API is running 🚀"

@app.route("/ping")
def ping():
    return "pong"
