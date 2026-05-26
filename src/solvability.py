"""
可解性判断 — 成员B负责
接口：is_solvable(start, goal) -> bool
输入：start/goal 为一维元组/列表（长度9，0表示空格）
输出：True=有解, False=无解

原理（逆序数法）：
  1. 将棋盘按行展开为一维序列，跳过空格(0)
  2. 统计逆序对数量：对每对 i<j，若 a[i] > a[j] 则记一个逆序
  3. 3×3棋盘（宽度为奇数）：初始与目标逆序数奇偶性相同则有解
     因为每次移动空格不改变逆序数的奇偶性
"""


def count_inversions(arr_1d):
    """计算一维数组的逆序数（跳过空格0）."""
    # 过滤掉空格0，只保留数字1~8
    nums = [x for x in arr_1d if x != 0]
    inversions = 0
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] > nums[j]:
                inversions += 1
    return inversions


def is_solvable(start, goal):
    """
    判断8数码从start到goal是否有解.

    Args:
        start: 一维元组/列表，如 (1,2,3,4,5,6,7,0,8)
        goal:  一维元组/列表，如 (1,2,3,4,5,6,7,8,0)

    Returns:
        bool: True表示有解
    """
    start_parity = count_inversions(start) % 2
    goal_parity = count_inversions(goal) % 2
    return start_parity == goal_parity


# ---------- 测试 ----------
if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src import DEFAULT_GOAL

    goal = DEFAULT_GOAL

    # 可解样例
    solvable_cases = [
        (1, 2, 3, 4, 5, 6, 7, 0, 8),   # 空格左移1步，逆序数=0
        (1, 2, 3, 4, 5, 6, 0, 7, 8),   # 空格左移2步，逆序数=0
        (8, 1, 3, 4, 0, 2, 7, 6, 5),   # 随机可解布局
    ]

    # 不可解样例：交换两个相邻数字改变奇偶性
    unsolvable_cases = [
        (2, 1, 3, 4, 5, 6, 7, 8, 0),   # 仅交换1和2，逆序数=1（奇数）
    ]

    print("=== 可解性测试 ===")
    for case in solvable_cases:
        result = is_solvable(case, goal)
        print(f"{case} -> {'有解' if result else '无解'} (预期: 有解)")

    for case in unsolvable_cases:
        result = is_solvable(case, goal)
        print(f"{case} -> {'有解' if result else '无解'} (预期: 无解)")
