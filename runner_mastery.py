"""
Enemy-Specific Training Mode Runner

New training system with enemy mastery:
1. Start with all enemies in active pool
2. Randomly select enemy from active pool for each iteration
3. On WIN: Run 5-battle validation test
4. If 100% win rate (5/5): Mark enemy as "mastered" and remove from pool
5. Continue until all enemies mastered or max iterations reached
"""

import os
import sys
import random
from datetime import datetime
from typing import Optional, Set

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.abstract_logger import AbstractLogger
from TextGame.bt_executor import create_bt_executor_from_dsl
from Agent.llm_agent import LLMAgent, MockLLMAgent
from Agent.ollama_agent import OllamaLLMAgent
from Agent.hybrid_agent import HybridLLMAgent
from Agent.single_stage_agent import SingleStageLLMAgent
from config import DEFAULT_LLM_CONFIG, DEFAULT_RUNNER_CONFIG


class ValidationTester:
    """Runs 5-battle validation test against ALL enemies"""
    
    def __init__(self, bt_dsl: str):
        self.bt_dsl = bt_dsl
    
    def run_validation_all_enemies(self) -> dict:
        """Run 20 battles against each enemy type and return results"""
        all_results = {}
        
        for enemy_type in [EnemyType.FIRE_GOLEM, EnemyType.ICE_WRAITH]:
            results = []
            
            for i in range(20):
                game = DungeonGame(enemy_type=enemy_type)
                executor = create_bt_executor_from_dsl(self.bt_dsl)
                
                if not executor:
                    return {'success': False, 'error': 'Failed to parse BT'}
                
                turn = 0
                max_turns = 35
                
                # Pre-telegraph
                if game.state.enemy:
                    game.engine.telegraph_enemy_action()
                
                while not game.game_over and turn < max_turns:
                    turn += 1
                    action = executor.execute(game.state)
                    if not action:
                        action = PlayerAction.ATTACK
                    
                    result = game.take_action(action)
                    
                    if game.game_over:
                        break
                
                results.append({
                    'victory': game.victory,
                    'turns': turn,
                    'player_hp': game.state.player.current_hp,
                    'enemy_hp': game.state.enemy.current_hp if game.state.enemy else 0
                })
            
            wins = sum(1 for r in results if r['victory'])
            all_results[enemy_type] = {
                'wins': wins,
                'total': 20,
                'win_rate': wins / 20.0,
                'results': results
            }
        
        # Calculate overall stats
        total_wins = sum(r['wins'] for r in all_results.values())
        total_battles = sum(r['total'] for r in all_results.values())
        overall_win_rate = total_wins / total_battles if total_battles > 0 else 0
        
        return {
            'success': True,
            'enemy_results': all_results,
            'total_wins': total_wins,
            'total_battles': total_battles,
            'overall_win_rate': overall_win_rate,
            'perfect': overall_win_rate == 1.0
        }


class GameRunner:
    """Runs single combat with BT and logging"""
    
    def __init__(self, bt_dsl: str, enemy_type: EnemyType, verbose: bool = False):
        self.bt_dsl = bt_dsl
        self.verbose = verbose
        self.enemy_type = enemy_type
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
        
        # Pre-telegraph first enemy action
        if self.game.state.enemy:
            self.game.engine.telegraph_enemy_action()
        
        while not self.game.game_over and turn < max_turns:
            turn += 1
            
            # Log turn start
            self.logger.log_turn_start(self.game.state)
            
            # Execute BT
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
                telegraph_msg = f" [Enemy telegraphs: {self.game.state.telegraphed_action}]" if self.game.state.telegraphed_action else ""
                print(f"Turn {turn}: {action.value} -> Player HP: {result['player_hp']}, Enemy HP: {result['enemy_hp']}{telegraph_msg}")
            
            if self.game.game_over:
                break
        
        # Generate summary
        summary = self.logger.generate_summary(self.game.state, self.game.victory, turn)
        critic_log = self.logger.generate_critic_log(self.game.state, self.game.victory, turn)
        
        return {
            'victory': self.game.victory,
            'turns': turn,
            'player_hp': self.game.state.player.current_hp,
            'enemy_hp': self.game.state.enemy.current_hp if self.game.state.enemy else 0,
            'enemy_type': self.enemy_type.value,
            'combat_log': self.logger.get_full_log(),
            'summary': summary,
            'critic_log': critic_log,
            'scanned': self.game.state.scanned
        }


class EnemyMasteryLoop:
    """LLM-driven BT improvement with enemy mastery system"""
    
    def __init__(self, config=None, agent=None):
        self.config = config or DEFAULT_RUNNER_CONFIG
        self.llm_config = DEFAULT_LLM_CONFIG
        
        if agent is None:
            raise ValueError("An LLM agent must be provided to EnemyMasteryLoop.")
        self.llm = agent
        
        self.iteration_results = []
        self.mastered_enemies: Set[EnemyType] = set()
        self.active_enemies: Set[EnemyType] = set(EnemyType)
        
        # Rollback tracking
        self.best_bt = None
        self.best_score = 0.0  # Total wins out of 40 (20 per enemy)
        self.iterations_without_improvement = 0
        self.best_iteration = -1
        
        # Create timestamp-based directories
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(self.config.log_directory, timestamp)
        self.bt_dir = os.path.join(self.config.bt_directory, timestamp)
        
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.bt_dir, exist_ok=True)
        
        print(f"[INFO] Logs will be saved to: {self.log_dir}")
        print(f"[INFO] BTs will be saved to: {self.bt_dir}")
    
    def run_iteration(self, iteration: int, bt_dsl: str) -> dict:
        """Run one iteration: game + optional validation"""
        # Select enemy from active pool
        if not self.active_enemies:
            print("[!] All enemies mastered!")
            return None
        
        enemy_type = random.choice(list(self.active_enemies))
        
        # Run game
        runner = GameRunner(bt_dsl, enemy_type=enemy_type, verbose=self.config.verbose)
        result = runner.run_game()
        
        # Get enemy max HP for display
        enemy_max_hp = result.get('enemy_hp', 0)
        if result['enemy_type'] == 'FireGolem':
            enemy_max_hp_total = 180
        else:  # IceWraith
            enemy_max_hp_total = 200
        
        # Save logs
        validation_status = ""
        if self.config.save_logs:
            log_file = os.path.join(
                self.log_dir,
                f"iter{iteration:02d}_{result['enemy_type']}_{'win' if result['victory'] else 'loss'}.txt"
            )
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(result['combat_log'])
                f.write("\n\n")
                f.write(result['summary'])
        
        # Save BT
        if self.config.save_bts:
            bt_file = os.path.join(
                self.bt_dir,
                f"iter{iteration:02d}_bt.txt"
            )
            with open(bt_file, 'w', encoding='utf-8') as f:
                f.write(bt_dsl)
        
        # Run validation test against ALL enemies (for both WIN and LOSS)
        validation_result = None
        should_stop = False
        
        # Always run validation test
        tester = ValidationTester(bt_dsl)
        validation_result = tester.run_validation_all_enemies()
        
        if validation_result['success']:
            # Format: FIREGOLEM[4/5], ICEWRAITH[3/5]
            enemy_results = validation_result['enemy_results']
            fg_result = enemy_results[EnemyType.FIRE_GOLEM]
            iw_result = enemy_results[EnemyType.ICE_WRAITH]
            
            validation_status = f"FIREGOLEM[{fg_result['wins']}/{fg_result['total']}], ICEWRAITH[{iw_result['wins']}/{iw_result['total']}]"
            
            # Update log file with validation status
            if self.config.save_logs:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n{'='*70}\n")
                    f.write(f"VALIDATION TEST: {validation_status}\n")
                    f.write(f"{'='*70}\n")
            
            # Check if both enemies have 80%+ win rate (4/5 or better)
            fg_win_rate = fg_result['wins'] / fg_result['total']
            iw_win_rate = iw_result['wins'] / iw_result['total']
            both_80_percent = fg_win_rate >= 0.8 and iw_win_rate >= 0.8
            
            # Stop if both enemies achieve 80%+ win rate (only on victory)
            if result['victory'] and both_80_percent:
                should_stop = True
                
                # Determine if it's perfect (100%) or excellent (80%+)
                is_perfect = validation_result['perfect']
                log_suffix = "PERFECT_100_PERCENT" if is_perfect else "EXCELLENT_80_PERCENT"
                
                # Save achievement log
                achievement_log_file = os.path.join(
                    self.log_dir,
                    f"iter{iteration:02d}_{log_suffix}.txt"
                )
                with open(achievement_log_file, 'w', encoding='utf-8') as f:
                    if is_perfect:
                        f.write(f"=== 100% WIN RATE ACHIEVED ===\n\n")
                    else:
                        f.write(f"=== 80%+ WIN RATE ACHIEVED ===\n\n")
                    f.write(f"Iteration: {iteration}\n")
                    f.write(f"Validation: {validation_status}\n\n")
                    f.write(f"FireGolem: {fg_result['wins']}/5 ({fg_win_rate*100:.0f}%)\n")
                    f.write(f"IceWraith: {iw_result['wins']}/5 ({iw_win_rate*100:.0f}%)\n\n")
                    for enemy_type_key, enemy_result in enemy_results.items():
                        f.write(f"\n{enemy_type_key.value} Details:\n")
                        for i, r in enumerate(enemy_result['results']):
                            f.write(f"  Battle {i+1}: {'WIN' if r['victory'] else 'LOSS'} - {r['turns']} turns\n")
        
        # Compact console output
        result_str = "WIN" if result['victory'] else "LOSS"
        hp_str = f"Player: {result['player_hp']}/100, Enemy: {result['enemy_hp']}/{enemy_max_hp_total}"
        
        if validation_status:
            print(f"[{iteration:02d}] {result['enemy_type']} {result_str} ({result['turns']} turns) | {hp_str} → {validation_status}")
            if should_stop:
                # Check if it's perfect or just excellent
                if validation_result and validation_result.get('perfect'):
                    print(f"     🎉 100% WIN RATE ACHIEVED!")
                else:
                    print(f"     ⭐ 80%+ WIN RATE ACHIEVED!")
        else:
            print(f"[{iteration:02d}] {result['enemy_type']} {result_str} ({result['turns']} turns) | {hp_str}")
        
        result['bt_dsl'] = bt_dsl
        result['validation'] = validation_result
        result['validation_status'] = validation_status
        result['should_stop'] = should_stop
        result['iteration'] = iteration  # Add iteration number to track
        
        # Track best BT based on validation score
        if validation_result and validation_result['success']:
            current_score = validation_result['total_wins']
            if current_score > self.best_score:
                self.best_score = current_score
                self.best_bt = bt_dsl
                self.best_iteration = iteration
                self.iterations_without_improvement = 0
                print(f"     ⭐ New best! Score: {current_score}/40 (iter {iteration})")
            else:
                self.iterations_without_improvement += 1
        
        return result

    
    def run(self, initial_bt_path: str = "examples/example_bt_balanced.txt"):
        """Run complete improvement loop with enemy mastery"""
        print("="*70)
        print("ENEMY MASTERY TRAINING MODE")
        print("="*70)
        print(f"Initial BT: {initial_bt_path}")
        print(f"Max iterations: {self.config.max_iterations}")
        print(f"LLM: {type(self.llm).__name__}")
        print("="*70)
        
        # Load initial BT
        with open(initial_bt_path, 'r', encoding='utf-8') as f:
            current_bt = f.read()
        
        # Run iterations
        for iteration in range(self.config.max_iterations):
            result = self.run_iteration(iteration, current_bt)
            
            if result is None:
                print("\n[!] All enemies mastered!")
                break
            
            self.iteration_results.append(result)
            
            # Check if 100% win rate achieved
            if result.get('should_stop', False):
                break
            
            # Generate improved BT using LLM (silent)
            if iteration < self.config.max_iterations - 1 and self.active_enemies:
                previous_results = self.iteration_results[-3:] if len(self.iteration_results) >= 3 else self.iteration_results
                
                improved_bt = self.llm.improve_bt(
                    current_bt=current_bt,
                    combat_log=result['critic_log'],
                    previous_results=previous_results
                )
                
                if improved_bt:
                    current_bt = improved_bt
                
                # Rollback check: If no improvement for 5 iterations, revert to best BT
                if self.iterations_without_improvement >= 5 and self.best_bt is not None:
                    print(f"\n[ROLLBACK] No improvement for 5 iterations. Reverting to best BT (iter {self.best_iteration}, score {self.best_score}/40)")
                    current_bt = self.best_bt
                    self.iterations_without_improvement = 0  # Reset counter
                    
                    # Save rollback event
                    rollback_file = os.path.join(self.bt_dir, f"iter{iteration:02d}_ROLLBACK.txt")
                    with open(rollback_file, 'w', encoding='utf-8') as f:
                        f.write(f"Rolled back to iteration {self.best_iteration}\n")
                        f.write(f"Best score: {self.best_score}/40\n\n")
                        f.write(current_bt)
        
        # Print final summary
        self._print_summary()
    
    def _run_final_test(self, bt_dsl: str):
        """Run final comprehensive test against all enemies (5 battles each)"""
        print(f"\n{'='*70}")
        print("FINAL COMPREHENSIVE TEST")
        print(f"{'='*70}\n")
        print("Testing final BT against all enemies (5 battles each)...\n")
        
        all_enemies = list(EnemyType)
        final_results = {}
        
        for enemy_type in all_enemies:
            print(f"Testing vs {enemy_type.value}...")
            tester = ValidationTester(bt_dsl, enemy_type)
            result = tester.run_validation()
            
            if result['success']:
                final_results[enemy_type] = result
                print(f"  Result: {result['wins']}/5 wins ({result['win_rate']*100:.0f}%)")
                
                # Save final test log
                final_log_file = os.path.join(
                    self.log_dir,
                    f"FINAL_TEST_{enemy_type.value}.txt"
                )
                with open(final_log_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== FINAL COMPREHENSIVE TEST: {enemy_type.value} ===\n\n")
                    f.write(f"Win Rate: {result['wins']}/5 ({result['win_rate']*100:.0f}%)\n\n")
                    for i, r in enumerate(result['results']):
                        f.write(f"Battle {i+1}: {'WIN' if r['victory'] else 'LOSS'} - {r['turns']} turns, "
                               f"Player HP: {r['player_hp']}, Enemy HP: {r['enemy_hp']}\n")
                print(f"  Saved: {final_log_file}")
            else:
                print(f"  ERROR: {result.get('error', 'Unknown error')}")
        
        # Print summary
        print(f"\n{'='*70}")
        print("FINAL TEST SUMMARY")
        print(f"{'='*70}\n")
        
        total_wins = sum(r['wins'] for r in final_results.values())
        total_battles = sum(r['total'] for r in final_results.values())
        overall_win_rate = (total_wins / total_battles * 100) if total_battles > 0 else 0
        
        for enemy_type, result in final_results.items():
            status = "✓" if result['mastered'] else "✗"
            print(f"  {status} {enemy_type.value:<15}: {result['wins']}/5 ({result['win_rate']*100:.0f}%)")
        
        print(f"\nOverall Performance: {total_wins}/{total_battles} ({overall_win_rate:.1f}%)")
        
        if overall_win_rate == 100.0:
            print("\n🎉 PERFECT SCORE! All enemies defeated with 100% win rate!")
        elif overall_win_rate >= 80.0:
            print("\n⭐ EXCELLENT! Strong performance across all enemies.")
        elif overall_win_rate >= 60.0:
            print("\n👍 GOOD! Decent performance, but room for improvement.")
        else:
            print("\n⚠️  NEEDS WORK! Consider further training.")
        
        # Save comprehensive summary
        summary_file = os.path.join(self.log_dir, "FINAL_TEST_SUMMARY.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=== FINAL COMPREHENSIVE TEST SUMMARY ===\n\n")
            f.write(f"Overall Win Rate: {total_wins}/{total_battles} ({overall_win_rate:.1f}%)\n\n")
            for enemy_type, result in final_results.items():
                f.write(f"{enemy_type.value}: {result['wins']}/5 ({result['win_rate']*100:.0f}%)\n")
        print(f"\nSaved summary: {summary_file}")
    
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
        
        print(f"\nIteration Details:")
        # Use actual iteration numbers from results to avoid duplicates
        seen_iterations = set()
        for r in self.iteration_results:
            iter_num = r.get('iteration', -1)
            # Skip duplicates
            if iter_num in seen_iterations:
                continue
            seen_iterations.add(iter_num)
            
            status = "WIN " if r['victory'] else "LOSS"
            val_str = ""
            if r.get('validation_status'):
                val_str = f" [{r['validation_status']}]"
            print(f"  {iter_num}: {status} vs {r['enemy_type']:<15} - {r['turns']:2d} turns{val_str}")



def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Enemy Mastery Training Mode")
    parser.add_argument('--iterations', type=int, default=20, help='Max iterations')
    parser.add_argument('--mock', action='store_true', help='Use mock LLM')
    parser.add_argument('--ollama', action='store_true', help='Use Ollama for both critic and generator')
    parser.add_argument('--hybrid', action='store_true', help='Use hybrid mode (Ollama critic + Gemini generator)')
    parser.add_argument('--ollama-model', type=str, default='gemma3:4b', help='Ollama model to use')
    parser.add_argument('--single-stage', action='store_true', help='Use single-stage LLM (combined critic+generator in one call)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--bt', type=str, default='examples/example_bt_balanced.txt', help='Initial BT file')
    parser.add_argument('--manual', action='store_true', help='Use examples/manual.txt as initial BT (manual mode)')
    
    args = parser.parse_args()
    
    # Override BT file if manual mode
    if args.manual:
        args.bt = 'examples/manual.txt'
        print("[INFO] Manual mode: Using examples/manual.txt as initial BT")
    
    config = DEFAULT_RUNNER_CONFIG
    config.max_iterations = args.iterations
    config.verbose = args.verbose
    
    # Select agent based on mode
    if args.mock:
        print("[MODE] Mock LLM (no API calls)")
        agent = MockLLMAgent()
    elif args.single_stage:
        print("[MODE] Single-Stage LLM (combined critic+generator)")
        agent = SingleStageLLMAgent(DEFAULT_LLM_CONFIG)
    elif args.hybrid:
        print("[MODE] Hybrid (Ollama Critic + Gemini Generator)")
        agent = HybridLLMAgent(DEFAULT_LLM_CONFIG, ollama_model=args.ollama_model)
    elif args.ollama:
        print(f"[MODE] Ollama Only (model: {args.ollama_model})")
        agent = OllamaLLMAgent(model=args.ollama_model)
    else:
        print("[MODE] Full Gemini (Critic + Generator)")
        agent = LLMAgent(DEFAULT_LLM_CONFIG)
    
    loop = EnemyMasteryLoop(config, agent=agent)
    loop.run(args.bt)


if __name__ == "__main__":
    main()
