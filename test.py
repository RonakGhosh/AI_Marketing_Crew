import google.generativeai as genai

# 1. Configure with your API key
genai.configure(api_key="AIzaSyAIBqXU-ynMp1dvK7LdgSoqkRtylF5k3x8")

# 2. Load the Gemini 1.5 Flash model
model = genai.GenerativeModel("gemini-1.5-flash")

# 3. Make a request
response = model.generate_content("What is the capital of india")

print(response.text)
