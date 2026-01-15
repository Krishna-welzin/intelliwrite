from sqlalchemy import text
from aeo_blog_engine.database.session import get_session

def inspect_raw():
    with get_session() as session:
        # We use raw SQL to avoid the TypeDecorator parsing
        result = session.execute(text("SELECT id, blog, twitter_post FROM blogs LIMIT 3"))
        for row in result:
            print(f"ID: {row[0]}")
            print(f"Raw Blog: {row[1]} (Type: {type(row[1])})")
            print(f"Raw Twitter: {row[2]} (Type: {type(row[2])})")
            print("-" * 20)

if __name__ == "__main__":
    inspect_raw()
