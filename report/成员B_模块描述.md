# 成员B 模块描述 — 算法优化与对比实验

## 一、可解性判断（逆序数法）

8数码问题中，并非任意初始状态都能通过合法移动到达目标状态。我在搜索前引入可解性判断，避免算法在无解状态上浪费计算。

实现原理：将3×3棋盘按行展开为一维序列，跳过空格(0)后统计逆序数（对每一对i<j，若a[i]>a[j]则记1）。对于3×3（奇数列）的8数码问题，每次移动空格（上下左右）不会改变逆序数的奇偶性，因此若初始状态与目标状态的逆序数奇偶性不同，则问题无解。函数 is_solvable(start, goal) 返回布尔值，搜索前自动调用，不可解时输出提示并终止。

## 二、多种启发式函数

除曼哈顿距离（h1，由成员A负责）外，我实现了三种启发式函数：

**h2 — 错位棋子数（Misplaced Tiles）：** 统计不在目标位置的棋子个数（不计空格）。每个错位棋子至少需要移动1次才能归位，因此可采纳。计算复杂度O(1)，但精度最低，在困难用例上扩展节点数可达h1的5-7倍。

**h3 — 欧几里得距离（Euclidean Distance）：** 计算每个棋子当前位置到目标位置的直线距离之和。由于欧几里得距离≤曼哈顿距离≤实际步数，该启发式也是可采纳的。精度介于h2和h1之间。

**h4 — 线性冲突（Linear Conflict，加分项）：** 在曼哈顿距离基础上，检测同行/同列中两个数字互相阻挡的线性冲突。例如，若两个棋子在同一行且目标行也相同但左右顺序颠倒，则需要一个棋子"让路"，至少额外消耗2步。每发现一个线性冲突，h值加2。该启发式仍然可采纳，且比曼哈顿距离更精确，在经典最难用例（31步）中，扩展节点数减少约40%。

## 三、算法改进：IDA*

除基础A*外，我实现了IDA*（迭代加深A*）算法。IDA*用递归DFS+深度限制替代OPEN/CLOSED表：每轮迭代以f(n)=g(n)+h(n)的阈值限制搜索深度，超出则剪枝并记录最小超出值作为下一轮阈值。其核心优势是内存占用极低（仅需存储当前搜索路径，O(d)），适合A*因OPEN表过大而内存不足的困难用例。实验表明，在经典最难用例上IDA*与A*的扩展节点数接近（15989 vs 20450），但IDA*无需维护大规模OPEN表，内存优势明显。IDA*的代价是可能重复扩展浅层节点，在部分用例上耗时略高。

## 四、对比实验与结果分析

我设计了8组测试用例（5步到40步随机游走+经典最难31步），对比四种启发式在A*和IDA*下的性能。

主要发现：(1) 启发式精度排序为h4>h1>h3>h2，扩展节点数与此排序一致；(2) h4虽然计算开销更大，但在困难用例上节省的扩展节点带来总耗时优势；(3) h2计算最快但扩展节点数最多，不适合困难用例；(4) IDA*在内存受限时是A*的有效替代方案。

实验结果以表格形式汇总并保存为CSV文件，完整数据见 experiments/results/benchmark_results.csv。


## 附：对外接口说明（供成员A、C调用）

### 数据格式约定

与成员A协商的统一数据格式：棋盘状态用长度为9的一维元组表示，0 代表空格。
例如：`(1, 2, 3, 4, 5, 6, 7, 8, 0)` 表示标准目标状态。

公共常量与工具函数位于 `src/__init__.py`：

```python
from src import DEFAULT_GOAL, PRESET_GOALS, parse_state, print_state

# DEFAULT_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
# PRESET_GOALS = {"标准": (...), "反序": (...)}
# parse_state("1 2 3 4 5 6 7 8 0") -> (1,2,3,4,5,6,7,8,0)
```

### 接口1：可解性判断

```python
from src.solvability import is_solvable, count_inversions

# 判断从 start 到 goal 是否有解
is_solvable(start: tuple, goal: tuple) -> bool

# 单独获取某个状态的逆序数（调试用）
count_inversions(arr_1d: tuple) -> int
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `start` | `tuple[int]`(9) | 初始状态一维元组 |
| `goal` | `tuple[int]`(9) | 目标状态一维元组 |
| 返回值 | `bool` | `True`=有解，`False`=无解 |

**调用示例：**
```python
goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)
start = (1, 2, 3, 4, 5, 6, 7, 0, 8)
if is_solvable(start, goal):
    path, stats = astar(start, goal, manhattan)
else:
    print("该布局无解，请更换初始状态")
```

### 接口2：启发式函数（h2/h3/h4）

```python
from src.heuristic import misplaced_tiles   # h2
from src.heuristic import euclidean          # h3
from src.heuristic import linear_conflict    # h4
from src.heuristic import HEURISTICS         # 注册表字典
```

| 函数签名 | 返回值类型 | 说明 |
|----------|-----------|------|
| `misplaced_tiles(state_1d, goal_1d)` | `int` | h2 错位棋子数 |
| `euclidean(state_1d, goal_1d)` | `float` | h3 欧几里得距离 |
| `linear_conflict(state_1d, goal_1d)` | `int` | h4 曼哈顿+线性冲突 |
| `HEURISTICS['h2']` | `(名称, 函数)` | 注册表，方便下拉选择 |

所有启发式函数签名统一为 `fn(state_1d: tuple, goal_1d: tuple) -> float`，可直接传递给 A* 或 IDA* 求解器。

**调用示例：**
```python
goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)
start = (2, 8, 3, 1, 6, 4, 7, 0, 5)

# 直接调用
h_val = misplaced_tiles(start, goal)

# 或遍历注册表（GUI下拉菜单场景）
for key, (name, fn) in HEURISTICS.items():
    print(f"{key} ({name}) = {fn(start, goal)}")
```

### 接口3：IDA* 求解器

```python
from src.solver import idastar

idastar(start_1d: tuple, goal_1d: tuple, heuristic_fn: callable) -> (path, stats)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `start_1d` | `tuple[int]`(9) | 初始状态 |
| `goal_1d` | `tuple[int]`(9) | 目标状态 |
| `heuristic_fn` | `callable` | 启发式函数，如 `manhattan` |
| 返回值 `path` | `list[tuple]` 或 `None` | `[(state_1d, action), ...]`，首个 action 为 `None` |
| 返回值 `stats` | `dict` | `{'expanded', 'time_ms', 'path_len'}` |

**调用示例：**
```python
from src.solver import idastar
from src.heuristic import linear_conflict

goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)
start = (8, 6, 7, 2, 5, 4, 3, 0, 1)

path, stats = idastar(start, goal, linear_conflict)
if path:
    print(f"找到解，步数={stats['path_len']}，扩展={stats['expanded']}")
    for state, action in path:
        print(f"  {action}: {state}")
```

### 接口4：对比实验（供成员C写入报告）

运行 `python experiments/benchmark.py` 即可生成完整对比表格。
结果自动保存为 CSV：`experiments/results/benchmark_results.csv`。

CSV 字段：`case, difficulty, state, heuristic, algorithm, path_len, expanded, time_ms, status`

成员C可直接引用以下结论：
- 启发式精度排序：h4(线性冲突) > h1(曼哈顿) > h3(欧几里得) > h2(错位数)
- 经典最难用例（31步）：h4 比 h1 扩展节点减少约40%
- IDA* 适合内存受限场景，扩展节点数与 A* 接近
