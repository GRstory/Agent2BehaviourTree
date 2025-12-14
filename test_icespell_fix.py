from TextGame.game_engine import EnemyType
from runner import GameRunner

with open('test_bt_icespell.txt') as f:
    bt_dsl = f.read()

runner = GameRunner(bt_dsl, enemy_type=EnemyType.FIRE_GOLEM, verbose=True)
result = runner.run_game()

print(f"\n{'='*70}")
print(f"Victory: {result['victory']}")
print(f"Turns: {result['turns']}")
print(f"Player HP: {result['player_hp']}")
print(f"Enemy HP: {result['enemy_hp']}")
print(f"{'='*70}")
