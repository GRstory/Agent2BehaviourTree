"""
Behaviour Tree Executor

Executes behaviour trees against game state to determine player actions.
Integrates the existing BT parser with game-specific nodes.
"""

from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bt_parser import BTNode, parse_bt_dsl
from .game_engine import GameState, ActionType
from .bt_nodes import create_condition_node, create_action_node, BTCondition, BTAction


class BTExecutor:
    """Executes behaviour trees to determine player actions"""
    
    def __init__(self, bt_root: BTNode):
        self.bt_root = bt_root
        self.execution_trace = []  # For debugging
    
    def execute(self, state: GameState) -> Optional[ActionType]:
        """
        Execute the behaviour tree and return the action to take
        Returns None if no valid action is determined
        """
        self.execution_trace = []
        action = self._execute_node(self.bt_root, state)
        return action
    
    def _execute_node(self, node: BTNode, state: GameState) -> Optional[ActionType]:
        """Recursively execute a BT node"""
        
        node_type = node.node_type.lower()
        
        # Root node - just execute children
        if node_type == "root":
            if node.children:
                return self._execute_node(node.children[0], state)
            return None
        
        # Selector node - try children until one succeeds
        elif node_type == "selector":
            self.execution_trace.append(f"Selector: trying {len(node.children)} children")
            for child in node.children:
                result = self._execute_node(child, state)
                if result is not None:  # Child succeeded
                    self.execution_trace.append(f"Selector: child succeeded")
                    return result
            self.execution_trace.append(f"Selector: all children failed")
            return None
        
        # Sequence node - execute children in order, all must succeed
        elif node_type == "sequence":
            self.execution_trace.append(f"Sequence: checking {len(node.children)} children")
            last_result = None
            for i, child in enumerate(node.children):
                # If it's a condition, evaluate it
                if child.node_type.lower() == "condition":
                    if not self._evaluate_condition(child, state):
                        self.execution_trace.append(f"Sequence: condition {i} failed")
                        return None
                    self.execution_trace.append(f"Sequence: condition {i} passed")
                # If it's an action or composite, execute it
                else:
                    result = self._execute_node(child, state)
                    if result is not None:
                        last_result = result
                    elif i < len(node.children) - 1:
                        # Non-final node failed
                        self.execution_trace.append(f"Sequence: child {i} failed")
                        return None
            return last_result
        
        # Condition node - evaluate condition
        elif node_type == "condition":
            result = self._evaluate_condition(node, state)
            self.execution_trace.append(f"Condition {node.param}: {result}")
            return None  # Conditions don't return actions
        
        # Task/Action node - execute action
        elif node_type == "task" or node_type == "action":
            action = self._execute_action(node, state)
            self.execution_trace.append(f"Action {node.param}: {action}")
            return action
        
        else:
            self.execution_trace.append(f"Unknown node type: {node_type}")
            return None
    
    def _evaluate_condition(self, node: BTNode, state: GameState) -> bool:
        """Evaluate a condition node"""
        if not node.param:
            return False
        
        try:
            # Parse condition parameter (e.g., "IsPlayerHPLow(30)")
            param_str = node.param
            
            # Extract node type and parameter
            if '(' in param_str:
                node_type = param_str[:param_str.index('(')]
                param = param_str[param_str.index('(')+1:param_str.rindex(')')]
            else:
                node_type = param_str
                param = None
            
            # Create and evaluate condition
            condition = create_condition_node(node_type, param)
            return condition.evaluate(state)
        
        except Exception as e:
            self.execution_trace.append(f"Error evaluating condition {node.param}: {e}")
            return False
    
    def _execute_action(self, node: BTNode, state: GameState) -> Optional[ActionType]:
        """Execute an action node"""
        if not node.param:
            return None
        
        try:
            # Parse action parameter (e.g., "LightAttack")
            action_type = node.param.strip()
            
            # Remove parentheses if present
            if '(' in action_type:
                action_type = action_type[:action_type.index('(')]
            
            # Create and execute action
            action = create_action_node(action_type)
            return action.execute(state)
        
        except Exception as e:
            self.execution_trace.append(f"Error executing action {node.param}: {e}")
            return None
    
    def get_trace(self) -> str:
        """Get execution trace for debugging"""
        return "\n".join(self.execution_trace)


def create_bt_executor_from_dsl(dsl_text: str) -> Optional[BTExecutor]:
    """
    Parse DSL text and create a BT executor
    Returns None if parsing fails
    """
    bt_tree = parse_bt_dsl(dsl_text)
    if bt_tree is None:
        return None
    return BTExecutor(bt_tree)


# ============================================================================
# EXAMPLE BTs FOR TESTING
# ============================================================================

EXAMPLE_BT_AGGRESSIVE = """
root :
    selector :
        sequence :
            condition : IsPlayerHPLow(20)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        sequence :
            condition : IsEnemyHPLow(30)
            task : HeavyAttack()
        task : LightAttack()
"""

EXAMPLE_BT_DEFENSIVE = """
root :
    selector :
        sequence :
            condition : IsPlayerHPLow(40)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : IsPlayerHPLow(50)
            task : Defend()
        sequence :
            condition : HasComboReady(CounterStrike)
            task : HeavyAttack()
        sequence :
            condition : IsEnemyHPLow(25)
            task : HeavyAttack()
        task : LightAttack()
"""

EXAMPLE_BT_BALANCED = """
root :
    selector :
        sequence :
            condition : IsPlayerHPLevel(Low)
            condition : CanHeal()
            task : Heal()
        sequence :
            condition : IsPlayerHPLevel(Low)
            condition : IsEnemyHPLevel(High)
            task : Defend()
        sequence :
            condition : HasComboReady(TripleLight)
            task : LightAttack()
        sequence :
            condition : HasComboReady(CounterStrike)
            task : HeavyAttack()
        sequence :
            condition : IsEnemyHPLevel(Low)
            task : HeavyAttack()
        task : LightAttack()
"""
