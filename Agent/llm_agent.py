"""
LLM Agent for Behaviour Tree Generation and Improvement

Implements the PORTAL-inspired iterative improvement loop:
1. Generate initial BT
2. Execute BT in game
3. Analyze logs
4. Generate feedback
5. Improve BT
6. Repeat
"""

import os
from typing import Optional, Dict, List, Any, Tuple

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from .prompts import (
    SYSTEM_PROMPT_BT_GENERATOR,
    SYSTEM_PROMPT_CRITIC,
    create_initial_bt_prompt,
    create_critic_prompt,
    create_generator_prompt,
    extract_bt_from_response
)


class LLMAgent:
    """LLM agent for BT generation and improvement"""
    
    def __init__(self, config_or_api_key=None, model: str = None, critic_model: str = None):
        """
        Initialize LLM agent
        
        Args:
            config_or_api_key: Either a config object with api_key and model attributes, or just an API key string
            model: Model to use for generation (default: gemini-2.0-flash)
            critic_model: Model to use for critique (default: gemini-2.0-flash)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")
        
        # Handle config object or direct API key
        if hasattr(config_or_api_key, 'api_key'):
            # It's a config object
            self.api_key = config_or_api_key.api_key or os.getenv("GEMINI_API_KEY")
            self.model_name = model or config_or_api_key.model
            self.critic_model_name = critic_model or config_or_api_key.critic_model
        else:
            # It's an API key string (or None)
            self.api_key = config_or_api_key or os.getenv("GEMINI_API_KEY")
            self.model_name = model or "gemini-2.0-flash"
            self.critic_model_name = critic_model or "gemini-2.0-flash"
        
        if not self.api_key:
            raise ValueError("Gemini API key not set. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.critic_model_instance = genai.GenerativeModel(self.critic_model_name)
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model_instance=None) -> str:
        """
        Call LLM with system and user prompts
        
        Args:
            system_prompt: System prompt defining the role
            user_prompt: User prompt with the task
            temperature: Sampling temperature
            model_instance: Specific model instance to use (optional)
            
        Returns:
            LLM response text
        """
        # Gemini doesn't have separate system/user roles in the same way
        # Combine system prompt into the user prompt
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Log the prompt to console (Simplified)

        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=2000,
        )
        
        # Safety settings - disable ALL blocking (only valid categories for current API)
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
        
        target_model = model_instance or self.model
        
        try:
            import time

            
            start_time = time.time()
            
            # Add timeout using request_options
            response = target_model.generate_content(
                combined_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                request_options={"timeout": 60}  # 60 second timeout
            )
            
            elapsed = time.time() - start_time

            
            # Check if response was blocked
            if not response.parts:
                print(f"\n[WARNING] Response blocked by safety filters")
                print(f"Finish reason: {response.candidates[0].finish_reason}")
                print(f"Safety ratings:")
                for rating in response.candidates[0].safety_ratings:
                    print(f"  - {rating.category}: {rating.probability}")
                
                return "Error: Response was blocked by safety filters."
            

            return response.text
            
        except TimeoutError as e:
            print(f"[ERROR] LLM call timed out after 60 seconds: {e}")
            return f"Error: Request timed out"
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def _validate_bt(self, bt_dsl: str) -> tuple[bool, str]:
        """Validate BT DSL syntax
        
        Returns:
            (is_valid, error_message)
        """
        if not bt_dsl or len(bt_dsl.strip()) < 10:
            return False, "BT is too short or empty"
        
        if not bt_dsl.strip().startswith("root :"):
            return False, "BT must start with 'root :'"
        
        # Check for fallback action (last line should be a task)
        lines = [l for l in bt_dsl.strip().split('\n') if l.strip()]
        if not lines:
            return False, "BT has no content"
        
        last_line = lines[-1].strip()
        if not last_line.startswith("task :"):
            return False, "BT must end with a fallback task action"
        
        # Check for invalid condition/action names
        invalid_patterns = [
            "isPlayerHP", "isEnemyHP", "isAbilityAvailable", "IsAbilityReady",
            "UseAbility", "executeCombo", "isComboAvailable"
        ]
        for pattern in invalid_patterns:
            if pattern in bt_dsl:
                return False, f"Invalid syntax detected: '{pattern}' is not a valid condition/action"
        
        return True, ""
    
    def generate_initial_bt(self) -> str:
        """
        Generate initial Behaviour Tree from game rules
        
        Returns:
            BT DSL string
        """
        print("[LLM] Generating initial Behaviour Tree...")
        
        prompt = create_initial_bt_prompt()
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.8)
        
        bt_dsl = extract_bt_from_response(response).strip()
        
        print("[OK] Initial BT generated")
        return bt_dsl
    

    
    def critique_combat(
        self, 
        combat_log: str, 
        victory: bool,
        current_bt: str
    ) -> str:
        """
        Analyze combat gameplay and provide improvement suggestions
        
        Args:
            combat_log: Combat log from the battle
            victory: Whether the game was won
            current_bt: Current BT DSL
            
        Returns:
            Critic feedback text
        """
        print("[CRITIC] Analyzing combat...")
        
        prompt = create_critic_prompt(combat_log, current_bt, [])
        feedback = self._call_llm(SYSTEM_PROMPT_CRITIC, prompt, temperature=0.5, model_instance=self.critic_model_instance)
        
        print("[OK] Critic analysis complete")
        return feedback
    
    def generate_improved_bt(self, current_bt: str, critic_feedback: str, previous_bts: list = None) -> Tuple[str, Optional[str]]:
        """
        Generate improved BT based on critic feedback
        
        Args:
            current_bt: Current BT DSL
            critic_feedback: Feedback from Critic LLM
            
        Returns:
            (Improved BT DSL string, Error message if failed)
        """
        print("[GENERATOR] Creating improved Behaviour Tree...")
        
        prompt = create_generator_prompt(current_bt, critic_feedback, previous_bts)
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.7)
        
        improved_bt = extract_bt_from_response(response).strip()
        
        # Validate the generated BT
        is_valid, error_msg = self._validate_bt(improved_bt)
        if not is_valid:
            print(f"[WARNING] Generated BT failed validation: {error_msg}")
            print("[FALLBACK] Using current BT instead")
            return current_bt, error_msg
        
        print("[OK] Improved BT generated and validated")
        return improved_bt, None
    
    def two_stage_improvement(
        self,
        current_bt: str,
        combat_log: str,
        victory: bool
    ) -> Dict[str, str]:
        """
        Execute two-stage improvement: Critic → Generator
        
        Args:
            current_bt: Current BT DSL
            combat_log: Combat log from the battle
            victory: Whether the game was won
            
        Returns:
            Dict with 'critic_feedback' and 'improved_bt'
        """
        # If victory achieved, no need to improve
        if victory:
            print("[LLM] Victory achieved! No improvement needed.")
            return {
                'critic_feedback': "Victory achieved. No changes needed.",
                'improved_bt': current_bt
            }
            
        # Analyze the combat
        print("[CRITIC] Analyzing combat...")
        
        critic_feedback = self.critique_combat(
            combat_log, 
            victory,
            current_bt
        )
        
        # Stage 2: Generator creates improved BT based on critic feedback
        improved_bt, error_msg = self.generate_improved_bt(current_bt, critic_feedback)
        
        result = {
            'critic_feedback': critic_feedback,
            'improved_bt': improved_bt
        }
        
        if error_msg:
            result['generation_error'] = error_msg
            
        return result
    
    def improve_bt(self, current_bt: str, combat_log: str, previous_results: list = None) -> Optional[str]:
        """
        Improve BT based on combat log
        
        Args:
            current_bt: Current BT DSL
            combat_log: Combat summary
            previous_results: List of previous combat results (dicts with 'iteration', 'bt', 'victory', 'turns', etc.)
            
        Returns:
            Improved BT DSL or None if failed
        """
        print("[LLM] Improving BT...")
        
        # Build previous_bts list from previous_results
        previous_bts = []
        if previous_results:
            for result in previous_results[-5:]:  # Last 5 results
                if not result.get('victory', False):  # Only failed attempts
                    iter_num = result.get('iteration', '?')
                    bt_dsl = result.get('bt', '')
                    turns = result.get('turns', 0)
                    enemy = result.get('enemy_type', 'Unknown')
                    result_summary = f"LOSS vs {enemy} in {turns} turns"
                    previous_bts.append((iter_num, bt_dsl, result_summary))
        
        # Get critic feedback
        from .prompts import create_critic_prompt, SYSTEM_PROMPT_CRITIC
        
        prompt = create_critic_prompt(combat_log, current_bt, previous_results or [])
        feedback = self._call_llm(SYSTEM_PROMPT_CRITIC, prompt, temperature=0.5, model_instance=self.critic_model_instance)
        
        if "Error" in feedback:
            print(f"[ERROR] Critic failed: {feedback}")
            return None
        
        # Generate improved BT with previous failed BTs
        improved_bt, error = self.generate_improved_bt(current_bt, feedback, previous_bts)
        
        if error:
            print(f"[ERROR] Generator failed: {error}")
            return None
        
        return improved_bt
    
    def generate_initial_bt(self) -> str:
        """
        Generate initial Behaviour Tree from game rules
        
        Returns:
            BT DSL string
        """
        print("[LLM] Generating initial Behaviour Tree...")
        
        prompt = create_initial_bt_prompt()
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.8)
        
        bt_dsl = extract_bt_from_response(response).strip()
        
        print("[OK] Initial BT generated")
        return bt_dsl
    

    
    def generate_improved_bt(self, current_bt: str, critic_feedback: str) -> Tuple[str, Optional[str]]:
        """
        Generate improved BT based on critic feedback
        
        Args:
            current_bt: Current BT DSL
            critic_feedback: Feedback from Critic LLM
            
        Returns:
            (Improved BT DSL string, Error message if failed)
        """
        print("[GENERATOR] Creating improved Behaviour Tree...")
        
        prompt = create_generator_prompt(current_bt, critic_feedback)
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.7)
        
        improved_bt = extract_bt_from_response(response).strip()
        
        # Validate the generated BT
        is_valid, error_msg = self._validate_bt(improved_bt)
        if not is_valid:
            print(f"[WARNING] Generated BT failed validation: {error_msg}")
            print("[FALLBACK] Using current BT instead")
            return current_bt, error_msg
        
        print("[OK] Improved BT generated and validated")
        return improved_bt, None
    

    



class MockLLMAgent(LLMAgent):
    """Mock LLM agent for testing without API calls"""
    
    def __init__(self, config=None):
        # Don't call parent __init__ to avoid API key requirement
        self.model = "mock"
        self.client = None
    
    def generate_initial_bt(self) -> str:
        """Return a simple test BT"""
        return """root :
    selector :
        sequence :
            condition : IsPlayerHPLow(30)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : IsTurnEarly(2)
            task : Scan()
        sequence :
            condition : EnemyWeakTo(Ice)
            condition : HasMP(20)
            task : IceSpell()
        task : Attack()"""
    
    def critique_combat(
        self, 
        combat_log: str, 
        victory: bool,
        current_bt: str
    ) -> str:
        """Return mock critic feedback"""
        return """## Analysis
The player is not utilizing elemental advantages effectively and healing too late.

## Improvement Suggestions
1. Scan earlier - Use Scan on turn 1 to identify enemy weakness
2. Heal earlier - Change healing threshold from 30% to 40% HP
3. Add defensive option - Use Defend when HP is low and heal is on cooldown
4. Exploit weakness - Use effective elemental spells after scanning"""
    
    def generate_improved_bt(self, current_bt: str, critic_feedback: str) -> Tuple[str, Optional[str]]:
        """Return improved mock BT"""
        return """root :
    selector :
        sequence :
            condition : IsPlayerHPLow(40)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : IsPlayerHPLow(50)
            task : Defend()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        sequence :
            condition : IsEnemyHPLow(30)
            task : HeavyAttack()
        task : LightAttack()""", None
    
    def two_stage_improvement(
        self,
        current_bt: str,
        combat_log: str,
        victory: bool
    ) -> Dict[str, str]:
        """Execute mock two-stage improvement"""
        print("[MOCK CRITIC] Analyzing combat...")
        
        critic_feedback = self.critique_combat(
            combat_log, victory, current_bt
        )
            
        improved_bt = self.generate_improved_bt(current_bt, critic_feedback)
        
        return {
            'critic_feedback': critic_feedback,
            'improved_bt': improved_bt
        }
    
    def improve_bt(self, current_bt: str, combat_log: str, previous_results: list = None) -> Optional[str]:
        """Return slightly improved mock BT"""
        print("[MOCK] Generating improved BT...")
        return """root :
    selector :
        sequence :
            condition : IsPlayerHPLow(35)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : IsTurnEarly(1)
            task : Scan()
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Ice)
            condition : HasMP(20)
            task : IceSpell()
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Fire)
            condition : HasMP(20)
            task : FireSpell()
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Lightning)
            condition : HasMP(20)
            task : LightningSpell()
        task : Attack()"""
