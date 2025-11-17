class BTNode:
    """
    Behavior Tree 노드를 위한 기본 클래스.
    - node_type: 'selector', 'sequence', 'condition', 'task' 등
    - param: 'IsHPLow', 'Attack' 등
    - children: 자식 노드 리스트
    """
    def __init__(self, node_type, param=None):
        self.node_type = node_type.strip()
        self.param = param.strip() if param else None
        self.children = []

    def __repr__(self, level=0):
        """트리 구조를 시각적으로 출력하기 위한 헬퍼 함수"""
        indent = "    " * level
        ret = f"{indent}{self.node_type}"
        if self.param:
            ret += f" : {self.param}"
        ret += "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

# 2. DSL 파서 함수
def parse_bt_dsl(dsl_text: str, indent_unit: int = 4) -> BTNode:
    """
    들여쓰기 기반 DSL 텍스트를 파싱하여 BTNode 트리로 변환한다.

    :param dsl_text: LLM이 생성한 DSL 텍스트
    :param indent_unit: 들여쓰기 단위 (기본값: 공백 4칸)
    :return: 루트 BTNode 객체
    """
    lines = dsl_text.strip().split('\n')
    if not lines:
        return None

    # 라인을 파싱하여 (레벨, 노드) 튜플로 변환
    def parse_line(line_str: str):
        indent_len = len(line_str) - len(line_str.lstrip(' '))
        if indent_len % indent_unit != 0:
            raise ValueError(f"일관되지 않은 들여쓰기: '{line_str}'")
        
        level = indent_len // indent_unit
        
        parts = line_str.strip().split(' : ', 1)
        node_type = parts[0]
        param = parts[1] if len(parts) > 1 else None
        
        return level, BTNode(node_type, param)

    # --- 스택 기반 파싱 로직 ---
    try:
        root_level, root_node = parse_line(lines[0])
        if root_level != 0:
            raise ValueError("루트 노드는 들여쓰기가 없어야 합니다.")

        # 스택은 (레벨, 노드) 튜플을 저장한다.
        # 스택의 최상단은 항상 현재 노드의 부모 후보이다.
        stack = [(root_level, root_node)]

        for line_str in lines[1:]:
            if not line_str.strip():
                continue
            
            level, new_node = parse_line(line_str)
            
            # 현재 레벨에 맞는 부모를 찾을 때까지 스택에서 pop
            # (현재 레벨이 스택 최상단 레벨보다 같거나 낮으면 pop)
            while level <= stack[-1][0]:
                stack.pop()
            
            # 스택의 최상단(이제 부모임)에 자식으로 추가
            parent_node = stack[-1][1]
            parent_node.children.append(new_node)
            
            # 현재 노드를 스택에 push (미래의 부모가 될 수 있음)
            stack.append((level, new_node))
            
        return root_node

    except Exception as e:
        print(f"DSL 파싱 오류: {e}")
        return None

# --- 예제 실행 ---
# (이전 대화에서 논의된 '포션 아끼기' 전략 BT)
dsl_example = """
root :
    selector :
        sequence :
            condition : IsHPLow(30)
            condition : HasItem(Potion)
            task : UseItem(Potion)
        sequence :
            condition : IsEnemyPresent
            selector :
                sequence :
                    condition : IsHPLow(20)
                    task : Flee
                sequence :
                    condition : IsHPLow(50)
                    task : Defend
                task : Attack
"""

bt_tree = parse_bt_dsl(dsl_example)
print("--- 파싱된 BT 트리 구조 ---")
print(bt_tree)