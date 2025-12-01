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
    max_floors: int = 10
    player_starting_hp: int = 100
    player_base_attack: int = 15
    player_defense: int = 5
    
    heal_amount: int = 30
    heal_cooldown: int = 3
    defend_bonus: int = 10
    
    # Enemy scaling
    enemy_base_hp: int = 50
    enemy_hp_per_floor: int = 10
    enemy_base_attack: int = 10
    enemy_attack_per_floor: int = 2
    enemy_base_defense: int = 2
    enemy_defense_per_floor: int = 1
    boss_multiplier: float = 1.2


@dataclass
class LLMConfig:
    """LLM agent configuration"""
    api_key: str = None
    model: str = "gemini-2.5-pro"
    critic_model: str = "gemini-2.5-flash"
    temperature_generation: float = 0.7
    temperature_analysis: float = 0.5
    temperature_feedback: float = 0.6
    max_tokens: int = 2000
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("GEMINI_API_KEY")


@dataclass
class RunnerConfig:
    """Main runner configuration"""
    max_iterations: int = 5
    use_mock_llm: bool = False  # Set to True for testing without API
    save_logs: bool = True
    log_directory: str = "logs"
    save_bts: bool = True
    bt_directory: str = "generated_bts"
    verbose: bool = True
    
    # Convergence criteria
    min_floor_improvement: int = 2  # Stop if no improvement in floor count
    min_floor_improvement: int = 2  # Stop if no improvement in floor count
    victory_early_stop: bool = True  # Stop if victory achieved
    single_run: bool = False  # Run once without improvement loop


# Default configurations
DEFAULT_GAME_CONFIG = GameConfig()
DEFAULT_LLM_CONFIG = LLMConfig()
DEFAULT_RUNNER_CONFIG = RunnerConfig()
