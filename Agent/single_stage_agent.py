"""
Single-Stage LLM Agent for Behaviour Tree Generation

Combines Critic and Generator into a single LLM call for comparison testing.
"""

import os
from typing import Optional, Tuple

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from .prompts import extract_bt_from_response


class SingleStageLLMAgent:
    """Single-stage LLM agent that combines analysis and generation in one step"""
    
    def __init__(self, config_or_api_key=None, model: str = None):
        """
        Initialize single-stage LLM agent
        
        Args:
            config_or_api_key: Either a config object with api_key, or just an API key string
            model: Model to use (default: gemini-2.0-flash)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")
        
        # Handle config object or direct API key
        if hasattr(config_or_api_key, 'api_key'):
            self.api_key = config_or_api_key.api_key or os.getenv("GEMINI_API_KEY")
            self.model_name = model or config_or_api_key.model
        else:
            self.api_key = config_or_api_key or os.getenv("GEMINI_API_KEY")
            self.model_name = model or "gemini-2.0-flash"
        
        if not self.api_key:
            raise ValueError("Gemini API key not set. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Call LLM with combined prompt"""
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
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
            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                request_options={"timeout": 60}
            )
            
            if not response.parts:
                print(f"\n[WARNING] Response blocked by safety filters")
                return "Error: Response was blocked by safety filters."
            
            return response.text
            
        except TimeoutError as e:
            print(f"[ERROR] LLM call timed out: {e}")
            return f"Error: Request timed out"
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def _validate_bt(self, bt_dsl: str) -> Tuple[bool, str]:
        """Validate BT DSL syntax"""
        if not bt_dsl or len(bt_dsl.strip()) < 10:
            return False, "BT is too short or empty"
        
        if not bt_dsl.strip().startswith("root :"):
            return False, "BT must start with 'root :'"
        
        lines = [l for l in bt_dsl.strip().split('\n') if l.strip()]
        if not lines:
            return False, "BT has no content"
        
        last_line = lines[-1].strip()
        if not last_line.startswith("task :"):
            return False, "BT must end with a fallback task action"
        
        return True, ""
    
    def improve_bt(self, current_bt: str, combat_log: str, previous_results: list = None) -> Optional[str]:
        """
        Improve BT based on combat log using single-stage approach
        
        Args:
            current_bt: Current BT DSL
            combat_log: Combat summary
            previous_results: List of previous combat results
            
        Returns:
            Improved BT DSL or None if failed
        """
        print("[SINGLE-STAGE LLM] Analyzing and improving BT in one step...")
        
        # Build performance context
        perf_context = ""
        current_enemy = "Unknown"
        if previous_results and len(previous_results) > 0:
            last_result = previous_results[-1]
            status = "VICTORY" if last_result.get('victory') else "DEFEAT"
            current_enemy = last_result.get('enemy_type', 'Unknown')
            perf_context = f"\n# This Combat Result\n"
            perf_context += f"{status} vs {current_enemy}: {last_result.get('turns', 0)} turns\n"
        
        # Combined system prompt
        system_prompt = """You are an expert AI strategist specializing in turn-based RPG combat and Behaviour Tree design.

CRITICAL: The Behaviour Tree executes ONE action per turn.

AVAILABLE ACTIONS:
- Attack: Free, 9 damage
- Charge: 15 MP, 7 damage + next turn all damage x2
- FireSpell: 20 MP, 7 damage (1.5x when enemy has Ice element), Burn 25%
- IceSpell: 20 MP, 10 damage (1.5x when enemy has Fire element), Freeze 25%
- Defend: Free, 50% damage reduction for 1 turn
- Heal: 30 MP, +40 HP, 3 turn cooldown
- Scan: 15 MP, reveals enemy weakness
- Cleanse: 25 MP, removes Burn/AttackDown, +10% damage for 1 turn

ELEMENTAL SYSTEM:
- Fire attacks deal 1.5x damage to Ice element enemies
- Ice attacks deal 1.5x damage to Fire element enemies
- Enemies start as Neutral (no weakness), can gain Fire/Ice element during combat

ENEMY MECHANICS:
- FireGolem (HP 180, Def 5): Phase 2 (HP < 50%) gains Fire element, FireSpell adds Burn (10/turn × 3)
- IceWraith (HP 200, Def 8): Debuff gives AttackDown -20%, DefensiveStance (+25% def, +20% dmg next turn)

RESOURCES:
- MP: Starts 100, regenerates 5 per turn

Your task is to analyze the combat log, identify strategic weaknesses, and generate an improved BT."""
        
        # Combined user prompt
        user_prompt = f"""# Current Behaviour Tree
```
{current_bt}
```
{perf_context}
# Combat Summary
{combat_log}

# Your Task

**Step 1: Analyze the combat**
Identify what went wrong or could be improved:
1. Telegraph reactions (defend against HeavySlam?)
2. Elemental strategy (scan? correct spell?)
3. Resource management (MP efficiency?)
4. Defensive decisions (heal/defend timing?)
5. BT issues (what parts caused problems?)

**Step 2: Generate improved BT**
Create an improved BT using ONLY this syntax:

**Control Nodes:**
- `root :` - Must be first line
- `selector :` - Tries children until one succeeds
- `sequence :` - All conditions must pass

**Conditions:**
- `IsPlayerHPLow(30)` - Player HP < threshold%
- `IsEnemyHPLow(30)` - Enemy HP < threshold%
- `HasMP(20)` - Player has >= amount MP
- `CanHeal()` - Heal off cooldown AND MP >= 30
- `EnemyHasElement(Fire)` or `EnemyHasElement(Ice)` - Enemy currently HAS this element
- `HasScannedEnemy()` - Enemy has been scanned
- `EnemyHasBuff(Burn)` or `EnemyHasBuff(AttackDown)` - Enemy has buff
- `EnemyIsTelegraphing(HeavySlam)` - Enemy will execute this action
- `NOT <condition>` - Negates a condition

**Actions:**
- `Attack()`, `Charge()`, `FireSpell()`, `IceSpell()`, `Defend()`, `Heal()`, `Scan()`, `Cleanse()`

**CRITICAL RULES:**
1. Use ONLY the syntax listed above
2. Use exactly 4 spaces per indentation level
3. Always end with fallback: `task : Attack()`
4. Focus improvements on {current_enemy} (don't add logic for enemies you haven't fought)

**Output Format:**
First, briefly explain your analysis (2-3 sentences).
Then output the improved BT DSL starting with `root :`.

Example:
Analysis: The player didn't defend against HeavySlam telegraph and wasted MP on wrong spells.

```
root :
    selector :
        sequence :
            condition : EnemyIsTelegraphing(HeavySlam)
            task : Defend()
        task : Attack()
```"""
        
        # Single LLM call
        response = self._call_llm(system_prompt, user_prompt, temperature=0.7)
        
        if "Error" in response:
            print(f"[ERROR] Single-stage LLM failed: {response}")
            return None
        
        # Extract BT from response
        improved_bt = extract_bt_from_response(response).strip()
        
        # Validate
        is_valid, error_msg = self._validate_bt(improved_bt)
        if not is_valid:
            print(f"[WARNING] Generated BT failed validation: {error_msg}")
            print("[FALLBACK] Using current BT instead")
            return None
        
        print("[OK] Improved BT generated and validated")
        return improved_bt
    
    def generate_initial_bt(self) -> str:
        """Generate initial BT (use example instead)"""
        print("[SINGLE-STAGE] Using example BT as initial")
        with open("examples/example_bt_balanced.txt", 'r') as f:
            return f.read()
