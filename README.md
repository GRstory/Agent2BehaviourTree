# PORTAL-Inspired Dungeon Game with LLM Behaviour Tree Agent

A clone of the PORTAL framework (from "Agents Play Thousands of 3D Video Games") adapted for text-based games. This project demonstrates how LLM agents can learn to play games by iteratively improving Behaviour Trees based on gameplay feedback.

## Overview

This system enables an LLM agent to:
1. **Generate** initial Behaviour Trees from game rules
2. **Execute** BTs to play a 10-floor turn-based dungeon game
3. **Analyze** abstract gameplay logs to identify mistakes
4. **Improve** BTs based on tactical feedback
5. **Iterate** until victory or convergence

### Key Differences from PORTAL

- **Input**: Text logs instead of video gameplay
- **Game**: Turn-based dungeon crawler instead of 3D FPS
- **Feedback**: Log-based tactical analysis instead of VLM video analysis
- **Output**: Behaviour Tree DSL instead of direct policy code

## Game Mechanics

### 10-Floor Dungeon Crawler
- **Turn-based combat**: Player acts first, then enemy
- **4 Actions**: Light Attack, Heavy Attack, Defend, Heal
- **Combo system**: Chain attacks for massive damage multipliers
- **Floor progression**: Enemies get stronger each floor (floors 5 & 10 are bosses)

### Combo Patterns
1. **Triple Light** (4x damage): Light → Light → Light
2. **Heavy Finisher** (3x damage): Light → Light → Heavy
3. **Counter Strike** (2.5x damage): Defend → Heavy

### Abstract Logging
Numerical stats are converted to natural language:
- HP: "Critical", "Very Low", "Low", "Medium", "High", "Very High", "Full"
- Damage: "Minimal", "Light", "Medium", "Heavy", "Massive"
- Includes tactical hints and observations

## Installation

```bash
# Clone repository
git clone <repository-url>
cd Agent2BehaviourTree

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key (if using real LLM)
export OPENAI_API_KEY="your-api-key-here"
# Or create .env file with: OPENAI_API_KEY=your-api-key-here
```

## Usage

### Quick Start (Mock LLM - No API Calls)

```bash
python runner.py --mock --iterations 3
```

This runs 3 iterations using a mock LLM (no API costs, for testing).

### Full Run (Real LLM)

```bash
python runner.py --iterations 5
```

This runs 5 iterations using GPT-4 to generate and improve BTs.

### Command Line Options

```bash
python runner.py [OPTIONS]

Options:
  --iterations N    Number of improvement iterations (default: 5)
  --mock           Use mock LLM (no API calls, for testing)
  --bt PATH        Path to initial BT file (skip LLM generation)
  --no-save        Don't save logs and BTs to disk
  --quiet          Minimal console output
```

### Example: Use Custom Initial BT

```bash
python runner.py --bt examples/example_bt_balanced.txt --iterations 3
```

## Project Structure

```
Agent2BehaviourTree/
├── main.py                    # Original BT parser
├── runner.py                  # Main orchestration script
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── TextGame/                  # Game engine and BT system
│   ├── game_engine.py         # Turn-based combat engine
│   ├── abstract_logger.py     # LLM-friendly log generation
│   ├── bt_nodes.py            # Condition and action nodes
│   ├── bt_executor.py         # BT execution engine
│   ├── bt_dsl_spec.md         # DSL specification for LLM
│   ├── llm_agent.py           # LLM integration
│   └── prompts.py             # Prompt templates
│
├── examples/                  # Example BTs
│   ├── example_bt_aggressive.txt
│   ├── example_bt_defensive.txt
│   └── example_bt_balanced.txt
│
├── logs/                      # Generated gameplay logs (created on run)
└── generated_bts/             # Generated BTs (created on run)
```

## Behaviour Tree DSL

### Example BT

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
        sequence :
            condition : IsEnemyHPLow(25)
            task : HeavyAttack()
        task : LightAttack()
```

### Available Nodes

**Conditions:**
- `IsPlayerHPLow(threshold)` / `IsPlayerHPHigh(threshold)`
- `IsEnemyHPLow(threshold)` / `IsEnemyHPHigh(threshold)`
- `CanHeal()` - Check if heal is off cooldown
- `HasComboReady(combo_name)` - Check if combo is ready
- `IsFloorBoss()` - Check if current floor is boss
- `IsTurnEarly(threshold)` - Check if early in fight

**Actions:**
- `LightAttack()` - Base damage attack
- `HeavyAttack()` - 2x damage attack
- `Defend()` - Increase defense
- `Heal()` - Restore 30 HP (3-turn cooldown)

See `TextGame/bt_dsl_spec.md` for complete specification.

## How It Works

### PORTAL-Inspired Improvement Loop

```
1. LLM generates initial BT from game rules
   ↓
2. BT executes in game → produces abstract logs
   ↓
3. LLM analyzes logs → identifies mistakes
   ↓
4. LLM generates tactical feedback
   ↓
5. LLM creates improved BT
   ↓
6. Repeat until victory or max iterations
```

### Example Iteration

**Iteration 1**: Simple aggressive BT → Dies on Floor 3
- **Analysis**: "Not using combos, healing too late"
- **Feedback**: "Add combo detection, heal at 40% instead of 30%"
- **Improved BT**: Adds `HasComboReady` conditions

**Iteration 2**: Combo-aware BT → Reaches Floor 6
- **Analysis**: "Good combo usage, but too aggressive when low HP"
- **Feedback**: "Add defensive sequence when HP < 50%"
- **Improved BT**: Adds defend logic

**Iteration 3**: Balanced BT → Victory! (All 10 floors cleared)

## Configuration

Edit `config.py` to customize:

```python
# LLM settings
model = "gpt-4"  # or "gpt-3.5-turbo"
temperature = 0.7

# Game settings
max_floors = 10
player_starting_hp = 100

# Runner settings
max_iterations = 5
victory_early_stop = True
```

## Development

### Running Tests

```bash
# Test game engine
python -c "from TextGame.game_engine import DungeonGame; game = DungeonGame(); print('Game engine OK')"

# Test BT parsing
python main.py

# Test BT execution
python -c "from TextGame.bt_executor import EXAMPLE_BT_BALANCED, create_bt_executor_from_dsl; exec = create_bt_executor_from_dsl(EXAMPLE_BT_BALANCED); print('BT executor OK')"

# Test full run with mock LLM
python runner.py --mock --iterations 1 --quiet
```

### Adding New Condition Nodes

1. Define class in `TextGame/bt_nodes.py`
2. Add to `create_condition_node()` factory
3. Document in `TextGame/bt_dsl_spec.md`

### Adding New Action Nodes

1. Define class in `TextGame/bt_nodes.py`
2. Add to `create_action_node()` factory
3. Document in `TextGame/bt_dsl_spec.md`

## Results and Analysis

After running, check:
- `logs/` - Gameplay logs with abstract descriptions
- `generated_bts/` - All generated BTs (initial and improved)
- Console output - Performance history and final summary

## Limitations

- Text-based only (no visual gameplay)
- Simple enemy AI (pattern-based)
- Limited to turn-based combat
- LLM API costs for real runs

## Future Enhancements

- [ ] More complex enemy behaviors
- [ ] Item system (potions, weapons, armor)
- [ ] Multiple player classes
- [ ] Procedurally generated enemies
- [ ] Visualization of BT execution
- [ ] Performance metrics dashboard

## References

- **PORTAL Paper**: "Agents Play Thousands of 3D Video Games" - Demonstrates VLM-based tactical feedback for game-playing agents
- **Behaviour Trees**: Common AI pattern in game development for decision-making

## License

MIT License

## Author

Created as a clone project inspired by the PORTAL framework.
