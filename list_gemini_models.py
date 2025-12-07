"""
List all available Gemini models
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    print("[OK] google.generativeai imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import google.generativeai: {e}")
    exit(1)

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[ERROR] GEMINI_API_KEY not found in environment variables")
    exit(1)

print(f"[OK] API key found: {api_key[:10]}...")

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    print("[OK] Gemini configured\n")
except Exception as e:
    print(f"[ERROR] Failed to configure Gemini: {e}")
    exit(1)

# List all available models
print("="*80)
print("AVAILABLE GEMINI MODELS")
print("="*80)

try:
    models = genai.list_models()
    
    generation_models = []
    for model in models:
        # Check if model supports generateContent
        if 'generateContent' in model.supported_generation_methods:
            generation_models.append(model)
            print(f"\n✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
    
    print("\n" + "="*80)
    print(f"Total models supporting generateContent: {len(generation_models)}")
    print("="*80)
    
    if generation_models:
        print("\n📋 RECOMMENDED MODELS FOR YOUR USE:")
        print("-" * 80)
        for model in generation_models:
            if 'flash' in model.name.lower():
                print(f"  🚀 {model.name.split('/')[-1]} - Fast and efficient")
            elif 'pro' in model.name.lower():
                print(f"  ⭐ {model.name.split('/')[-1]} - High quality")
    
except Exception as e:
    print(f"[ERROR] Failed to list models: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
