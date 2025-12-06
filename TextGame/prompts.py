"""
Prompt Templates for Enhanced Combat System LLM Agent

Contains prompts for BT generation and improvement based on combat logs.
"""

import os

DSL_SPEC_PATH = os.path.join(os.path.dirname(__file__), "bt_dsl_spec.md")

def load_dsl_spec() -> str:
    """Load the BT DSL specification"""
    try:
        with open(DSL_SPEC_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "[DSL Spec not found]"


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

SYSTEM_PROMPT_BT_GENERATOR = """You are an expert AI strategist specializing in turn-based RPG combat and Behaviour Tree design.

Your expertise includes:
- Elemental weakness exploitation (Fire/Ice/Lightning rock-paper-scissors)
- Resource management (TP/MP optimization)
- Status effect timing and usage
- Enemy pattern recognition and adaptation
- Defensive vs aggressive strategy selection

Always output valid BT DSL following the specification exactly. Use 4 spaces for indentation."""

SYSTEM_PROMPT_CRITIC = """You are a tactical analyst for turn-based RPG combat.

Your task is to analyze combat logs and identify:
- Elemental advantage usage (did they exploit weakness?)
- Resource efficiency (TP/MP management)
- Status effect timing
- Defensive decisions (Defend, Heal timing)
- Enemy pattern adaptation

Provide specific, actionable insights for BT improvement."""


# ============================================================================
# INITIAL BT GENERATION
# ============================================================================

def create_initial_bt_prompt() -> str:
    """Create prompt for initial BT generation"""
    dsl_spec = load_dsl_spec()
    
    return f"""Generate an optimal Behaviour Tree for a turn-based RPG combat system.

# Game Overview

**Combat System:**
- Single-floor combat against 1 of 3 enemy types
- Turn-based: Player acts, then enemy acts
- Win: Reduce enemy HP to 0
- Lose: Player HP reaches 0 OR turn limit (35 turns)

**Enemy Types (random selection):**
1. Fire Golem 🔥: Aggressive berserker, weak to Ice
2. Ice Wraith ❄️: Defensive healer, weak to Lightning
3. Thunder Drake ⚡: Balanced tactical, weak to Fire

**Player Actions (8 total):**
- Attack (free, builds TP)
- PowerStrike (30 TP, high damage)
- FireSpell, IceSpell, LightningSpell (20 MP each, elemental)
- Defend (free, -50% damage, +20 TP)
- Heal (30 MP, 45 HP, 3 turn cooldown)
- Scan (15 MP, reveals enemy weakness)

**Resources:**
- TP: Starts 50, regenerates +15/turn, max 100
- MP: Starts 100, regenerates +12/turn, max 100

**Key Strategy:**
1. Scan enemy early (turn 1-2) to identify weakness
2. Spam effective elemental spell (1.5x damage!)
3. Defend when enemy telegraphs heavy attack
4. Heal only when HP < 30%

# Behaviour Tree DSL Specification

{dsl_spec}

# Your Task

Generate a Behaviour Tree that:
1. **Scans early** to identify enemy weakness
2. **Exploits elemental advantage** (1.5x damage is huge!)
3. **Manages resources** (don't waste MP on wrong spells)
4. **Defends strategically** (when enemy telegraphs)
5. **Heals wisely** (only when HP < 30%)

# CRITICAL REQUIREMENTS

1. Use ONLY exact names from DSL spec
2. Use 4 spaces for indentation
3. Include colons: `root :`, `selector :`, `condition :`, `task :`
4. Use parentheses: `IsPlayerHPLow(30)`, `Heal()`
5. Always end with fallback: `task : Attack()`

Output ONLY the BT DSL, no explanations. Start with `root :`."""


# ============================================================================
# IMPROVEMENT PROMPTS
# ============================================================================

def create_critic_prompt(combat_summary: str, current_bt: str, previous_results: list) -> str:
    """Create prompt for combat analysis and improvement suggestions"""
    dsl_spec = load_dsl_spec()
    
    # Build performance context
    perf_context = ""
    if previous_results:
        victories = sum(1 for r in previous_results if r.get('victory', False))
        total = len(previous_results)
        perf_context = f"\n# Recent Performance\n"
        perf_context += f"Last {total} battles: {victories} victories, {total - victories} defeats\n"
        for i, r in enumerate(previous_results[-3:]):
            status = "WIN " if r.get('victory') else "LOSS"
            perf_context += f"  {status} vs {r.get('enemy_type', 'Unknown')}: {r.get('turns', 0)} turns\n"
    
    return f"""Analyze this combat and suggest BT improvements.

# Current Behaviour Tree
```
{current_bt}
```
{perf_context}
# Combat Summary
{combat_summary}

# Available DSL
{dsl_spec}

# Your Task

Analyze the combat and identify:

1. **Elemental Strategy**: Did they scan? Did they use the right spell?
2. **Resource Management**: TP/MP usage efficiency
3. **Defensive Decisions**: Heal/Defend timing
4. **BT Issues**: What parts of the tree caused problems?

Provide 3-5 specific improvement suggestions.

**IMPORTANT**: 
- Describe logic changes in plain text, NOT code
- Example: "Scan on turn 1 instead of turn 2"
- Example: "Increase heal threshold from 30% to 40%"

**Output Format:**
## Analysis
[What went wrong or could be better]

## Improvement Suggestions
1. [Logic change description]
2. [Logic change description]
3. [Logic change description]

Be concise and actionable."""


def create_generator_prompt(current_bt: str, critic_feedback: str) -> str:
    """Create prompt for improved BT generation"""
    dsl_spec = load_dsl_spec()
    
    return f"""Generate an IMPROVED Behaviour Tree based on feedback.

# Current Behaviour Tree
```
{current_bt}
```

# Improvement Feedback
{critic_feedback}

# DSL Specification
{dsl_spec}

# Your Task

Create an improved BT that addresses the feedback.

# CRITICAL REQUIREMENTS

1. Use ONLY exact names from DSL spec:
   - Conditions: HasTP, HasMP, IsPlayerHPLow, EnemyWeakTo, HasScannedEnemy, etc.
   - Actions: Attack, PowerStrike, FireSpell, IceSpell, LightningSpell, Defend, Heal, Scan

2. Correct syntax:
   - `root :`, `selector :`, `sequence :`
   - `condition : IsPlayerHPLow(30)`
   - `task : Heal()`

3. Use 4 spaces for indentation

4. Always include fallback: `task : Attack()`

# STRATEGIC GUIDANCE

- **BE BOLD**: If performance was poor, restructure the tree!
- **REORDER PRIORITIES**: Move important logic higher
- **TRY NEW STRATEGIES**: Aggressive vs defensive
- **NO DUPLICATES**: Must be different from current BT

# COMMON MISTAKES TO AVOID

❌ `isPlayerHP <= 30` - Use `IsPlayerHPLow(30)`
❌ `UseSpell(Fire)` - Use `FireSpell()`
❌ Wrong indentation (2 spaces or tabs)

Output ONLY the improved BT DSL, no explanations. Start with `root :`."""


# ============================================================================
# EXTRACTION HELPERS
# ============================================================================

def extract_bt_from_response(response: str) -> str:
    """Extract BT DSL from LLM response"""
    # Look for code blocks
    if "```" in response:
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Code blocks
                lines = part.strip().split('\n')
                if lines[0].strip() and not lines[0].strip().startswith('root'):
                    lines = lines[1:]
                return '\n'.join(lines).strip()
    
    # Look for "root :"
    if "root :" in response:
        start_idx = response.index("root :")
        return response[start_idx:].strip()
    
    return response.strip()
