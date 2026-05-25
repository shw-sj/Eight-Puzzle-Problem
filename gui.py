import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from main import EightPuzzleAStar

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
EXAMPLE_INITIAL = (2, 8, 3, 1, 6, 4, 5, 0, 7)


class PuzzleBoard(tk.Frame):
    """3x3 棋盘展示组件"""

    TILE_SIZE = 72
    GAP = 4

    def __init__(self, master, title="", editable=False, **kwargs):
        super().__init__(master, **kwargs)
        self.editable = editable
        self.entries = []

        if title:
            tk.Label(self, text=title, font=("Microsoft YaHei UI", 10, "bold")).pack(pady=(0, 6))

        grid = tk.Frame(self)
        grid.pack()

        for row in range(3):
            row_entries = []
            for col in range(3):
                if editable:
                    var = tk.StringVar(value="")
                    entry = tk.Entry(
                        grid,
                        textvariable=var,
                        width=3,
                        font=("Consolas", 16),
                        justify="center",
                    )
                    entry.grid(row=row, column=col, padx=2, pady=2)
                    row_entries.append(var)
                else:
                    lbl = tk.Label(
                        grid,
                        text="",
                        width=4,
                        height=2,
                        font=("Consolas", 18, "bold"),
                        relief="raised",
                        bg="#e8e8e8",
                    )
                    lbl.grid(row=row, column=col, padx=self.GAP, pady=self.GAP)
                    row_entries.append(lbl)
            self.entries.append(row_entries)

    def set_state(self, state):
        for i, value in enumerate(state):
            row, col = divmod(i, 3)
            cell = self.entries[row][col]
            text = "" if value == 0 else str(value)
            if self.editable:
                cell.set(text)
            else:
                cell.config(
                    text=text,
                    bg="#ffffff" if value != 0 else "#c8e6c9",
                    fg="#333333",
                )

    def get_state(self):
        values = []
        for row in range(3):
            for col in range(3):
                raw = self.entries[row][col].get().strip()
                if raw == "":
                    values.append(0)
                else:
                    try:
                        values.append(int(raw))
                    except ValueError:
                        raise ValueError(f"无效数字: {raw!r}")
        return tuple(values)

    @staticmethod
    def validate_state(state, label):
        if len(state) != 9:
            raise ValueError(f"{label}必须包含 9 个格子")
        nums = [x for x in state if x != 0]
        if sorted(nums) != list(range(1, 9)):
            raise ValueError(f"{label}必须包含数字 1-8 各一次，0 表示空白")
        if state.count(0) != 1:
            raise ValueError(f"{label}必须有且仅有一个空白格 (0)")


class EightPuzzleGUI(tk.Tk):
  ANIMATION_MS = 600

  def __init__(self):
    super().__init__()
    self.title("8 数码问题 — A* 求解器")
    self.geometry("820x680")
    self.minsize(760, 620)
    self.configure(bg="#f5f5f5")

    self.path = []
    self.current_step = 0
    self.animation_job = None
    self.is_playing = False
    self.solve_thread = None

    self._build_ui()
    self._load_defaults()

  def _build_ui(self):
    header = tk.Label(
      self,
      text="8 数码问题 A* 求解器（曼哈顿距离启发式）",
      font=("Microsoft YaHei UI", 14, "bold"),
      bg="#f5f5f5",
      fg="#1565c0",
    )
    header.pack(pady=(14, 8))

    input_frame = tk.LabelFrame(
      self, text="状态输入", font=("Microsoft YaHei UI", 10), padx=12, pady=10
    )
    input_frame.pack(fill="x", padx=16, pady=6)

    boards_row = tk.Frame(input_frame)
    boards_row.pack()

    self.initial_board = PuzzleBoard(boards_row, title="初始状态", editable=True)
    self.initial_board.pack(side="left", padx=24)

    tk.Label(boards_row, text="→", font=("Consolas", 24), fg="#666").pack(side="left")

    self.goal_board = PuzzleBoard(boards_row, title="目标状态", editable=True)
    self.goal_board.pack(side="left", padx=24)

    hint = tk.Label(
      input_frame,
      text="提示：每格输入 0-8，0 表示空白；须包含 1-8 各一次",
      font=("Microsoft YaHei UI", 9),
      fg="#666",
    )
    hint.pack(pady=(8, 0))

    btn_row = tk.Frame(self, bg="#f5f5f5")
    btn_row.pack(pady=8)

    self.solve_btn = tk.Button(
      btn_row,
      text="开始求解",
      font=("Microsoft YaHei UI", 10),
      width=10,
      command=self._on_solve,
      bg="#1565c0",
      fg="white",
      activebackground="#0d47a1",
      activeforeground="white",
      relief="flat",
      padx=8,
      pady=4,
    )
    self.solve_btn.pack(side="left", padx=6)

    tk.Button(
      btn_row,
      text="重置默认",
      font=("Microsoft YaHei UI", 10),
      width=10,
      command=self._load_defaults,
      padx=8,
      pady=4,
    ).pack(side="left", padx=6)

    tk.Button(
      btn_row,
      text="加载示例",
      font=("Microsoft YaHei UI", 10),
      width=10,
      command=self._load_example,
      padx=8,
      pady=4,
    ).pack(side="left", padx=6)

    anim_frame = tk.LabelFrame(
      self, text="求解过程", font=("Microsoft YaHei UI", 10), padx=12, pady=10
    )
    anim_frame.pack(fill="both", expand=True, padx=16, pady=6)

    ctrl_row = tk.Frame(anim_frame)
    ctrl_row.pack(pady=(0, 8))

    self.prev_btn = tk.Button(
      ctrl_row, text="◀ 上一步", command=self._prev_step, state="disabled", width=10
    )
    self.prev_btn.pack(side="left", padx=4)

    self.play_btn = tk.Button(
      ctrl_row, text="▶ 播放", command=self._toggle_play, state="disabled", width=10
    )
    self.play_btn.pack(side="left", padx=4)

    self.next_btn = tk.Button(
      ctrl_row, text="下一步 ▶", command=self._next_step, state="disabled", width=10
    )
    self.next_btn.pack(side="left", padx=4)

    self.step_label = tk.Label(
      anim_frame, text="步骤：— / —", font=("Microsoft YaHei UI", 10)
    )
    self.step_label.pack()

    self.display_board = PuzzleBoard(anim_frame, editable=False)
    self.display_board.pack(pady=10)

    speed_row = tk.Frame(anim_frame)
    speed_row.pack(pady=4)
    tk.Label(speed_row, text="播放速度：", font=("Microsoft YaHei UI", 9)).pack(side="left")
    self.speed_var = tk.DoubleVar(value=600)
    speed_scale = ttk.Scale(
      speed_row,
      from_=200,
      to=1500,
      orient="horizontal",
      variable=self.speed_var,
      length=200,
    )
    speed_scale.pack(side="left", padx=6)
    tk.Label(speed_row, text="慢 ← → 快", font=("Microsoft YaHei UI", 9), fg="#666").pack(
      side="left"
    )

    result_frame = tk.LabelFrame(
      self, text="搜索结果", font=("Microsoft YaHei UI", 10), padx=12, pady=10
    )
    result_frame.pack(fill="x", padx=16, pady=(6, 14))

    self.status_label = tk.Label(
      result_frame,
      text="状态：等待求解",
      font=("Microsoft YaHei UI", 10),
      anchor="w",
    )
    self.status_label.pack(fill="x")

    stats_row = tk.Frame(result_frame)
    stats_row.pack(fill="x", pady=(6, 0))

    self.steps_var = tk.StringVar(value="—")
    self.expanded_var = tk.StringVar(value="—")
    self.time_var = tk.StringVar(value="—")

    for label, var in [
      ("总步数", self.steps_var),
      ("扩展节点数", self.expanded_var),
      ("耗时 (秒)", self.time_var),
    ]:
      box = tk.Frame(stats_row, padx=16)
      box.pack(side="left")
      tk.Label(box, text=label, font=("Microsoft YaHei UI", 9), fg="#666").pack()
      tk.Label(box, textvariable=var, font=("Consolas", 14, "bold"), fg="#1565c0").pack()

  def _load_defaults(self):
    self.initial_board.set_state(DEFAULT_GOAL)
    self.goal_board.set_state(DEFAULT_GOAL)
    self.display_board.set_state(DEFAULT_GOAL)
    self._reset_results()
    self.status_label.config(text="状态：已加载默认状态（初始=目标，0 步）")

  def _load_example(self):
    self.initial_board.set_state(EXAMPLE_INITIAL)
    self.goal_board.set_state(DEFAULT_GOAL)
    self.display_board.set_state(EXAMPLE_INITIAL)
    self._reset_results()
    self.status_label.config(text="状态：已加载示例，点击「开始求解」")

  def _reset_results(self):
    self._stop_animation()
    self.path = []
    self.current_step = 0
    self.steps_var.set("—")
    self.expanded_var.set("—")
    self.time_var.set("—")
    self.step_label.config(text="步骤：— / —")
    for btn in (self.prev_btn, self.play_btn, self.next_btn):
      btn.config(state="disabled")

  def _parse_inputs(self):
    try:
      initial = self.initial_board.get_state()
      goal = self.goal_board.get_state()
      PuzzleBoard.validate_state(initial, "初始状态")
      PuzzleBoard.validate_state(goal, "目标状态")
      return initial, goal
    except ValueError as exc:
      messagebox.showerror("输入错误", str(exc))
      return None, None

  def _on_solve(self):
    if self.solve_thread and self.solve_thread.is_alive():
      return

    initial, goal = self._parse_inputs()
    if initial is None:
      return

    if initial == goal:
      self.path = [initial]
      self._show_solution(initial, goal, expanded=0, elapsed=0.0)
      self.status_label.config(text="状态：初始状态与目标状态相同，无需移动")
      return

    if not EightPuzzleAStar.is_solvable(initial, goal):
      self._reset_results()
      self.display_board.set_state(initial)
      self.status_label.config(text="状态：无解（初始与目标奇偶性不同）", fg="#c62828")
      messagebox.showwarning("无解", "该初始状态无法到达目标状态！\n（逆序数奇偶性不一致）")
      return

    self._reset_results()
    self.solve_btn.config(state="disabled")
    self.status_label.config(text="状态：正在搜索…", fg="#333")

    def worker():
      start = time.perf_counter()
      solver = EightPuzzleAStar(initial, goal)
      path, expanded = solver.solve()
      elapsed = time.perf_counter() - start
      self.after(0, lambda: self._on_solve_done(path, expanded, elapsed, initial, goal))

    self.solve_thread = threading.Thread(target=worker, daemon=True)
    self.solve_thread.start()

  def _on_solve_done(self, path, expanded, elapsed, initial, goal):
    self.solve_btn.config(state="normal")

    if path is None:
      self.display_board.set_state(initial)
      self.status_label.config(text="状态：搜索失败（未找到路径）", fg="#c62828")
      self.expanded_var.set(str(expanded))
      self.time_var.set(f"{elapsed:.4f}")
      return

    self.path = path
    self.current_step = 0
    self._update_display()
    self._show_solution(initial, goal, expanded, elapsed)

    for btn in (self.prev_btn, self.play_btn, self.next_btn):
      btn.config(state="normal")

  def _show_solution(self, initial, goal, expanded, elapsed):
    steps = len(self.path) - 1 if self.path else 0
    self.steps_var.set(str(steps))
    self.expanded_var.set(str(expanded))
    self.time_var.set(f"{elapsed:.4f}")
    self.status_label.config(
      text=f"状态：求解完成！共 {steps} 步，扩展 {expanded} 个节点，耗时 {elapsed:.4f} 秒",
      fg="#2e7d32",
    )

  def _update_display(self):
    if not self.path:
      return
    self.display_board.set_state(self.path[self.current_step])
    total = len(self.path) - 1
    self.step_label.config(text=f"步骤：{self.current_step} / {total}")

  def _prev_step(self):
    if self.current_step > 0:
      self._stop_animation()
      self.current_step -= 1
      self._update_display()

  def _next_step(self):
    if self.path and self.current_step < len(self.path) - 1:
      self.current_step += 1
      self._update_display()
      if self.current_step >= len(self.path) - 1:
        self._stop_animation()

  def _toggle_play(self):
    if self.is_playing:
      self._stop_animation()
    else:
      self.is_playing = True
      self.play_btn.config(text="⏸ 暂停")
      self._schedule_next()

  def _stop_animation(self):
    self.is_playing = False
    self.play_btn.config(text="▶ 播放")
    if self.animation_job is not None:
      self.after_cancel(self.animation_job)
      self.animation_job = None

  def _schedule_next(self):
    if not self.is_playing or not self.path:
      return
    if self.current_step >= len(self.path) - 1:
      self._stop_animation()
      return
    delay = int(self.speed_var.get())
    self.animation_job = self.after(delay, self._animation_tick)

  def _animation_tick(self):
    if not self.is_playing:
      return
    self._next_step()
    self._schedule_next()


def main():
  app = EightPuzzleGUI()
  app.mainloop()


if __name__ == "__main__":
  main()
