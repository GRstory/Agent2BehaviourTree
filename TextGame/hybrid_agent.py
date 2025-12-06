"""
Hybrid LLM Agent - Best of Both Worlds

Uses local Gemma 3 for critic (fast, free) and Gemini API for generator (accurate).
"""

from typing import Optional, Tuple
from .ollama_agent import OllamaLLMAgent
from .llm_agent import LLMAgent


class HybridLLMAgent:
    """Hybrid agent using Ollama for critic and Gemini for generator"""
    
    def __init__(self, gemini_config, ollama_model: str = "gemma3:4b"):
        """
        Initialize hybrid agent
        
        Args:
            gemini_config: Config for Gemini API
            ollama_model: Ollama model for critic
        """
        print("[HYBRID] Initializing hybrid LLM agent...")
        print(f"  Critic: Ollama {ollama_model} (local, free)")
        print(f"  Generator: Gemini API (cloud, accurate)")
        
        # Critic uses Ollama (local)
        self.critic = OllamaLLMAgent(model=ollama_model)
        
        # Generator uses Gemini (API)
        self.generator = LLMAgent(gemini_config)
    
    def improve_bt(self, current_bt: str, combat_log: str, previous_results: list = None) -> Optional[str]:
        """
        Improve BT using hybrid approach
        
        Args:
            current_bt: Current BT DSL
            combat_log: Combat summary
            previous_results: List of previous combat results
            
        Returns:
            Improved BT DSL or None if failed
        """
        print("[HYBRID] Improving BT with hybrid approach...")
        
        # Import prompts
        from .prompts import (
            create_critic_prompt,
            create_generator_prompt,
            SYSTEM_PROMPT_CRITIC,
            SYSTEM_PROMPT_BT_GENERATOR,
            extract_bt_from_response
        )
        
        # Step 1: Critic analysis using Ollama (local, fast)
        print("[CRITIC] Using Ollama Gemma 3 4B (local)...")
        prompt = create_critic_prompt(combat_log, current_bt, previous_results or [])
        feedback = self.critic._call_llm(SYSTEM_PROMPT_CRITIC, prompt, temperature=0.5)
        
        if "Error" in feedback:
            print(f"[ERROR] Critic failed: {feedback}")
            return None
        
        print("[OK] Critic analysis complete")
        
        # Step 2: Generator using Gemini (API, accurate)
        print("[GENERATOR] Using Gemini API (cloud)...")
        improved_bt, error = self.generator.generate_improved_bt(current_bt, feedback)
        
        if error:
            print(f"[ERROR] Generator failed: {error}")
            return None
        
        print("[OK] Improved BT generated")
        return improved_bt
    
    def generate_initial_bt(self) -> str:
        """Generate initial BT (use example instead)"""
        print("[HYBRID] Using example BT as initial")
        with open("examples/example_bt_balanced.txt", 'r') as f:
            return f.read()
