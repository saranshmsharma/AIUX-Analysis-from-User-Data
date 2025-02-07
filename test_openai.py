import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_openai_connection():
    print("Testing OpenAI Connection...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return False
        
    print(f"API Key found: {'*' * len(api_key)}")
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! This is a test message."}
            ]
        )
        print("✅ OpenAI connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Error connecting to OpenAI: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai_connection() 