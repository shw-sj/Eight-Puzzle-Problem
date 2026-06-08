"""
辅助算法 — 成员C负责

- random_state: 从目标状态随机游走，生成保证有解的初始状态
- verify_astar_path: 用 BFS 验证 A* 路径是否为最短
"""
import random

from src import DEFAULT_GOAL
from src.solvability import is_solvable
from src.solver import bfs, _get_neighbors

# 难度 → 随机游走步数范围（从目标出发，保证有解）
DIFFICULTY_STEPS = {
    "简单": (5, 10),
    "中等": (15, 25),
    "困难": (30, 50),
}

REVERSE_ACTION = {"up": "down", "down": "up", "left": "right", "right": "left"}


def random_state(goal=None, steps=None, difficulty=None, seed=None, exclude_goal=True):
    """
    从目标状态出发随机执行 N 步合法移动，生成有解的初始状态。

    Args:
        goal: 目标状态，默认标准完成态
        steps: 游走步数；与 difficulty 二选一
        difficulty: "简单" | "中等" | "困难"
        seed: 随机种子，None 表示不固定
        exclude_goal: 若结果为 goal 本身则重试

    Returns:
        tuple: 初始状态（一维元组）
    """
    if goal is None:
        goal = DEFAULT_GOAL

    rng = random.Random(seed)

    if steps is None:
        if difficulty not in DIFFICULTY_STEPS:
            raise ValueError(f"未知难度: {difficulty!r}，可选: {list(DIFFICULTY_STEPS)}")
        lo, hi = DIFFICULTY_STEPS[difficulty]
        steps = rng.randint(lo, hi)

    for _ in range(32):
        state = list(goal)
        prev_action = None
        for _ in range(steps):
            neighbors = _get_neighbors(tuple(state))
            if prev_action is not None:
                rev = REVERSE_ACTION[prev_action]
                filtered = [(s, a) for s, a in neighbors if a != rev]
                if filtered:
                    neighbors = filtered
            next_state, action = rng.choice(neighbors)
            state = list(next_state)
            prev_action = action

        result = tuple(state)
        if not exclude_goal or result != goal:
            assert is_solvable(result, goal), "随机生成状态应始终有解"
            return result

    return result


def bfs_shortest_steps(start, goal):
    """
    BFS 求最短步数。

    Returns:
        (steps, expanded) — 无解时 steps 为 None
    """
    path, expanded = bfs(start, goal)
    if path is None:
        return None, expanded
    return len(path) - 1, expanded


def verify_astar_path(initial, goal, astar_path):
    """
    用 BFS 验证 A* 路径长度是否为最短。

    Args:
        initial: 初始状态
        goal: 目标状态
        astar_path: A* 返回的状态列表（含起点与终点）

    Returns:
        dict:
            is_optimal (bool): A* 路径是否最短
            astar_steps (int): A* 步数
            bfs_steps (int|None): BFS 最短步数
            bfs_expanded (int): BFS 扩展节点数
            message (str): 可读结论
    """
    if astar_path is None:
        bfs_steps, bfs_expanded = bfs_shortest_steps(initial, goal)
        if bfs_steps is None:
            return {
                "is_optimal": True,
                "astar_steps": None,
                "bfs_steps": None,
                "bfs_expanded": bfs_expanded,
                "message": "A* 与 BFS 均未找到解",
            }
        return {
            "is_optimal": False,
            "astar_steps": None,
            "bfs_steps": bfs_steps,
            "bfs_expanded": bfs_expanded,
            "message": f"A* 无解，但 BFS 找到 {bfs_steps} 步解（异常）",
        }

    astar_steps = len(astar_path) - 1
    bfs_steps, bfs_expanded = bfs_shortest_steps(initial, goal)

    if bfs_steps is None:
        return {
            "is_optimal": False,
            "astar_steps": astar_steps,
            "bfs_steps": None,
            "bfs_expanded": bfs_expanded,
            "message": "A* 找到解，但 BFS 未找到（异常）",
        }

    is_optimal = astar_steps == bfs_steps
    if is_optimal:
        msg = f"验证通过：A* 路径 {astar_steps} 步 = BFS 最短 {bfs_steps} 步"
    else:
        msg = f"验证失败：A* {astar_steps} 步 > BFS 最短 {bfs_steps} 步"

    return {
        "is_optimal": is_optimal,
        "astar_steps": astar_steps,
        "bfs_steps": bfs_steps,
        "bfs_expanded": bfs_expanded,
        "message": msg,
    }


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.main import EightPuzzleAStar

    goal = DEFAULT_GOAL
    print("=== 随机生成测试 ===")
    for diff in DIFFICULTY_STEPS:
        state = random_state(goal=goal, difficulty=diff, seed=42)
        print(f"  {diff}: {state}, 有解={is_solvable(state, goal)}")

    print("\n=== BFS 验证测试 ===")
    start = random_state(goal=goal, difficulty="简单", seed=1)
    solver = EightPuzzleAStar(start, goal)
    path, expanded = solver.solve()
    result = verify_astar_path(start, goal, path)
    print(f"  初始: {start}")
    print(f"  A* 扩展: {expanded}")
    print(f"  {result['message']}")
