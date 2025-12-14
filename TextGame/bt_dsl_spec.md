# Behaviour Tree DSL Specification - Enhanced Combat System

## Overview
This DSL defines Behaviour Trees for controlling a player character in a turn-based RPG-style combat game with elemental weaknesses, resource management, and status effects.

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

---

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
- **Use for**: Prioritized decision-making (e.g., emergency heal > attack)

#### Sequence Node
```
sequence :
```
- Executes children in order until one fails
- Returns success only if all children succeed
- Returns failure on first failed child
- **Use for**: Conditional actions (e.g., if HP low AND can heal, then heal)

---

### 2. Condition Nodes

Conditions evaluate game state and return true/false. They do NOT execute actions.

#### HP Conditions

```
condition : IsPlayerHPLow(threshold)
```
- Returns true if player HP percentage < threshold
- Example: `condition : IsPlayerHPLow(30)` - true if HP < 30%
- Default: 30

```
condition : IsPlayerHPHigh(threshold)
```
- Returns true if player HP percentage > threshold
- Default: 70

```
condition : IsEnemyHPLow(threshold)
```
- Returns true if enemy HP percentage < threshold
- Default: 30

```
condition : IsEnemyHPHigh(threshold)
```
- Returns true if enemy HP percentage > threshold
- Default: 70

#### Resource Conditions (NEW!)

```
condition : HasTP(amount)
```
- Returns true if player has >= amount TP
- Example: `condition : HasTP(30)` - true if TP >= 30
- Default: 30

```
condition : HasMP(amount)
```
- Returns true if player has >= amount MP
- Example: `condition : HasMP(20)` - true if MP >= 20
- Default: 20

```
condition : IsTPLow(threshold)
```
- Returns true if player TP < threshold
- Default: 30

```
condition : IsMPLow(threshold)
```
- Returns true if player MP < threshold
- Default: 30

#### Enemy Type Conditions (NEW!)

```
condition : IsEnemy(enemy_name)
```
- Returns true if current enemy matches specific type
- Values: `FireGolem`, `IceWraith`, `ThunderDrake`
- Example: `condition : IsEnemy(FireGolem)`

```
condition : EnemyWeakTo(element)
```
- Returns true if enemy is weak to specific element (takes 1.5x damage)
- Values: `Fire`, `Ice`, `Lightning`
- Example: `condition : EnemyWeakTo(Ice)` - true if enemy weak to Ice

```
condition : EnemyResistantTo(element)
```
- Returns true if enemy is resistant to element (takes 0.5x damage)
- Values: `Fire`, `Ice`, `Lightning`
- Example: `condition : EnemyResistantTo(Fire)`

```
condition : HasScannedEnemy()
```
- Returns true if enemy has been scanned (weakness revealed)
- No parameters

#### Status Ailment Conditions (NEW!)

```
condition : HasAilment(ailment_name)
```
- Returns true if player has specific status ailment
- Values: `Burn`, `Freeze`, `Paralyze`, `AttackDown`, `Defending`
- Example: `condition : HasAilment(Paralyze)`

```
condition : EnemyHasBuff(buff_name)
```
- Returns true if enemy has specific buff
- Values: `RageBuff`, `Enrage`, `StormCharge`, `FrostAura`
- Example: `condition : EnemyHasBuff(Enrage)`

```
condition : IsFrozen()
```
- Returns true if player is frozen (will skip next turn)

```
condition : IsParalyzed()
```
- Returns true if player is paralyzed (50% miss chance)

#### Tactical Conditions

```
condition : CanHeal()
```
- Returns true if Heal is off cooldown AND player has >= 30 MP
- No parameters

```
condition : EnemyInPhase(phase_name)
```
- Returns true if enemy is in specific HP phase
- Values: `Healthy` (HP > 60%), `Wounded` (30-60%), `Critical` (< 30%)
- Example: `condition : EnemyInPhase(Critical)`

```
condition : EnemyIsTelegraphing(action_name)
```
- Returns true if enemy has telegraphed a specific action for THIS turn
- Enemy telegraphs at end of previous turn, visible at start of current turn
- Values: `HeavySlam`, `ThunderStrike`, `Slam`, `FireSpell`, etc.
- Example: `condition : EnemyIsTelegraphing(HeavySlam)` - Defend against heavy attack

```
condition : IsTurnEarly(threshold)
```
- Returns true if turn count <= threshold
- Example: `condition : IsTurnEarly(3)` - true for turns 1-3
- Default: 3

---

### 3. Action/Task Nodes

Actions execute player abilities and return the action to perform.

#### Neutral Attacks

```
task : Attack()
```
- **Cost**: 0 TP (FREE!)
- **Damage**: 15-18 (neutral)
- **Effect**: Gains +15 TP
- **Use**: Default action, TP generation

```
task : PowerStrike()
```
- **Cost**: 30 TP
- **Damage**: 40-50 (neutral, high damage)
- **Use**: When TP is high, against Neutral enemies

#### Elemental Magic

```
task : FireSpell()
```
- **Cost**: 20 MP
- **Damage**: 25-30 (Fire element)
- **Effect**: 1.5x vs Ice enemies, 0.5x vs Fire enemies, 25% chance to Burn
- **Use**: Against Ice enemies (Ice Wraith)

```
task : IceSpell()
```
- **Cost**: 20 MP
- **Damage**: 25-30 (Ice element)
- **Effect**: 1.5x vs Lightning enemies, 0.5x vs Ice enemies, 25% chance to Freeze
- **Use**: Against Lightning enemies (Thunder Drake)

```
task : LightningSpell()
```
- **Cost**: 20 MP
- **Damage**: 25-30 (Lightning element)
- **Effect**: 1.5x vs Fire enemies, 0.5x vs Lightning enemies, 25% chance to Paralyze
- **Use**: Against Fire enemies (Fire Golem)

#### Support Actions

```
task : Defend()
```
- **Cost**: 0 TP (FREE!)
- **Effect**: Reduce damage by 50% for 1 turn, gain +20 TP
- **Use**: When enemy telegraphs heavy attack, or to build TP

```
task : Heal()
```
- **Cost**: 30 MP
- **Effect**: Restore 45 HP
- **Cooldown**: 3 turns
- **Use**: When HP < 30-40%

```
task : Scan()
```
- **Cost**: 15 MP
- **Effect**: Reveal enemy type, weakness, and current HP
- **Duration**: Permanent (for this battle)
- **Use**: Turn 1-2 to identify optimal strategy

---


---

## Quick Reference

### Common Patterns

**Exploit Weakness:**
```
sequence :
    condition : HasScannedEnemy()
    condition : EnemyWeakTo(Ice)
    condition : HasMP(20)
    task : IceSpell()
```

**Emergency Heal:**
```
sequence :
    condition : IsPlayerHPLow(30)
    condition : CanHeal()
    task : Heal()
```

**Defend on Telegraph (Reactive Defense):**
```
# Enemy telegraphed HeavySlam at end of last turn
# Now we can react defensively
sequence :
    condition : EnemyIsTelegraphing(HeavySlam)
    task : Defend()
```

---

## Key Strategy Points

- **React to telegraphs** - Enemy shows next action, defend against heavy attacks!
- **Scan on turn 1-2** to identify enemy weakness
- **Exploit elemental advantage** (1.5x damage!)
- **Heal when HP < 30-40%**
- **Always end with fallback**: `task : Attack()`

---

## Elemental Matchups

- Fire Golem → Use IceSpell (1.5x)
- Ice Wraith → Use LightningSpell (1.5x)  
- Thunder Drake → Use FireSpell (1.5x)

