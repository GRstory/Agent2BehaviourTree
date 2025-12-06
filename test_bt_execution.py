"""
Test BT execution with new system
"""
from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.bt_executor import create_bt_executor_from_dsl

# Test BT for new system
TEST_BT = """
root :
    selector :
        # Emergency heal
        sequence :
            condition : IsPlayerHPLow(30)
            condition : CanHeal()
            task : Heal()
        
        # Scan early
        sequence :
            condition : IsTurnEarly(2)
            condition : HasMP(15)
            task : Scan()
        
        # Use elemental advantage
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Ice)
            condition : HasMP(20)
            task : IceSpell()
        
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Fire)
            condition : HasMP(20)
            task : FireSpell()
        
        sequence :
            condition : HasScannedEnemy()
            condition : EnemyWeakTo(Lightning)
            condition : HasMP(20)
            task : LightningSpell()
        
        # Default: Attack
        task : Attack()
"""

print("=== Testing BT Execution ===\n")

# Create BT executor
executor = create_bt_executor_from_dsl(TEST_BT)
if not executor:
    print("ERROR: Failed to parse BT!")
    exit(1)

print("[OK] BT parsed successfully")

# Test with Fire Golem (weak to Ice)
print("\n=== Test 1: Fire Golem (weak to Ice) ===")
game = DungeonGame(EnemyType.FIRE_GOLEM)

for turn in range(5):
    # Execute BT to get action
    action = executor.execute(game.state)
    print(f"Turn {turn+1}: BT chose {action.value if action else 'None'}")
    
    # Execute action
    if action:
        result = game.take_action(action)
        print(f"  Player HP: {result['player_hp']}, Enemy HP: {result['enemy_hp']}")
        print(f"  Scanned: {game.state.scanned}")
    
    if game.game_over:
        print(f"  Game Over! Victory: {game.victory}")
        break

# Test with Ice Wraith (weak to Lightning)
print("\n=== Test 2: Ice Wraith (weak to Lightning) ===")
game2 = DungeonGame(EnemyType.ICE_WRAITH)

for turn in range(5):
    action = executor.execute(game2.state)
    print(f"Turn {turn+1}: BT chose {action.value if action else 'None'}")
    
    if action:
        result = game2.take_action(action)
        print(f"  Player HP: {result['player_hp']}, Enemy HP: {result['enemy_hp']}")
        print(f"  Scanned: {game2.state.scanned}")
    
    if game2.game_over:
        print(f"  Game Over! Victory: {game2.victory}")
        break

print("\n[OK] BT execution tests passed!")
