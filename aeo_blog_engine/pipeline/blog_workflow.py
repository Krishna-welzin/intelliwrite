from aeo_blog_engine.agents import get_researcher_agent, get_planner_agent, get_writer_agent, get_optimizer_agent, get_base_model, get_reddit_agent, get_linkedin_agent, get_twitter_agent, get_social_qa_agent, get_topic_generator_agent
from agno.agent import Agent
from langfuse import observe, Langfuse

# Initialize Langfuse client
langfuse = Langfuse()

class AEOBlogPipeline:
    def __init__(self):
        print("Initializing AEO Blog Pipeline with Agno Agents...")

    @observe()
    def run(self, topic: str = None, prompt: str = None):
        if not topic and not prompt:
            raise ValueError("Either 'topic' or 'prompt' must be provided.")

        print(f"--- Starting AEO Blog Generation ---")
        
        total_input_tokens = 0
        total_output_tokens = 0
        
        # 0. Topic Generation (if needed)
        topic_gen_response = None
        if prompt and not topic:
            print(f"\n[0/5] Generating Topic from Prompt: '{prompt}'...")
            topic_generator = get_topic_generator_agent()
            topic_gen_response = topic_generator.run(f"Generate a blog topic for: {prompt}", stream=False)
            topic = topic_gen_response.content.strip()
            print(f"Generated Topic: {topic}")

        print(f"Target Topic: {topic}")

        # 1. Research
        print("\n[1/5] Researching...")
        researcher = get_researcher_agent()
        research_response = researcher.run(f"Research key facts, statistics, and user questions about: {topic}", stream=False)
        research_summary = research_response.content
        
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
            3. STRICTLY output ONLY the blog content. No \"Here is the blog\" conversation.
            """],
            markdown=True
        )
        final_response = finalizer.run(f"Draft:\n{draft}\n\nOptimization Suggestions:\n{optimization_report}\n\nProduce the Final Blog Post.", stream=False)
        
        # --- Capture Aggregate Token Usage ---
        try:
            # Agno responses contain metadata with usage information
            responses = [research_response, plan_response, draft_response, opt_response, final_response]
            if topic_gen_response:
                responses.insert(0, topic_gen_response)
                
            for resp in responses:
                if hasattr(resp, 'metrics') and resp.metrics:
                    total_input_tokens += getattr(resp.metrics, "input_tokens", 0)
                    total_output_tokens += getattr(resp.metrics, "output_tokens", 0)
            
            # Record a "Generation" to represent the total LLM usage for this pipeline run.
            generation = langfuse.start_generation(
                name="Total_Pipeline_Usage",
                model="gemini-flash-latest",
                input=prompt if prompt else topic,
                output=final_response.content,
                usage_details={
                    "prompt_tokens": total_input_tokens,
                    "completion_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens
                },
                metadata={
                    "source": "agno-agent-aggregation",
                    "generated_topic": topic if prompt else None
                }
            )
            generation.end()

            
        except Exception as e:
            print(f"Note: Could not capture token usage: {e}")

        # If run via prompt, we might want to return the topic too, but for now return content as per signature
        # To handle saving, the caller might need the topic. 
        # But `run` traditionally returns content. 
        # We will attach the topic to the final string via a property or tuple if possible?
        # Actually, let's keep it simple: return content. The Service layer handles DB updates.
        return final_response.content

    def generate_topic_only(self, prompt: str) -> str:
        """Helper to just generate a topic without running the full pipeline."""
        topic_generator = get_topic_generator_agent()
        response = topic_generator.run(f"Generate a blog topic for: {prompt}", stream=False)
        return response.content.strip()

    # ----------------- Social Media Posts -----------------

    @observe()
    def run_social_post(self, topic: str, platform: str):
        print(f"--- Starting Social Post Generation for: {topic} ({platform}) ---")

        # 1. Research (Reusing the researcher from the blog flow)
        print("\n[1/3] Researching...")
        researcher = get_researcher_agent()
        research_response = researcher.run(
            f"Research key facts and trends about: {topic}",
            stream=False
        )
        research_summary = research_response.content
        print(f"Research completed ({len(research_summary)} chars).")

        # 2. Write Post
        print(f"\n[2/3] Writing {platform} post...")

        if platform.lower() == "reddit":
            writer = get_reddit_agent()
        elif platform.lower() == "linkedin":
            writer = get_linkedin_agent()
        elif platform.lower() == "twitter":
            writer = get_twitter_agent()
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        # Pass the research as context to the social writer
        prompt = (
            f"Topic: '{topic}'\n\n"
            f"Context/Research:\n{research_summary}"
        )

        draft_response = writer.run(prompt, stream=False)
        draft_content = draft_response.content
        
        # 3. QA & Refine
        print(f"\n[3/3] QA Checking for {platform} compliance...")
        qa_agent = get_social_qa_agent()
        qa_response = qa_agent.run(
            f"Platform: {platform}\nDraft Post:\n{draft_content}\n\nReview and fix if necessary.",
            stream=False
        )
        final_content = qa_response.content

        # --- Capture Aggregate Token Usage for Social ---
        try:
            total_input_tokens = 0
            total_output_tokens = 0
            
            responses = [research_response, draft_response, qa_response]
            for resp in responses:
                if hasattr(resp, 'metrics') and resp.metrics:
                    total_input_tokens += getattr(resp.metrics, "input_tokens", 0)
                    total_output_tokens += getattr(resp.metrics, "output_tokens", 0)
            
            generation = langfuse.start_generation(
                name=f"Social_Post_Usage_{platform}",
                model="gemini-flash-latest",
                input=topic,
                output=final_content,
                usage_details={
                    "prompt_tokens": total_input_tokens,
                    "completion_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens
                },
                metadata={
                    "source": "agno-agent-social",
                    "platform": platform
                }
            )
            generation.end()
        except Exception as e:
            print(f"Note: Could not capture token usage: {e}")

        return final_content

if __name__ == "__main__":
    pipeline = AEOBlogPipeline()
    result = pipeline.run("What Is Answer Engine Optimization?")
    print("\n\n--- FINAL AEO BLOG CONTENT ---\n")
    print(result)
    
    # Flush Langfuse traces before exiting
    langfuse.flush()
