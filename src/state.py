"""8数码问题状态建模 — 成员A负责."""
from copy import deepcopy

# 默认目标状态（从公共常量导入，以src/__init__.py为准）
from . import DEFAULT_GOAL as GOAL_1D

# 移动方向映射
DIRECTIONS = [(-1, 0, 'up'), (1, 0, 'down'), (0, -1, 'left'), (0, 1, 'right')]


class PuzzleState:
    """8数码棋盘状态，内部用一维元组存储（可哈希），按需转二维."""

    def __init__(self, board, goal_1d=None):
        if isinstance(board, (list, tuple)) and len(board) == 9 and not isinstance(board[0], (list, tuple)):
            self.board_1d = tuple(board)
        else:
            flat = []
            for row in board:
                flat.extend(row)
            self.board_1d = tuple(flat)
        self.goal_1d = goal_1d if goal_1d is not None else GOAL_1D

    def to_2d(self):
        """转为3×3二维列表（用于打印和移动逻辑展示）."""
        return [
            list(self.board_1d[0:3]),
            list(self.board_1d[3:6]),
            list(self.board_1d[6:9]),
        ]

    @property
    def blank_pos(self):
        """空格(0)的坐标 (row, col)."""
        idx = self.board_1d.index(0)
        return (idx // 3, idx % 3)

    def get_neighbors(self):
        """生成所有合法的后继状态，返回 [(new_state, action), ...]."""
        r, c = self.blank_pos
        neighbors = []
        for dr, dc, action in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                lst = list(self.board_1d)
                bi = r * 3 + c
                si = nr * 3 + nc
                lst[bi], lst[si] = lst[si], lst[bi]
                neighbors.append((PuzzleState(lst, self.goal_1d), action))
        return neighbors

    def is_goal(self):
        return self.board_1d == self.goal_1d

    def __eq__(self, other):
        return self.board_1d == other.board_1d

    def __hash__(self):
        return hash(self.board_1d)

    def __lt__(self, other):
        return self.board_1d < other.board_1d

    def __repr__(self):
        b = self.to_2d()
        lines = [' '.join(str(x) if x != 0 else '_' for x in row) for row in b]
        return '\n'.join(lines)

    @staticmethod
    def from_string(s):
        """从字符串解析状态，如 '1 2 3 4 5 6 7 8 0'."""
        nums = [int(x) for x in s.split()]
        return PuzzleState(nums)

    @staticmethod
    def copy(state):
        """深拷贝状态（当需要修改时用）."""
        return PuzzleState(list(state.board_1d), state.goal_1d)


def print_path(path):
    """打印搜索路径：每一步的棋盘 + 动作."""
    for i, (state, action) in enumerate(path):
        if action:
            print(f"Step {i}: {action}")
        else:
            print(f"Step {i}: start")
        print(state)
        print()
