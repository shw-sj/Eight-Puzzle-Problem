# Eight Puzzle Problem - A* Search

# 默认目标状态（一维元组，0=空格）
DEFAULT_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)

# 预设目标状态（可扩展）
PRESET_GOALS = {
    "标准": (1, 2, 3, 4, 5, 6, 7, 8, 0),
    "反序": (8, 7, 6, 5, 4, 3, 2, 1, 0),
}


def parse_state(user_input):
    """
    解析用户输入的状态字符串.

    支持格式:
      "1 2 3 4 5 6 7 8 0"  (空格分隔)
      "1,2,3,4,5,6,7,8,0"  (逗号分隔)
      "123456780"           (无分隔，9位数字)

    返回: tuple[int] 长度9，0表示空格.
    异常: ValueError 若输入不合法.
    """
    s = user_input.strip()
    # 去掉可能的逗号，合并空白
    if ',' in s:
        parts = [x.strip() for x in s.split(',')]
    else:
        parts = s.split()
    # 如果拆分后仍不是9个，尝试逐字符解析
    if len(parts) == 1 and len(parts[0]) == 9:
        parts = list(parts[0])
    nums = [int(x) for x in parts]
    if len(nums) != 9:
        raise ValueError(f"需要9个数字，实际得到{len(nums)}个")
    if set(nums) != set(range(9)):
        raise ValueError(f"必须包含0~8各一次，实际: {sorted(nums)}")
    return tuple(nums)


def print_state(state_1d):
    """打印3×3棋盘."""
    for i in range(3):
        row = [str(x) if x != 0 else '_' for x in state_1d[i*3:(i+1)*3]]
        print(' '.join(row))
