# -*- coding: utf-8 -*-
"""
8数码 A* 求解器

成员A: A*算法框架 + 曼哈顿距离 h1
成员B: 可解性判断 + 多启发式 h2/h3/h4 + IDA* + 对比实验
成员C: GUI 交互界面

使用方式:
    from main import EightPuzzleAStar
    solver = EightPuzzleAStar(start, goal)
    path, expanded = solver.solve()
"""
import heapq
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from src.solvability import is_solvable as _b_is_solvable
from src.heuristic import manhattan, HEURISTICS

from src.solver import idastar as _b_idastar, bfs as _b_bfs
from src.generator import random_state, verify_astar_path


class EightPuzzleAStar:
    """8数码 A* 求解器，支持多种启发式函数."""

    def __init__(self, initial_state, goal_state=(1, 2, 3, 4, 5, 6, 7, 8, 0)):
        self.initial_state = initial_state
        self.goal_state = goal_state
        self.size = 3
        self.goal_positions = {v: i for i, v in enumerate(goal_state)}

    # ── 可解性（委托给成员B的 src/solvability.py）──────────────

    @staticmethod
    def is_solvable(state, goal_state=(1, 2, 3, 4, 5, 6, 7, 8, 0)):
        return _b_is_solvable(state, goal_state)

    # ── 启发式函数 ──────────────────────────────────────────────

    def heuristic(self, state, name='h1'):
        """根据名称获取启发式值. name: 'h1'|'h2'|'h3'|'h4'."""
        fn = HEURISTICS[name][1]
        return fn(state, self.goal_state)

    # ── 移动生成 ────────────────────────────────────────────────

    def _get_neighbors(self, state):
        idx = state.index(0)
        r, c = divmod(idx, 3)
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        result = []
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                lst = list(state)
                ni = nr * 3 + nc
                lst[idx], lst[ni] = lst[ni], lst[idx]
                result.append(tuple(lst))
        return result

    # ── A* 搜索 ─────────────────────────────────────────────────

    def solve(self, heuristic_func=None, heuristic_name=None):
        """
        A* 搜索.
        heuristic_func: 直接传函数，优先级高于 heuristic_name
        heuristic_name:  'h1'|'h2'|'h3'|'h4'
        返回: (path, expanded_nodes)
        """
        if heuristic_func is None:
            if heuristic_name is not None:
                heuristic_func = lambda s: HEURISTICS[heuristic_name][1](s, self.goal_state)
            else:
                heuristic_func = lambda s: manhattan(s, self.goal_state)

        if not _b_is_solvable(self.initial_state, self.goal_state):
            return None, 0

        class _Node:
            __slots__ = ('state', 'parent', 'g', 'h', 'f')
            def __init__(self, state, parent, g, h):
                self.state = state; self.parent = parent
                self.g = g; self.h = h; self.f = g + h
            def __lt__(self, other):
                return self.f < other.f

        open_heap = []
        start_h = heuristic_func(self.initial_state)
        heapq.heappush(open_heap, _Node(self.initial_state, None, 0, start_h))

        closed_set = set()
        g_values = {self.initial_state: 0}
        expanded = 0

        while open_heap:
            current = heapq.heappop(open_heap)

            if current.state in closed_set:
                continue

            closed_set.add(current.state)
            expanded += 1

            if current.state == self.goal_state:
                path = []
                node = current
                while node is not None:
                    path.append(node.state)
                    node = node.parent
                path.reverse()
                return path, expanded

            for nb in self._get_neighbors(current.state):
                ng = current.g + 1
                if ng < g_values.get(nb, float('inf')):
                    g_values[nb] = ng
                    nh = heuristic_func(nb)
                    heapq.heappush(open_heap, _Node(nb, current, ng, nh))
                    if nb in closed_set:
                        closed_set.discard(nb)

        return None, expanded

    # ── IDA* 搜索（成员B）────────────────────────────────────────

    def solve_idastar(self, heuristic_func=None, heuristic_name=None):
        """
        IDA* 搜索（成员B负责）.
        参数同 solve().
        返回: (path_list, expanded_nodes) 或 (None, 0)
        """
        # 统一为 1-arg 函数
        if heuristic_func is not None:
            h_fn = heuristic_func
        elif heuristic_name is not None:
            goal = self.goal_state
            h_fn = lambda s: HEURISTICS[heuristic_name][1](s, goal)
        else:
            goal = self.goal_state
            h_fn = lambda s: manhattan(s, goal)

        if not _b_is_solvable(self.initial_state, self.goal_state):
            return None, 0

        # _b_idastar 调用 fn(state, goal)，适配为 2-arg
        adapter = lambda s, g: h_fn(s)
        path, stats = _b_idastar(self.initial_state, self.goal_state, adapter)
        if path:
            return [s for s, _ in path], stats['expanded']
        return None, 0

    # ── 结果对比（成员B的benchmark简化版）────────────────────────

    @classmethod
    def compare_heuristics(cls, initial_state, goal_state, algo):
        """
        用全部4种启发式求解并返回对比表.
        返回: [(heuristic_name, path_len, expanded_nodes), ...]
        """
        results = []
        for key, (name, _fn) in HEURISTICS.items():
            solver = cls(initial_state, goal_state)
            start = time.perf_counter()
            if algo=="A*":
                path, expanded = solver.solve(heuristic_name=key)
            elif algo=="IDA*":
                path, expanded = solver.solve_idastar(heuristic_name=key)
            elapsed = (time.perf_counter() - start) * 1000
            results.append((algo, name, len(path) - 1 if path else None, expanded, round(elapsed, 2)))
        return results

    # ── 辅助算法（成员C）────────────────────────────────────────

    @staticmethod
    def generate_random(goal_state=None, steps=None, difficulty=None, seed=None):
        """随机生成有解的初始状态（从目标出发随机游走）."""
        return random_state(goal=goal_state, steps=steps, difficulty=difficulty, seed=seed)

    @staticmethod
    def verify_path(initial_state, goal_state, path):
        """BFS 验证 A* 路径是否为最短."""
        return verify_astar_path(initial_state, goal_state, path)

    def bfs_solve(self):
        """BFS 求最短路径，返回 (path_states, expanded)."""
        if not _b_is_solvable(self.initial_state, self.goal_state):
            return None, 0
        path_with_actions, expanded = _b_bfs(self.initial_state, self.goal_state)
        if path_with_actions is None:
            return None, expanded
        return [s for s, _ in path_with_actions], expanded

    # ── 路径打印 ────────────────────────────────────────────────

    @staticmethod
    def print_path(path):
        if not path:
            print("无解或路径为空")
            return
        print(f"找到解，共 {len(path) - 1} 步：")
        for step, state in enumerate(path):
            label = "初始状态：" if step == 0 else f"第 {step} 步："
            print(f"\n{label}")
            for i in range(3):
                row = state[i * 3:(i + 1) * 3]
                print(' '.join(str(x) if x != 0 else '_' for x in row))


# ================================================================
# 命令行测试
# ================================================================
if __name__ == '__main__':
    goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)

    # 简单测试
    print("=== A* 简单测试 ===")
    solver = EightPuzzleAStar((1, 2, 3, 4, 5, 6, 7, 0, 8), goal)
    path, expanded = solver.solve()
    print(f"步数={len(path)-1}, 扩展={expanded}")
    solver.print_path(path)

    # 多启发式对比
    print("\n=== 多启发式对比 ===")
    start = (8, 6, 7, 2, 5, 4, 3, 0, 1)
    for name, steps, exp in EightPuzzleAStar.compare_heuristics(start, goal):
        print(f"  {name}: 步数={steps}, 扩展={exp}")

    # IDA* 对比
    print("\n=== IDA* 测试 ===")
    solver2 = EightPuzzleAStar(start, goal)
    path_i, expanded_i = solver2.solve_idastar()
    print(f"IDA*: 步数={len(path_i)-1 if path_i else 'None'}, 扩展={expanded_i}")

    # 随机生成 + BFS 验证
    print("\n=== 随机生成 + BFS 验证 ===")
    for diff in ("简单", "中等", "困难"):
        rand_start = EightPuzzleAStar.generate_random(goal_state=goal, difficulty=diff)
        solver_r = EightPuzzleAStar(rand_start, goal)
        path_r, exp_r = solver_r.solve()
        verify = EightPuzzleAStar.verify_path(rand_start, goal, path_r)
        print(f"  [{diff}] {rand_start}")
        print(f"    A* 扩展={exp_r}, {verify['message']}")
