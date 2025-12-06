"""
Integration Test for Enhanced Combat System

Tests complete game flow with BT execution and logging.
"""
from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.bt_executor import create_bt_executor_from_dsl
from TextGame.abstract_logger import AbstractLogger

# Load example BT
with open("examples/example_bt_balanced.txt", "r") as f:
    BT_CODE = f.read()

print("=== Enhanced Combat System Integration Test ===\n")

# Create BT executor
executor = create_bt_executor_from_dsl(BT_CODE)
if not executor:
    print("ERROR: Failed to parse BT!")
    exit(1)

print("[OK] BT parsed successfully\n")

# Test against all 3 enemy types
enemy_types = [
    (EnemyType.FIRE_GOLEM, "Fire Golem (weak to Ice)"),
    (EnemyType.ICE_WRAITH, "Ice Wraith (weak to Lightning)"),
    (EnemyType.THUNDER_DRAKE, "Thunder Drake (weak to Fire)")
]

results = []

for enemy_type, enemy_name in enemy_types:
    print(f"=== Testing vs {enemy_name} ===")
    
    # Create game
    game = DungeonGame(enemy_type)
    logger = AbstractLogger()
    logger.start_combat(game.state)
    
    # Run combat
    turn = 0
    while not game.game_over and turn < 35:
        turn += 1
        
        # Log turn start
        logger.log_turn_start(game.state)
        
        # Execute BT to get action
        action = executor.execute(game.state)
        if not action:
            print(f"  ERROR: BT returned no action on turn {turn}")
            break
        
        # Execute action
        result = game.take_action(action)
        
        # Log player action
        logger.log_player_action(action, result['player_info'], game.state)
        
        # Log enemy action
        logger.log_enemy_action(result['enemy_info'], game.state)
        
        # Log turn end
        logger.log_turn_end(game.state)
        
        if game.game_over:
            break
    
    # Generate summary
    summary = logger.generate_summary(game.state, game.victory, turn)
    
    # Print result
    print(f"  Result: {'VICTORY' if game.victory else 'DEFEAT'}")
    print(f"  Turns: {turn}")
    print(f"  Final Player HP: {game.state.player.current_hp}/{game.state.player.max_hp}")
    print(f"  Final Enemy HP: {game.state.enemy.current_hp if game.state.enemy else 0}/{game.state.enemy.max_hp if game.state.enemy else 0}")
    print(f"  Scanned: {game.state.scanned}")
    print()
    
    results.append({
        'enemy': enemy_name,
        'victory': game.victory,
        'turns': turn,
        'player_hp': game.state.player.current_hp,
        'scanned': game.state.scanned
    })

# Summary
print("=== TEST SUMMARY ===")
victories = sum(1 for r in results if r['victory'])
print(f"Victories: {victories}/3")
print(f"Average Turns: {sum(r['turns'] for r in results) / 3:.1f}")
print(f"Scanned: {sum(1 for r in results if r['scanned'])}/3")
print()

for r in results:
    status = "[WIN]" if r['victory'] else "[LOSS]"
    print(f"{status} {r['enemy']}: {r['turns']} turns, {r['player_hp']} HP remaining")

if victories == 3:
    print("\n[OK] All tests passed! System working correctly.")
else:
    print(f"\n[WARNING] Only {victories}/3 victories. BT may need tuning.")
