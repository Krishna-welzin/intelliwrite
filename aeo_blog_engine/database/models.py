import json

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator

Base = declarative_base()


class JSONList(TypeDecorator):
    """Stores Python lists as JSON strings in Text columns."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            value = [value]
        return json.dumps(list(value))

    def process_result_value(self, value, dialect):
        if not value:
            return []
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return [value]


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Text, nullable=False)
    company_url = Column(Text, nullable=False)
    email_id = Column(Text)
    brand_name = Column(Text)
    blogs = Column("blog", JSONList, nullable=False, default=list)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    topic = Column(JSONList, nullable=True, default=list)
    status = Column(String, nullable=False, server_default="PENDING")
    
    # Social Media Content
    twitter_post = Column("twitter_post", JSONList, nullable=True, default=list)
    linkedin_post = Column("linkedin_post", JSONList, nullable=True, default=list)
    reddit_post = Column("reddit_post", JSONList, nullable=True, default=list)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_url": self.company_url,
            "email_id": self.email_id,
            "brand_name": self.brand_name,
            "blogs": self.blogs or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "topic": self.topic or [],
            "status": self.status,
            "twitter_post": self.twitter_post or [],
            "linkedin_post": self.linkedin_post or [],
            "reddit_post": self.reddit_post or [],
        }
