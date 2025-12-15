"""
Local LLM Agent using Ollama

Supports local models like Gemma 2 4B for cost-free BT improvement.
"""

from typing import Optional, Tuple
import requests
import json


class OllamaLLMAgent:
    """LLM agent using local Ollama models"""
    
    def __init__(self, model: str = "gemma3:4b", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama LLM agent
        
        Args:
            model: Ollama model name (e.g., "gemma3:4b", "gemma2:9b")
            base_url: Ollama API base URL
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
        # Test connection and check model
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if model not in model_names:
                    self._install_model(model)
                else:
                    pass  # Model already available
            else:
                print(f"[WARNING] Ollama connection failed: {response.status_code}")
        except Exception as e:
            print(f"[WARNING] Could not connect to Ollama: {e}")
            print(f"Make sure Ollama is running: ollama serve")
    
    def _install_model(self, model: str):
        """Auto-install Ollama model"""
        import subprocess
        
        try:

            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"[OK] Model {model} installed successfully!")
            else:
                print(f"[ERROR] Failed to install model: {result.stderr}")
                print(f"Please manually run: ollama pull {model}")
        except subprocess.TimeoutExpired:
            print(f"[ERROR] Installation timed out. Please manually run: ollama pull {model}")
        except FileNotFoundError:
            print(f"[ERROR] 'ollama' command not found. Please install Ollama first.")
        except Exception as e:
            print(f"[ERROR] Installation failed: {e}")
            print(f"Please manually run: ollama pull {model}")
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Call Ollama API
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Sampling temperature
            
        Returns:
            LLM response text
        """
        # Combine prompts
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        

        
        payload = {
            "model": self.model,
            "prompt": combined_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2000
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=120  # Local models can be slow
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                return f"Error: Ollama API returned {response.status_code}"
        
        except Exception as e:
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
        Improve BT based on combat log
        
        Args:
            current_bt: Current BT DSL
            combat_log: Combat summary
            previous_results: List of previous combat results
            
        Returns:
            Improved BT DSL or None if failed
        """

        
        # Import prompts
        from .prompts import (
            create_critic_prompt,
            create_generator_prompt,
            SYSTEM_PROMPT_CRITIC,
            SYSTEM_PROMPT_BT_GENERATOR,
            extract_bt_from_response
        )
        
        # Get critic feedback
        prompt = create_critic_prompt(combat_log, current_bt, previous_results or [])
        feedback = self._call_llm(SYSTEM_PROMPT_CRITIC, prompt, temperature=0.5)
        
        if "Error" in feedback:
            print(f"[ERROR] Critic failed: {feedback}")
            return None
        
        print("[OK] Critic analysis complete")
        
        # Generate improved BT

        prompt = create_generator_prompt(current_bt, feedback)
        response = self._call_llm(SYSTEM_PROMPT_BT_GENERATOR, prompt, temperature=0.7)
        
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
        """Generate initial BT (not implemented for local, use example instead)"""

        with open("examples/example_bt_balanced.txt", 'r') as f:
            return f.read()
