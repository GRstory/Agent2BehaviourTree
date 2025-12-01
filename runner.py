"""
Main Runner for PORTAL-Inspired Dungeon Game

Orchestrates the complete LLM improvement loop:
1. Generate initial BT
2. Execute game with BT
3. Analyze logs
4. Generate feedback
5. Improve BT
6. Repeat
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TextGame.game_engine import DungeonGame, ActionType
from TextGame.abstract_logger import AbstractLogger
from TextGame.bt_executor import create_bt_executor_from_dsl
from TextGame.llm_agent import LLMAgent, MockLLMAgent
from config import DEFAULT_GAME_CONFIG, DEFAULT_LLM_CONFIG, DEFAULT_RUNNER_CONFIG


class GameRunner:
    """Runs the complete game with BT and logging"""
    
    def __init__(self, bt_dsl: str, verbose: bool = True):
        self.bt_dsl = bt_dsl
        self.verbose = verbose
        self.game = DungeonGame()
        self.logger = AbstractLogger()
        self.executor = create_bt_executor_from_dsl(bt_dsl)
        
        if self.executor is None:
            raise ValueError("Failed to parse BT DSL")
    
    def _print_debug(self, message: str):
        """Print debug message to console only (not in LLM log)"""
        if self.verbose:
            print(message)
    
    def _print_turn_header(self, floor: int, turn: int):
        """Print detailed turn header to console"""
        if self.verbose:
            print(f"\n{'─'*70}")
            floor_label = f"FLOOR {floor}" + (" [BOSS]" if floor % 5 == 0 else "")
            print(f"│ {floor_label:<30} Turn {turn:>3} │")
            print(f"{'─'*70}")
    
    def _print_state(self):
        """Print detailed game state to console"""
        if not self.verbose:
            return
        
        state = self.game.state
        player_hp_pct = state.player.hp_percentage()
        enemy_hp_pct = state.enemy.hp_percentage() if state.enemy else 0
        
        # Player status
        print(f"│ 플레이어 HP: {state.player.current_hp:>3}/{state.player.max_hp:<3} ({player_hp_pct:>5.1f}%)", end="")
        if state.is_defending:
            print(" [방어중]", end="")
        print(" " * (70 - 45 - (9 if state.is_defending else 0)) + "│")
        
        # Enemy status
        if state.enemy:
            print(f"│ 적 HP:       {state.enemy.current_hp:>3}/{state.enemy.max_hp:<3} ({enemy_hp_pct:>5.1f}%)" + " " * 24 + "│")
        
        # Heal cooldown
        if state.heal_cooldown > 0:
            print(f"│ 힐 쿨다운:   {state.heal_cooldown}턴 남음" + " " * 44 + "│")
        else:
            print(f"│ 힐 상태:     사용 가능" + " " * 43 + "│")
        
        print(f"{'─'*70}")
    
    def _print_action_result(self, action: ActionType, enemy_damage: int, player_damage: int, combo: str = None):
        """Print action result to console"""
        if not self.verbose:
            return
        
        print(f"│ 행동: {action.value:<20}", end="")
        
        if action in [ActionType.LIGHT_ATTACK, ActionType.HEAVY_ATTACK]:
            print(f"적에게 {enemy_damage} 데미지!", end="")
            if combo:
                print(f" [COMBO: {combo}]", end="")
        elif action == ActionType.DEFEND:
            print(f"방어 태세!", end="")
        elif action == ActionType.HEAL:
            if enemy_damage > 0:  # Using enemy_damage as heal amount
                print(f"{enemy_damage} HP 회복!", end="")
            else:
                print(f"실패 (쿨다운)", end="")
        
        print(" " * (70 - 45 - len(action.value)) + "│")
        
        if player_damage > 0:
            print(f"│ 적의 반격: {player_damage} 데미지 받음!" + " " * 40 + "│")
    
    def run_game(self) -> dict:
        """
        Run complete game and return results
        
        Returns:
            Dict with 'victory', 'final_floor', 'total_turns', 'log', 'summary', 'defeat_reason'
        """
        total_turns = 0
        defeat_reason = None
        
        if self.verbose:
            print("\n" + "="*70)
            print(" "*20 + "게임 시작!")
            print("="*70)
        
        while not self.game.game_over:
            # Print debug turn header (Disabled for cleaner output)
            # self._print_turn_header(self.game.state.current_floor, self.game.state.turn_count + 1)
            # self._print_state()
            
            # Log turn start (for LLM)
            self.logger.log_turn_start(self.game.state)
            
            # Execute BT to get action
            action = self.executor.execute(self.game.state)
            
            if action is None:
                self._print_debug("[WARNING] BT가 행동을 결정하지 못함, 기본 약공격 사용")
                action = ActionType.LIGHT_ATTACK
            
            # Store old state for logging
            old_player_hp = self.game.state.player.current_hp
            old_enemy_hp = self.game.state.enemy.current_hp if self.game.state.enemy else 0
            
            # Execute action in game
            turn_info = self.game.take_action(action)
            total_turns += 1
            
            # Track defeat reason if present
            if 'defeat_reason' in turn_info:
                defeat_reason = turn_info['defeat_reason']
            
            # Calculate values for logging
            player_hp_change = turn_info['player_hp_change']
            enemy_hp_change = turn_info['enemy_hp_change']
            enemy_damage = abs(enemy_hp_change) if enemy_hp_change < 0 else abs(enemy_hp_change)
            player_damage = abs(player_hp_change) if player_hp_change < 0 else 0
            combo = turn_info.get('combo')  # Extract combo from turn_info
            
            # Print action result to console (Disabled for cleaner output)
            # self._print_action_result(action, enemy_damage, player_damage, combo)
            
            # Log player action (for LLM)
            self.logger.log_player_action(
                action, 
                enemy_damage, 
                combo, 
                self.game.state
            )
            
            # Log enemy action if game continues (for LLM)
            if not self.game.game_over and turn_info['result'] == 'continue':
                self.logger.log_enemy_action("Attack", player_damage, self.game.state)
            
            # Log floor cleared
            if turn_info.get('floor_cleared'):
                self.logger.log_floor_cleared(turn_info['floor'] - 1)
                if self.verbose:
                    print(f"{'─'*70}")
                    print(f"│ {str(turn_info['floor'] - 1) + '층 클리어!':^66} │")
                    print(f"{'─'*70}\n")
                
                # Start new stage for next floor
                self.logger.start_new_stage(self.game.state.current_floor)
            
            # Update state snapshot
            self.logger.update_state_snapshot(self.game.state)
        
        # Log game over with defeat reason
        self.logger.log_game_over(self.game.victory, self.game.state.current_floor, defeat_reason)
        
        # Print final result to console
        if self.verbose:
            print("\n" + "="*70)
            if self.game.victory:
                print(" "*25 + "[승리!]")
                print(f" "*20 + f"전체 10층 클리어!")
            else:
                print(" "*25 + "[패배]")
                if defeat_reason == "turn_limit_exceeded":
                    print(f" "*15 + f"{self.game.state.current_floor}층에서 30턴 초과로 패배")
                else:
                    print(f" "*20 + f"{self.game.state.current_floor}층에서 사망")
            print(f" "*20 + f"총 {total_turns}턴 소요")
            print("="*70 + "\n")
        
        # Generate summary
        summary = self.logger.generate_summary(self.game.state, total_turns)
        
        return {
            'victory': self.game.victory,
            'final_floor': self.game.state.current_floor if self.game.victory else self.game.state.current_floor,
            'total_turns': total_turns,
            'log': self.logger.get_full_log(),
            'last_stage_log': self.logger.get_last_stage_log(),  # Only last stage for LLM
            'stage_history': self.logger.get_stage_history(),    # History of all stages
            'summary': summary,
            'defeat_reason': defeat_reason  # Add defeat reason to results
        }


class ImprovementLoop:
    """Manages the iterative BT improvement loop"""
    
    def __init__(self, config=None, llm_config=None):
        self.config = config or DEFAULT_RUNNER_CONFIG
        self.llm_config = llm_config or DEFAULT_LLM_CONFIG
        
        # Initialize LLM agent
        if self.config.use_mock_llm:
            print("Using Mock LLM (no API calls)")
            self.agent = MockLLMAgent()
        else:
            print(f"Using LLM: {self.llm_config.model}")
            self.agent = LLMAgent(
                api_key=self.llm_config.api_key,
                model=self.llm_config.model
            )
        
        # Session timestamp for consistent file naming
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create session-specific directories
        if self.config.save_logs:
            self.session_log_dir = os.path.join(self.config.log_directory, self.session_timestamp)
            os.makedirs(self.session_log_dir, exist_ok=True)
        if self.config.save_bts:
            self.session_bt_dir = os.path.join(self.config.bt_directory, self.session_timestamp)
            os.makedirs(self.session_bt_dir, exist_ok=True)
        
        # Track performance
        self.performance_history = []
        self.best_bt = None
        self.best_floor = 0
    
    def save_bt(self, bt_dsl: str, iteration: int):
        """Save BT to file"""
        if not self.config.save_bts:
            return
        
        # Save in session directory with simple filename
        filename = f"iter{iteration}.txt"
        filepath = os.path.join(self.session_bt_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(bt_dsl)
        
        print(f"[SAVED] BT: {self.session_timestamp}/{filename}")
    
    def save_log(self, log: str, iteration: int):
        """Save gameplay log to file"""
        if not self.config.save_logs:
            return
        
        # Save in session directory with simple filename
        filename = f"log_iter{iteration}.txt"
        filepath = os.path.join(self.session_log_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(log)
        
        print(f"[SAVED] Log: {self.session_timestamp}/{filename}")
    
    def run_iteration(self, bt_dsl: str, iteration: int) -> dict:
        """Run one iteration: execute game and collect results"""
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}")
        print(f"{'='*60}\n")
        
        # Run game
        print("[GAME] Running game...")
        runner = GameRunner(bt_dsl, verbose=self.config.verbose)
        results = runner.run_game()
        
        # Save logs
        self.save_log(results['log'] + "\n\n" + results['summary'], iteration)
        
        # Track performance
        performance = {
            'iteration': iteration,
            'victory': results['victory'],
            'floor': results['final_floor'],
            'turns': results['total_turns']
        }
        self.performance_history.append(performance)
        
        # Update best
        if results['final_floor'] > self.best_floor:
            self.best_floor = results['final_floor']
            self.best_bt = bt_dsl
        
        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS - Iteration {iteration}")
        print(f"{'='*60}")
        print(f"Victory: {results['victory']}")
        print(f"Final Floor: {results['final_floor']}")
        print(f"Total Turns: {results['total_turns']}")
        print(f"{'='*60}\n")
        
        return results
    
    def run(self, initial_bt: Optional[str] = None):
        """Run the complete improvement loop"""
        print("\n" + "="*60)
        print("PORTAL-INSPIRED DUNGEON GAME - LLM IMPROVEMENT LOOP")
        print("="*60 + "\n")
        
        # Use predefined initial BT instead of generating
        if initial_bt:
            print("Using provided initial BT")
            current_bt = initial_bt
        else:
            print("Using predefined balanced BT")
            # Import from bt_executor
            from TextGame.bt_executor import EXAMPLE_BT_BALANCED
            current_bt = EXAMPLE_BT_BALANCED
        
        if self.config.single_run:
            print("[MODE] Single Run Mode (No LLM Improvement)")
            self.save_bt(current_bt, 1)
            self.run_iteration(current_bt, 1)
            return
        
        self.save_bt(current_bt, 0)
        
        # Initialize best BT
        self.best_bt = current_bt
        
        # Track previous floor for performance comparison
        previous_floor = 0
        stagnation_counter = 0
        
        # Run iterations
        for i in range(1, self.config.max_iterations + 1):
            # Run game with current BT
            results = self.run_iteration(current_bt, i)
            
            # Check stagnation/regression
            if results['final_floor'] <= self.best_floor:
                stagnation_counter += 1
            else:
                stagnation_counter = 0
            
            # Rollback if stagnated for 2+ iterations
            if stagnation_counter >= 2:
                print(f"\n[ROLLBACK] Performance stagnated/dropped for {stagnation_counter} iterations.")
                print(f"[ROLLBACK] Reverting to Best BT (Floor {self.best_floor}) for improvement.")
                current_bt = self.best_bt
                stagnation_counter = 0
            
            # Check for early stop (victory)
            if results['victory'] and self.config.victory_early_stop:
                print("[VICTORY] Stopping early.")
                break
            
            # Check if this is the last iteration
            if i == self.config.max_iterations:
                print("Reached maximum iterations.")
                break
            
            # Improve BT for next iteration
            print("\n[LLM] Generating improved BT...")
            improvement_result = self.agent.two_stage_improvement(
                current_bt=current_bt,
                last_stage_log=results['last_stage_log'],
                stage_history=results['stage_history'],
                final_floor=results['final_floor'],
                victory=results['victory'],
                previous_floor=previous_floor  # Pass previous floor for comparison
            )
            
            # Update previous floor for next iteration
            previous_floor = results['final_floor']
            
            current_bt = improvement_result['improved_bt']
            self.save_bt(current_bt, i)
            
            # Save critic feedback
            if self.config.save_logs:
                feedback_file = os.path.join(
                    self.session_log_dir, 
                    f"critic_feedback_iter{i}.txt"
                )
                with open(feedback_file, 'w', encoding='utf-8') as f:
                    f.write("# CRITIC FEEDBACK\n\n")
                    f.write(improvement_result['critic_feedback'])
                    
                    if 'generation_error' in improvement_result:
                        f.write("\n\n" + "="*50 + "\n")
                        f.write("GENERATION ERROR\n")
                        f.write("="*50 + "\n")
                        f.write(f"Failed to generate valid BT: {improvement_result['generation_error']}\n")
                        f.write("Falling back to previous BT.\n")
        
        # Final summary
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"Total Iterations: {len(self.performance_history)}")
        print(f"Best Floor Reached: {self.best_floor}")
        print(f"\nPerformance History:")
        for perf in self.performance_history:
            status = "VICTORY" if perf['victory'] else f"Floor {perf['floor']}"
            print(f"  Iteration {perf['iteration']}: {status} ({perf['turns']} turns)")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="PORTAL-Inspired Dungeon Game Runner")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM (no API calls)")
    parser.add_argument("--bt", type=str, help="Path to initial BT file")
    parser.add_argument("--no-save", action="store_true", help="Don't save logs/BTs")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--single-run", action="store_true", help="Run game once without LLM improvement")
    
    args = parser.parse_args()
    
    # Configure
    config = DEFAULT_RUNNER_CONFIG
    config.max_iterations = args.iterations
    config.use_mock_llm = args.mock
    config.save_logs = not args.no_save
    config.save_bts = not args.no_save
    config.verbose = not args.quiet
    config.single_run = args.single_run
    
    # Load initial BT if provided
    initial_bt = None
    
    # In single-run mode, default to example/manual.txt if no BT specified
    if args.single_run and not args.bt:
        manual_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'examples', 'manual.txt')
        if os.path.exists(manual_path):
            print(f"[MODE] Single Run: Loading BT from {manual_path}")
            args.bt = manual_path
        else:
            print(f"[WARNING] Single Run Mode: '{manual_path}' not found.")
            
    if args.bt:
        with open(args.bt, 'r', encoding='utf-8') as f:
            initial_bt = f.read()
    
    # Run improvement loop
    loop = ImprovementLoop(config=config)
    loop.run(initial_bt=initial_bt)


if __name__ == "__main__":
    main()
