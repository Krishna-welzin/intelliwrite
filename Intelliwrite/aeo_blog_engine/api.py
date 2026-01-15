from flask import Flask, jsonify, request
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge", "docs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "AEO Blog Engine API is running",
        "endpoints": [
            "POST /blogs",
            "GET /blogs/<id>",
            "GET /blogs/latest",
            "GET /blogs/latest/topic",
            "GET /blogs/latest/social",
            "POST /ingest",
            "POST /generate-social"
        ]
    })


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/blogs/latest", methods=["GET"])
def get_latest_blog_full():
    from aeo_blog_engine.services import fetch_blog_by_user

    user_id = request.args.get("user_id")
    company_url = request.args.get("company_url")

    if not user_id or not company_url:
        return jsonify({"error": "Missing user_id or company_url parameters"}), 400

    blog = fetch_blog_by_user(user_id, company_url)
    if not blog:
        return jsonify({"error": "Blog not found"}), 404

    return jsonify(blog)


@app.route("/blogs/latest/topic", methods=["GET"])
def get_latest_blog_topic():
    from aeo_blog_engine.services import fetch_blog_by_user

    user_id = request.args.get("user_id")
    company_url = request.args.get("company_url")

    if not user_id or not company_url:
        return jsonify({"error": "Missing user_id or company_url parameters"}), 400

    blog = fetch_blog_by_user(user_id, company_url)
    if not blog:
        return jsonify({"error": "Blog not found"}), 404

    return jsonify({"topic": blog.get("topic", [])})


@app.route("/blogs/latest/social", methods=["GET"])
def get_latest_blog_social():
    from aeo_blog_engine.services import fetch_blog_by_user

    user_id = request.args.get("user_id")
    company_url = request.args.get("company_url")

    if not user_id or not company_url:
        return jsonify({"error": "Missing user_id or company_url parameters"}), 400

    blog = fetch_blog_by_user(user_id, company_url)
    if not blog:
        return jsonify({"error": "Blog not found"}), 404

    return jsonify({
        "twitter_post": blog.get("twitter_post", []),
        "linkedin_post": blog.get("linkedin_post", []),
        "reddit_post": blog.get("reddit_post", [])
    })


@app.route("/ingest", methods=["POST"])
def ingest_knowledge():
    from aeo_blog_engine.knowledge.ingest import ingest_docs

    uploaded_files = []

    if "files" in request.files:
        files = request.files.getlist("files")
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(path)
                uploaded_files.append(filename)

    ingest_docs()

    return jsonify({
        "status": "success",
        "uploaded_files": uploaded_files
    }), 200


@app.route("/blogs", methods=["POST"])
def create_blog():
    from aeo_blog_engine.services import generate_and_store_blog

    data = request.get_json(force=True)
    result = generate_and_store_blog(data)
    return jsonify(result), 201


@app.route("/generate-social", methods=["POST"])
def generate_social_post():
    from aeo_blog_engine.pipeline.blog_workflow import AEOBlogPipeline
    from aeo_blog_engine.services import store_social_post

    data = request.get_json(force=True)

    pipeline = AEOBlogPipeline()
    post_content = pipeline.run_social_post(
        data["topic"], data["platform"]
    )

    saved = store_social_post(
        data["user_id"],
        data["company_url"],
        data["topic"],
        data["platform"],
        post_content
    )

    return jsonify({
        "status": "success",
        "content": post_content,
        "blog": saved
    }), 200


@app.route("/blogs/<int:blog_id>", methods=["GET"])
def get_blog(blog_id):
    from aeo_blog_engine.database import get_blog_by_id, get_session

    with get_session() as session:
        blog = get_blog_by_id(session, blog_id)
        if not blog:
            return jsonify({"error": "Blog not found"}), 404
        return jsonify(blog.to_dict())
