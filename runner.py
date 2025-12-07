"""
Main Runner for Enhanced Combat System

Orchestrates LLM improvement loop:
1. Run game with current BT
2. Analyze combat logs
3. Generate improved BT
4. Repeat
"""

import os
import sys
import random
from datetime import datetime
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.abstract_logger import AbstractLogger
from TextGame.bt_executor import create_bt_executor_from_dsl
from TextGame.llm_agent import LLMAgent, MockLLMAgent
from TextGame.ollama_agent import OllamaLLMAgent
from TextGame.hybrid_agent import HybridLLMAgent
from config import DEFAULT_LLM_CONFIG, DEFAULT_RUNNER_CONFIG


class GameRunner:
    """Runs single combat with BT and logging"""
    
    def __init__(self, bt_dsl: str, enemy_type: Optional[EnemyType] = None, verbose: bool = False):
        self.bt_dsl = bt_dsl
        self.verbose = verbose
        self.enemy_type = enemy_type if enemy_type else random.choice(list(EnemyType))
        self.game = DungeonGame(self.enemy_type)
        self.logger = AbstractLogger()
        self.executor = create_bt_executor_from_dsl(bt_dsl)
        
        if self.executor is None:
            raise ValueError("Failed to parse BT DSL")
    
    def run_game(self) -> dict:
        """Run complete combat and return results"""
        self.logger.start_combat(self.game.state)
        
        turn = 0
        max_turns = 35
        
        while not self.game.game_over and turn < max_turns:
            turn += 1
            
            # Log turn start
            self.logger.log_turn_start(self.game.state)
            
            # Execute BT to get action
            action = self.executor.execute(self.game.state)
            if not action:
                if self.verbose:
                    print(f"Turn {turn}: BT returned no action, using Attack")
                action = PlayerAction.ATTACK
            
            # Execute action
            result = self.game.take_action(action)
            
            # Log actions
            self.logger.log_player_action(action, result['player_info'], self.game.state)
            self.logger.log_enemy_action(result['enemy_info'], self.game.state)
            self.logger.log_turn_end(self.game.state)
            
            if self.verbose:
                print(f"Turn {turn}: {action.value} -> Player HP: {result['player_hp']}, Enemy HP: {result['enemy_hp']}")
            
            if self.game.game_over:
                break
        
        # Generate summary
        summary = self.logger.generate_summary(self.game.state, self.game.victory, turn)
        
        return {
            'victory': self.game.victory,
            'turns': turn,
            'player_hp': self.game.state.player.current_hp,
            'enemy_hp': self.game.state.enemy.current_hp if self.game.state.enemy else 0,
            'enemy_type': self.enemy_type.value,
            'scanned': self.game.state.scanned,
            'combat_log': self.logger.get_full_log(),
            'summary': summary
        }


class ImprovementLoop:
    """LLM-driven BT improvement loop"""
    
    def __init__(self, config=None, use_mock=False, use_ollama=False, use_hybrid=False, ollama_model="gemma3:4b"):
        self.config = config or DEFAULT_RUNNER_CONFIG
        self.llm_config = DEFAULT_LLM_CONFIG
        
        if use_hybrid:
            self.llm = HybridLLMAgent(self.llm_config, ollama_model=ollama_model)
        elif use_ollama:
            self.llm = OllamaLLMAgent(model=ollama_model)
        elif use_mock or self.config.use_mock_llm:
            self.llm = MockLLMAgent(self.llm_config)
        else:
            self.llm = LLMAgent(self.llm_config)
        
        self.iteration_results = []
        
        # Create timestamp-based directories
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(self.config.log_directory, timestamp)
        self.bt_dir = os.path.join(self.config.bt_directory, timestamp)
        
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.bt_dir, exist_ok=True)
        
        print(f"[INFO] Logs will be saved to: {self.log_dir}")
        print(f"[INFO] BTs will be saved to: {self.bt_dir}")
    
    def run_iteration(self, iteration: int, bt_dsl: str) -> dict:
        """Run one iteration: game + analysis"""
        print(f"\n{'='*70}")
        print(f"ITERATION {iteration}")
        print(f"{'='*70}\n")
        
        # Run game with current BT (always use FireGolem for consistent testing)
        runner = GameRunner(bt_dsl, enemy_type=EnemyType.FIRE_GOLEM, verbose=self.config.verbose)
        result = runner.run_game()
        
        print(f"\nResult: {'VICTORY' if result['victory'] else 'DEFEAT'}")
        print(f"Enemy: {result['enemy_type']}")
        print(f"Turns: {result['turns']}")
        print(f"Final Player HP: {result['player_hp']}/100")
        print(f"Scanned: {result['scanned']}")
        
        # Save logs
        if self.config.save_logs:
            log_file = os.path.join(
                self.log_dir,
                f"iter{iteration:02d}_{result['enemy_type']}_{'win' if result['victory'] else 'loss'}.txt"
            )
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(result['combat_log'])
                f.write("\n\n")
                f.write(result['summary'])
            print(f"Saved log: {log_file}")
        
        # Save BT
        if self.config.save_bts:
            bt_file = os.path.join(
                self.bt_dir,
                f"iter{iteration:02d}_bt.txt"
            )
            with open(bt_file, 'w', encoding='utf-8') as f:
                f.write(bt_dsl)
            print(f"Saved BT: {bt_file}")
        
        result['bt_dsl'] = bt_dsl
        return result
    
    def run(self, initial_bt_path: str = "examples/example_bt_balanced.txt"):
        """Run complete improvement loop"""
        print("="*70)
        print("ENHANCED COMBAT SYSTEM - LLM IMPROVEMENT LOOP")
        print("="*70)
        
        # Load initial BT
        with open(initial_bt_path, 'r', encoding='utf-8') as f:
            current_bt = f.read()
        
        print(f"\nLoaded initial BT from: {initial_bt_path}")
        print(f"Max iterations: {self.config.max_iterations}")
        print(f"Using LLM: {type(self.llm).__name__}")
        
        # Run iterations
        for iteration in range(self.config.max_iterations):
            result = self.run_iteration(iteration, current_bt)
            self.iteration_results.append(result)
            
            # Check for early stop
            if result['victory'] and self.config.victory_early_stop:
                print(f"\n[!] Victory achieved! Stopping early.")
                break
            
            # Generate improved BT using LLM
            if iteration < self.config.max_iterations - 1:
                print(f"\nGenerating improved BT...")
                
                # Prepare context for LLM
                previous_results = self.iteration_results[-3:] if len(self.iteration_results) >= 3 else self.iteration_results
                
                improved_bt = self.llm.improve_bt(
                    current_bt=current_bt,
                    combat_log=result['summary'],
                    previous_results=previous_results
                )
                
                if improved_bt:
                    current_bt = improved_bt
                    print("[OK] BT improved")
                else:
                    print("[!] Failed to improve BT, keeping current")
        
        # Print final summary
        self._print_summary()
    
    def _print_summary(self):
        """Print summary of all iterations"""
        print(f"\n{'='*70}")
        print("FINAL SUMMARY")
        print(f"{'='*70}\n")
        
        victories = sum(1 for r in self.iteration_results if r['victory'])
        total = len(self.iteration_results)
        
        print(f"Total Iterations: {total}")
        print(f"Victories: {victories}/{total} ({victories/total*100:.1f}%)")
        print(f"Average Turns: {sum(r['turns'] for r in self.iteration_results) / total:.1f}")
        print(f"Scanned: {sum(1 for r in self.iteration_results if r['scanned'])}/{total}")
        
        print(f"\nIteration Details:")
        for i, r in enumerate(self.iteration_results):
            status = "WIN " if r['victory'] else "LOSS"
            print(f"  {i}: {status} vs {r['enemy_type']:<15} - {r['turns']:2d} turns, {r['player_hp']:3d} HP")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Enhanced Combat System")
    parser.add_argument('--iterations', type=int, default=10, help='Max iterations')
    parser.add_argument('--mock', action='store_true', help='Use mock LLM')
    parser.add_argument('--ollama', action='store_true', help='Use local Ollama LLM (both critic & generator)')
    parser.add_argument('--hybrid', action='store_true', help='Use hybrid mode (Ollama critic + Gemini generator)')
    parser.add_argument('--ollama-model', type=str, default='gemma3:4b', help='Ollama model name')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--bt', type=str, default='examples/example_bt_balanced.txt', help='Initial BT file')
    parser.add_argument('--single', action='store_true', help='Single run (no improvement)')
    
    args = parser.parse_args()
    
    if args.single:
        # Single run
        with open(args.bt, 'r', encoding='utf-8') as f:
            bt_dsl = f.read()
        
        runner = GameRunner(bt_dsl, verbose=True)
        result = runner.run_game()
        
        print(f"\n{'='*70}")
        print("RESULT")
        print(f"{'='*70}")
        print(f"Victory: {result['victory']}")
        print(f"Enemy: {result['enemy_type']}")
        print(f"Turns: {result['turns']}")
        print(f"Final HP: {result['player_hp']}/100")
        print(f"\n{result['summary']}")
    else:
        # Improvement loop
        config = DEFAULT_RUNNER_CONFIG
        config.max_iterations = args.iterations
        config.verbose = args.verbose
        
        loop = ImprovementLoop(
            config, 
            use_mock=args.mock,
            use_ollama=args.ollama,
            use_hybrid=args.hybrid,
            ollama_model=args.ollama_model
        )
        loop.run(args.bt)


if __name__ == "__main__":
    main()
