import heapq
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

class EightPuzzleAStar:
    """8数码A*求解器，使用曼哈顿距离启发式"""
    def __init__(self, initial_state, goal_state=(1, 2, 3, 4, 5, 6, 7, 8, 0)):
        """
        初始化求解器
        :param initial_state: 初始状态元组，长度9，0表示空白
        :param goal_state: 目标状态，默认(1,2,3,4,5,6,7,8,0)
        """
        self.initial_state = initial_state
        self.goal_state = goal_state
        self.size = 3  # 3x3棋盘
        # 预计算每个数字在目标状态中的位置，用于快速曼哈顿距离
        self.goal_positions = {value: idx for idx, value in enumerate(goal_state)}

    @staticmethod
    def _inversion_count(state):
        """计算状态中（不含空白）的逆序数"""
        arr = [x for x in state if x != 0]
        inversions = 0
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                if arr[i] > arr[j]:
                    inversions += 1
        return inversions

    @staticmethod
    def _blank_row_from_bottom(state, size=3):
        """空白格所在行，从下往上数（1-based）"""
        blank_idx = state.index(0)
        row_from_top = blank_idx // size
        return size - row_from_top

    @classmethod
    def is_solvable(cls, state, goal_state=(1, 2, 3, 4, 5, 6, 7, 8, 0)):
        """
        判断初始状态能否到达目标状态（逆序数 + 空白行奇偶性）
        """
        size = 3
        parity = (
            cls._inversion_count(state) + cls._blank_row_from_bottom(state, size)
        ) % 2
        goal_parity = (
            cls._inversion_count(goal_state) + cls._blank_row_from_bottom(goal_state, size)
        ) % 2
        return parity == goal_parity

    def find_blank(self, state):
        """返回空白格(0)的索引"""
        return state.index(0)

    def is_valid_move(self, blank_idx, direction):
        """判断移动是否合法，合法返回移动后空白格的新索引，否则返回None"""
        row = blank_idx // self.size
        col = blank_idx % self.size
        if direction == 'up' and row > 0:
            return (row - 1) * self.size + col
        if direction == 'down' and row < self.size - 1:
            return (row + 1) * self.size + col
        if direction == 'left' and col > 0:
            return row * self.size + (col - 1)
        if direction == 'right' and col < self.size - 1:
            return row * self.size + (col + 1)
        return None

    def get_neighbors(self, state):
        """生成当前状态的所有合法邻居状态（一维元组）"""
        neighbors = []
        blank_idx = self.find_blank(state)
        for direction in ('up', 'down', 'left', 'right'):
            new_blank_idx = self.is_valid_move(blank_idx, direction)
            if new_blank_idx is not None:
                lst = list(state)
                lst[blank_idx], lst[new_blank_idx] = lst[new_blank_idx], lst[blank_idx]
                neighbors.append(tuple(lst))
        return neighbors

    def manhattan_distance(self, state):
        """
        曼哈顿距离启发式函数 h(n)
        计算每个非空白棋子到目标位置的曼哈顿距离之和
        """

        dist = 0
        for pos, value in enumerate(state):
            if value == 0:
                continue
            goal_pos = self.goal_positions[value]
            cur_row, cur_col = divmod(pos, self.size)
            goal_row, goal_col = divmod(goal_pos, self.size)
            dist += abs(cur_row - goal_row) + abs(cur_col - goal_col)
        return dist

    def solve(self, heuristic_func=None):
        """
        A*算法求解主函数
        :param heuristic_func: 启发式函数，默认使用曼哈顿距离
        :return: (path, expanded_nodes)   path为从初始到目标的路径（状态列表），若无解则返回(None, 0)
        """
        
        if heuristic_func is None:
            heuristic_func = self.manhattan_distance

        if not self.is_solvable(self.initial_state, self.goal_state):
            return None, 0

        # 定义节点类（使用__slots__节省内存）
        class Node:
            __slots__ = ('state', 'parent', 'g', 'h', 'f')
            def __init__(self, state, parent, g, h):
                self.state = state
                self.parent = parent
                self.g = g
                self.h = h
                self.f = g + h
            def __lt__(self, other):
                return self.f < other.f

        open_heap = []
        start_h = heuristic_func(self.initial_state)
        start_node = Node(self.initial_state, None, 0, start_h)
        heapq.heappush(open_heap, start_node)

        closed_set = set()          # 存储已扩展的状态
        g_values = {self.initial_state: 0}   # 记录每个状态的最优g值
        expanded_nodes = 0

        while open_heap:
            current = heapq.heappop(open_heap)

            # 如果当前状态已经在closed表中，说明被重新开放过，跳过
            if current.state in closed_set:
                continue

            # 扩展当前节点
            closed_set.add(current.state)
            expanded_nodes += 1

            # 到达目标状态，回溯路径
            if current.state == self.goal_state:
                path = []
                node = current
                while node is not None:
                    path.append(node.state)
                    node = node.parent
                path.reverse()
                return path, expanded_nodes

            # 生成邻居并加入开放集
            for neighbor_state in self.get_neighbors(current.state):
                neighbor_g = current.g + 1

                # 如果新g值更小，或者该状态从未出现过
                if neighbor_g < g_values.get(neighbor_state, float('inf')):
                    g_values[neighbor_state] = neighbor_g
                    neighbor_h = heuristic_func(neighbor_state)
                    neighbor_node = Node(neighbor_state, current, neighbor_g, neighbor_h)
                    heapq.heappush(open_heap, neighbor_node)
                    # 如果该状态之前已在closed_set中，需要重新开放（移除出closed_set）
                    if neighbor_state in closed_set:
                        closed_set.remove(neighbor_state)

        # 开放集耗尽仍未找到解（理论上可解的题目一定会找到，但以防万一）
        return None, expanded_nodes

    @staticmethod
    def print_path(path):
        """打印路径，每步显示3x3棋盘"""
        if not path:
            print("无解或路径为空")
            return
        total_steps = len(path) - 1
        print(f"找到解，共 {total_steps} 步：")
        for step, state in enumerate(path):
            print(f"\n第 {step} 步：" if step > 0 else "\n初始状态：")
            for i in range(3):
                row = state[i*3:(i+1)*3]
                print(' '.join(str(x) for x in row))


# 测试代码
# if __name__ == "__main__":
#     # 测试用例1：简单（1步）
#     init1 = (1, 2, 3, 4, 5, 6, 7, 0, 8)
#     solver1 = EightPuzzleAStar(init1)
#     path1, expanded1 = solver1.solve()
#     solver1.print_path(path1)
#     print(f"扩展节点数：{expanded1}")

#     print("\n" + "="*50 + "\n")

#     # 测试用例2：中等难度
#     init2 = (2, 8, 3, 1, 6, 4, 5, 0, 7)
#     solver2 = EightPuzzleAStar(init2)
#     path2, expanded2 = solver2.solve()
#     solver2.print_path(path2)
#     print(f"扩展节点数：{expanded2}")

#     # 测试用例3：无解状态
#     init3 = (1, 2, 3, 4, 5, 6, 8, 7, 0)  # 交换7和8，逆序数为奇数，无解
#     solver3 = EightPuzzleAStar(init3)
#     path3, expanded3 = solver3.solve()
#     if path3 is None:
#         print("测试3：无解，返回正确")