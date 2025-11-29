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
from typing import Optional, Dict, List, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from .prompts import (
    SYSTEM_PROMPT_BT_GENERATOR,
    SYSTEM_PROMPT_LOG_ANALYZER,
    SYSTEM_PROMPT_FEEDBACK_GENERATOR,
    create_initial_bt_prompt,
    create_critic_prompt,
    create_generator_prompt,
    extract_bt_from_response
)


class LLMAgent:
    """LLM agent for BT generation and improvement"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize LLM agent
        
        Args:
            api_key: Gemini API key (or None to use environment variable)
            model: Model to use (default: gemini-1.5-flash)
                   Options: gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not set. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        self.model_name = model
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Call LLM with system and user prompts
        
        Args:
            system_prompt: System prompt defining the role
            user_prompt: User prompt with the task
            temperature: Sampling temperature
            
        Returns:
            LLM response text
        """
        # Gemini doesn't have separate system/user roles in the same way
        # Combine system prompt into the user prompt
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=2000,
        )
        
        # Safety settings - disable blocking for game-related content
        # Using HarmBlockThreshold.BLOCK_NONE for all categories
        safety_settings = [
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "block_none"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "block_none"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "block_none"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "block_none"
            }
        ]
        
        try:
            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response was blocked
            if not response.parts:
                print(f"\n[ERROR] Response blocked!")
                print(f"Finish reason: {response.candidates[0].finish_reason}")
                print(f"Safety ratings:")
                for rating in response.candidates[0].safety_ratings:
                    print(f"  - {rating.category}: {rating.probability}")
                return "Error: Response was blocked by safety filters. Please try again."
            
            return response.text
            
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def generate_initial_bt(self) -> str:
        """
        Generate initial Behaviour Tree from game rules
        
        Returns:
            BT DSL string
        """
        print("[LLM] Generating initial Behaviour Tree...")
        
        prompt = create_initial_bt_prompt()
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.8)
        
        bt_dsl = extract_bt_from_response(response)
        
        print("[OK] Initial BT generated")
        return bt_dsl
    
    def critique_last_stage(
        self, 
        last_stage_log: str, 
        final_floor: int, 
        victory: bool,
        current_bt: str
    ) -> str:
        """
        Analyze last stage gameplay and provide improvement suggestions
        
        Args:
            last_stage_log: Log from the last stage only
            final_floor: Final floor reached
            victory: Whether the game was won
            current_bt: Current BT DSL
            
        Returns:
            Critic feedback text
        """
        print("[CRITIC] Analyzing last stage...")
        
        prompt = create_critic_prompt(last_stage_log, final_floor, victory, current_bt)
        feedback = self._call_llm(SYSTEM_PROMPT_LOG_ANALYZER, prompt, temperature=0.5)
        
        print("[OK] Critic analysis complete")
        return feedback
    
    def generate_improved_bt(self, current_bt: str, critic_feedback: str) -> str:
        """
        Generate improved BT based on critic feedback
        
        Args:
            current_bt: Current BT DSL
            critic_feedback: Feedback from Critic LLM
            
        Returns:
            Improved BT DSL string
        """
        print("[GENERATOR] Creating improved Behaviour Tree...")
        
        prompt = create_generator_prompt(current_bt, critic_feedback)
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.7)
        
        improved_bt = extract_bt_from_response(response)
        
        print("[OK] Improved BT generated")
        return improved_bt
    
    def two_stage_improvement(
        self,
        current_bt: str,
        last_stage_log: str,
        final_floor: int,
        victory: bool,
        stage_history: Dict[int, str] = None
    ) -> Dict[str, str]:
        """
        Execute two-stage improvement: Critic → Generator
        
        Args:
            current_bt: Current BT DSL
            last_stage_log: Log from last stage only (fallback if history not provided)
            final_floor: Final floor reached
            victory: Whether the game was won
            stage_history: Dictionary of logs per floor {floor_num: log_text}
            
        Returns:
            Dict with 'critic_feedback' and 'improved_bt'
        """
        aggregated_feedback = []
        
        # If stage history is provided, analyze each stage
        if stage_history:
            print(f"[CRITIC] Analyzing {len(stage_history)} stages...")
            for floor, log in sorted(stage_history.items()):
                print(f"  - Analyzing Floor {floor}...")
                # Determine if this specific stage was a victory (cleared) or defeat
                # If it's not the final floor, it was cleared. If it is the final floor, check victory flag.
                stage_victory = True if floor < final_floor else victory
                
                feedback = self.critique_last_stage(
                    log, 
                    floor, 
                    stage_victory,
                    current_bt
                )
                aggregated_feedback.append(f"## Floor {floor} Analysis\n{feedback}")
                
            full_feedback = "\n\n".join(aggregated_feedback)
        else:
            # Fallback to single stage analysis
            print("[CRITIC] Analyzing last stage only (no history)...")
            full_feedback = self.critique_last_stage(
                last_stage_log, 
                final_floor, 
                victory,
                current_bt
            )
        
        # Stage 2: Generator creates improved BT based on aggregated feedback
        improved_bt = self.generate_improved_bt(current_bt, full_feedback)
        
        return {
            'critic_feedback': full_feedback,
            'improved_bt': improved_bt
        }


class MockLLMAgent(LLMAgent):
    """Mock LLM agent for testing without API calls"""
    
    def __init__(self):
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
            condition : IsEnemyHPLow(25)
            task : HeavyAttack()
        task : LightAttack()"""
    
    def critique_last_stage(
        self, 
        last_stage_log: str, 
        final_floor: int, 
        victory: bool,
        current_bt: str
    ) -> str:
        """Return mock critic feedback"""
        return """## Analysis
The player is not utilizing combos effectively and healing too late.

## Improvement Suggestions
1. Add combo detection - Use HasComboReady conditions to trigger combo finishers
2. Heal earlier - Change healing threshold from 30% to 40% HP
3. Add defensive option - Use Defend when HP is low and heal is on cooldown
4. Prioritize combo completion - Don't interrupt combo chains with healing"""
    
    def generate_improved_bt(self, current_bt: str, critic_feedback: str) -> str:
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
        task : LightAttack()"""
    
    def two_stage_improvement(
        self,
        current_bt: str,
        last_stage_log: str,
        final_floor: int,
        victory: bool,
        stage_history: Dict[int, str] = None
    ) -> Dict[str, str]:
        """Execute mock two-stage improvement"""
        aggregated_feedback = []
        
        if stage_history:
            print(f"[MOCK CRITIC] Analyzing {len(stage_history)} stages...")
            for floor, log in sorted(stage_history.items()):
                print(f"  - Analyzing Floor {floor}...")
                stage_victory = True if floor < final_floor else victory
                
                feedback = self.critique_last_stage(
                    log, floor, stage_victory, current_bt
                )
                aggregated_feedback.append(f"## Floor {floor} Analysis\n{feedback}")
            
            critic_feedback = "\n\n".join(aggregated_feedback)
        else:
            critic_feedback = self.critique_last_stage(
                last_stage_log, final_floor, victory, current_bt
            )
            
        improved_bt = self.generate_improved_bt(current_bt, critic_feedback)
        
        return {
            'critic_feedback': critic_feedback,
            'improved_bt': improved_bt
        }
