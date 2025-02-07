"""OpenAI integration manager for ShopAiInsight."""

from openai import OpenAI
import os

class OpenAIManager:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def get_response(self, prompt):
        """Get response from OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting OpenAI response: {e}")
            return None 