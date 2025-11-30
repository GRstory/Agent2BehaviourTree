"""
Test script to verify 30-turn limit feature
"""
from TextGame.game_engine import DungeonGame, ActionType
from TextGame.abstract_logger import AbstractLogger

# Test 1: Verify turn limit triggers defeat
print("Test 1: Testing 30-turn limit...")
game = DungeonGame()
logger = AbstractLogger()

for i in range(35):
    if game.game_over:
        break
    turn_info = game.take_action(ActionType.DEFEND)
    
print(f"Game over after {game.state.floor_turn_count} turns on floor {game.state.current_floor}")
print(f"Game over: {game.game_over}, Victory: {game.victory}")
print(f"Defeat reason in turn_info: {turn_info.get('defeat_reason', 'None')}")

# Test 2: Verify logger message
print("\nTest 2: Testing logger output...")
game2 = DungeonGame()
logger2 = AbstractLogger()

for i in range(35):
    if game2.game_over:
        break
    logger2.log_turn_start(game2.state)
    turn_info = game2.take_action(ActionType.DEFEND)

defeat_reason = turn_info.get('defeat_reason')
logger2.log_game_over(game2.victory, game2.state.current_floor, defeat_reason)
log_output = logger2.get_full_log()

if "TURN LIMIT EXCEEDED" in log_output:
    print("[PASS] Logger correctly shows TURN LIMIT EXCEEDED message")
else:
    print("[FAIL] Logger missing TURN LIMIT EXCEEDED message")

if "30 turns" in log_output:
    print("[PASS] Logger mentions 30 turns")
else:
    print("[FAIL] Logger doesn't mention 30 turns")

print("\nAll tests completed!")
