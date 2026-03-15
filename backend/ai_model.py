# -*- coding: utf-8 -*-
"""
marCram's bones
"""

import os
import requests
from dotenv import load_dotenv
from anthropic import Anthropic


print("Yay! All libraries imported successfully!\n")

# Load environment variables from .env file
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY").strip()
CHAT_MODEL = os.getenv("CHAT_MODEL").strip()
MODEL_BASE_URL=os.getenv("MODEL_BASE_URL").strip()

raw_ALLOWED_SEARCH_DOMAINS = os.getenv("ALLOWED_SEARCH_DOMAINS").split(",")

def _parse_allowed_search_domains() -> list[str]:
    domains: list[str] = list()
    for part in raw_ALLOWED_SEARCH_DOMAINS:
        part = part.strip()
        if not part:
            continue
        try:
            domains.append(str(part))
        except ValueError:
            raise RuntimeError(
                "TELEGRAM_ADMIN_IDS must be comma-separated integers. "
                f"Bad value: {part!r}"
            )
    return domains

client = Anthropic(api_key=CLAUDE_API_KEY, base_url=MODEL_BASE_URL)


def marcram_chat(user_question):
    system_prompt = """
        You are a helpful study buddy that assists students in clarifying topics.
        Always search the web for answers. Always cite your sources with links.
        Reply in less than 150 words, and in a text message format.
        
        For example: "Ahem! According to [link], [answer]"
    """
    
    user_prompt = f"""        
        Use the following context to answer the question, search the web if you are unsure about anything. 
        If you are unable to find any answers, say "Sorry, I can't find any info on your question :("
        
        Question: {user_question}
        """
        
    tools = [
        {
            "type": "web_search",
            "filters": {
                "allowed_domains": _parse_allowed_search_domains()
            }
        }
    ]
    
    response = client.messages.create(
        model=CHAT_MODEL,  # or your model
        max_tokens=250,
        system=system_prompt,
        tools=[
            {
                "type": "web_search_20250305",  # Anthropic's web search tool
                "name": "web_search",
                "max_uses": 1,
                "allowed_domains": _parse_allowed_search_domains()  
            }
            ],
            messages=[
                {"role": "user", "content": user_question}
            ]
        )

    # Extract text from response content blocks
    # print(response);
    
    text_response = " ".join(block.text for block in response.content if block.type == "text")
    print (text_response)
    return text_response


# def run_chatbot():
    # """
    # Start a chatbot session
    # """
    # print("\n" + "="*70)
    # print("marCram - Powered by Anthropic")
    # print("="*70)
    # print("Ask me about what you're studying :]")
    # print("\nCommands:")
    # print("  - Type 'quit' or 'exit' to stop")
    # print("="*70 + "\n")
    
#     while True:
#         # Get user input
#         user_input = input("You: ").strip()
        
#         # Check for exit commands
#         if user_input.lower() in ['quit', 'exit', 'bye']:
#             print("\nThanks for chatting! Goodbye!\n")
#             break
            
#         # Skip empty inputs
#         if not user_input:
#             continue
        
#         try:
#             # Get AI response
#             print("\n[THINKING] Processing your question...\n")
#             response = clarify(user_input)
#             print(f"Bot: {response}\n")
#             print("-" * 70 + "\n")
            
#         except Exception as e:
#             print(f"\n[ERROR] {str(e)}\n")
#             print("Make sure your API keys are set correctly!\n")

# if __name__ == "__main__":
#     print("\n" + "="*70)
#     print("\n--- Starting chatbot ---\n")
    
#     run_chatbot()
