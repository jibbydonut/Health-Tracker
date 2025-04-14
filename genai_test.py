from google import genai
from dotenv import load_dotenv
import os

client = genai.Client(api_key=os.getenv("GOOGLE_GENAI_API"))

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a short paragraph"
)

print(response.text)