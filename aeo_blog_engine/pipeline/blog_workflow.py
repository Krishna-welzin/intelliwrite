from agents import get_researcher_agent, get_planner_agent, get_writer_agent, get_optimizer_agent, get_base_model
from agno.agent import Agent

class AEOBlogPipeline:
    def __init__(self):
        print("Initializing AEO Blog Pipeline with Agno Agents...")

    def run(self, topic: str):
        print(f"--- Starting AEO Blog Generation for: {topic} ---")

        # 1. Research
        print("\n[1/5] Researching...")
        researcher = get_researcher_agent()
        # Ensure we get the full response, not a stream
        research_response = researcher.run(f"Research key facts, statistics, and user questions about: {topic}", stream=False)
        research_summary = research_response.content
        print(f"Research completed ({len(research_summary)} chars).")

        # 2. Plan
        print("\n[2/5] Planning...")
        planner = get_planner_agent()
        plan_response = planner.run(f"Topic: '{topic}'\n\nResearch:\n{research_summary}", stream=False)
        plan = plan_response.content
        
        # 3. Write
        print("\n[3/5] Writing...")
        writer = get_writer_agent()
        draft_response = writer.run(f"Write the blog for '{topic}' using this outline:\n\n{plan}\n\nResearch:\n{research_summary}", stream=False)
        draft = draft_response.content
        
        # 4. Optimize
        print("\n[4/5] Optimizing...")
        optimizer = get_optimizer_agent()
        opt_response = optimizer.run(f"Draft:\n{draft}", stream=False)
        optimization_report = opt_response.content
        
        # 5. Finalize
        print("\n[5/5] Finalizing...")
        finalizer = Agent(
            model=get_base_model(),
            instructions=["""You are the Final Editor. Your goal is to produce the final, publish-ready markdown file.
            1. Take the Draft and apply the improvements from the Optimization Report.
            2. Ensure the formatting is perfect Markdown.
            3. STRICTLY output ONLY the blog content. No "Here is the blog" conversation."""],
            markdown=True
        )
        final_response = finalizer.run(f"Draft:\n{draft}\n\nOptimization Suggestions:\n{optimization_report}\n\nProduce the Final Blog Post.", stream=False)
        
        return final_response.content
    
# ----------------- Social Media Posts -----------------
    def run_social_post(self, topic: str, platform: str):
        # 1. Retrieve brand + platform knowledge
        knowledge_context = self._retrieve_knowledge(f"Brand style, {platform} guidelines")
        
        # 2. Optional research
        research_summary = self._search_web(f"{topic} key facts for {platform}")

        # 3. Set system instructions per platform
        platform_instructions = {
            "reddit": """
    You are the Reddit Writer Agent. Your role is to create engaging, discussion-friendly posts.
    - Use brand tone from the knowledge base.
    - 3–7 short paragraphs or bullets.
    - Encourage community interaction.
    - Follow subreddit rules strictly.
    """,
            "linkedin": """
    You are the LinkedIn Writer Agent. Your role is to create professional, concise, and engaging posts.
    - Use brand tone from the knowledge base.
    - Focus on thought leadership and professional value.
    - Posts should be 2–4 short paragraphs.
    - Keep a clear, professional, yet approachable tone.
    """,
            "twitter": """
    You are the Twitter Writer Agent. Your role is to create punchy, attention-grabbing tweets.
    - Use brand tone from the knowledge base.
    - 1–5 tweets per topic.
    - Include concise, informative content; hashtags optional.
    - Encourage engagement and discussion.
    """
        }

        sys_prompt = platform_instructions.get(platform.lower())
        if not sys_prompt:
            raise ValueError(f"Unsupported platform: {platform}")

        # 4. Create user prompt
        user_prompt = f"Topic: '{topic}'\nResearch:\n{research_summary}\nGuidelines:\n{knowledge_context}"

        # 5. Generate content
        return self._get_completion(sys_prompt, user_prompt)


# ----------------- Example Usage -----------------
if __name__ == "__main__":
    pipeline = AEOBlogPipeline()

    # Blog
    blog_post = pipeline.run("What Is Answer Engine Optimization?")
    print("\n--- BLOG CONTENT ---\n")
    print(blog_post)

    # Social Media Posts
    reddit_post = pipeline.run_social_post("Web3 Trends 2026", "reddit")
    print("\n--- REDDIT POST ---\n")
    print(reddit_post)

    linkedin_post = pipeline.run_social_post("Web3 Trends 2026", "linkedin")
    print("\n--- LINKEDIN POST ---\n")
    print(linkedin_post)

    twitter_post = pipeline.run_social_post("Web3 Trends 2026", "twitter")
    print("\n--- TWITTER POST ---\n")
    print(twitter_post)


if __name__ == "__main__":
    pipeline = AEOBlogPipeline()
    result = pipeline.run("What Is Answer Engine Optimization?")
    print("\n\n--- FINAL AEO BLOG CONTENT ---\n")
    print(result)