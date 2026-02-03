import json
import base64
import io
import urllib.request
from PIL import Image
import sys

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def check_json_capability(model_id, test_image_path):
    print(f"Checking model: {model_id}...", end=" ", flush=True)
    
    try:
        # Prepare test image
        img = Image.open(test_image_path).convert("RGB")
        img.thumbnail((400, 400)) # Small for speed
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        prompt = "Task: Return a JSON object with one key 'status' and value 'ready'. Return ONLY valid JSON."
        
        payload = {
            "model": model_id,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "format": "json"
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            response_obj = json.loads(raw)
            response_text = response_obj.get("response", "")
            
        print(f"Response: {response_text[:50]}...", end=" ")
        
        # Try to parse JSON from response
        try:
            json.loads(response_text)
            print("[\033[92mPASS\033[0m]")
            return True
        except Exception:
            print("[\033[91mFAIL\033[0m] (Invalid JSON)")
            return False
            
    except Exception as e:
        print(f"[\033[91mERROR\033[0m] ({str(e)})")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 sanity_check.py <image_path> <model_id1,model_id2,...>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    models = sys.argv[2].split(",")
    
    capable_models = []
    for model in models:
        if check_json_capability(model.strip(), image_path):
            capable_models.append(model.strip())
            
    print("\nCapable Models:", ",".join(capable_models))
