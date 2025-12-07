"""
Test Gemini API with gemini-2.5-flash model using current Generator LLM code
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
    print("[OK] Gemini configured")
except Exception as e:
    print(f"[ERROR] Failed to configure Gemini: {e}")
    exit(1)

# Test with gemini-2.5-flash
model_name = "gemini-2.5-flash"
print(f"\n[TEST] Testing with model: {model_name}")

try:
    model = genai.GenerativeModel(model_name)
    print(f"[OK] Model created: {model_name}")
except Exception as e:
    print(f"[ERROR] Failed to create model: {e}")
    exit(1)

# Use the same configuration as current Generator LLM code
test_prompt = "Hello? Please respond with 'Hi!' and nothing else."
print(f"\n[TEST] Sending prompt: '{test_prompt}'")

generation_config = genai.types.GenerationConfig(
    temperature=0.7,
    max_output_tokens=2000,
)

safety_settings = [
    {
        "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
    }
]

try:
    print("[INFO] Calling Gemini API... (waiting for response)")
    import time
    start_time = time.time()
    
    response = model.generate_content(
        test_prompt,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    elapsed_time = time.time() - start_time
    print(f"[OK] Response received in {elapsed_time:.2f} seconds!")
    
    # Check if response was blocked
    if not response.parts:
        print(f"\n[WARNING] Response blocked by safety filters")
        print(f"Finish reason: {response.candidates[0].finish_reason}")
        print(f"Safety ratings:")
        for rating in response.candidates[0].safety_ratings:
            print(f"  - {rating.category}: {rating.probability}")
    else:
        print(f"\n[SUCCESS] Response text:")
        print(f"'{response.text}'")
        print(f"\nResponse length: {len(response.text)} chars")
        print(f"Response time: {elapsed_time:.2f} seconds")
    
except Exception as e:
    print(f"\n[ERROR] API call failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[DONE] Test completed successfully!")
print(f"\n✅ gemini-2.5-flash is working correctly!")
