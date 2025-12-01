"""
Prompt Templates for LLM Agent

Contains all prompt templates for BT generation, log analysis, and tactical feedback.
"""

# Load BT DSL specification
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

SYSTEM_PROMPT_BT_GENERATOR = """You are an expert AI game strategist specializing in Behaviour Tree design for turn-based combat games.

Your task is to generate optimal Behaviour Trees (BTs) that control a player character in a 10-floor dungeon crawler.

Key Capabilities:
- Deep understanding of turn-based combat tactics
- Expertise in Behaviour Tree design patterns
- Ability to balance aggression, defense, and resource management
- Strategic thinking about combo execution and timing

Always output valid BT DSL that follows the specification exactly. Use proper indentation (4 spaces per level) and correct syntax."""

SYSTEM_PROMPT_LOG_ANALYZER = """You are an expert tactical analyst for turn-based combat games.

Your task is to analyze gameplay logs and identify:
- Strategic mistakes and missed opportunities
- Inefficient resource usage (healing, defending)
- Combo execution failures
- Poor timing decisions
- Death causes and how they could have been prevented

Provide specific, actionable insights that can be used to improve the Behaviour Tree."""

SYSTEM_PROMPT_FEEDBACK_GENERATOR = """You are a tactical coach providing feedback to improve combat AI performance.

Your task is to generate constructive, specific feedback based on gameplay analysis. Focus on:
- What went wrong and why
- What could have been done better
- Specific BT changes that would address the issues
- Strategic principles to apply

Be concise but thorough. Prioritize the most impactful improvements."""


# ============================================================================
# INITIAL BT GENERATION
# ============================================================================

def create_initial_bt_prompt() -> str:
    """Create prompt for initial BT generation"""
    dsl_spec = load_dsl_spec()
    
    return f"""Generate an optimal Behaviour Tree for a 10-floor turn-based dungeon crawler.

# Game Rules

**Combat System:**
- Turn-based: Player acts first, then enemy
- 4 Actions: Light Attack, Heavy Attack, Defend, Heal
- Player starts with 100 HP
- Enemies get stronger each floor (floors 5 and 10 are boss floors)

**Actions:**
- Light Attack: Base damage
- Heavy Attack: 2x base damage
- Defend: Increases defense for this turn and next enemy turn
- Heal: Restores 30 HP, has 3-turn cooldown

**Combo System (CRITICAL):**
1. Triple Light: Light → Light → Light = 4x damage on final hit
2. Heavy Finisher: Light → Light → Heavy = 3x damage on heavy
3. Counter Strike: Defend → Heavy = 2.5x damage on heavy

**Win Condition:** Defeat all enemies on all 10 floors
**Lose Condition:** Player HP reaches 0

# Behaviour Tree DSL Specification

{dsl_spec}

# Your Task

Generate a Behaviour Tree that:
1. **Survives all 10 floors** - Prioritize staying alive
2. **Uses combos effectively** - Combos are the key to victory
3. **Manages resources wisely** - Don't waste heals
4. **Adapts to enemy strength** - Different tactics for different situations

# CRITICAL REQUIREMENTS

1. **ONLY use the exact condition and action names from the DSL specification above**
2. **Use 4 spaces for indentation** (not tabs, not 2 spaces)
3. **Include colons after node types**: `root :`, `selector :`, `sequence :`, `condition :`, `task :`
4. **Always end with a fallback action**: Last child should be `task : LightAttack()`
5. **Use parentheses for all conditions and actions**: `IsPlayerHPLow(30)`, `Heal()`

# INVALID EXAMPLES (DO NOT USE)
❌ `condition : isPlayerHP <= 30` - Wrong syntax
❌ `action : UseAbility(Heal)` - Wrong action name
❌ `condition : IsAbilityReady(Heal)` - Wrong condition name
❌ `task : LightAttack` - Missing parentheses

# VALID EXAMPLE
✅ 
```
root :
    selector :
        sequence :
            condition : IsPlayerHPLow(30)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        task : LightAttack()
```

Output ONLY the BT DSL, no explanations. Start with `root :` and use proper indentation."""


# ============================================================================
# CRITIC LLM - Analyzes last stage and suggests improvements
# ============================================================================

def create_critic_prompt(last_stage_log: str, final_floor: int, victory: bool, current_bt: str, previous_floor: int = 0) -> str:
    """Create prompt for Critic LLM to analyze last stage gameplay"""
    dsl_spec = load_dsl_spec()
    
    outcome = "VICTORY (All 10 floors cleared)" if victory else f"DEFEAT (Died on Floor {final_floor})"
    
    # Add performance comparison if available
    performance_context = ""
    if previous_floor > 0:
        if final_floor > previous_floor:
            performance_context = f"\n# Performance Improvement\n✅ **IMPROVED**: Previous iteration reached Floor {previous_floor}, current reached Floor {final_floor} (+{final_floor - previous_floor} floors)\n"
        elif final_floor < previous_floor:
            performance_context = f"\n# Performance Regression\n❌ **WORSE**: Previous iteration reached Floor {previous_floor}, current only reached Floor {final_floor} (-{previous_floor - final_floor} floors)\n"
        else:
            performance_context = f"\n# Performance Status\n➡️ **SAME**: Both iterations reached Floor {final_floor}\n"
    
    return f"""You are a tactical analyst for turn-based combat games.

# Game Outcome
{outcome}
{performance_context}
# Current Behaviour Tree
```
{current_bt}
```

# Available BT Functions & DSL Spec
{dsl_spec}

# Last Stage Gameplay Log
{last_stage_log}

# Your Task

Analyze ONLY the last stage gameplay log and identify:

1. **Critical Mistakes**: What specific decisions led to problems?
2. **Missed Opportunities**: Where could combos or better actions have been used?
3. **Resource Management**: Was healing/defending used wisely?
4. **BT Issues**: What parts of the Behaviour Tree caused these problems?

Provide 3-5 specific, actionable improvement suggestions.

**IMPORTANT**: 
- **DO NOT write full BT DSL code or code blocks.**
- Describe the logic changes in plain text.
- Example: "Change the healing threshold from 30% to 40%" instead of writing the code.
- Example: "Add a condition to check for TripleLight combo before attacking" instead of writing the code.

**Output Format:**
## Analysis
[Brief analysis of what went wrong or what could be better]

## Improvement Suggestions
1. [Description of logic change]
2. [Description of logic change]
3. [Description of logic change]
...

Be concise and focus on the most impactful changes."""


# ============================================================================
# GENERATOR LLM - Creates new BT from feedback
# ============================================================================

def create_generator_prompt(current_bt: str, critic_feedback: str) -> str:
    """Create prompt for Generator LLM to create improved BT"""
    dsl_spec = load_dsl_spec()
    
    return f"""You are an expert Behaviour Tree designer for turn-based combat games.

# Current Behaviour Tree
```
{current_bt}
```

# Improvement Feedback
{critic_feedback}

# Behaviour Tree DSL Specification
{dsl_spec}

# Your Task

Generate an IMPROVED Behaviour Tree that addresses the feedback while maintaining valid DSL syntax.

# CRITICAL REQUIREMENTS

1. **ONLY use the exact condition and action names from the DSL specification**
   - Valid conditions: IsPlayerHPLow, IsPlayerHPHigh, IsEnemyHPLow, IsEnemyHPHigh, CanHeal, IsDefending, HasComboReady, IsFloorBoss, IsTurnEarly
   - Valid actions: LightAttack, HeavyAttack, Defend, Heal
   
2. **Use correct syntax**:
   - Control nodes: `root :`, `selector :`, `sequence :`
   - Conditions: `condition : IsPlayerHPLow(30)`
   - Actions: `task : Heal()`
   
3. **Use 4 spaces for indentation** (not tabs, not 2 spaces)

4. **Always include a fallback action** at the end: `task : LightAttack()`

5. **Use parentheses** for all conditions and actions

# COMMON MISTAKES TO AVOID

❌ `isPlayerHP <= 30` - Use `IsPlayerHPLow(30)` instead
❌ `UseAbility(Heal)` - Use `Heal()` instead
❌ `IsAbilityReady(Heal)` - Use `CanHeal()` instead
❌ `isAbilityAvailable` - Not a valid condition
❌ `executeCombo` - Not a valid action
❌ Using 2 spaces or tabs for indentation

# VALID EXAMPLE
```
root :
    selector :
        sequence :
            condition : IsPlayerHPLow(40)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        sequence :
            condition : IsEnemyHPLow(25)
            task : HeavyAttack()
        task : LightAttack()
```

**Requirements:**
1. Fix the identified problems from the feedback
2. Implement suggested improvements
3. Maintain proper DSL syntax and indentation (4 spaces)
4. Keep the tree reasonably simple
5. Ensure there's always a fallback action

**IMPORTANT STRATEGIC GUIDANCE:**
- **BE BOLD**: If the previous performance was poor or stagnant, do not just tweak numbers. Change the structure!
- **REORDER PRIORITIES**: Try moving defensive or combo logic higher up in the tree.
- **TRY NEW STRATEGIES**: If the current strategy isn't working, try a completely different approach (e.g., aggressive vs defensive).
- **DON'T BE AFRAID TO REWRITE**: You can completely restructure the tree if the current one is fundamentally flawed.
- **ABSOLUTELY NO DUPLICATES**: You MUST generate a DIFFERENT Behaviour Tree. Do not output the exact same code as the "Current Behaviour Tree".

Output ONLY the improved BT DSL, no explanations. Start with `root :` and use proper indentation."""


# ============================================================================
# EXTRACTION HELPERS
# ============================================================================

def extract_bt_from_response(response: str) -> str:
    """Extract BT DSL from LLM response"""
    # Look for code blocks
    if "```" in response:
        # Extract content between ``` markers
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Odd indices are code blocks
                # Remove language identifier if present
                lines = part.strip().split('\n')
                if lines[0].strip() and not lines[0].strip().startswith('root'):
                    lines = lines[1:]
                return '\n'.join(lines).strip()
    
    # If no code blocks, look for "root :" and take everything after
    if "root :" in response:
        start_idx = response.index("root :")
        return response[start_idx:].strip()
    
    # Return as-is if nothing found
    return response.strip()
