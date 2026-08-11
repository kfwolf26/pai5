import tkinter as tk
from tkinter import ttk
import random
from utils.history_manager import HistoryManager

PREDICTOR_NAMES = [
    "神算子", "好运来", "金手指", "财源广", "福星照",
    "财运通", "吉祥星", "如意宝", "聚宝盆", "鸿运达"
]

# 排列5 - 5 个位置键 + Tab 名
# 0=万,1=千,2=百,3=十,4=个
LD_POS_KEYS = ["w", "q", "b", "s", "g"]
LD_POS_TAB_NAMES = {
    "w": "万位定三胆",
    "q": "千位定三胆",
    "b": "百位定三胆",
    "s": "十位定三胆",
    "g": "个位定三胆",
}


class LocationDingDan:
    def __init__(self, parent):
        self.parent = parent
        self.history_manager = HistoryManager()
        self.predictors = {}
        self.canvas_frames = {}
        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 不定位 + 5 个定位 Tab,共 6 个
        tabs = [("unpositioned", "不定位三胆")]
        for pk in LD_POS_KEYS:
            tabs.append((pk, LD_POS_TAB_NAMES[pk]))

        for tab_key, tab_name in tabs:
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=f"  {tab_name}  ")
            self._build_sub_tab(tab_frame, tab_key)

    def _build_sub_tab(self, parent, tab_key):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="统计期数：").pack(side=tk.LEFT, padx=(0, 5))
        period_var = tk.StringVar(value="25")
        ttk.Entry(control_frame, textvariable=period_var, width=8).pack(side=tk.LEFT, padx=(0, 10))

        self.predictors[tab_key] = {
            "period_var": period_var,
            "data": {}
        }

        tk.Button(control_frame, text="  🔄 刷新  ", bg="#5bc0de", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=lambda k=tab_key: self._refresh_tab(k)).pack(side=tk.LEFT, padx=5)

        result_frame = ttk.LabelFrame(parent, text="预测结果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        canvas = tk.Canvas(result_frame, bg="white")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        table_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=table_frame, anchor=tk.NW)

        table_frame.bind("<Configure>", lambda e, c=canvas: self._on_frame_configure(c))

        self.canvas_frames[tab_key] = {
            "canvas": canvas,
            "table_frame": table_frame,
            "labels": []
        }

        self._refresh_tab(tab_key)

    def _on_frame_configure(self, canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _get_next_issue(self):
        history = self.history_manager.get_all()
        if not history:
            return ""
        history.sort(key=lambda x: str(x["issue"]), reverse=True)
        latest_issue = str(history[0]["issue"])
        year = int(latest_issue[:4])
        period_num = int(latest_issue[4:])
        next_period = period_num + 1
        if next_period > 999:
            next_period = 1
            year += 1
        return f"{year}{next_period:03d}"

    def _refresh_tab(self, tab_key):
        history = self.history_manager.get_all()
        if not history:
            self._clear_table(tab_key)
            return

        history.sort(key=lambda x: str(x["issue"]), reverse=False)

        try:
            periods = int(self.predictors[tab_key]["period_var"].get())
        except ValueError:
            periods = 30

        recent_history = history[-periods:] if len(history) > periods else history

        all_data = {}
        for record in recent_history:
            issue = str(record["issue"])
            result_num = record["number"]
            predictors_data = self._generate_predictors_for_period(tab_key, result_num)
            all_data[issue] = {
                "result": result_num,
                "predictors": predictors_data
            }

        next_issue = self._get_next_issue()
        if next_issue:
            all_data[next_issue] = {
                "result": "",
                "predictors": self._generate_predictors_for_period(tab_key, "")
            }

        self.predictors[tab_key]["data"] = all_data
        self._display_results(tab_key)

    def _generate_predictors_for_period(self, tab_key, result_num):
        predictors_data = []
        # 计算目标位索引:不定位=集合判断,定位 Tab=对应位的字符
        if tab_key == "unpositioned":
            target_idx = None  # 集合判断
        elif tab_key in LD_POS_KEYS:
            target_idx = LD_POS_KEYS.index(tab_key)  # 0..4
        else:
            target_idx = None

        for i in range(10):
            name = PREDICTOR_NAMES[i]
            numbers = random.sample(range(10), 3)
            random.shuffle(numbers)

            hit_numbers = []

            if result_num:
                if target_idx is None:
                    # 不定位:5 位开奖号去重为集合,数字命中即标红
                    result_digits = set(result_num)
                    for num in numbers:
                        if str(num) in result_digits:
                            hit_numbers.append(num)
                else:
                    # 定位:对应位的开奖数字
                    if target_idx < len(result_num):
                        target = result_num[target_idx]
                        for num in numbers:
                            if str(num) == target:
                                hit_numbers.append(num)

            predictors_data.append({
                "name": name,
                "numbers": numbers,
                "hit_numbers": hit_numbers
            })

        return predictors_data

    def _display_results(self, tab_key):
        self._clear_table(tab_key)
        table_frame = self.canvas_frames[tab_key]["table_frame"]
        labels = []

        header_font = ("微软雅黑", 9, "bold")
        cell_font = ("微软雅黑", 9)

        row = 0

        ttk.Label(table_frame, text="期号", font=header_font, width=8, anchor=tk.CENTER).grid(row=row, column=0, padx=2, pady=2, sticky="nsew")
        ttk.Label(table_frame, text="开奖号", font=header_font, width=8, anchor=tk.CENTER).grid(row=row, column=1, padx=2, pady=2, sticky="nsew")

        col = 2
        for idx, name in enumerate(PREDICTOR_NAMES):
            ttk.Label(table_frame, text=name, font=header_font, width=15, anchor=tk.CENTER).grid(row=row, column=col, columnspan=3, padx=2, pady=2, sticky="nsew")
            col += 3
            if idx < len(PREDICTOR_NAMES) - 1:
                sep = ttk.Separator(table_frame, orient='vertical')
                sep.grid(row=row, column=col, sticky='ns', padx=1)
                col += 1

        ttk.Label(table_frame, text="统计概况", font=header_font, width=8, anchor=tk.CENTER).grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        row += 1

        data = self.predictors[tab_key]["data"]
        for issue in sorted(data.keys()):
            record = data[issue]
            result_num = record["result"]
            is_next = result_num == ""

            if is_next:
                ttk.Label(table_frame, text=issue, font=("微软雅黑", 9, "bold"), width=8, anchor=tk.CENTER, foreground="#f57c00").grid(row=row, column=0, padx=2, pady=2, sticky="nsew")
                ttk.Label(table_frame, text="待开奖", font=("微软雅黑", 9, "bold"), width=8, anchor=tk.CENTER, foreground="#f57c00").grid(row=row, column=1, padx=2, pady=2, sticky="nsew")
            else:
                ttk.Label(table_frame, text=issue, font=cell_font, width=8, anchor=tk.CENTER).grid(row=row, column=0, padx=2, pady=2, sticky="nsew")
                ttk.Label(table_frame, text=result_num, font=cell_font, width=8, anchor=tk.CENTER, foreground="#1976d2").grid(row=row, column=1, padx=2, pady=2, sticky="nsew")

            col = 2
            total_hits = 0
            for idx, pred in enumerate(record["predictors"]):
                numbers = pred["numbers"]
                hit_numbers = pred["hit_numbers"]

                for num in numbers:
                    if num in hit_numbers:
                        lbl = tk.Label(table_frame, text=str(num), font=cell_font, width=5, anchor=tk.CENTER, foreground="#d32f2f")
                        total_hits += 1
                    else:
                        lbl = tk.Label(table_frame, text=str(num), font=cell_font, width=5, anchor=tk.CENTER, foreground="#333333")
                    lbl.grid(row=row, column=col, padx=1, pady=2, sticky="nsew")
                    labels.append(lbl)
                    col += 1

                if idx < len(record["predictors"]) - 1:
                    sep = ttk.Separator(table_frame, orient='vertical')
                    sep.grid(row=row, column=col, sticky='ns', padx=1)
                    col += 1

            ttk.Label(table_frame, text=str(total_hits), font=cell_font, width=8, anchor=tk.CENTER).grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

            row += 1

        self.canvas_frames[tab_key]["labels"] = labels

        canvas = self.canvas_frames[tab_key]["canvas"]
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _clear_table(self, tab_key):
        table_frame = self.canvas_frames[tab_key]["table_frame"]
        for widget in table_frame.winfo_children():
            widget.destroy()
        self.canvas_frames[tab_key]["labels"] = []