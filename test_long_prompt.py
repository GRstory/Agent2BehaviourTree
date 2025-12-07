"""
Test Gemini API with gemini-2.5-flash using 2500 character prompt
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

# Create a ~2500 character prompt (similar to actual Generator prompt)
test_prompt = """Generate an IMPROVED Behaviour Tree based on feedback.

# Current Behaviour Tree
```
root :
    selector :
        # Heal when critical
        sequence :
            condition : IsPlayerHPLow(20)
            condition : CanHeal()
            task : Heal()
        
        # Default: Attack
        task : Attack()
```

# Improvement Feedback
## Analysis
The ThunderDrake fight highlights several key issues with the current BT and strategy. The primary problem is a complete lack of scanning and adaptation. The player immediately attacked, failing to identify the ThunderDrake's weakness to Lightning. This resulted in the player being heavily damaged by the Drake's attacks.

## Improvement Suggestions
1. Mandatory Scan on Turn 1: Immediately after the battle starts, the BT must execute the Scan() task.
2. Prioritize Lightning Spell: After the Scan, the BT should immediately trigger the LightningSpell() task if the ThunderDrake is weak to Lightning.
3. Adjust Heal Threshold: Increase the HP threshold for the Heal action from 30% to 40%.
4. Introduce a "Telegraph Detection" Condition: Add a condition to detect when the ThunderDrake is telegraphing a heavy attack.

# Available Syntax

**Control Nodes:** `root :`, `selector :`, `sequence :`

**Conditions:**
- HP: `IsPlayerHPLow(30)`, `IsEnemyHPLow(30)`
- Resources: `HasTP(30)`, `HasMP(20)`, `CanHeal()`
- Enemy: `EnemyWeakTo(Fire/Ice/Lightning)`, `HasScannedEnemy()`, `EnemyHasBuff(Enrage)`, `EnemyIsTelegraphing(HeavySlam)`
- Turn: `IsTurnEarly(2)`

**Actions:**
- `Attack()` - free, builds TP
- `PowerStrike()` - 30 TP, high damage
- `FireSpell()`, `IceSpell()`, `LightningSpell()` - 20 MP each, 1.5x vs weakness
- `Defend()` - free, -50% damage
- `Heal()` - 30 MP, +45 HP, 3 turn cooldown
- `Scan()` - 15 MP, reveals weakness

**Syntax Rules:**
1. Use 4 spaces for indentation
2. Format: `condition : IsPlayerHPLow(30)` and `task : Heal()`
3. Always end with fallback: `task : Attack()`

# Your Task

Apply the feedback to create an improved BT. Output ONLY the BT DSL, no explanations. Start with `root :`."""

print(f"\n[TEST] Prompt length: {len(test_prompt)} characters")
print(f"[TEST] Sending prompt to Gemini API...")

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
        safety_settings=safety_settings,
        request_options={"timeout": 60}
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
        print(f"\n[SUCCESS] Response received!")
        print(f"Response length: {len(response.text)} chars")
        print(f"Response time: {elapsed_time:.2f} seconds")
        print(f"\n--- RESPONSE START ---")
        print(response.text)
        print(f"--- RESPONSE END ---")
    
except Exception as e:
    print(f"\n[ERROR] API call failed: {e}")
    print(f"Exception type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[DONE] Test completed!")
