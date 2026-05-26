# -*- coding: utf-8 -*-
"""
成员B模块 — 完整调用示例
供成员A（算法核心）和成员C（GUI+报告）参考

运行方式: python demo_B模块调用示例.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from src import DEFAULT_GOAL, PRESET_GOALS, parse_state, print_state
from src.solvability import is_solvable, count_inversions
from src.heuristic import (
    manhattan,          # h1 
    misplaced_tiles,    # h2 — 成员B
    euclidean,          # h3 — 成员B
    linear_conflict,    # h4 — 成员B
    HEURISTICS,         # 注册表: {'h1':('曼哈顿距离',fn), 'h2':..., ...}
)
from src.solver import astar, idastar, bfs


# ================================================================
# 示例1: 用户输入状态 → 可解性判断 → 搜索
# ================================================================
def demo1_完整流程():
    print("=" * 50)
    print("示例1: 用户输入 → 可解性判断 → A*搜索 → 输出路径")
    print("=" * 50)

    # ---- 1a. 解析用户输入 ----
    # 支持三种格式: "1 2 3 4 5 6 7 0 8" / "1,2,3,4,5,6,7,0,8" / "123456708"
    start = parse_state("1 2 3 4 5 6 7 0 8")

    # 目标状态: 用户不选则用默认
    goal = DEFAULT_GOAL  # (1,2,3,4,5,6,7,8,0)

    print("初始状态:")
    print_state(start)
    print("目标状态:")
    print_state(goal)

    # ---- 1b. 可解性判断 (成员B) ----
    if not is_solvable(start, goal):
        print("该布局无解，请更换初始状态！")
        return

    # 也可单独查看逆序数
    print(f"起始逆序数: {count_inversions(start)}, 目标逆序数: {count_inversions(goal)}")

    # ---- 1c. A*搜索 (成员A的astar) ----
    path, stats = astar(start, goal, manhattan)
    if path is None:
        print("搜索失败")
        return

    print(f"\n求解成功! 步数={stats['path_len']}, 扩展节点={stats['expanded']}, 耗时={stats['time_ms']}ms")

    # ---- 1d. 输出路径 (成员C可用于GUI动画) ----
    print("\n移动步骤:")
    for step_num, (state, action) in enumerate(path):
        if action:
            print(f"  Step {step_num}: {action}")
        else:
            print(f"  Step {step_num}: 起点")
        print_state(state)
        print()


# ================================================================
# 示例2: 遍历所有启发式函数 (成员C做下拉菜单时参考)
# ================================================================
def demo2_遍历启发式():
    print("=" * 50)
    print("示例2: 遍历所有启发式函数，对比搜索结果")
    print("=" * 50)

    start = (8, 6, 7, 2, 5, 4, 3, 0, 1)  # 经典最难31步
    goal = DEFAULT_GOAL

    for key, (name, fn) in HEURISTICS.items():
        path, stats = astar(start, goal, fn)
        print(f"  {key} ({name}): 步数={stats['path_len']}, "
              f"扩展={stats['expanded']}, 耗时={stats['time_ms']}ms")


# ================================================================
# 示例3: A* vs IDA* 对比 (成员B的核心贡献)
# ================================================================
def demo3_A星_vs_IDA星():
    print("=" * 50)
    print("示例3: A* vs IDA* 对比")
    print("=" * 50)

    start = (8, 6, 7, 2, 5, 4, 3, 0, 1)  # 经典最难31步
    goal = DEFAULT_GOAL

    if not is_solvable(start, goal):
        print("不可解")
        return

    # A*
    path_a, stats_a = astar(start, goal, manhattan)
    # IDA* (成员B)
    path_i, stats_i = idastar(start, goal, manhattan)

    print(f"  {'':<8} {'步数':<6} {'扩展节点':<10} {'耗时(ms)':<10}")
    print(f"  {'A*':<8} {stats_a['path_len']:<6} {stats_a['expanded']:<10} {stats_a['time_ms']:<10}")
    print(f"  {'IDA*':<8} {stats_i['path_len']:<6} {stats_i['expanded']:<10} {stats_i['time_ms']:<10}")

    # 用线性冲突(h4)再跑IDA*
    path_i4, stats_i4 = idastar(start, goal, linear_conflict)
    print(f"  {'IDA*+h4':<8} {stats_i4['path_len']:<6} {stats_i4['expanded']:<10} {stats_i4['time_ms']:<10}")


# ================================================================
# 示例4: BFS验证 (成员C用于验证A*结果正确性)
# ================================================================
def demo4_BFS验证():
    print("=" * 50)
    print("示例4: BFS验证A*结果 (仅浅层用例)")
    print("=" * 50)

    start = (1, 2, 3, 4, 5, 6, 0, 7, 8)  # 简单用例，2步
    goal = DEFAULT_GOAL

    # A*
    path_a, stats_a = astar(start, goal, manhattan)
    # BFS保证最短
    bfs_path, bfs_expanded = bfs(start, goal)

    bfs_len = len(bfs_path) - 1
    print(f"  A* 步数: {stats_a['path_len']}, 扩展: {stats_a['expanded']}")
    print(f"  BFS 步数: {bfs_len}, 扩展: {bfs_expanded}")
    print(f"  一致: {stats_a['path_len'] == bfs_len}")


# ================================================================
# 示例5: 预设目标状态 + 自定义目标
# ================================================================
def demo5_预设与自定义目标():
    print("=" * 50)
    print("示例5: 预设目标状态 + 自定义目标")
    print("=" * 50)

    start = (1, 2, 3, 4, 5, 6, 7, 0, 8)

    # 方式一: 默认目标
    print(f"默认目标: {DEFAULT_GOAL}")

    # 方式二: 预设目标
    for name, g in PRESET_GOALS.items():
        ok = is_solvable(start, g)
        print(f"  预设'{name}': {g}  可解={ok}")

    # 方式三: 用户自定义目标 (用parse_state解析输入)
    custom_goal = parse_state("8 7 6 5 4 3 2 1 0")
    ok = is_solvable(start, custom_goal)
    print(f"  自定义反序目标: {custom_goal}  可解={ok}")


# ================================================================
# 示例6: 批量运行benchmark (成员C写报告时取数据)
# ================================================================
def demo6_运行Benchmark():
    print("=" * 50)
    print("示例6: 运行完整对比实验")
    print("=" * 50)

    from experiments.benchmark import run_benchmark
    results = run_benchmark()


# ================================================================
# 接口速查表
# ================================================================
def print_api_reference():
    print("""
┌─────────────────────────────────────────────────────────────────┐
│                    成员B 接口速查表                              │
├─────────────────────────────────────────────────────────────────┤
│ 【可解性判断】 src/solvability.py                                │
│   is_solvable(start_tuple, goal_tuple) -> bool                  │
│   count_inversions(state_tuple) -> int                          │
├─────────────────────────────────────────────────────────────────┤
│ 【启发式函数】 src/heuristic.py                                  │
│   misplaced_tiles(state, goal) -> int      # h2 错位数          │
│   euclidean(state, goal) -> float          # h3 欧几里得        │
│   linear_conflict(state, goal) -> int      # h4 线性冲突        │
│   HEURISTICS  # 注册表, 遍历用: {key: (中文名, fn)}             │
│                                                                 │
│   统一签名: fn(state_1d: tuple, goal_1d: tuple) -> float        │
│   可直接传给 astar() 或 idastar()                                │
├─────────────────────────────────────────────────────────────────┤
│ 【IDA* 求解器】 src/solver.py                                    │
│   idastar(start, goal, heuristic_fn) -> (path, stats)           │
│   path: [(state_1d, action), ...], 首个action为None             │
│   stats: {'expanded':int, 'time_ms':float, 'path_len':int}      │
├─────────────────────────────────────────────────────────────────┤
│ 【公共工具】 src/__init__.py                                     │
│   DEFAULT_GOAL          # (1,2,3,4,5,6,7,8,0)                   │
│   PRESET_GOALS          # {"标准":(...), "反序":(...)}           │
│   parse_state("1 2 3 4 5 6 7 0 8") -> tuple                    │
│   print_state(tuple)    # 打印3×3棋盘                            │
├─────────────────────────────────────────────────────────────────┤
│ 【对比实验】 experiments/benchmark.py                            │
│   运行: python experiments/benchmark.py                         │
│   结果: experiments/results/benchmark_results.csv               │
└─────────────────────────────────────────────────────────────────┘
""")


# ================================================================
if __name__ == '__main__':
    demo1_完整流程()
    demo2_遍历启发式()
    demo3_A星_vs_IDA星()
    demo4_BFS验证()
    demo5_预设与自定义目标()
    print_api_reference()

    # demo6 耗时较长，按需取消注释
    # demo6_运行Benchmark()
