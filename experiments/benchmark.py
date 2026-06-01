# -*- coding: utf-8 -*-
"""
对比实验脚本 — 成员B负责

测试不同启发式函数(h1/h2/h3/h4)在A*和IDA*下的性能.
输出：控制台表格 + CSV文件 + 可选图表.

用法: python experiments/benchmark.py
"""
import sys
import os
import time
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import DEFAULT_GOAL
from src.heuristic import manhattan, misplaced_tiles, euclidean, linear_conflict, HEURISTICS
from src.solver import astar, idastar, _get_neighbors
from src.solvability import is_solvable
import random

GOAL = DEFAULT_GOAL


def generate_case(steps, seed):
    """从目标状态出发随机游走steps步，保证有解."""
    random.seed(seed)
    state = list(GOAL)
    prev_action = None
    for _ in range(steps):
        neighbors = _get_neighbors(tuple(state))
        # 过滤掉撤销上一步的移动（减少无意义回退）
        if prev_action:
            reverse = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
            neighbors = [(s, a) for s, a in neighbors if a != reverse[prev_action]]
        if not neighbors:
            neighbors = _get_neighbors(tuple(state))
        state_tuple, action = random.choice(neighbors)
        state = list(state_tuple)
        prev_action = action
    return tuple(state)


# ============================================================
# 测试用例（从目标状态出发随机游走生成，保证有解）
# ============================================================
# 不同seed产生不同布局，steps越大通常越难（但不保证最优解长度=steps）

TEST_CASES = [
    # (标签, 初始状态, 难度)
    ("简单-5步",   generate_case(5, seed=10),    "简单"),
    ("简单-8步",   generate_case(8, seed=20),    "简单"),
    ("中等-15步",  generate_case(15, seed=30),   "中等"),
    ("中等-20步",  generate_case(20, seed=40),   "中等"),
    ("困难-25步",  generate_case(25, seed=50),   "困难"),
    ("困难-30步",  generate_case(30, seed=60),   "困难"),
    ("极端-40步",  generate_case(40, seed=70),   "极端"),
    ("经典最难",   (8, 6, 7, 2, 5, 4, 3, 0, 1),  "极端"),  # 需31步
]


def print_table_header():
    print(f"{'测试用例':<14} {'启发式':<12} {'算法':<6} {'路径长度':<8} {'扩展节点':<10} {'耗时(ms)':<10} {'状态':<6}")
    print("-" * 72)


def print_row(case_name, heur_name, algo, path_len, expanded, time_ms, status="OK"):
    print(f"{case_name:<14} {heur_name:<12} {algo:<6} {path_len:<8} {expanded:<10} {time_ms:<10.3f} {status:<6}")


def run_benchmark():
    results = []

    print("=" * 72)
    print("  8数码 A* / IDA* 启发式函数性能对比")
    print("=" * 72)
    print()

    # 先验证可解性
    print(">>> 可解性检查")
    all_ok = True
    for name, state, diff in TEST_CASES:
        ok = is_solvable(state, GOAL)
        flag = "OK" if ok else "FAIL"
        print(f"  {name}: solvable={ok} {flag}")
        if not ok:
            all_ok = False
    if not all_ok:
        print("  [警告] 存在不可解用例，已跳过")
    print()

    # 启发式函数列表（只对比h1~h3，h4用于展示最强效果）
    heuristics_to_test = [
        ('h1-曼哈顿', manhattan),
        ('h2-错位数', misplaced_tiles),
        ('h3-欧几里得', euclidean),
        ('h4-线性冲突', linear_conflict),
    ]

    # ---- A* 对比 ----
    print(">>> A* 搜索 — 不同启发式对比")
    print_table_header()

    for case_name, state, diff in TEST_CASES:
        if not is_solvable(state, GOAL):
            continue
        for heur_name, heur_fn in heuristics_to_test:
            path, stats = astar(state, GOAL, heur_fn)
            status = "OK" if path else "FAIL"
            print_row(case_name, heur_name, "A*",
                      stats['path_len'], stats['expanded'], stats['time_ms'], status)
            results.append({
                'case': case_name, 'difficulty': diff, 'state': str(state),
                'heuristic': heur_name, 'algorithm': 'A*',
                'path_len': stats['path_len'], 'expanded': stats['expanded'],
                'time_ms': stats['time_ms'], 'status': status,
            })

    print()

    # ---- IDA* 对比（仅困难用例，用h1和h4）----
    print(">>> IDA* 搜索（困难用例，h1 vs h4）")
    print_table_header()

    for case_name, state, diff in TEST_CASES:
        if diff not in ("困难", "极端"):
            continue
        if not is_solvable(state, GOAL):
            continue
        for heur_name, heur_fn in [('h1-曼哈顿', manhattan), ('h4-线性冲突', linear_conflict)]:
            path, stats = idastar(state, GOAL, heur_fn)
            status = "OK" if path else "FAIL"
            print_row(case_name, heur_name, "IDA*",
                      stats['path_len'], stats['expanded'], stats['time_ms'], status)
            results.append({
                'case': case_name, 'difficulty': diff, 'state': str(state),
                'heuristic': heur_name, 'algorithm': 'IDA*',
                'path_len': stats['path_len'], 'expanded': stats['expanded'],
                'time_ms': stats['time_ms'], 'status': status,
            })

    print()

    # ---- A* vs IDA* 对比 ----
    print(">>> A* vs IDA* 对比（均用h1曼哈顿）")
    print(f"{'测试用例':<14} {'A*扩展':<10} {'A*耗时':<10} {'IDA*扩展':<10} {'IDA*耗时':<10}")
    print("-" * 58)

    for case_name, state, diff in TEST_CASES:
        if not is_solvable(state, GOAL):
            continue
        pa, sa = astar(state, GOAL, manhattan)
        pi, si = idastar(state, GOAL, manhattan)
        print(f"{case_name:<14} {sa['expanded']:<10} {sa['time_ms']:<10.3f} {si['expanded']:<10} {si['time_ms']:<10.3f}")

    # 保存CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'results', 'benchmark_results.csv')
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n结果已保存至: {csv_path}")

    return results


if __name__ == '__main__':
    run_benchmark()
