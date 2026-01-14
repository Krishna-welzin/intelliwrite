from typing import Dict

from aeo_blog_engine.database import create_blog_entry, get_blog_by_id, get_session, update_blog_status, save_social_post, Blog
from aeo_blog_engine.pipeline.blog_workflow import AEOBlogPipeline


pipeline = AEOBlogPipeline()


def generate_and_store_blog(payload: Dict) -> Dict:
    # Allow prompt instead of topic
    if not payload.get("topic") and not payload.get("prompt"):
        raise ValueError("Missing required field: 'topic' or 'prompt'")
    
    if not payload.get("company_url"):
        raise ValueError("Missing required field: 'company_url'")

    topic = payload.get("topic")
    prompt = payload.get("prompt")
    
    # Step 0: If only prompt is provided, generate the topic first
    if prompt and not topic:
        # Use the pipeline helper to generate the topic
        topic = pipeline.generate_topic_only(prompt)

    topic = topic.strip()
    company_url = payload["company_url"].strip()
    email_id = payload.get("email_id")
    brand_name = payload.get("brand_name")

    with get_session() as session:
        blog_entry = create_blog_entry(
            session,
            topic=topic,
            company_url=company_url,
            email_id=email_id,
            brand_name=brand_name,
            status="PENDING",
        )
        blog_id = blog_entry.id

    try:
        # Run the pipeline with the finalized topic
        blog_content = pipeline.run(topic)
        with get_session() as session:
            updated = update_blog_status(
                session,
                blog_id,
                status="COMPLETED",
                blog_content=blog_content,
            )
            return updated.to_dict()
    except Exception as exc:
        with get_session() as session:
            update_blog_status(
                session,
                blog_id,
                status="FAILED",
            )
        raise exc


def fetch_blog(blog_id: int) -> Dict:
    with get_session() as session:
        blog = get_blog_by_id(session, blog_id)
        if not blog:
            raise ValueError(f"Blog with id {blog_id} not found")
        return blog.to_dict()


def store_social_post(topic: str, platform: str, content: str) -> Dict:
    """
    Finds the latest blog entry for the given topic and updates it with the social post.
    If no blog entry exists, it creates a new placeholder entry.
    """
    with get_session() as session:
        # Find latest blog for this topic
        blog = session.query(Blog).filter(Blog.topic == topic).order_by(Blog.created_at.desc()).first()
        
        if not blog:
            # Create a placeholder entry if none exists (fallback)
            blog = create_blog_entry(
                session,
                topic=topic,
                company_url="unknown", # Placeholder
                status="SOCIAL_ONLY"
            )
        
        updated_blog = save_social_post(session, blog.id, platform, content)
        return updated_blog.to_dict()
