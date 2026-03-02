# -*- coding: utf-8 -*-
"""
marCram's bones
"""

import os
import requests
from dotenv import load_dotenv
import anthropic
import time

print("Yay! All libraries imported successfully!\n")

# Load environment variables from .env file
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
MAX_SEARCHES_PER_REQUEST = os.getenv("MAX_SEARCHES_PER_REQUEST")
ALLOWED_SEARCH_DOMAINS = os.getenv("ALLOWED_SEARCH_DOMAINS")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def clarify(question):
    system_prompt = """
        You are a helpful study buddy that tries it's best to answer questions based on the resources you have access to

        You are to state the website you are currently accessing to retrieve information from before stating your answer.
        
        For example:
        "Ahem! According to [link here], [answer here]"
    """
    
    user_prompt = f"""Use the following context to answer the question. 
        If you are unable to find any answers, say "Sorry, I can't find any info on your question :("

        Question: {user_question}
        """
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": user_prompt,
            },
            {
                "role": "system",
                "content": system_prompt
            }
        ],
            tools=[{
                "type": "web_search_20260209", 
                "name": "web_search",
                "max_uses": 5,
                "allowed_domains": ["https://en.wikipedia.org/"],
                }],
    )
    
    print("Used " + message.usage + "!")
    
    

def run_chatbot():
    """
    Start a chatbot session
    """
    print("\n" + "="*70)
    print("marCram- Powered by Claude")
    print("="*70)
    print("Ask me about what you're studying :]")
    print("\nCommands:")
    print("  - Type 'quit' or 'exit' to stop")
    print("="*70 + "\n")
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit commands
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nThanks for chatting! Goodbye!\n")
            break
            
        # Skip empty inputs
        if not user_input:
            continue
        
        try:
            # Get AI response
            print("\n[THINKING] Processing your question...\n")
            response = clarify(user_input)
            print(f"Bot: {response}\n")
            print("-" * 70 + "\n")
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}\n")
            print("Make sure your API keys are set correctly!\n")


print(message.content)
