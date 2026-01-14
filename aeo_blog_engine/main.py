import argparse

from knowledge.ingest import ingest_docs
from pipeline.blog_workflow import AEOBlogPipeline, langfuse
from services import generate_and_store_blog, store_social_post


def main():
    parser = argparse.ArgumentParser(description="AEO Blog Engine CLI")

    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest documents into Knowledge Base before running"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Topic to generate a blog for"
    )
    parser.add_argument(
        "--company-url",
        type=str,
        help="Company URL to store with the generated blog"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Contact email to store with the generated blog"
    )
    parser.add_argument(
        "--brand",
        type=str,
        help="Brand name to store with the generated blog"
    )
    parser.add_argument(
        "--platform",
        type=str,
        choices=["reddit", "linkedin", "twitter"],
        help="Generate a social media post for a specific platform"
    )

    args = parser.parse_args()

    if args.ingest:
        ingest_docs()

    if args.topic:
        # Initialize pipeline once
        pipeline = AEOBlogPipeline()

        if args.platform:
            # Generate social media post
            post = pipeline.run_social_post(args.topic, args.platform)
            print(f"\n--- {args.platform.upper()} POST ---\n")
            print(post)
            
            # Save to database
            try:
                saved = store_social_post(args.topic, args.platform, post)
                print(f"\n[DB] Saved {args.platform} post to Blog ID: {saved['id']}")
            except Exception as e:
                print(f"\n[DB Error] Could not save post: {e}")

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
            # Generate blog only (CLI run without saving implies dry run, but let's be safe)
            # If user wants to save, they should provide company-url, or we can assume a default.
            # For now, we follow existing logic: just print.
            result = pipeline.run(args.topic)
            print("\n--- BLOG CONTENT ---\n")
            print(result)

    else:
        if not args.ingest:
            parser.print_help()
            
    # Ensure Langfuse traces are sent
    langfuse.flush()


if __name__ == "__main__":
    main()

