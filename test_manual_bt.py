"""
Test manual BT from examples/manual.txt
Run a single game with the manually crafted BT and display results
"""
from TextGame.game_engine import DungeonGame, PlayerAction, EnemyType
from TextGame.bt_executor import create_bt_executor_from_dsl
import random

def load_bt_from_file(filepath: str) -> str:
    """Load BT from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def run_single_game(bt_text: str, enemy_type: EnemyType = None, verbose: bool = True):
    """Run a single game with the given BT"""
    # Parse BT
    executor = create_bt_executor_from_dsl(bt_text)
    if not executor:
        print("ERROR: Failed to parse BT!")
        return None
    
    if verbose:
        print("[OK] BT parsed successfully\n")
    
    # Create game
    if enemy_type is None:
        enemy_type = random.choice(list(EnemyType))
    
    game = DungeonGame(enemy_type)
    
    if verbose:
        print(f"=== Starting Game ===")
        print(f"Enemy: {enemy_type.value}")
        print(f"Player HP: {game.state.player.current_hp}/{game.state.player.max_hp}")
        print(f"Enemy HP: {game.state.enemy.current_hp}/{game.state.enemy.max_hp}\n")
    
    # Game loop
    turn = 0
    while not game.game_over and turn < 50:
        turn += 1
        
        # Execute BT to get action
        action = executor.execute(game.state)
        
        if not action:
            print(f"Turn {turn}: ERROR - BT returned no action!")
            break
        
        # Execute action
        result = game.take_action(action)
        
        if verbose:
            print(f"Turn {turn}: {action.value}")
            print(f"  Player: {result['player_hp']}/{game.state.player.max_hp} HP | "
                  f"TP: {game.state.player_resources.tp} | MP: {game.state.player_resources.mp}")
            print(f"  Enemy:  {result['enemy_hp']}/{game.state.enemy.max_hp} HP")
            
            # Show player action result
            if result['player_info'].get('message'):
                print(f"  → {result['player_info']['message']}")
            
            # Show enemy action result
            if result['enemy_info'].get('message'):
                print(f"  ← {result['enemy_info']['message']}")
            
            # Show status
            if game.state.scanned:
                weakness = {
                    EnemyType.FIRE_GOLEM: "Ice",
                    EnemyType.ICE_WRAITH: "Lightning",
                    EnemyType.THUNDER_DRAKE: "Fire"
                }.get(enemy_type, "None")
                print(f"  [Scanned: Enemy weak to {weakness}]")
            
            print()
        
        if game.game_over:
            break
    
    # Show final result
    if verbose:
        print("=" * 50)
        if game.victory:
            print(f"VICTORY! Defeated {enemy_type.value} in {turn} turns")
        else:
            print(f"DEFEAT! Lost to {enemy_type.value} on turn {turn}")
            if result.get('defeat_reason') == 'turn_limit_exceeded':
                print("   Reason: Turn limit exceeded")
        print("=" * 50)
    
    return {
        'victory': game.victory,
        'turns': turn,
        'enemy_type': enemy_type.value,
        'scanned': game.state.scanned,
        'final_player_hp': game.state.player.current_hp,
        'final_enemy_hp': game.state.enemy.current_hp if game.state.enemy else 0
    }


if __name__ == "__main__":
    import sys
    
    # Load manual BT
    bt_file = "examples/manual.txt"
    print(f"Loading BT from: {bt_file}\n")
    
    try:
        bt_text = load_bt_from_file(bt_file)
    except FileNotFoundError:
        print(f"ERROR: File not found: {bt_file}")
        sys.exit(1)
    
    # Check if enemy type specified
    enemy_type = None
    if len(sys.argv) > 1:
        enemy_arg = sys.argv[1].upper()
        if enemy_arg == "FIRE" or enemy_arg == "FIREGOLEM":
            enemy_type = EnemyType.FIRE_GOLEM
        elif enemy_arg == "ICE" or enemy_arg == "ICEWRAITH":
            enemy_type = EnemyType.ICE_WRAITH
        elif enemy_arg == "THUNDER" or enemy_arg == "THUNDERDRAKE":
            enemy_type = EnemyType.THUNDER_DRAKE
    
    # Run game
    result = run_single_game(bt_text, enemy_type=enemy_type, verbose=True)
    
    if result:
        print(f"\nFinal Stats:")
        print(f"  Victory: {result['victory']}")
        print(f"  Turns: {result['turns']}")
        print(f"  Enemy: {result['enemy_type']}")
        print(f"  Scanned: {result['scanned']}")
