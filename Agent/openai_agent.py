"""
OpenAI LLM Agent for Behaviour Tree Generation and Improvement

Implements the same interface as LLMAgent but uses OpenAI's GPT models.
"""

import os
from typing import Optional, Dict, List, Any, Tuple

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from .prompts import (
    SYSTEM_PROMPT_BT_GENERATOR,
    SYSTEM_PROMPT_CRITIC,
    create_initial_bt_prompt,
    create_critic_prompt,
    create_generator_prompt,
    extract_bt_from_response
)


class OpenAILLMAgent:
    """OpenAI LLM agent for BT generation and improvement"""
    
    def __init__(self, config_or_api_key=None, model: str = None, critic_model: str = None):
        """
        Initialize OpenAI LLM agent
        
        Args:
            config_or_api_key: Either a config object with api_key and model attributes, or just an API key string
            model: Model to use for generation (default: gpt-4o)
            critic_model: Model to use for critique (default: gpt-4o-mini)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Install with: pip install openai")
        
        # Handle config object or direct API key
        if hasattr(config_or_api_key, 'openai_api_key'):
            # It's a config object - use OpenAI-specific key
            self.api_key = config_or_api_key.openai_api_key or os.getenv("OPENAI_API_KEY")
            self.model_name = model or getattr(config_or_api_key, 'openai_model', 'gpt-4o')
            self.critic_model_name = critic_model or getattr(config_or_api_key, 'openai_critic_model', 'gpt-4o-mini')
        else:
            # It's an API key string (or None)
            self.api_key = config_or_api_key or os.getenv("OPENAI_API_KEY")
            self.model_name = model or "gpt-4o"
            self.critic_model_name = critic_model or "gpt-4o-mini"
        
        if not self.api_key:
            raise ValueError("OpenAI API key not set. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure OpenAI client
        self.client = OpenAI(api_key=self.api_key)
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, use_critic_model: bool = False) -> str:
        """
        Call OpenAI LLM with system and user prompts
        
        Args:
            system_prompt: System prompt defining the role
            user_prompt: User prompt with the task
            temperature: Sampling temperature
            use_critic_model: Whether to use the critic model (cheaper/faster)
            
        Returns:
            LLM response text
        """
        model = self.critic_model_name if use_critic_model else self.model_name
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_completion_tokens=2000,  # Changed from max_tokens for newer models
                timeout=60
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[ERROR] OpenAI API call failed with model '{model}': {e}")
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
        prompt = create_initial_bt_prompt()
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.8)
        
        bt_dsl = extract_bt_from_response(response).strip()
        
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
        prompt = create_critic_prompt(combat_log, current_bt, [])
        feedback = self._call_llm(SYSTEM_PROMPT_CRITIC, prompt, temperature=0.5, use_critic_model=True)
        
        return feedback
    
    def generate_improved_bt(self, current_bt: str, critic_feedback: str) -> Tuple[str, Optional[str]]:
        """
        Generate improved BT based on critic feedback
        
        Args:
            current_bt: Current BT DSL
            critic_feedback: Feedback from Critic LLM
            
        Returns:
            (Improved BT DSL string, Error message if failed)
        """
        prompt = create_generator_prompt(current_bt, critic_feedback)
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.7)
        
        improved_bt = extract_bt_from_response(response).strip()
        
        # Validate the generated BT
        is_valid, error_msg = self._validate_bt(improved_bt)
        if not is_valid:
            return current_bt, error_msg
        
        return improved_bt, None
    
    def improve_bt(self, current_bt: str, combat_log: str, previous_results: list = None) -> Optional[str]:
        """
        Improve BT based on combat log
        
        Args:
            current_bt: Current BT DSL
            combat_log: Combat summary
            previous_results: List of previous combat results
            
        Returns:
            Improved BT DSL or None if failed
        """
        # Get critic feedback
        prompt = create_critic_prompt(combat_log, current_bt, previous_results or [])
        feedback = self._call_llm(SYSTEM_PROMPT_CRITIC, prompt, temperature=0.5, use_critic_model=True)
        
        if "Error" in feedback:
            return None
        
        # Generate improved BT
        improved_bt, error = self.generate_improved_bt(current_bt, feedback)
        
        if error:
            return None
        
        return improved_bt
