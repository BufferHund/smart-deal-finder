
import google.generativeai as genai
import os

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    # Try to load from .env or similar if possible, or just print warning
    print("WARNING: No GOOGLE_API_KEY found in env.")

try:
    if api_key:
        genai.configure(api_key=api_key)
        
    print("Listing available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
            
    print("\nTrying to init gemini-2.5-flash-preview-05-20...")
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    print("Init successful (client-side check only).")
except Exception as e:
    print(f"Error: {e}")
