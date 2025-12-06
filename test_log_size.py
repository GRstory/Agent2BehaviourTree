"""
Test to check log size for API cost estimation
"""
from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.abstract_logger import AbstractLogger

# Create a test game
game = DungeonGame(EnemyType.FIRE_GOLEM)
logger = AbstractLogger()
logger.start_combat(game.state)

# Simulate a few turns
for turn in range(5):
    logger.log_turn_start(game.state)
    
    # Player action
    action = PlayerAction.ATTACK
    result = game.take_action(action)
    logger.log_player_action(action, result['player_info'], game.state)
    logger.log_enemy_action(result['enemy_info'], game.state)
    logger.log_turn_end(game.state)
    
    if game.game_over:
        break

# Get logs
full_log = logger.get_full_log()
summary = logger.generate_summary(game.state, game.victory, game.state.turn_count)

print("=== LOG SIZE ANALYSIS ===\n")
print(f"Full Combat Log:")
print(f"  Characters: {len(full_log):,}")
print(f"  Lines: {len(full_log.split(chr(10)))}")
print(f"  Estimated tokens: ~{len(full_log) // 4:,} (rough estimate)")

print(f"\nCombat Summary:")
print(f"  Characters: {len(summary):,}")
print(f"  Lines: {len(summary.split(chr(10)))}")
print(f"  Estimated tokens: ~{len(summary) // 4:,}")

print(f"\n=== SAMPLE LOGS ===\n")
print("Full Log (first 500 chars):")
print(full_log[:500])
print("\n...")

print("\n" + "="*70)
print("Summary:")
print("="*70)
print(summary)

# Estimate for full game
avg_turns = 15
full_game_chars = len(full_log) * (avg_turns / game.state.turn_count)
summary_chars = len(summary)

print(f"\n=== COST ESTIMATION ===")
print(f"Assuming average {avg_turns} turns per game:")
print(f"  Full log: ~{int(full_game_chars):,} chars (~{int(full_game_chars // 4):,} tokens)")
print(f"  Summary only: ~{summary_chars:,} chars (~{summary_chars // 4:,} tokens)")
print(f"\nRecommendation: Use SUMMARY ONLY for LLM (much cheaper!)")
