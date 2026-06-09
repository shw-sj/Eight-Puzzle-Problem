"""
搜索求解器 — 成员A负责A*, 成员B负责IDA*

接口约定（与成员A协商）：
  astar(start_1d, goal_1d, heuristic_fn) -> (path, stats)
  idastar(start_1d, goal_1d, heuristic_fn) -> (path, stats)

  输入/输出:
    start_1d: 长度为9的一维元组，0=空格
    goal_1d:  同上
    heuristic_fn: fn(state_1d, goal_1d) -> float
    path: [(state_1d, action), ...]，首个元素action为None（起点）
    stats: {'expanded': int, 'time_ms': float, 'path_len': int}
"""
import heapq
import math
import time
from collections import deque

# ---- 移动生成 ----

def _get_neighbors(state_1d):
    """生成空格上下左右移动后的合法后继."""
    idx = state_1d.index(0)
    r, c = idx // 3, idx % 3
    moves = [(-1, 0, 'up'), (1, 0, 'down'), (0, -1, 'left'), (0, 1, 'right')]
    result = []
    for dr, dc, action in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            lst = list(state_1d)
            ni = nr * 3 + nc
            lst[idx], lst[ni] = lst[ni], lst[idx]
            result.append((tuple(lst), action))
    return result


def _reconstruct(parent_map, end_state):
    """从parent_map回溯路径."""
    path = []
    s = end_state
    while s is not None:
        parent, action = parent_map[s]
        path.append((s, action))
        s = parent
    path.reverse()
    return path


# ============================================================
# A* 搜索 (成员A负责基础实现)
# ============================================================

def astar(start_1d, goal_1d, heuristic_fn):
    """
    A*搜索算法.
    OPEN表: 小顶堆 (heapq), 按 f = g + h 排序
    CLOSED表: set, 存储已扩展的state
    parent_map: {state: (parent_state, action)} 用于路径回溯
    """
    start_h = heuristic_fn(start_1d, goal_1d)

    counter = 0
    open_heap = [(start_h, counter, 0, start_1d)]  # (f, id, g, state)
    counter += 1

    open_g = {start_1d: 0}           # 记录OPEN中每个state的最优g
    parent_map = {start_1d: (None, None)}  # {state: (parent, action)}
    closed = set()

    expanded = 0
    max_open = 1
    start_time = time.perf_counter()

    while open_heap:
        f_val, _, g, current = heapq.heappop(open_heap)
        max_open = max(max_open, len(open_heap))

        # 懒删除: 若当前g不是最优则跳过
        if open_g.get(current, float('inf')) < g:
            continue

        if current == goal_1d:
            elapsed = (time.perf_counter() - start_time) * 1000
            path = _reconstruct(parent_map, current)
            return path, {
                'expanded': expanded,
                'time_ms': round(elapsed, 3),
                'path_len': len(path) - 1,
            }

        closed.add(current)
        open_g.pop(current, None)
        expanded += 1

        for nb, action in _get_neighbors(current):
            if nb in closed:
                continue
            new_g = g + 1
            if nb in open_g and open_g[nb] <= new_g:
                continue
            new_h = heuristic_fn(nb, goal_1d)
            open_g[nb] = new_g
            parent_map[nb] = (current, action)
            heapq.heappush(open_heap, (new_g + new_h, counter, new_g, nb))
            counter += 1

    return None, {
        'expanded': expanded,
        'time_ms': round((time.perf_counter() - start_time) * 1000, 3),
        'path_len': 0,
    }


# ============================================================
# IDA* 迭代加深A* (成员B负责)
# ============================================================

def idastar(start_1d, goal_1d, heuristic_fn):
    """
    IDA* 算法 — 用深度限制替代OPEN/CLOSED表.

    每轮迭代以 threshold 为 f 值的上限做DFS:
      f(n) = g(n) + h(n) <= threshold 则深入
      否则剪枝并记录最小超出值作为下一轮的 threshold

    优势:
      - 内存 O(depth)，只需存储当前搜索路径
      - 适合状态空间大、A*内存不足的困难用例
    劣势:
      - 可能重复扩展浅层节点
    """
    threshold = heuristic_fn(start_1d, goal_1d)
    expanded = [0]  # 用列表包装以便在嵌套函数中修改
    start_time = time.perf_counter()

    def dfs(state_1d, g, limit, visited, parent_chain):
        """DFS搜索，返回 (next_limit, found_flag, result)."""
        f = g + heuristic_fn(state_1d, goal_1d)
        if f > limit:
            return f, False

        if state_1d == goal_1d:
            return -1, True

        expanded[0] += 1
        min_bound = float('inf')

        # 按启发式值排序，优先后继（优化扩展顺序）
        neighbors = _get_neighbors(state_1d)
        neighbors.sort(key=lambda x: heuristic_fn(x[0], goal_1d))

        for nb, action in neighbors:
            if nb in visited:
                continue
            visited.add(nb)
            parent_chain.append((nb, action))
            t, found = dfs(nb, g + 1, limit, visited, parent_chain)
            if found:
                return t, True
            parent_chain.pop()
            visited.discard(nb)
            if t < min_bound:
                min_bound = t
        return min_bound, False

    path_chain = [(start_1d, None)]  # 存储当前搜索路径

    while True:
        visited = {start_1d}
        t, found = dfs(start_1d, 0, threshold, visited, path_chain)
        if found:
            elapsed = (time.perf_counter() - start_time) * 1000
            # path_chain中已有完整路径
            return list(path_chain), {
                'expanded': expanded[0],
                'time_ms': round(elapsed, 3),
                'path_len': len(path_chain) - 1,
            }
        if t == float('inf'):
            return None, {
                'expanded': expanded[0],
                'time_ms': round((time.perf_counter() - start_time) * 1000, 3),
                'path_len': 0,
            }
        threshold = math.ceil(t)


# ============================================================
# BFS 验证器
# ============================================================

def bfs(start_1d, goal_1d):
    """
    广度优先搜索 — 保证最短路径，用于验证A*结果正确性.
    仅适用于浅层用例 (深度<15), 深层会指数爆炸.
    """
    queue = deque([start_1d])
    parent_map = {start_1d: (None, None)}
    expanded = 0

    while queue:
        current = queue.popleft()
        expanded += 1

        if current == goal_1d:
            path = _reconstruct(parent_map, current)
            return path, expanded

        for nb, action in _get_neighbors(current):
            if nb not in parent_map:
                parent_map[nb] = (current, action)
                queue.append(nb)

    return None, expanded


# ---------- 测试 ----------
if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src import DEFAULT_GOAL
    from src.heuristic import manhattan

    goal = DEFAULT_GOAL
    start = (1, 2, 3, 4, 5, 6, 7, 0, 8)

    print("=== A* ===")
    path, stats = astar(start, goal, manhattan)
    print(f"路径长度: {stats['path_len']}, 扩展: {stats['expanded']}, 耗时: {stats['time_ms']}ms")
    for s, a in path:
        print(f"  {a}: {s}")

    print("\n=== IDA* ===")
    path2, stats2 = idastar(start, goal, manhattan)
    print(f"路径长度: {stats2['path_len']}, 扩展: {stats2['expanded']}, 耗时: {stats2['time_ms']}ms")
