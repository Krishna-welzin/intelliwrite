from agents import get_researcher_agent, get_planner_agent, get_writer_agent, get_optimizer_agent, get_base_model
from agno.agent import Agent
from langfuse import observe, Langfuse

# Initialize Langfuse client
langfuse = Langfuse()

class AEOBlogPipeline:
    def __init__(self):
        print("Initializing AEO Blog Pipeline with Agno Agents...")

    @observe()
    def run(self, topic: str):
        print(f"--- Starting AEO Blog Generation for: {topic} ---")

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
            3. STRICTLY output ONLY the blog content. No "Here is the blog" conversation."""],
            markdown=True
        )
        final_response = finalizer.run(f"Draft:\n{draft}\n\nOptimization Suggestions:\n{optimization_report}\n\nProduce the Final Blog Post.", stream=False)
        
        # --- Capture Aggregate Token Usage ---
        try:
            # Agno responses contain metadata with usage information
            total_input_tokens = 0
            total_output_tokens = 0
            
            responses = [research_response, plan_response, draft_response, opt_response, final_response]
            for resp in responses:
                if hasattr(resp, 'metrics') and resp.metrics:
                    total_input_tokens += getattr(resp.metrics, "input_tokens", 0)
                    total_output_tokens += getattr(resp.metrics, "output_tokens", 0)
            
            # Update the current span with the token counts in metadata
            langfuse.update_current_span(
                metadata={
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens
                }
            )
        except Exception as e:
            print(f"Note: Could not capture token usage: {e}")

        return final_response.content

if __name__ == "__main__":
    pipeline = AEOBlogPipeline()
    result = pipeline.run("What Is Answer Engine Optimization?")
    print("\n\n--- FINAL AEO BLOG CONTENT ---\n")
    print(result)
    
    # Flush Langfuse traces before exiting
    langfuse.flush()