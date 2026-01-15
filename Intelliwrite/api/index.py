from aeo_blog_engine.api import app

# Vercel expects 'app', 'application', or 'handler'
application = app

# Debug route to verify index.py is loaded
@app.route("/ping")
def ping():
    return "pong"

# Print registered routes to logs (visible in Vercel functions logs)
print("Registered Routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule} -> {rule.endpoint}")

if __name__ == "__main__":
    app.run(debug=True)
