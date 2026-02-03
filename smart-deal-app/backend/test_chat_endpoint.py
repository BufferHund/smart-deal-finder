
import sys
import os

# Add backend directory to sys.path so we can import 'services'
sys.path.append(os.getcwd())

from services.storage import get_ai_token
import google.generativeai as genai

print("--- Testing AI Chef Backend Logic ---")

# 1. Get Token
try:
    token = get_ai_token()
    if token:
        print(f"PASS: Found API Token: {token[:5]}...{token[-4:]}")
    else:
        print("FAIL: No API Token returned from get_ai_token()")
        sys.exit(1)
        
    # 2. Configure GenAI
    genai.configure(api_key=token)
    print("PASS: GenAI Configured")
    
    # 3. Test Model Init
    model_name = "gemini-2.5-flash-preview-05-20"
    print(f"Testing Model: {model_name}")
    
    try:
        model = genai.GenerativeModel(model_name)
        print("PASS: Model Object Created")
        
        # 4. Test Generation
        print("Sending test prompt...")
        response = model.generate_content("Hello Chef, just say 'Ready' if you can hear me.")
        print(f"PASS: Generation Connection Successful")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"FAIL: Model Generation Error: {e}")
        # Try fallback
        print("Trying fallback to gemini-1.5-flash...")
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Hello fallback?")
            print(f"PASS: Fallback successful: {response.text}")
        except Exception as e2:
            print(f"FAIL: Fallback also failed: {e2}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
