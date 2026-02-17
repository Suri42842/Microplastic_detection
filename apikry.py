import google.generativeai as genai
import os

# Put your API Key here
os.environ["GOOGLE_API_KEY"] = "x"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)