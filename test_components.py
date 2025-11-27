"""
Quick test script to verify all components work
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Test 1: Import all modules
print("="*70)
print("테스트 1: 모듈 임포트")
print("="*70)

try:
    from TextGame.game_engine import DungeonGame, ActionType
    print("✓ game_engine 임포트 성공")
except Exception as e:
    print(f"✗ game_engine 임포트 실패: {e}")
    sys.exit(1)

try:
    from TextGame.abstract_logger import AbstractLogger
    print("✓ abstract_logger 임포트 성공")
except Exception as e:
    print(f"✗ abstract_logger 임포트 실패: {e}")
    sys.exit(1)

try:
    from TextGame.bt_executor import create_bt_executor_from_dsl, EXAMPLE_BT_BALANCED
    print("✓ bt_executor 임포트 성공")
except Exception as e:
    print(f"✗ bt_executor 임포트 실패: {e}")
    sys.exit(1)

try:
    from TextGame.llm_agent import MockLLMAgent
    print("✓ llm_agent 임포트 성공 (Mock)")
except Exception as e:
    print(f"✗ llm_agent 임포트 실패: {e}")
    sys.exit(1)

# Test 2: Game engine basic functionality
print("\n" + "="*70)
print("테스트 2: 게임 엔진 기본 기능")
print("="*70)

game = DungeonGame()
print(f"✓ 게임 생성 성공")
print(f"  - 플레이어 HP: {game.state.player.current_hp}/{game.state.player.max_hp}")
print(f"  - 적 HP: {game.state.enemy.current_hp}/{game.state.enemy.max_hp}")
print(f"  - 현재 층: {game.state.current_floor}")

# Test a few actions
turn1 = game.take_action(ActionType.LIGHT_ATTACK)
print(f"✓ 약공격 실행: 적 HP {turn1['enemy_hp']}")

turn2 = game.take_action(ActionType.LIGHT_ATTACK)
print(f"✓ 약공격 실행: 적 HP {turn2['enemy_hp']}")

turn3 = game.take_action(ActionType.LIGHT_ATTACK)
combo = turn3.get('combo')
print(f"✓ 약공격 실행: 적 HP {turn3['enemy_hp']}" + (f" (콤보: {combo})" if combo else ""))

# Test 3: BT parsing and execution
print("\n" + "="*70)
print("테스트 3: Behaviour Tree 파싱 및 실행")
print("="*70)

executor = create_bt_executor_from_dsl(EXAMPLE_BT_BALANCED)
if executor:
    print("✓ BT 파싱 성공")
    
    # Create fresh game
    test_game = DungeonGame()
    action = executor.execute(test_game.state)
    
    if action:
        print(f"✓ BT 실행 성공: 선택된 행동 = {action.value}")
    else:
        print("✗ BT 실행 실패: 행동을 결정하지 못함")
else:
    print("✗ BT 파싱 실패")
    sys.exit(1)

# Test 4: Abstract logger
print("\n" + "="*70)
print("테스트 4: 추상 로거")
print("="*70)

logger = AbstractLogger()
test_game = DungeonGame()

logger.log_turn_start(test_game.state)
logger.log_player_action(ActionType.LIGHT_ATTACK, 15, None, test_game.state)

log = logger.get_full_log()
if "Player HP:" in log and "Enemy HP:" in log:
    print("✓ 로거 작동 성공")
    print(f"  - 로그 길이: {len(log)} 문자")
else:
    print("✗ 로거 작동 실패")
    sys.exit(1)

# Test 5: Mock LLM agent
print("\n" + "="*70)
print("테스트 5: Mock LLM 에이전트")
print("="*70)

agent = MockLLMAgent()
initial_bt = agent.generate_initial_bt()

if "root :" in initial_bt:
    print("✓ Mock LLM BT 생성 성공")
    print(f"  - BT 길이: {len(initial_bt)} 문자")
else:
    print("✗ Mock LLM BT 생성 실패")
    sys.exit(1)

# All tests passed
print("\n" + "="*70)
print("✓ 모든 테스트 통과!")
print("="*70)
print("\n실제 게임 실행 테스트:")
print("  python runner.py --mock --iterations 1")
print("\nLLM 에이전트 테스트 (API 키 필요):")
print("  python runner.py --iterations 1")
