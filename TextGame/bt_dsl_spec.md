# Behaviour Tree DSL Specification

## Overview
This DSL defines Behaviour Trees for controlling a player character in a turn-based dungeon crawler game.

## Basic Structure

```
root :
    <control_node> :
        <child_nodes>
```

### Indentation Rules
- Use **4 spaces** per indentation level
- Each node must be properly indented relative to its parent
- Colons (`:`) are required after node types

## Node Types

### 1. Control Nodes

#### Root Node
```
root :
```
- Must be the first line
- Can have exactly one child (usually a selector or sequence)

#### Selector Node
```
selector :
```
- Tries children in order until one succeeds
- Returns success on first successful child
- Returns failure if all children fail

#### Sequence Node
```
sequence :
```
- Executes children in order until one fails
- Returns success only if all children succeed
- Returns failure on first failed child

### 2. Condition Nodes

Conditions evaluate game state and return true/false. They do NOT execute actions.

#### Player HP Conditions

```
condition : IsPlayerHPLevel(level)
```
- Returns true if player HP matches the specified level
- **Valid levels**:
  - `Low` - HP is 0-33% (critical, need healing!)
  - `Mid` - HP is 33-66% (moderate, be careful)
  - `High` - HP is 66-100% (healthy, can be aggressive)
- Example: `condition : IsPlayerHPLevel(Low)` - true if HP < 33%
- **Use this for better abstraction**

#### Enemy HP Conditions

```
condition : IsEnemyHPLevel(level)
```
- Returns true if enemy HP matches the specified level
- **Valid levels**: `Low`, `Mid`, `High` (same as player)
- Example: `condition : IsEnemyHPLevel(Low)` - true if enemy HP < 33%
- **Tip**: Use `Low` to finish off enemies with heavy attacks

#### Ability Conditions

```
condition : CanHeal()
```
- Returns true if Heal has not been used on the current floor
- No parameters
- **Important**: Heal is LIMITED to once per floor, use wisely!

```
condition : IsDefending()
```
- Returns true if player is currently in defend stance
- No parameters

#### Combo Conditions

```
condition : HasComboReady(combo_name)
```
- Returns true if the specified combo is ready to be completed
- **Valid combo names**:
  - `TripleLight` - Two Light Attacks performed → next Light Attack = **4x damage**
  - `HeavyFinisher` - Two Light Attacks performed → next Heavy Attack = **3x damage**
  - `CounterStrike` - Defend performed → next Heavy Attack = **2.5x damage**
- Example: `condition : HasComboReady(TripleLight)`

**💡 COMBO STRATEGY - How to Build Combos:**

Combos are built by **repeating the same action**. No special function needed!

- **Want Triple Light (4x damage)?**
  ```
  Turn 1: LightAttack()  ← First hit
  Turn 2: LightAttack()  ← Second hit (combo building...)
  Turn 3: LightAttack()  ← BOOM! 4x damage!
  ```
  Just use `task : LightAttack()` as your default action!

- **Want Heavy Finisher (3x damage)?**
  ```
  Turn 1: LightAttack()  ← First hit
  Turn 2: LightAttack()  ← Second hit (combo ready!)
  Turn 3: HeavyAttack()  ← BOOM! 3x damage!
  ```
  Use `HasComboReady(HeavyFinisher)` to detect when ready

- **Want Counter Strike (2.5x damage)?**
  ```
  Turn 1: Defend()       ← Block incoming damage
  Turn 2: HeavyAttack()  ← BOOM! 2.5x damage!
  ```
  Use `HasComboReady(CounterStrike)` to detect when ready

**Key Insight**: You don't need a special "start combo" function. Just use the same attack repeatedly, and combos happen automatically!

#### Floor Conditions

```
condition : IsFloorBoss()
```
- Returns true if current floor is a boss floor (5 or 10)
- No parameters

```
condition : IsTurnEarly(threshold)
```
- Returns true if turn count <= threshold
- Example: `condition : IsTurnEarly(3)` - true for first 3 turns
- Default threshold: 3

### 3. Action/Task Nodes

Actions execute game actions and always succeed. Use `task :` keyword.

```
task : LightAttack()
```
- Performs a Light Attack (base damage)
- **Part of combo chains** - use repeatedly to build Triple Light!

```
task : HeavyAttack()
```
- Performs a Heavy Attack (1.5x base damage)
- **Penalty**: Same turn, you take 2x damage from enemy
- **Can finish combos** - use after 2 Light Attacks for 3x damage!

```
task : Defend()
```
- Reduces incoming damage by 50% for this turn
- **Part of Counter Strike combo** - follow with Heavy Attack!

```
task : Heal()
```
- Restores 25% of max HP (25 HP if max is 100)
- **Can only be used once per floor**
- Fails if already used on current floor (but BT continues)

## Complete Example

```
root :
    selector :
        sequence :
            condition : IsPlayerHPLevel(Low)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        sequence :
            condition : IsEnemyHPLevel(Low)
            task : HeavyAttack()
        sequence :
            condition : IsPlayerHPLevel(Low)
            task : Defend()
        task : LightAttack()
```

## Important Rules

1. **Always have a fallback action**: The last child of the root selector should be an unconditional action (usually `task : LightAttack()`)

2. **Proper indentation**: Each level must be indented exactly 4 spaces more than its parent

3. **Valid node names**: Only use the condition and action names listed above. Custom names will cause errors.

4. **Combo awareness**: Use `HasComboReady()` conditions to detect when combos can be triggered, OR just use the same attack repeatedly!

5. **Survival first**: Consider healing/defending before aggressive actions

6. **No parameters for actions**: Actions like `LightAttack()` don't take parameters (the parentheses are required but empty)

## Common Mistakes to Avoid

❌ **Wrong**: `condition : isPlayerHP <= 30` (invalid syntax)
✅ **Correct**: `condition : IsPlayerHPLevel(Low)`

❌ **Wrong**: `action : UseAbility(Heal)` (invalid action name)
✅ **Correct**: `task : Heal()`

❌ **Wrong**: `condition : IsAbilityReady(Heal)` (invalid condition name)
✅ **Correct**: `condition : CanHeal()`

❌ **Wrong**: Using 2 spaces for indentation
✅ **Correct**: Using 4 spaces for indentation

❌ **Wrong**: `task : LightAttack` (missing parentheses)
✅ **Correct**: `task : LightAttack()`

❌ **Wrong**: `condition : IsPlayerHPLow(30)` (old numeric style)
✅ **Correct**: `condition : IsPlayerHPLevel(Low)` (use abstract levels)
