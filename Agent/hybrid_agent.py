"""
Hybrid LLM Agent - Best of Both Worlds

Uses local Gemma 3 for critic (fast, free) and Gemini API for generator (accurate).
Includes adaptive temperature to escape local minima.
"""

import os
from datetime import datetime
from typing import Optional
from .ollama_agent import OllamaLLMAgent
from .llm_agent import LLMAgent


class HybridLLMAgent:
    """Hybrid agent using Ollama for critic and Gemini for generator with adaptive temperature"""
    
    def __init__(self, config, ollama_model: str = "gemma3:4b"):
        """
        Initialize hybrid LLM agent
        
        Args:
            config: LLM configuration
            ollama_model: Ollama model name for critic
        """

        
        self.critic = OllamaLLMAgent(model=ollama_model)
        self.generator = LLMAgent(config)
        self.iteration = 0
        
        # Adaptive temperature for escaping local minima
        self.base_temperature = 0.7
        self.current_temperature = 0.7
        self.no_improvement_count = 0
        self.best_score = -float('inf')
        
        # Create timestamped log directory
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join("llm_logs", self.session_timestamp)
        os.makedirs(self.log_dir, exist_ok=True)

    
    def _save_llm_log(self, agent_type: str, system_prompt: str, user_prompt: str, response: str):
        """Save LLM communication log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"iter{self.iteration:02d}_{agent_type}_{timestamp}.txt")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"{agent_type.upper()} LLM LOG\n")
            f.write(f"Iteration: {self.iteration}\n")
            f.write(f"Timestamp: {timestamp}\n")
            if agent_type == "generator":
                f.write(f"Temperature: {self.current_temperature}\n")
                f.write(f"No improvement count: {self.no_improvement_count}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("SYSTEM PROMPT\n")
            f.write("-" * 80 + "\n")
            f.write(system_prompt + "\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("USER PROMPT\n")
            f.write("-" * 80 + "\n")
            f.write(user_prompt + "\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("RESPONSE\n")
            f.write("-" * 80 + "\n")
            f.write(response + "\n\n")
            
            f.write("=" * 80 + "\n")
            f.write(f"Prompt length: {len(user_prompt)} chars\n")
            f.write(f"Response length: {len(response)} chars\n")
            f.write("=" * 80 + "\n")
        

    
    def _update_temperature(self, current_score: float):
        """
        Update temperature based on performance to escape local minima
        
        Args:
            current_score: Current iteration score (e.g., turns survived, or 1000 if victory)
        """
        # Check if we improved
        if current_score > self.best_score:
            self.best_score = current_score
            self.no_improvement_count = 0
            # Reset to base temperature on improvement
            self.current_temperature = self.base_temperature

        else:
            self.no_improvement_count += 1
            
            # Increase temperature if stuck (no improvement for 3+ iterations)
            if self.no_improvement_count >= 3:
                # Gradually increase temperature (max 1.2)
                self.current_temperature = min(1.2, self.base_temperature + (self.no_improvement_count - 2) * 0.1)

    
    def improve_bt(self, current_bt: str, combat_log: str, previous_results: list = None) -> Optional[str]:
        """
        Improve BT using hybrid approach (Ollama critic + Gemini generator)
        
        Args:
            current_bt: Current behaviour tree DSL
            combat_log: Combat summary/log
            previous_results: List of previous iteration results
            
        Returns:
            Improved BT DSL or None if failed
        """

        
        # Calculate current score for temperature adaptation
        if previous_results and len(previous_results) > 0:
            last_result = previous_results[-1]
            # Score: 1000 for victory, otherwise turns survived
            current_score = 1000 if last_result.get('victory', False) else last_result.get('turns', 0)
            self._update_temperature(current_score)
        
        from .prompts import (
            create_critic_prompt,
            create_generator_prompt,
            SYSTEM_PROMPT_CRITIC,
            SYSTEM_PROMPT_BT_GENERATOR,
            extract_bt_from_response
        )
        
        # Step 1: Critic analysis using Ollama (local, fast)

        critic_user_prompt = create_critic_prompt(combat_log, current_bt, previous_results or [])
        feedback = self.critic._call_llm(SYSTEM_PROMPT_CRITIC, critic_user_prompt, temperature=0.5)
        
        # Save critic log
        self._save_llm_log("critic", SYSTEM_PROMPT_CRITIC, critic_user_prompt, feedback)
        
        if "Error" in feedback:
            print(f"[ERROR] Critic failed: {feedback}")
            print(f"[FALLBACK] Keeping current BT and continuing...")
            return None  # Keep current BT, continue to next iteration
        

        
        # Step 2: Generator using Gemini (API, accurate) with adaptive temperature

        
        try:
            generator_user_prompt = create_generator_prompt(current_bt, feedback)

            
            # Call generator and capture response with adaptive temperature

            response = self.generator._call_llm(SYSTEM_PROMPT_BT_GENERATOR, generator_user_prompt, temperature=self.current_temperature)

            
            # Save generator log
            self._save_llm_log("generator", SYSTEM_PROMPT_BT_GENERATOR, generator_user_prompt, response)
            
            # Check for error in response
            if "Error" in response:
                print(f"[ERROR] Generator returned error: {response}")
                print(f"[FALLBACK] Keeping current BT and continuing...")
                return None  # Keep current BT, continue to next iteration
            

            improved_bt = extract_bt_from_response(response).strip()

            
            # Validate the generated BT
            is_valid, error_msg = self.generator._validate_bt(improved_bt)
            if not is_valid:
                print(f"[WARNING] Generated BT failed validation: {error_msg}")

                print("[FALLBACK] Keeping current BT and continuing...")
                return None  # Keep current BT, continue to next iteration
            

            
            # Increment iteration counter
            self.iteration += 1
            
            return improved_bt
            
        except Exception as e:
            print(f"[ERROR] Exception in Generator step: {e}")
            print(f"[FALLBACK] Keeping current BT and continuing...")
            import traceback
            traceback.print_exc()
            return None  # Keep current BT, continue to next iteration
    
    def generate_initial_bt(self) -> str:
        """Generate initial BT (use example instead)"""
        print("[HYBRID] Using example BT as initial")
        with open("examples/example_bt_balanced.txt", 'r') as f:
            return f.read()
