import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.messagebox import showwarning, showinfo
import itertools


class FilterTool:
    def __init__(self, parent):
        self.parent = parent
        self.filter_vars = self._init_filter_vars()

        main_pane = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_pane, width=600)
        main_pane.add(left_frame, weight=1)
        left_canvas = tk.Canvas(left_frame, bg="white")
        left_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=left_canvas.yview)
        self.filter_content = tk.Frame(left_canvas, bg="white")
        self.filter_content.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.create_window((0, 0), window=self.filter_content, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        right_frame = ttk.Frame(main_pane, width=600)
        main_pane.add(right_frame, weight=1)
        ttk.Label(right_frame, text="过滤结果", font=("Arial", 12, "bold")).pack(pady=5)
        self.result_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=("Arial", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=8, pady=8)
        self.start_btn = tk.Button(btn_frame, text="  🚀 开始过滤  ", bg="#5cb85c", fg="white",
                                   relief=tk.RAISED, padx=5, pady=4, font=("微软雅黑", 9, "bold"),
                                   command=self.start_filter)
        self.start_btn.pack(side=tk.LEFT, padx=6)
        self.clear_btn = tk.Button(btn_frame, text="  🗑 清空条件  ", bg="#f0ad4e", fg="white",
                                   relief=tk.RAISED, padx=5, pady=4, font=("微软雅黑", 9),
                                   command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=6)
        self.help_btn = tk.Button(btn_frame, text="  💡 使用说明  ", bg="#5bc0de", fg="white",
                                   relief=tk.RAISED, padx=5, pady=4, font=("微软雅黑", 9),
                                   command=self.show_help)
        self.help_btn.pack(side=tk.RIGHT, padx=6)

        self.radio_zhixuan_baoz = None
        self.radio_zhixuan_zusan = None
        self.radio_zhixuan_zuliu = None
        self.radio_zuxuan_zusan = None
        self.radio_zuxuan_zuliu = None

        self.direct_pos_text = None
        self.non_pos_direct_text = None
        self._build_filter_ui()

    def _init_filter_vars(self):
        vars_dict = {}

        vars_dict["pos"] = {
            "b": [tk.BooleanVar() for _ in range(10)],
            "s": [tk.BooleanVar() for _ in range(10)],
            "g": [tk.BooleanVar() for _ in range(10)]
        }

        vars_dict["direct_pos_mode"] = tk.IntVar(value=1)

        vars_dict["non_pos_direct_mode"] = tk.IntVar(value=1)

        vars_dict["kill"] = {
            "b": [tk.BooleanVar() for _ in range(10)],
            "s": [tk.BooleanVar() for _ in range(10)],
            "g": [tk.BooleanVar() for _ in range(10)]
        }

        vars_dict["dan"] = {
            "b": [tk.BooleanVar() for _ in range(10)],
            "s": [tk.BooleanVar() for _ in range(10)],
            "g": [tk.BooleanVar() for _ in range(10)]
        }

        vars_dict["two_sum_mode"] = tk.IntVar(value=1)
        vars_dict["two_sum"] = [tk.BooleanVar() for _ in range(19)]

        vars_dict["two_diff_mode"] = tk.IntVar(value=1)
        vars_dict["two_diff"] = [tk.BooleanVar() for _ in range(10)]

        vars_dict["two_code_mode"] = tk.IntVar(value=1)
        two_codes = [f"{i:02d}" for i in range(100)]
        unique_codes = sorted(list({''.join(sorted(c)) for c in two_codes}))
        vars_dict["two_code_list"] = unique_codes
        vars_dict["two_code"] = [tk.BooleanVar() for _ in range(len(unique_codes))]

        vars_dict["o12_mode"] = tk.IntVar(value=1)
        o12_types = [f"{a}{b}{c}" for a in range(3) for b in range(3) for c in range(3)]
        vars_dict["o12_list"] = o12_types
        vars_dict["o12"] = [tk.BooleanVar() for _ in range(len(o12_types))]

        vars_dict["sum_mode"] = tk.IntVar(value=1)
        vars_dict["sum_val"] = [tk.BooleanVar() for _ in range(28)]

        vars_dict["sum_tail_mode"] = tk.IntVar(value=1)
        vars_dict["sum_tail"] = [tk.BooleanVar() for _ in range(10)]

        vars_dict["span_mode"] = tk.IntVar(value=1)
        vars_dict["span"] = [tk.BooleanVar() for _ in range(10)]

        vars_dict["sms_mode"] = tk.IntVar(value=1)
        sms_types = self._generate_sms_types()
        vars_dict["sms_list"] = sms_types
        vars_dict["sms"] = [tk.BooleanVar() for _ in range(len(sms_types))]

        vars_dict["size_mode"] = tk.IntVar(value=1)
        size_types = ["大大大", "大大小", "大小大", "小大大", "小小小", "小小大", "小大小", "大小小"]
        vars_dict["size_list"] = size_types
        vars_dict["size"] = [tk.BooleanVar() for _ in range(len(size_types))]

        vars_dict["oe_mode"] = tk.IntVar(value=1)
        oe_types = ["奇奇奇", "奇奇偶", "奇偶奇", "偶奇奇", "偶偶偶", "偶偶奇", "偶奇偶", "奇偶偶"]
        vars_dict["oe_list"] = oe_types
        vars_dict["oe"] = [tk.BooleanVar() for _ in range(len(oe_types))]

        vars_dict["pc_mode"] = tk.IntVar(value=1)
        pc_types = ["质质质", "质质合", "质合质", "合质质", "合合合", "合合质", "合质合", "质合合"]
        vars_dict["pc_list"] = pc_types
        vars_dict["pc"] = [tk.BooleanVar() for _ in range(len(pc_types))]

        vars_dict["straight_mode"] = tk.IntVar(value=0)

        vars_dict["number_group"] = []
        for _ in range(5):
            vars_dict["number_group"].append({
                "nums": [tk.BooleanVar() for _ in range(10)],
                "count": tk.StringVar(value="0")
            })

        vars_dict["combine_level"] = tk.StringVar(value="zhixuan")
        vars_dict["combine_sub"] = tk.StringVar(value="all")

        return vars_dict

    def _generate_sms_types(self):
        sms = ["小", "中", "大"]
        return [f"{a}{b}{c}" for a in sms for b in sms for c in sms]

    def _on_combine_level_change(self, *args):
        level = self.filter_vars["combine_level"].get()
        if level == "zhixuan":
            self.radio_zhixuan_baoz.config(state="normal")
            self.radio_zhixuan_zusan.config(state="normal")
            self.radio_zhixuan_zuliu.config(state="normal")
            self.radio_zuxuan_zusan.config(state="disabled")
            self.radio_zuxuan_zuliu.config(state="disabled")
            self.filter_vars["combine_sub"].set("all")
        elif level == "zuxuan":
            self.radio_zhixuan_baoz.config(state="disabled")
            self.radio_zhixuan_zusan.config(state="disabled")
            self.radio_zhixuan_zuliu.config(state="disabled")
            self.radio_zuxuan_zusan.config(state="normal")
            self.radio_zuxuan_zuliu.config(state="normal")
            self.filter_vars["combine_sub"].set("all")

    def _build_filter_ui(self):
        self._add_section_title("1. 定位选择（可选，勾选为选中号码）")
        pos_container = tk.Frame(self.filter_content, bg="white")
        pos_container.pack(fill=tk.X, padx=10, pady=5)

        b_frame = tk.Frame(pos_container, bg="white")
        b_frame.pack(fill=tk.X, pady=2)
        tk.Label(b_frame, text="百位：", bg="white", width=8).pack(side=tk.LEFT)
        b_digit_frame = tk.Frame(b_frame, bg="white")
        b_digit_frame.pack(side=tk.LEFT)
        for i in range(10):
            tk.Checkbutton(b_digit_frame, variable=self.filter_vars["pos"]["b"][i], text=str(i), bg="white").grid(row=0, column=i)
        b_btn_frame = tk.Frame(b_frame, bg="white")
        b_btn_frame.pack(side=tk.LEFT, padx=10)
        ttk.Button(b_btn_frame, text="全选", command=lambda: self._select_single_pos("b", True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(b_btn_frame, text="取消", command=lambda: self._select_single_pos("b", False)).pack(side=tk.LEFT, padx=2)

        s_frame = tk.Frame(pos_container, bg="white")
        s_frame.pack(fill=tk.X, pady=2)
        tk.Label(s_frame, text="十位：", bg="white", width=8).pack(side=tk.LEFT)
        s_digit_frame = tk.Frame(s_frame, bg="white")
        s_digit_frame.pack(side=tk.LEFT)
        for i in range(10):
            tk.Checkbutton(s_digit_frame, variable=self.filter_vars["pos"]["s"][i], text=str(i), bg="white").grid(row=0, column=i)
        s_btn_frame = tk.Frame(s_frame, bg="white")
        s_btn_frame.pack(side=tk.LEFT, padx=10)
        ttk.Button(s_btn_frame, text="全选", command=lambda: self._select_single_pos("s", True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(s_btn_frame, text="取消", command=lambda: self._select_single_pos("s", False)).pack(side=tk.LEFT, padx=2)

        g_frame = tk.Frame(pos_container, bg="white")
        g_frame.pack(fill=tk.X, pady=2)
        tk.Label(g_frame, text="个位：", bg="white", width=8).pack(side=tk.LEFT)
        g_digit_frame = tk.Frame(g_frame, bg="white")
        g_digit_frame.pack(side=tk.LEFT)
        for i in range(10):
            tk.Checkbutton(g_digit_frame, variable=self.filter_vars["pos"]["g"][i], text=str(i), bg="white").grid(row=0, column=i)
        g_btn_frame = tk.Frame(g_frame, bg="white")
        g_btn_frame.pack(side=tk.LEFT, padx=10)
        ttk.Button(g_btn_frame, text="全选", command=lambda: self._select_single_pos("g", True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(g_btn_frame, text="取消", command=lambda: self._select_single_pos("g", False)).pack(side=tk.LEFT, padx=2)

        self._add_section_title("2. 直选定位（每行一个组合，格式：百位,十位,个位，数字无需空格分隔）")
        direct_pos_frame = tk.Frame(self.filter_content, bg="white")
        direct_pos_frame.pack(fill=tk.X, padx=10, pady=5)

        mode_frame = tk.Frame(direct_pos_frame, bg="white")
        mode_frame.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(mode_frame, text="包含选中", variable=self.filter_vars["direct_pos_mode"], value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="排除选中", variable=self.filter_vars["direct_pos_mode"], value=0).pack(side=tk.LEFT, padx=5)

        input_frame = tk.Frame(direct_pos_frame, bg="white")
        input_frame.pack(fill=tk.X, pady=2)
        tk.Label(input_frame, text="输入示例：\n135,246,789\n02,13,45", bg="white", justify=tk.LEFT).pack(side=tk.LEFT, padx=5)
        self.direct_pos_text = tk.Text(input_frame, width=60, height=5, font=("Arial", 10))
        self.direct_pos_text.pack(side=tk.LEFT, padx=5)

        self._add_section_title("3. 非定位直选（每行一个三位数字，匹配所有排列，顺序不限）")
        non_pos_direct_frame = tk.Frame(self.filter_content, bg="white")
        non_pos_direct_frame.pack(fill=tk.X, padx=10, pady=5)

        non_pos_mode_frame = tk.Frame(non_pos_direct_frame, bg="white")
        non_pos_mode_frame.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(non_pos_mode_frame, text="包含选中", variable=self.filter_vars["non_pos_direct_mode"], value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(non_pos_mode_frame, text="排除选中", variable=self.filter_vars["non_pos_direct_mode"], value=0).pack(side=tk.LEFT, padx=5)

        non_pos_input_frame = tk.Frame(non_pos_direct_frame, bg="white")
        non_pos_input_frame.pack(fill=tk.X, pady=2)
        tk.Label(non_pos_input_frame, text="输入示例：\n123 （匹配123、132、213、231、312、321）\n456\n778", bg="white", justify=tk.LEFT).pack(side=tk.LEFT, padx=5)
        self.non_pos_direct_text = tk.Text(non_pos_input_frame, width=60, height=5, font=("Arial", 10))
        self.non_pos_direct_text.pack(side=tk.LEFT, padx=5)

        self._add_section_title("4. 杀号过滤（可选，勾选为排除号码）")
        kill_frame = ttk.Frame(self.filter_content)
        kill_frame.pack(fill=tk.X, padx=10, pady=5)
        self._add_digit_checkgroup(kill_frame, "百位", self.filter_vars["kill"]["b"])
        self._add_digit_checkgroup(kill_frame, "十位", self.filter_vars["kill"]["s"])
        self._add_digit_checkgroup(kill_frame, "个位", self.filter_vars["kill"]["g"])
        self._add_select_all_clear_buttons(kill_frame, self.filter_vars["kill"])

        self._add_section_title("5. 胆码过滤（可选，勾选为必含号码）")
        dan_frame = ttk.Frame(self.filter_content)
        dan_frame.pack(fill=tk.X, padx=10, pady=5)
        self._add_digit_checkgroup(dan_frame, "百位", self.filter_vars["dan"]["b"])
        self._add_digit_checkgroup(dan_frame, "十位", self.filter_vars["dan"]["s"])
        self._add_digit_checkgroup(dan_frame, "个位", self.filter_vars["dan"]["g"])
        self._add_select_all_clear_buttons(dan_frame, self.filter_vars["dan"])

        self._add_section_title("6. 二码和过滤（0-18，勾选为目标和值）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["two_sum_mode"], self.filter_vars["two_sum"], list(range(19)), cols=10)

        self._add_section_title("7. 二码差过滤（0-9，勾选为目标差）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["two_diff_mode"], self.filter_vars["two_diff"], list(range(10)), cols=10)

        self._add_section_title("8. 二码过滤（勾选为目标二码）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["two_code_mode"], self.filter_vars["two_code"], self.filter_vars["two_code_list"], cols=10)

        self._add_section_title("9. 012路过滤（勾选为目标形态）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["o12_mode"], self.filter_vars["o12"], self.filter_vars["o12_list"], cols=9)

        self._add_section_title("10. 和值过滤（0-27，勾选为目标和值）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["sum_mode"], self.filter_vars["sum_val"], list(range(28)), cols=10)

        self._add_section_title("11. 和尾过滤（0-9，勾选为目标和尾）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["sum_tail_mode"], self.filter_vars["sum_tail"], list(range(10)), cols=10)

        self._add_section_title("12. 跨度过滤（0-9，勾选为目标跨度）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["span_mode"], self.filter_vars["span"], list(range(10)), cols=10)

        self._add_section_title("13. 大中小过滤（小=0-2，中=3-6，大=7-9）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["sms_mode"], self.filter_vars["sms"], self.filter_vars["sms_list"], cols=9)

        self._add_section_title("14. 大小过滤（小=0-4，大=5-9）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["size_mode"], self.filter_vars["size"], self.filter_vars["size_list"], cols=4)

        self._add_section_title("15. 奇偶过滤（奇=13579，偶=02468）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["oe_mode"], self.filter_vars["oe"], self.filter_vars["oe_list"], cols=4)

        self._add_section_title("16. 质合过滤（质=12357，合=04689）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["pc_mode"], self.filter_vars["pc"], self.filter_vars["pc_list"], cols=4)

        self._add_section_title("17. 顺子过滤")
        straight_frame = ttk.Frame(self.filter_content)
        straight_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Radiobutton(straight_frame, text="不过滤", variable=self.filter_vars["straight_mode"], value=0).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(straight_frame, text="过滤顺子", variable=self.filter_vars["straight_mode"], value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(straight_frame, text="过滤半顺子", variable=self.filter_vars["straight_mode"], value=2).pack(side=tk.LEFT, padx=5)

        self._add_section_title("18. 号码组过滤（最多5组，勾选为胆码，输入出现次数）")
        for i in range(5):
            group_frame = tk.Frame(self.filter_content, relief=tk.RAISED, borderwidth=1, bg="white")
            group_frame.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(group_frame, text=f"第{i + 1}组：", bg="white").pack(side=tk.LEFT, padx=5)
            num_frame = tk.Frame(group_frame, bg="white")
            num_frame.pack(side=tk.LEFT, padx=5)
            for j in range(10):
                tk.Checkbutton(num_frame, variable=self.filter_vars["number_group"][i]["nums"][j], text=str(j), bg="white").grid(row=0, column=j)
            tk.Label(group_frame, text="出现次数：", bg="white").pack(side=tk.LEFT, padx=5)
            count_entry = ttk.Entry(group_frame, textvariable=self.filter_vars["number_group"][i]["count"], width=5)
            count_entry.pack(side=tk.LEFT)
            tk.Label(group_frame, text="（0-3）", bg="white").pack(side=tk.LEFT)

        self._add_section_title("19. 组合选项")
        combine_frame = ttk.Frame(self.filter_content)
        combine_frame.pack(fill=tk.X, padx=10, pady=5)

        level_frame = ttk.Frame(combine_frame)
        level_frame.pack(fill=tk.X, pady=2)
        ttk.Label(level_frame, text="一级选择：").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="直选", variable=self.filter_vars["combine_level"], value="zhixuan", command=self._on_combine_level_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="组选", variable=self.filter_vars["combine_level"], value="zuxuan", command=self._on_combine_level_change).pack(side=tk.LEFT, padx=5)

        zhixuan_sub_frame = ttk.Frame(combine_frame)
        zhixuan_sub_frame.pack(fill=tk.X, pady=2)
        ttk.Label(zhixuan_sub_frame, text="直选子选项：").pack(side=tk.LEFT, padx=5)
        self.radio_zhixuan_baoz = ttk.Radiobutton(zhixuan_sub_frame, text="豹子", variable=self.filter_vars["combine_sub"], value="baoz")
        self.radio_zhixuan_baoz.pack(side=tk.LEFT, padx=5)
        self.radio_zhixuan_zusan = ttk.Radiobutton(zhixuan_sub_frame, text="组三", variable=self.filter_vars["combine_sub"], value="zusan")
        self.radio_zhixuan_zusan.pack(side=tk.LEFT, padx=5)
        self.radio_zhixuan_zuliu = ttk.Radiobutton(zhixuan_sub_frame, text="组六", variable=self.filter_vars["combine_sub"], value="zuliu")
        self.radio_zhixuan_zuliu.pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(zhixuan_sub_frame, text="全部（豹子+组三+组六）", variable=self.filter_vars["combine_sub"], value="all").pack(side=tk.LEFT, padx=5)

        zuxuan_sub_frame = ttk.Frame(combine_frame)
        zuxuan_sub_frame.pack(fill=tk.X, pady=2)
        ttk.Label(zuxuan_sub_frame, text="组选子选项：").pack(side=tk.LEFT, padx=5)
        self.radio_zuxuan_zusan = ttk.Radiobutton(zuxuan_sub_frame, text="组三", variable=self.filter_vars["combine_sub"], value="zusan")
        self.radio_zuxuan_zusan.pack(side=tk.LEFT, padx=5)
        self.radio_zuxuan_zuliu = ttk.Radiobutton(zuxuan_sub_frame, text="组六", variable=self.filter_vars["combine_sub"], value="zuliu")
        self.radio_zuxuan_zuliu.pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(zuxuan_sub_frame, text="全部（组三+组六）", variable=self.filter_vars["combine_sub"], value="all").pack(side=tk.LEFT, padx=5)

        self._on_combine_level_change()

    def _select_single_pos(self, pos, state):
        for var in self.filter_vars["pos"][pos]:
            var.set(state)

    def _add_section_title(self, text):
        tk.Label(self.filter_content, text=text, font=("Arial", 10, "bold"), fg="#2c3e50", bg="white").pack(anchor="w", padx=10, pady=(10, 5))

    def _add_digit_checkgroup(self, parent, title, var_list):
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(frame, text=title).pack()
        digit_frame = tk.Frame(frame, bg="white")
        digit_frame.pack()
        for i in range(10):
            tk.Checkbutton(digit_frame, variable=var_list[i], text=str(i), bg="white").grid(row=0, column=i)

    def _add_select_all_clear_buttons(self, parent, var_dict):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="全选", command=lambda: self._select_all(var_dict, True)).pack(pady=2)
        ttk.Button(btn_frame, text="取消", command=lambda: self._select_all(var_dict, False)).pack(pady=2)

    def _select_all(self, var_dict, state):
        for pos in ["b", "s", "g"]:
            for var in var_dict[pos]:
                var.set(state)

    def _add_mode_checkgroup(self, parent, mode_var, var_list, item_list, cols=10):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)
        mode_frame = ttk.Frame(frame)
        mode_frame.pack(side=tk.TOP, padx=5)
        ttk.Radiobutton(mode_frame, text="排除选中", variable=mode_var, value=0).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="包含选中", variable=mode_var, value=1).pack(side=tk.LEFT, padx=5)
        item_frame = tk.Frame(frame, bg="white")
        item_frame.pack(side=tk.TOP, padx=5, pady=5)
        for idx, (item, var) in enumerate(zip(item_list, var_list)):
            row = idx // cols
            col = idx % cols
            tk.Checkbutton(item_frame, variable=var, text=str(item), bg="white").grid(row=row, column=col, padx=2, pady=2)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.TOP, padx=5)
        ttk.Button(btn_frame, text="全选", command=lambda: self._check_all(var_list, True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=lambda: self._check_all(var_list, False)).pack(side=tk.LEFT, padx=5)

    def _check_all(self, var_list, state):
        for var in var_list:
            var.set(state)

    def start_filter(self):
        self.result_text.delete(1.0, tk.END)
        try:
            filters = self._parse_filters()
            all_nums = self._generate_all_direct()
            self._log(f"初始直选号码总数：{len(all_nums)}")

            nums = all_nums
            nums = self._filter_position(nums, filters["pos"])
            self._log(f"定位过滤后剩余：{len(nums)}注")

            nums = self._filter_direct_pos(nums, filters["direct_pos_combines"], filters["direct_pos_mode"])
            self._log(f"直选定位过滤后剩余：{len(nums)}注")

            nums = self._filter_non_pos_direct(nums, filters["non_pos_direct_permutations"], filters["non_pos_direct_mode"])
            self._log(f"非定位直选过滤后剩余：{len(nums)}注")

            nums = self._filter_kill(nums, filters["kill"])
            self._log(f"杀号过滤后剩余：{len(nums)}注")

            nums = self._filter_dan(nums, filters["dan"])
            self._log(f"胆码过滤后剩余：{len(nums)}注")

            nums = self._filter_two_sum(nums, filters["two_sum_mode"], filters["two_sum"])
            self._log(f"二码和过滤后剩余：{len(nums)}注")

            nums = self._filter_two_diff(nums, filters["two_diff_mode"], filters["two_diff"])
            self._log(f"二码差过滤后剩余：{len(nums)}注")

            nums = self._filter_two_code(nums, filters["two_code_mode"], filters["two_code"])
            self._log(f"二码过滤后剩余：{len(nums)}注")

            nums = self._filter_012(nums, filters["o12_mode"], filters["o12"])
            self._log(f"012路过滤后剩余：{len(nums)}注")

            nums = self._filter_sum(nums, filters["sum_mode"], filters["sum_val"])
            self._log(f"和值过滤后剩余：{len(nums)}注")

            nums = self._filter_sum_tail(nums, filters["sum_tail_mode"], filters["sum_tail"])
            self._log(f"和尾过滤后剩余：{len(nums)}注")

            nums = self._filter_span(nums, filters["span_mode"], filters["span"])
            self._log(f"跨度过滤后剩余：{len(nums)}注")

            nums = self._filter_sms(nums, filters["sms_mode"], filters["sms"])
            self._log(f"大中小过滤后剩余：{len(nums)}注")

            nums = self._filter_size(nums, filters["size_mode"], filters["size"])
            self._log(f"大小过滤后剩余：{len(nums)}注")

            nums = self._filter_oe(nums, filters["oe_mode"], filters["oe"])
            self._log(f"奇偶过滤后剩余：{len(nums)}注")

            nums = self._filter_pc(nums, filters["pc_mode"], filters["pc"])
            self._log(f"质合过滤后剩余：{len(nums)}注")

            nums = self._filter_straight(nums, filters["straight_mode"])
            self._log(f"顺子过滤后剩余：{len(nums)}注")

            nums = self._filter_number_group(nums, filters["number_group"])
            self._log(f"号码组过滤后剩余：{len(nums)}注")

            final_nums = self._convert_combine_new(nums, filters["combine_level"], filters["combine_sub"])
            combine_name = "直选" if filters["combine_level"] == "zhixuan" else "组选"
            sub_name = {"all": "全部", "baoz": "豹子", "zusan": "组三", "zuliu": "组六"}.get(filters["combine_sub"], "全部")
            self._log(f"\n最终{combine_name}-{sub_name}形态号码数：{len(final_nums)}注")

            if final_nums:
                self._log("\n" + "=" * 50)
                for i in range(0, len(final_nums), 10):
                    self._log(' '.join(final_nums[i:i + 10]))
            else:
                self._log("\n暂无符合所有条件的号码！")

            self._log("\n" + "=" * 50)
            self._log("过滤完成！（注：彩票开奖随机，本工具仅为号码筛选，不保证中奖）")

        except Exception as e:
            showwarning("错误", f"过滤过程中出现异常：{str(e)}")

    def _parse_filters(self):
        filters = {}

        filters["pos"] = {
            "b": {str(i) for i, var in enumerate(self.filter_vars["pos"]["b"]) if var.get()},
            "s": {str(i) for i, var in enumerate(self.filter_vars["pos"]["s"]) if var.get()},
            "g": {str(i) for i, var in enumerate(self.filter_vars["pos"]["g"]) if var.get()}
        }

        filters["direct_pos_mode"] = self.filter_vars["direct_pos_mode"].get()
        if self.direct_pos_text:
            input_content = self.direct_pos_text.get(1.0, tk.END).strip()
            filters["direct_pos_combines"] = self._parse_direct_pos_multi(input_content)
        else:
            filters["direct_pos_combines"] = []

        filters["non_pos_direct_mode"] = self.filter_vars["non_pos_direct_mode"].get()
        if self.non_pos_direct_text:
            input_content = self.non_pos_direct_text.get(1.0, tk.END).strip()
            filters["non_pos_direct_permutations"] = self._parse_non_pos_direct_multi(input_content)
        else:
            filters["non_pos_direct_permutations"] = set()

        filters["kill"] = {
            "b": {str(i) for i, var in enumerate(self.filter_vars["kill"]["b"]) if var.get()},
            "s": {str(i) for i, var in enumerate(self.filter_vars["kill"]["s"]) if var.get()},
            "g": {str(i) for i, var in enumerate(self.filter_vars["kill"]["g"]) if var.get()}
        }

        filters["dan"] = {
            "b": {str(i) for i, var in enumerate(self.filter_vars["dan"]["b"]) if var.get()},
            "s": {str(i) for i, var in enumerate(self.filter_vars["dan"]["s"]) if var.get()},
            "g": {str(i) for i, var in enumerate(self.filter_vars["dan"]["g"]) if var.get()}
        }

        filters["two_sum_mode"] = self.filter_vars["two_sum_mode"].get()
        filters["two_sum"] = {i for i, var in enumerate(self.filter_vars["two_sum"]) if var.get()}

        filters["two_diff_mode"] = self.filter_vars["two_diff_mode"].get()
        filters["two_diff"] = {i for i, var in enumerate(self.filter_vars["two_diff"]) if var.get()}

        filters["two_code_mode"] = self.filter_vars["two_code_mode"].get()
        filters["two_code"] = {self.filter_vars["two_code_list"][i] for i, var in enumerate(self.filter_vars["two_code"]) if var.get()}

        filters["o12_mode"] = self.filter_vars["o12_mode"].get()
        filters["o12"] = {self.filter_vars["o12_list"][i] for i, var in enumerate(self.filter_vars["o12"]) if var.get()}

        filters["sum_mode"] = self.filter_vars["sum_mode"].get()
        filters["sum_val"] = {i for i, var in enumerate(self.filter_vars["sum_val"]) if var.get()}

        filters["sum_tail_mode"] = self.filter_vars["sum_tail_mode"].get()
        filters["sum_tail"] = {i for i, var in enumerate(self.filter_vars["sum_tail"]) if var.get()}

        filters["span_mode"] = self.filter_vars["span_mode"].get()
        filters["span"] = {i for i, var in enumerate(self.filter_vars["span"]) if var.get()}

        filters["sms_mode"] = self.filter_vars["sms_mode"].get()
        filters["sms"] = {self.filter_vars["sms_list"][i] for i, var in enumerate(self.filter_vars["sms"]) if var.get()}

        filters["size_mode"] = self.filter_vars["size_mode"].get()
        filters["size"] = {self.filter_vars["size_list"][i] for i, var in enumerate(self.filter_vars["size"]) if var.get()}

        filters["oe_mode"] = self.filter_vars["oe_mode"].get()
        filters["oe"] = {self.filter_vars["oe_list"][i] for i, var in enumerate(self.filter_vars["oe"]) if var.get()}

        filters["pc_mode"] = self.filter_vars["pc_mode"].get()
        filters["pc"] = {self.filter_vars["pc_list"][i] for i, var in enumerate(self.filter_vars["pc"]) if var.get()}

        filters["straight_mode"] = self.filter_vars["straight_mode"].get()

        filters["number_group"] = []
        for group in self.filter_vars["number_group"]:
            nums = {str(i) for i, var in enumerate(group["nums"]) if var.get()}
            if not nums:
                continue
            count_str = group["count"].get().strip()
            count = int(count_str) if count_str.isdigit() and 0 <= int(count_str) <= 3 else 0
            filters["number_group"].append((nums, count))

        filters["combine_level"] = self.filter_vars["combine_level"].get()
        filters["combine_sub"] = self.filter_vars["combine_sub"].get()

        return filters

    def _parse_direct_pos_single(self, line):
        line = line.strip()
        if not line:
            return []
        parts = line.split(',')
        if len(parts) != 3:
            return []
        b_chars = list(parts[0].strip())
        s_chars = list(parts[1].strip())
        g_chars = list(parts[2].strip())
        b_valid = [d for d in b_chars if d.isdigit() and 0 <= int(d) <= 9]
        s_valid = [d for d in s_chars if d.isdigit() and 0 <= int(d) <= 9]
        g_valid = [d for d in g_chars if d.isdigit() and 0 <= int(d) <= 9]
        if not (b_valid and s_valid and g_valid):
            return []
        return list(set([''.join(combo) for combo in itertools.product(b_valid, s_valid, g_valid)]))

    def _parse_direct_pos_multi(self, input_content):
        all_combines = []
        lines = input_content.splitlines()
        for line in lines:
            line_combines = self._parse_direct_pos_single(line)
            all_combines.extend(line_combines)
        return list(set(all_combines))

    def _parse_non_pos_direct_single(self, line):
        line = line.strip()
        if len(line) != 3 or not line.isdigit():
            return set()
        permutations = itertools.permutations(line)
        unique_perms = set([''.join(p) for p in permutations])
        return unique_perms

    def _parse_non_pos_direct_multi(self, input_content):
        all_perms = set()
        lines = input_content.splitlines()
        for line in lines:
            line_perms = self._parse_non_pos_direct_single(line)
            all_perms.update(line_perms)
        return all_perms

    def _filter_direct_pos(self, numbers, direct_combines, mode):
        if not direct_combines:
            return numbers
        filtered = []
        for num in numbers:
            if mode == 1:
                if num in direct_combines:
                    filtered.append(num)
            else:
                if num not in direct_combines:
                    filtered.append(num)
        return filtered

    def _filter_non_pos_direct(self, numbers, target_permutations, mode):
        if not target_permutations:
            return numbers
        filtered = []
        for num in numbers:
            is_match = num in target_permutations
            if mode == 1:
                if is_match:
                    filtered.append(num)
            else:
                if not is_match:
                    filtered.append(num)
        return filtered

    def _get_combine_type(self, num):
        digits = list(num)
        if len(set(digits)) == 1:
            return "baoz"
        elif len(set(digits)) == 2:
            return "zusan"
        else:
            return "zuliu"

    def _convert_combine_new(self, numbers, combine_level, combine_sub):
        if combine_level == "zhixuan":
            if combine_sub == "all":
                return numbers
            else:
                return [num for num in numbers if self._get_combine_type(num) == combine_sub]
        elif combine_level == "zuxuan":
            zuxuan_set = set()
            for num in numbers:
                sorted_num = ''.join(sorted(num))
                zuxuan_set.add(sorted_num)
            zuxuan_list = sorted(list(zuxuan_set))
            if combine_sub == "all":
                return [num for num in zuxuan_list if self._get_combine_type(num) in ["zusan", "zuliu"]]
            else:
                return [num for num in zuxuan_list if self._get_combine_type(num) == combine_sub]
        else:
            return numbers

    def _generate_all_direct(self):
        return [f"{i:03d}" for i in range(1000)]

    def _filter_position(self, numbers, pos):
        filtered = []
        for num in numbers:
            b, s, g = num[0], num[1], num[2]
            cond_b = (not pos["b"]) or (b in pos["b"])
            cond_s = (not pos["s"]) or (s in pos["s"])
            cond_g = (not pos["g"]) or (g in pos["g"])
            if cond_b and cond_s and cond_g:
                filtered.append(num)
        return filtered

    def _filter_kill(self, numbers, kill):
        filtered = []
        for num in numbers:
            b, s, g = num[0], num[1], num[2]
            cond_b = (b not in kill["b"])
            cond_s = (s not in kill["s"])
            cond_g = (g not in kill["g"])
            if cond_b and cond_s and cond_g:
                filtered.append(num)
        return filtered

    def _filter_dan(self, numbers, dan):
        filtered = []
        for num in numbers:
            b, s, g = num[0], num[1], num[2]
            cond_b = (not dan["b"]) or (b in dan["b"])
            cond_s = (not dan["s"]) or (s in dan["s"])
            cond_g = (not dan["g"]) or (g in dan["g"])
            if cond_b and cond_s and cond_g:
                filtered.append(num)
        return filtered

    def _get_two_sum(self, num):
        b, s, g = map(int, num)
        return {b + s, b + g, s + g}

    def _filter_two_sum(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_sums = self._get_two_sum(num)
            if (mode == 1 and num_sums & selected) or (mode == 0 and not num_sums & selected):
                filtered.append(num)
        return filtered

    def _get_two_diff(self, num):
        b, s, g = map(int, num)
        return {abs(b - s), abs(b - g), abs(s - g)}

    def _filter_two_diff(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_diffs = self._get_two_diff(num)
            if (mode == 1 and num_diffs & selected) or (mode == 0 and not num_diffs & selected):
                filtered.append(num)
        return filtered

    def _get_two_code(self, num):
        digits = list(num)
        codes = set()
        codes.add(''.join(sorted([digits[0], digits[1]])))
        codes.add(''.join(sorted([digits[0], digits[2]])))
        codes.add(''.join(sorted([digits[1], digits[2]])))
        return codes

    def _filter_two_code(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_codes = self._get_two_code(num)
            if (mode == 1 and num_codes & selected) or (mode == 0 and not num_codes & selected):
                filtered.append(num)
        return filtered

    def _get_012_type(self, num):
        return ''.join([str(int(c) % 3) for c in num])

    def _filter_012(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_type = self._get_012_type(num)
            if (mode == 1 and num_type in selected) or (mode == 0 and num_type not in selected):
                filtered.append(num)
        return filtered

    def _get_sum(self, num):
        return sum(map(int, num))

    def _filter_sum(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_sum = self._get_sum(num)
            if (mode == 1 and num_sum in selected) or (mode == 0 and num_sum not in selected):
                filtered.append(num)
        return filtered

    def _get_sum_tail(self, num):
        return self._get_sum(num) % 10

    def _filter_sum_tail(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_tail = self._get_sum_tail(num)
            if (mode == 1 and num_tail in selected) or (mode == 0 and num_tail not in selected):
                filtered.append(num)
        return filtered

    def _get_span(self, num):
        digits = list(map(int, num))
        return max(digits) - min(digits)

    def _filter_span(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_span = self._get_span(num)
            if (mode == 1 and num_span in selected) or (mode == 0 and num_span not in selected):
                filtered.append(num)
        return filtered

    def _get_sms_type(self, num):
        sms_map = {str(i): "小" for i in range(3)}
        sms_map.update({str(i): "中" for i in range(3, 7)})
        sms_map.update({str(i): "大" for i in range(7, 10)})
        return ''.join([sms_map[c] for c in num])

    def _filter_sms(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_type = self._get_sms_type(num)
            if (mode == 1 and num_type in selected) or (mode == 0 and num_type not in selected):
                filtered.append(num)
        return filtered

    def _get_size_type(self, num):
        size_map = {str(i): "小" for i in range(5)}
        size_map.update({str(i): "大" for i in range(5, 10)})
        return ''.join([size_map[c] for c in num])

    def _filter_size(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_type = self._get_size_type(num)
            if (mode == 1 and num_type in selected) or (mode == 0 and num_type not in selected):
                filtered.append(num)
        return filtered

    def _get_oe_type(self, num):
        oe_map = {str(i): "奇" if i % 2 == 1 else "偶" for i in range(10)}
        return ''.join([oe_map[c] for c in num])

    def _filter_oe(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_type = self._get_oe_type(num)
            if (mode == 1 and num_type in selected) or (mode == 0 and num_type not in selected):
                filtered.append(num)
        return filtered

    def _get_pc_type(self, num):
        pc_map = {str(i): "质" if i in [1, 2, 3, 5, 7] else "合" for i in range(10)}
        return ''.join([pc_map[c] for c in num])

    def _filter_pc(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_type = self._get_pc_type(num)
            if (mode == 1 and num_type in selected) or (mode == 0 and num_type not in selected):
                filtered.append(num)
        return filtered

    def _is_straight(self, num):
        digits = sorted(map(int, num))
        return (digits[1] - digits[0] == 1 and digits[2] - digits[1] == 1) or (digits == [0, 1, 9])

    def _is_semi_straight(self, num):
        digits = list(map(int, num))
        pairs = [(digits[0], digits[1]), (digits[0], digits[2]), (digits[1], digits[2])]
        for a, b in pairs:
            if abs(a - b) == 1 or abs(a - b) == 9:
                return True
        return False

    def _filter_straight(self, numbers, mode):
        if mode == 0:
            return numbers
        filtered = []
        for num in numbers:
            if mode == 1 and not self._is_straight(num):
                filtered.append(num)
            elif mode == 2 and not self._is_semi_straight(num):
                filtered.append(num)
        return filtered

    def _filter_number_group(self, numbers, groups):
        if not groups:
            return numbers
        filtered = []
        for num in numbers:
            num_digits = list(num)
            valid = True
            for (group_nums, count) in groups:
                actual_count = sum(1 for d in num_digits if d in group_nums)
                if actual_count != count:
                    valid = False
                    break
            if valid:
                filtered.append(num)
        return filtered

    def _log(self, text):
        self.result_text.insert(tk.END, text + "\n")
        self.result_text.see(tk.END)

    def clear_all(self):
        for pos in ["b", "s", "g"]:
            for var in self.filter_vars["pos"][pos]:
                var.set(False)

        if self.direct_pos_text:
            self.direct_pos_text.delete(1.0, tk.END)
        self.filter_vars["direct_pos_mode"].set(1)

        if self.non_pos_direct_text:
            self.non_pos_direct_text.delete(1.0, tk.END)
        self.filter_vars["non_pos_direct_mode"].set(1)

        for pos in ["b", "s", "g"]:
            for var in self.filter_vars["kill"][pos]:
                var.set(False)
            for var in self.filter_vars["dan"][pos]:
                var.set(False)

        for key in ["two_sum", "two_diff", "two_code", "o12", "sum_val", "sum_tail", "span", "sms", "size", "oe", "pc"]:
            for var in self.filter_vars[key]:
                var.set(False)

        self.filter_vars["two_sum_mode"].set(1)
        self.filter_vars["two_diff_mode"].set(1)
        self.filter_vars["two_code_mode"].set(1)
        self.filter_vars["o12_mode"].set(1)
        self.filter_vars["sum_mode"].set(1)
        self.filter_vars["sum_tail_mode"].set(1)
        self.filter_vars["span_mode"].set(1)
        self.filter_vars["sms_mode"].set(1)
        self.filter_vars["size_mode"].set(1)
        self.filter_vars["oe_mode"].set(1)
        self.filter_vars["pc_mode"].set(1)
        self.filter_vars["straight_mode"].set(0)

        for group in self.filter_vars["number_group"]:
            for var in group["nums"]:
                var.set(False)
            group["count"].set("0")

        self.filter_vars["combine_level"].set("zhixuan")
        self.filter_vars["combine_sub"].set("all")
        self._on_combine_level_change()

        self.result_text.delete(1.0, tk.END)

    def show_help(self):
        help_text = """
3D缩水工具使用说明：
1. 定位选择：勾选百位/十位/个位的可选数字，未勾选则不限制该位（每个位置单独全选/取消）
2. 直选定位：多行输入，每行一个组合，格式为「百位,十位,个位」，数字无需空格分隔
   示例：
   135,246,789 （第一行：百位1/3/5，十位2/4/6，个位7/8/9）
   02,13,45     （第二行：百位0/2，十位1/3，个位4/5）
   7,8,9        （第三行：百位7，十位8，个位9）
   模式：
   - 包含选中：仅保留所有行组合内的号码；
   - 排除选中：移除所有行组合内的号码。
3. 直选定位二：功能与「直选定位」完全一致，可设置第二组直选定位条件（逻辑与直选定位叠加）
4. 杀号过滤：勾选需要排除的数字（该位不会出现勾选数字）
5. 胆码过滤：勾选必须包含的数字（该位必须是勾选数字）
6. 二码和/差/过滤：选择目标条件，模式选择"包含选中"或"排除选中"
7. 012路：每位数字%3的余数组合（0/1/2）
8. 和值：三位数字之和（0-27），和尾：和值的个位数（0-9）
9. 跨度：最大数-最小数（0-9）
10. 大中小：小=0-2，中=3-6，大=7-9；大小：小=0-4，大=5-9
11. 奇偶：奇=13579，偶=02468；质合：质=12357，合=04689
12. 顺子过滤：顺子=三位数连号（如123），半顺子=两位数连号（如125）
13. 号码组：每组勾选胆码，输入需要出现的次数（0-3）
14. 组合选项（分层）：
    - 一级选择：直选 / 组选（并列）
    - 直选子选项：豹子、组三、组六、全部（包含前三者）
    - 组选子选项：组三、组六、全部（仅包含前两者，无豹子）
    - 直选：保留号码原始顺序；组选：号码排序去重（如123/132/213等合并为123）

注意事项：
- 过滤条件过多可能导致无符合条件的号码，请合理设置
- 彩票开奖为随机事件，本工具仅为号码筛选，不保证中奖
- 输入非法内容会自动忽略，请按提示格式输入
        """
        showinfo("使用说明", help_text)
