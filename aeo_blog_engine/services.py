from typing import Dict

from aeo_blog_engine.database import (
    Blog,
    append_social_post,
    create_blog_entry,
    get_blog_by_id,
    get_session,
    get_blog_by_user_and_company,
    update_blog_status,
)
from aeo_blog_engine.pipeline.blog_workflow import AEOBlogPipeline


pipeline = AEOBlogPipeline()


def _get_or_create_blog(session, *, user_id: str, company_url: str, topic: str, email_id=None, brand_name=None):
    blog = get_blog_by_user_and_company(session, user_id=user_id, company_url=company_url)
    if blog:
        # Ensure topic is tracked
        topics = Blog.ensure_entries(blog.topic)
        contents = Blog.entry_contents(topics)
        if topic and topic not in contents:
            topics.append(Blog.make_entry(topic))
            blog.topic = topics
        session.add(blog)
        session.flush()
        return blog

    return create_blog_entry(
        session,
        user_id=user_id,
        topic=topic,
        company_url=company_url,
        email_id=email_id,
        brand_name=brand_name,
        status="PENDING",
    )


def generate_and_store_blog(payload: Dict) -> Dict:
    # Allow prompt instead of topic
    if not payload.get("topic") and not payload.get("prompt"):
        raise ValueError("Missing required field: 'topic' or 'prompt'")

    if not payload.get("company_url"):
        raise ValueError("Missing required field: 'company_url'")

    if not payload.get("user_id"):
        raise ValueError("Missing required field: 'user_id'")

    topic = payload.get("topic")
    prompt = payload.get("prompt")

    # Step 0: If only prompt is provided, generate the topic first
    if prompt and not topic:
        # Use the pipeline helper to generate the topic
        topic = pipeline.generate_topic_only(prompt)

    topic = topic.strip()
    company_url = payload["company_url"].strip()
    user_id = payload["user_id"].strip()
    email_id = payload.get("email_id")
    brand_name = payload.get("brand_name")

    with get_session() as session:
        blog_entry = _get_or_create_blog(
            session,
            user_id=user_id,
            topic=topic,
            company_url=company_url,
            email_id=email_id,
            brand_name=brand_name,
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
                topic=topic,
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


def store_social_post(user_id: str, company_url: str, topic: str, platform: str, content: str) -> Dict:
    """
    Finds or creates the blog entry for the given user/company and updates it with the social post.
    """
    with get_session() as session:
        blog = _get_or_create_blog(
            session,
            user_id=user_id,
            company_url=company_url,
            topic=topic,
        )
        append_social_post(session, blog, platform, content)
        return blog.to_dict()
