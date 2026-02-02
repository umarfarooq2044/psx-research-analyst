
import os
from google import genai

def list_gemini_models():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return
        
    client = genai.Client(api_key=api_key)
    print("Available Models:")
    try:
        for model in client.models.list():
            print(f"- {model.name} (ID: {model.base_model_id if hasattr(model, 'base_model_id') else 'N/A'})")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_gemini_models()
