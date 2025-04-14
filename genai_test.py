from google import genai

client = genai.Client(api_key="AIzaSyBWjBKQFkUN4ou6xNJB_hdTnTl2Kpvhga8")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a short paragraph"
)

print(response)