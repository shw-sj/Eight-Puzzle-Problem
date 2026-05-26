"""
启发式函数模块 — 成员A负责h1, 成员B负责h2/h3/h4

接口约定（与成员A协商）：
  每个启发式函数签名: fn(state_1d, goal_1d) -> float
  - state_1d: 长度为9的一维元组，0表示空格，如 (1,2,3,4,5,6,7,0,8)
  - goal_1d:  同上格式的目标状态
  - 返回值: 启发式估计代价（越小越精确，0=已到达目标）

可采纳性 (admissibility):
  所有启发式必须满足 h(n) <= h*(n)，即不高估实际代价。
  这是A*算法找到最优解的充分条件。
"""
import math

# ---------- h1: 曼哈顿距离 (成员A负责) ----------

def manhattan(state_1d, goal_1d):
    """
    h1 — 曼哈顿距离 (Manhattan Distance).

    每个棋子（1~8）当前位置到目标位置的曼哈顿距离之和.
    公式: h = Σ |r_cur - r_goal| + |c_cur - c_goal|

    可采纳性: 每次移动最多让一个棋子靠近目标1步，故曼哈顿距离 <= 实际步数.
    """
    distance = 0
    for idx, val in enumerate(state_1d):
        if val == 0:
            continue
        goal_idx = goal_1d.index(val)
        r1, c1 = idx // 3, idx % 3
        r2, c2 = goal_idx // 3, goal_idx % 3
        distance += abs(r1 - r2) + abs(c1 - c2)
    return distance


# ============================================================
# 以下为成员B负责的启发式函数
# ============================================================

# ---------- h2: 错位棋子数 (成员B) ----------

def misplaced_tiles(state_1d, goal_1d):
    """
    h2 — 错位棋子数 (Misplaced Tiles).

    统计不在目标位置的棋子个数（不计空格0）.
    每个错位棋子至少需要移动1次才能归位.

    可采纳性: 每次移动最多修正1个错位棋子，故错位数 <= 实际步数.
    特点: 计算极快 O(1)，但精度最低，会扩展较多节点.
    """
    count = 0
    for i, val in enumerate(state_1d):
        if val != 0 and val != goal_1d[i]:
            count += 1
    return count


# ---------- h3: 欧几里得距离 (成员B) ----------

def euclidean(state_1d, goal_1d):
    """
    h3 — 欧几里得距离 (Euclidean Distance).

    每个棋子当前位置到目标位置的直线距离之和.
    公式: h = Σ sqrt((r_cur - r_goal)^2 + (c_cur - c_goal)^2)

    可采纳性: 直线距离 <= 曼哈顿距离 <= 实际步数，因此也是可采纳的.
    特点: 精度介于 h2 和 h1 之间，但包含 sqrt 运算，计算稍慢.
    """
    distance = 0.0
    for idx, val in enumerate(state_1d):
        if val == 0:
            continue
        goal_idx = goal_1d.index(val)
        r1, c1 = idx // 3, idx % 3
        r2, c2 = goal_idx // 3, goal_idx % 3
        distance += math.sqrt((r1 - r2) ** 2 + (c1 - c2) ** 2)
    return distance


# ---------- h4: 线性冲突 (成员B, 加分项) ----------

def linear_conflict(state_1d, goal_1d):
    """
    h4 — 曼哈顿距离 + 线性冲突惩罚 (Linear Conflict).

    基础值为曼哈顿距离。在此基础上检测:
      - 同行冲突: 两个数字在同一行且目标行也相同，但左右顺序颠倒
      - 同列冲突: 两个数字在同一列且目标列也相同，但上下顺序颠倒
    每发现一个线性冲突，至少需要多走 2 步来解决（一个让路，一个归位），
    故额外加 2.

    可采纳性: 线性冲突是解决过程中不可避免的额外代价，
    因此 h4 = 曼哈顿 + 2*冲突数 仍然是可采纳的.
    特点: 8数码最精确的可采纳启发式之一，扩展节点数最少.
    参考文献: Hansson, Mayer, & Yung (1992)
    """
    h = manhattan(state_1d, goal_1d)

    # 检测行冲突
    for row in range(3):
        row_tiles = []
        for col in range(3):
            val = state_1d[row * 3 + col]
            if val == 0:
                continue
            goal_idx = goal_1d.index(val)
            goal_row = goal_idx // 3
            goal_col = goal_idx % 3
            if goal_row == row:
                row_tiles.append((col, goal_col))
        # 两两检查是否顺序颠倒
        for i in range(len(row_tiles)):
            for j in range(i + 1, len(row_tiles)):
                if (row_tiles[i][0] < row_tiles[j][0] and
                    row_tiles[i][1] > row_tiles[j][1]):
                    h += 2
                elif (row_tiles[i][0] > row_tiles[j][0] and
                      row_tiles[i][1] < row_tiles[j][1]):
                    h += 2

    # 检测列冲突
    for col in range(3):
        col_tiles = []
        for row in range(3):
            val = state_1d[row * 3 + col]
            if val == 0:
                continue
            goal_idx = goal_1d.index(val)
            goal_row = goal_idx // 3
            goal_col = goal_idx % 3
            if goal_col == col:
                col_tiles.append((row, goal_row))
        for i in range(len(col_tiles)):
            for j in range(i + 1, len(col_tiles)):
                if (col_tiles[i][0] < col_tiles[j][0] and
                    col_tiles[i][1] > col_tiles[j][1]):
                    h += 2
                elif (col_tiles[i][0] > col_tiles[j][0] and
                      col_tiles[i][1] < col_tiles[j][1]):
                    h += 2

    return h


# ---------- 启发式函数注册表 ----------

HEURISTICS = {
    'h1': ('曼哈顿距离', manhattan),
    'h2': ('错位棋子数', misplaced_tiles),
    'h3': ('欧几里得距离', euclidean),
    'h4': ('线性冲突', linear_conflict),
}


# ---------- 测试 ----------
if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src import DEFAULT_GOAL

    goal = DEFAULT_GOAL

    # 一个简单测试状态：8和空格交换
    test_states = [
        ("目标状态", (1, 2, 3, 4, 5, 6, 7, 8, 0)),
        ("空格左移1步", (1, 2, 3, 4, 5, 6, 7, 0, 8)),
        ("困难布局", (8, 6, 7, 2, 5, 4, 3, 0, 1)),
        ("著名最难", (8, 6, 7, 2, 5, 4, 3, 1, 0)),
    ]

    print("=== 启发式函数测试 ===")
    for name, state in test_states:
        print(f"\n{name}: {state}")
        for key, (desc, fn) in HEURISTICS.items():
            print(f"  {key} ({desc}): {fn(state, goal)}")
