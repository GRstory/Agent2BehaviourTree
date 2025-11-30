"""
Test script to verify prompt logging
"""
from TextGame.llm_agent import MockLLMAgent

print("Testing prompt logging with Mock LLM...\n")

# Create mock agent
agent = MockLLMAgent()

# Test two-stage improvement (this will trigger multiple LLM calls)
current_bt = """root :
    selector :
        task : LightAttack()"""

last_stage_log = """
[Floor 1] Turn 1
Player HP: High
Enemy HP: High
>>> Player Action: LightAttack
Result: Hit! Enemy took Light damage
"""

print("\n" + "="*80)
print("Running two_stage_improvement to see prompt logging...")
print("="*80 + "\n")

result = agent.two_stage_improvement(
    current_bt=current_bt,
    last_stage_log=last_stage_log,
    final_floor=1,
    victory=False,
    stage_history={1: last_stage_log}
)

print("\n" + "="*80)
print("Test completed!")
print("="*80)
print("\nNote: Mock LLM doesn't actually call _call_llm, so no prompts were logged.")
print("To see actual prompt logging, run with real LLM using: python main.py --iterations 1")
