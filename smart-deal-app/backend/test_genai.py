
import google.generativeai as genai
import os
import sys

# Try to look for API key in env or args
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("No API Key found in env. Creating simple test...")
    # We can't really test without a key, but we can list models to see if lib works
    # Actually list_models doesn't need key? No it usually does.
    pass

try:
    print(f"GenAI Version: {genai.__version__}")
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    print("Model initialized successfully.")
except Exception as e:
    print(f"Error initializing model: {e}")
