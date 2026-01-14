from flask import Flask, jsonify, request
import os
from werkzeug.utils import secure_filename

from aeo_blog_engine.database import get_blog_by_id, get_session
from aeo_blog_engine.services import generate_and_store_blog
from aeo_blog_engine.knowledge.ingest import ingest_docs
from aeo_blog_engine.pipeline.blog_workflow import AEOBlogPipeline

app = Flask(__name__)

# Configure upload folder
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
            "POST /ingest",
            "POST /generate-social"
        ]
    })


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/ingest", methods=["POST"])
def ingest_knowledge():
    """
    Triggers knowledge base ingestion.
    Optionally accepts file uploads (multipart/form-data) to add to the knowledge base before ingesting.
    """
    uploaded_files = []
    
    # Handle file uploads if present
    if "files" in request.files:
        files = request.files.getlist("files")
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
                uploaded_files.append(filename)
    
    try:
        # Trigger the ingestion process
        ingest_docs()
        
        response = {
            "status": "success", 
            "message": "Knowledge base ingested successfully",
        }
        
        if uploaded_files:
            response["uploaded_files"] = uploaded_files
            
        return jsonify(response), 200
        
    except Exception as exc:
        return jsonify({"error": "Failed to ingest knowledge", "details": str(exc)}), 500


@app.route("/blogs", methods=["POST"])
def create_blog():
    data = request.get_json(force=True)
    try:
        result = generate_and_store_blog(data)
        return jsonify(result), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": "Failed to generate blog", "details": str(exc)}), 500


@app.route("/generate-social", methods=["POST"])
def generate_social_post():
    """
    Generates a social media post for a given topic and platform.
    Expected JSON body: {"topic": "...", "platform": "twitter|reddit|linkedin"}
    """
    data = request.get_json(force=True)
    
    topic = data.get("topic")
    platform = data.get("platform")
    
    if not topic or not platform:
        return jsonify({"error": "Both 'topic' and 'platform' are required."}), 400
        
    valid_platforms = ["reddit", "linkedin", "twitter"]
    if platform.lower() not in valid_platforms:
        return jsonify({"error": f"Invalid platform. Choose from: {valid_platforms}"}), 400

    try:
        pipeline = AEOBlogPipeline()
        post_content = pipeline.run_social_post(topic, platform)
        
        return jsonify({
            "status": "success",
            "topic": topic,
            "platform": platform,
            "content": post_content
        }), 200
        
    except Exception as exc:
        return jsonify({"error": "Failed to generate social post", "details": str(exc)}), 500


@app.route("/blogs/<int:blog_id>", methods=["GET"])
def get_blog(blog_id):
    with get_session() as session:
        blog = get_blog_by_id(session, blog_id)
        if not blog:
            return jsonify({"error": "Blog not found"}), 404
        return jsonify(blog.to_dict())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
