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
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

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
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize LLM agent
        
        Args:
            api_key: OpenAI API key (or None to use environment variable)
            model: Model to use (default: gpt-4)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
        # Track conversation history for each role
        self.bt_generator_history = []
        self.log_analyzer_history = []
        self.feedback_generator_history = []
    
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
        if not self.client:
            raise ValueError("OpenAI API key not set. Set OPENAI_API_KEY environment variable.")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def generate_initial_bt(self) -> str:
        """
        Generate initial Behaviour Tree from game rules
        
        Returns:
            BT DSL string
        """
        print("🤖 LLM: Generating initial Behaviour Tree...")
        
        prompt = create_initial_bt_prompt()
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.8)
        
        bt_dsl = extract_bt_from_response(response)
        
        print("✓ Initial BT generated")
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
        print("🤖 Critic LLM: Analyzing last stage...")
        
        prompt = create_critic_prompt(last_stage_log, final_floor, victory, current_bt)
        feedback = self._call_llm(SYSTEM_PROMPT_LOG_ANALYZER, prompt, temperature=0.5)
        
        print("✓ Critic analysis complete")
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
        print("🤖 Generator LLM: Creating improved Behaviour Tree...")
        
        prompt = create_generator_prompt(current_bt, critic_feedback)
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.7)
        
        improved_bt = extract_bt_from_response(response)
        
        print("✓ Improved BT generated")
        return improved_bt
    
    def two_stage_improvement(
        self,
        current_bt: str,
        last_stage_log: str,
        final_floor: int,
        victory: bool
    ) -> Dict[str, str]:
        """
        Execute two-stage improvement: Critic → Generator
        
        Args:
            current_bt: Current BT DSL
            last_stage_log: Log from last stage only
            final_floor: Final floor reached
            victory: Whether the game was won
            
        Returns:
            Dict with 'critic_feedback' and 'improved_bt'
        """
        # Stage 1: Critic analyzes last stage
        critic_feedback = self.critique_last_stage(
            last_stage_log, 
            final_floor, 
            victory,
            current_bt
        )
        
        # Stage 2: Generator creates improved BT
        improved_bt = self.generate_improved_bt(current_bt, critic_feedback)
        
        return {
            'critic_feedback': critic_feedback,
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
        victory: bool
    ) -> Dict[str, str]:
        """Execute mock two-stage improvement"""
        critic_feedback = self.critique_last_stage(
            last_stage_log, final_floor, victory, current_bt
        )
        improved_bt = self.generate_improved_bt(current_bt, critic_feedback)
        
        return {
            'critic_feedback': critic_feedback,
            'improved_bt': improved_bt
        }
