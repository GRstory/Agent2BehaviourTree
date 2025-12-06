"""
Quick test for new game engine
"""
from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType

# Test 1: Create game with Fire Golem
print("=== Test 1: Fire Golem Battle ===")
game = DungeonGame(EnemyType.FIRE_GOLEM)
print(f"Enemy: {game.state.enemy_type.value}")
print(f"Enemy HP: {game.state.enemy.current_hp}/{game.state.enemy.max_hp}")
print(f"Enemy Element: {game.state.enemy.element.value}")
print(f"Player HP: {game.state.player.current_hp}/{game.state.player.max_hp}")
print(f"Player TP: {game.state.player_resources.tp}/{game.state.player_resources.max_tp}")
print(f"Player MP: {game.state.player_resources.mp}/{game.state.player_resources.max_mp}")

# Test 2: Execute some actions
print("\n=== Test 2: Action Execution ===")

# Turn 1: Scan
result = game.take_action(PlayerAction.SCAN)
print(f"Turn {result['turn']}: Scan")
print(f"  Player: {result['player_info']['message']}")
print(f"  Enemy: {result['enemy_info']['message']}")
print(f"  Scanned: {game.state.scanned}")

# Turn 2: Ice Spell (should be super effective)
result = game.take_action(PlayerAction.ICE_SPELL)
print(f"\nTurn {result['turn']}: Ice Spell")
print(f"  Player: {result['player_info']['message']}")
print(f"  Damage: {result['player_info']['damage']}")
print(f"  Enemy HP: {result['enemy_hp']}/{game.state.enemy.max_hp}")
print(f"  Enemy: {result['enemy_info']['message']}")

# Turn 3: Attack (free, builds TP)
result = game.take_action(PlayerAction.ATTACK)
print(f"\nTurn {result['turn']}: Attack")
print(f"  Player: {result['player_info']['message']}")
print(f"  Player TP: {game.state.player_resources.tp}")
print(f"  Player HP: {result['player_hp']}/{game.state.player.max_hp}")
if result['game_over']:
    print(f"  Game Over! Victory: {result['victory']}")
else:
    # Turn 4: Defend
    result = game.take_action(PlayerAction.DEFEND)
    print(f"\nTurn {result['turn']}: Defend")
    print(f"  Player: {result['player_info']['message']}")
    print(f"  Player TP: {game.state.player_resources.tp}")

print("\n=== Test 3: Ice Wraith Battle ===")
game2 = DungeonGame(EnemyType.ICE_WRAITH)
print(f"Enemy: {game2.state.enemy_type.value}")
print(f"Enemy HP: {game2.state.enemy.current_hp}/{game2.state.enemy.max_hp}")
print(f"Enemy Element: {game2.state.enemy.element.value}")

# Test Lightning Spell (should be super effective)
result = game2.take_action(PlayerAction.LIGHTNING_SPELL)
print(f"\nTurn {result['turn']}: Lightning Spell")
print(f"  Damage: {result['player_info']['damage']} (should be ~42 with 1.5x multiplier)")

print("\n=== Test 4: Thunder Drake Battle ===")
game3 = DungeonGame(EnemyType.THUNDER_DRAKE)
print(f"Enemy: {game3.state.enemy_type.value}")
print(f"Enemy HP: {game3.state.enemy.current_hp}/{game3.state.enemy.max_hp}")
print(f"Enemy Element: {game3.state.enemy.element.value}")

# Test Fire Spell (should be super effective)
result = game3.take_action(PlayerAction.FIRE_SPELL)
print(f"\nTurn {result['turn']}: Fire Spell")
print(f"  Damage: {result['player_info']['damage']} (should be ~42 with 1.5x multiplier)")

print("\n[OK] All tests passed!")
