import argparse

from knowledge.ingest import ingest_docs
from pipeline.blog_workflow import AEOBlogPipeline
from services import generate_and_store_blog


def main():
    parser = argparse.ArgumentParser(description="AEO Blog Engine CLI")
    parser.add_argument("--ingest", action="store_true", help="Ingest documents into Knowledge Base before running")
    parser.add_argument("--topic", type=str, help="Topic to generate a blog for")
    parser.add_argument("--company-url", type=str, help="Company URL to store with the generated blog")
    parser.add_argument("--email", type=str, help="Contact email to store with the generated blog")
    parser.add_argument("--brand", type=str, help="Brand name to store with the generated blog")
    parser.add_argument("--platform", type=str, choices=["reddit", "linkedin", "twitter"], help="Generate a social media post for a specific platform")

    args = parser.parse_args()
    
    if args.ingest:
        ingest_docs()
    
    if args.topic:
        pipeline = AEOBlogPipeline()  # Initialize pipeline once

        if args.platform:
            # Generate social media post
            post = pipeline.run_social_post(args.topic, args.platform)
            print(f"\n--- {args.platform.upper()} POST ---\n")
            print(post)

        elif args.company_url:
            # Generate blog and store it
            payload = {
                "topic": args.topic,
                "company_url": args.company_url,
                "email_id": args.email,
                "brand_name": args.brand,
            }
            result = generate_and_store_blog(payload)
            print(result)

        else:
            # Generate blog only
            result = pipeline.run(args.topic)
            print("\n--- BLOG CONTENT ---\n")
            print(result)

    else:
        if not args.ingest:
            parser.print_help()


if __name__ == "__main__":
    main()

