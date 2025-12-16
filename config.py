"""
Configuration Settings for Dungeon Game and LLM Agent
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class GameConfig:
    """Game engine configuration"""
    # Single-floor combat (no floor progression)
    max_floors: int = 1
    turn_limit: int = 35
    
    # Player stats
    player_starting_hp: int = 100
    player_base_attack: int = 15
    player_defense: int = 5
    
    # Player resources
    player_starting_tp: int = 50
    player_max_tp: int = 100
    player_tp_regen: int = 15
    player_starting_mp: int = 100
    player_max_mp: int = 100
    player_mp_regen: int = 12
    
    # Player abilities
    heal_amount: int = 45
    heal_cooldown: int = 3
    
    # Enemy stats (defined per enemy type in game_engine.py)
    # Fire Golem: HP 200, Atk 22, Def 14
    # Ice Wraith: HP 180, Atk 16, Def 8
    # Thunder Drake: HP 220, Atk 20, Def 10
    
    # Combat mechanics
    crit_chance: float = 0.20
    elemental_weakness_multiplier: float = 1.5
    elemental_resistance_multiplier: float = 0.5


@dataclass
class LLMConfig:
    """LLM agent configuration"""
    api_key: str = None
    provider: str = "gemini"  # "gemini", "openai", "ollama"
    
    # Gemini settings
    model: str = "gemini-2.0-flash"
    critic_model: str = "gemini-2.0-flash"
    
    # OpenAI settings
    openai_api_key: str = None
    openai_model: str = "gpt-5.2"
    openai_critic_model: str = "gpt-5.2"
    
    # Common settings
    temperature_generation: float = 0.7
    temperature_analysis: float = 0.5
    temperature_feedback: float = 0.6
    max_tokens: int = 2000
    
    def __post_init__(self):
        if self.api_key is None:
            if self.provider == "gemini":
                self.api_key = os.getenv("GEMINI_API_KEY")
            elif self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
                if self.openai_api_key is None:
                    self.openai_api_key = self.api_key


@dataclass
class RunnerConfig:
    """Main runner configuration"""
    max_iterations: int = 10
    use_mock_llm: bool = False
    save_logs: bool = True
    log_directory: str = "logs"
    save_bts: bool = True
    bt_directory: str = "generated_bts"
    verbose: bool = True
    
    # Convergence criteria
    victory_early_stop: bool = False  # Continue even after victory
    single_run: bool = False


# Default configurations
DEFAULT_GAME_CONFIG = GameConfig()
DEFAULT_LLM_CONFIG = LLMConfig()
DEFAULT_RUNNER_CONFIG = RunnerConfig()
