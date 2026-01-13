# test_agents.py

from intelliwrite.aeo_blog_engine.agents import RedditWriterAgent, LinkedInWriterAgent, TwitterWriterAgent

def test_agent(agent, topic):
    print(f"\nTesting {agent.__class__.__name__} with topic: '{topic}'\n")
    output = agent.generate_text(topic)  # Make sure each agent has generate_text()
    print("Generated Text:\n")
    print(output)
    print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    platform = input("Choose platform (reddit/linkedin/twitter): ").lower()
    
    if platform == "reddit":
        agent = RedditWriterAgent()
    elif platform == "linkedin":
        agent = LinkedInWriterAgent()
    elif platform == "twitter":
        agent = TwitterWriterAgent()
    else:
        print("Invalid platform!")
        exit()

    topic = input("Enter the topic: ")
    test_agent(agent, topic)