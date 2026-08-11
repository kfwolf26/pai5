import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.messagebox import showwarning, showinfo
import itertools


# 排列5 玩法常量
# 5 位:万(w) / 千(q) / 百(b) / 十(s) / 个(g)
POS_KEYS = ["w", "q", "b", "s", "g"]
POS_NAMES = {"w": "万位", "q": "千位", "b": "百位", "s": "十位", "g": "个位"}
POS_LABELS = {"w": "万", "q": "千", "b": "百", "s": "十", "g": "个"}

# 5 位形态列表(用 itertools.product 生成)
def _gen_form_types(chars, repeat):
    """生成形态列表,如 ['大小大小大', ...]"""
    return ["".join(p) for p in itertools.product(chars, repeat=repeat)]


SIZE_TYPES = _gen_form_types("大小", 5)   # 2^5 = 32
OE_TYPES = _gen_form_types("奇偶", 5)    # 2^5 = 32
PC_TYPES = _gen_form_types("质合", 5)    # 2^5 = 32
O12_TYPES = _gen_form_types("012", 5)    # 3^5 = 243
SMS_TYPES = _gen_form_types("小中大", 5)  # 3^5 = 243


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

        self.direct_pos_text = None
        self.non_pos_direct_text = None
        self._build_filter_ui()

    def _init_filter_vars(self):
        vars_dict = {}

        # 1. 定位/杀号/胆码:5 个位置,每位 0-9
        for key in ["pos", "kill", "dan"]:
            vars_dict[key] = {pos: [tk.BooleanVar() for _ in range(10)] for pos in POS_KEYS}

        vars_dict["direct_pos_mode"] = tk.IntVar(value=1)
        vars_dict["non_pos_direct_mode"] = tk.IntVar(value=1)

        # 二码和/差/二码:5 位时两两组合 C(5,2)=10 对
        vars_dict["two_sum_mode"] = tk.IntVar(value=1)
        vars_dict["two_sum"] = [tk.BooleanVar() for _ in range(19)]  # 0-18

        vars_dict["two_diff_mode"] = tk.IntVar(value=1)
        vars_dict["two_diff"] = [tk.BooleanVar() for _ in range(10)]  # 0-9

        vars_dict["two_code_mode"] = tk.IntVar(value=1)
        two_codes = [f"{i:02d}" for i in range(100)]
        unique_codes = sorted(list({''.join(sorted(c)) for c in two_codes}))
        vars_dict["two_code_list"] = unique_codes
        vars_dict["two_code"] = [tk.BooleanVar() for _ in range(len(unique_codes))]

        # 012 路:5 位 3^5=243
        vars_dict["o12_mode"] = tk.IntVar(value=1)
        vars_dict["o12_list"] = O12_TYPES
        vars_dict["o12"] = [tk.BooleanVar() for _ in range(len(O12_TYPES))]

        # 和值:5 位 0-45
        vars_dict["sum_mode"] = tk.IntVar(value=1)
        vars_dict["sum_val"] = [tk.BooleanVar() for _ in range(46)]

        # 和尾:0-9
        vars_dict["sum_tail_mode"] = tk.IntVar(value=1)
        vars_dict["sum_tail"] = [tk.BooleanVar() for _ in range(10)]

        # 跨度:0-9
        vars_dict["span_mode"] = tk.IntVar(value=1)
        vars_dict["span"] = [tk.BooleanVar() for _ in range(10)]

        # 大中小:5 位 3^5=243
        vars_dict["sms_mode"] = tk.IntVar(value=1)
        vars_dict["sms_list"] = SMS_TYPES
        vars_dict["sms"] = [tk.BooleanVar() for _ in range(len(SMS_TYPES))]

        # 大小/奇偶/质合:5 位 2^5=32
        vars_dict["size_mode"] = tk.IntVar(value=1)
        vars_dict["size_list"] = SIZE_TYPES
        vars_dict["size"] = [tk.BooleanVar() for _ in range(len(SIZE_TYPES))]

        vars_dict["oe_mode"] = tk.IntVar(value=1)
        vars_dict["oe_list"] = OE_TYPES
        vars_dict["oe"] = [tk.BooleanVar() for _ in range(len(OE_TYPES))]

        vars_dict["pc_mode"] = tk.IntVar(value=1)
        vars_dict["pc_list"] = PC_TYPES
        vars_dict["pc"] = [tk.BooleanVar() for _ in range(len(PC_TYPES))]

        vars_dict["straight_mode"] = tk.IntVar(value=0)

        # 号码组:最多 5 组,每组出现次数 0-5
        vars_dict["number_group"] = []
        for _ in range(5):
            vars_dict["number_group"].append({
                "nums": [tk.BooleanVar() for _ in range(10)],
                "count": tk.StringVar(value="0")
            })

        return vars_dict

    def _build_filter_ui(self):
        self._add_section_title("1. 定位选择（可选，勾选为选中号码，未勾选则不限制该位）")
        pos_container = tk.Frame(self.filter_content, bg="white")
        pos_container.pack(fill=tk.X, padx=10, pady=5)

        for pos in POS_KEYS:
            self._add_position_row(pos_container, pos)

        self._add_section_title("2. 直选定位（每行一个组合，格式：万位,千位,百位,十位,个位，数字无需空格分隔）")
        direct_pos_frame = tk.Frame(self.filter_content, bg="white")
        direct_pos_frame.pack(fill=tk.X, padx=10, pady=5)

        mode_frame = tk.Frame(direct_pos_frame, bg="white")
        mode_frame.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(mode_frame, text="包含选中", variable=self.filter_vars["direct_pos_mode"], value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="排除选中", variable=self.filter_vars["direct_pos_mode"], value=0).pack(side=tk.LEFT, padx=5)

        input_frame = tk.Frame(direct_pos_frame, bg="white")
        input_frame.pack(fill=tk.X, pady=2)
        tk.Label(input_frame, text="输入示例：\n13579,24680,13579\n01234,56789\n1,2,3,4,5", bg="white", justify=tk.LEFT).pack(side=tk.LEFT, padx=5)
        self.direct_pos_text = tk.Text(input_frame, width=60, height=5, font=("Arial", 10))
        self.direct_pos_text.pack(side=tk.LEFT, padx=5)

        self._add_section_title("3. 非定位直选（每行一个五位数字，匹配所有排列，顺序不限）")
        non_pos_direct_frame = tk.Frame(self.filter_content, bg="white")
        non_pos_direct_frame.pack(fill=tk.X, padx=10, pady=5)

        non_pos_mode_frame = tk.Frame(non_pos_direct_frame, bg="white")
        non_pos_mode_frame.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(non_pos_mode_frame, text="包含选中", variable=self.filter_vars["non_pos_direct_mode"], value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(non_pos_mode_frame, text="排除选中", variable=self.filter_vars["non_pos_direct_mode"], value=0).pack(side=tk.LEFT, padx=5)

        non_pos_input_frame = tk.Frame(non_pos_direct_frame, bg="white")
        non_pos_input_frame.pack(fill=tk.X, pady=2)
        tk.Label(non_pos_input_frame, text="输入示例：\n12345（匹配所有排列，共120种）\n11234（含重复，匹配60种）\n11123", bg="white", justify=tk.LEFT).pack(side=tk.LEFT, padx=5)
        self.non_pos_direct_text = tk.Text(non_pos_input_frame, width=60, height=5, font=("Arial", 10))
        self.non_pos_direct_text.pack(side=tk.LEFT, padx=5)

        self._add_section_title("4. 杀号过滤（可选，勾选为排除号码）")
        kill_frame = ttk.Frame(self.filter_content)
        kill_frame.pack(fill=tk.X, padx=10, pady=5)
        for pos in POS_KEYS:
            self._add_digit_checkgroup(kill_frame, POS_NAMES[pos], self.filter_vars["kill"][pos])
        self._add_select_all_clear_buttons(kill_frame, self.filter_vars["kill"])

        self._add_section_title("5. 胆码过滤（可选，勾选为必含号码）")
        dan_frame = ttk.Frame(self.filter_content)
        dan_frame.pack(fill=tk.X, padx=10, pady=5)
        for pos in POS_KEYS:
            self._add_digit_checkgroup(dan_frame, POS_NAMES[pos], self.filter_vars["dan"][pos])
        self._add_select_all_clear_buttons(dan_frame, self.filter_vars["dan"])

        self._add_section_title("6. 二码和过滤（0-18，勾选为目标和值，5位共10对两两组合）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["two_sum_mode"], self.filter_vars["two_sum"], list(range(19)), cols=10)

        self._add_section_title("7. 二码差过滤（0-9，勾选为目标差）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["two_diff_mode"], self.filter_vars["two_diff"], list(range(10)), cols=10)

        self._add_section_title("8. 二码过滤（勾选为目标二码）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["two_code_mode"], self.filter_vars["two_code"], self.filter_vars["two_code_list"], cols=10)

        self._add_section_title("9. 012路过滤（5位共243种形态，勾选为目标形态）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["o12_mode"], self.filter_vars["o12"], self.filter_vars["o12_list"], cols=12)

        self._add_section_title("10. 和值过滤（0-45，勾选为目标和值）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["sum_mode"], self.filter_vars["sum_val"], list(range(46)), cols=12)

        self._add_section_title("11. 和尾过滤（0-9，勾选为目标和尾）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["sum_tail_mode"], self.filter_vars["sum_tail"], list(range(10)), cols=10)

        self._add_section_title("12. 跨度过滤（0-9，勾选为目标跨度）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["span_mode"], self.filter_vars["span"], list(range(10)), cols=10)

        self._add_section_title("13. 大中小过滤（小=0-2，中=3-6，大=7-9，5位共243种形态）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["sms_mode"], self.filter_vars["sms"], self.filter_vars["sms_list"], cols=12)

        self._add_section_title("14. 大小过滤（小=0-4，大=5-9，5位共32种形态）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["size_mode"], self.filter_vars["size"], self.filter_vars["size_list"], cols=8)

        self._add_section_title("15. 奇偶过滤（奇=13579，偶=02468，5位共32种形态）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["oe_mode"], self.filter_vars["oe"], self.filter_vars["oe_list"], cols=8)

        self._add_section_title("16. 质合过滤（质=12357，合=04689，5位共32种形态）")
        self._add_mode_checkgroup(self.filter_content, self.filter_vars["pc_mode"], self.filter_vars["pc"], self.filter_vars["pc_list"], cols=8)

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
            tk.Label(group_frame, text="（0-5）", bg="white").pack(side=tk.LEFT)

    def _add_position_row(self, parent, pos):
        """添加一行定位选择(万/千/百/十/个)"""
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.X, pady=2)
        tk.Label(frame, text=f"{POS_NAMES[pos]}：", bg="white", width=8).pack(side=tk.LEFT)
        digit_frame = tk.Frame(frame, bg="white")
        digit_frame.pack(side=tk.LEFT)
        for i in range(10):
            tk.Checkbutton(digit_frame, variable=self.filter_vars["pos"][pos][i], text=str(i), bg="white").grid(row=0, column=i)
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="全选", command=lambda p=pos: self._select_single_pos(p, True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="取消", command=lambda p=pos: self._select_single_pos(p, False)).pack(side=tk.LEFT, padx=2)

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
        for pos in POS_KEYS:
            for var in var_dict[pos]:
                var.set(state)

    def _add_mode_checkgroup(self, parent, mode_var, var_list, item_list, cols=10):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)
        mode_frame = tk.Frame(frame)
        mode_frame.pack(side=tk.TOP, padx=5)
        ttk.Radiobutton(mode_frame, text="排除选中", variable=mode_var, value=0).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="包含选中", variable=mode_var, value=1).pack(side=tk.LEFT, padx=5)
        item_frame = tk.Frame(frame, bg="white")
        item_frame.pack(side=tk.TOP, padx=5, pady=5)
        for idx, (item, var) in enumerate(zip(item_list, var_list)):
            row = idx // cols
            col = idx % cols
            tk.Checkbutton(item_frame, variable=var, text=str(item), bg="white").grid(row=row, column=col, padx=2, pady=2)
        btn_frame = tk.Frame(frame)
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

            final_nums = nums
            self._log(f"\n最终直选号码数：{len(final_nums)}注")

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
            pos: {str(i) for i, var in enumerate(self.filter_vars["pos"][pos]) if var.get()}
            for pos in POS_KEYS
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
            pos: {str(i) for i, var in enumerate(self.filter_vars["kill"][pos]) if var.get()}
            for pos in POS_KEYS
        }

        filters["dan"] = {
            pos: {str(i) for i, var in enumerate(self.filter_vars["dan"][pos]) if var.get()}
            for pos in POS_KEYS
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
            count = int(count_str) if count_str.isdigit() and 0 <= int(count_str) <= 5 else 0
            filters["number_group"].append((nums, count))

        return filters

    def _parse_direct_pos_single(self, line):
        """解析单行直选定位，格式：万位,千位,百位,十位,个位"""
        line = line.strip()
        if not line:
            return []
        parts = line.split(',')
        if len(parts) != 5:
            return []
        valid_parts = []
        for p in parts:
            chars = list(p.strip())
            valid = [d for d in chars if d.isdigit() and 0 <= int(d) <= 9]
            if not valid:
                return []
            valid_parts.append(valid)
        return list(set([''.join(combo) for combo in itertools.product(*valid_parts)]))

    def _parse_direct_pos_multi(self, input_content):
        all_combines = []
        lines = input_content.splitlines()
        for line in lines:
            line_combines = self._parse_direct_pos_single(line)
            all_combines.extend(line_combines)
        return list(set(all_combines))

    def _parse_non_pos_direct_single(self, line):
        """非定位直选：5位数字，匹配所有排列"""
        line = line.strip()
        if len(line) != 5 or not line.isdigit():
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

    def _generate_all_direct(self):
        """生成全部排列5直选号码：00000-99999，共100000注"""
        return [f"{i:05d}" for i in range(100000)]

    def _filter_position(self, numbers, pos):
        filtered = []
        for num in numbers:
            digits = list(num)
            ok = True
            for i, pkey in enumerate(POS_KEYS):
                cond = (not pos[pkey]) or (digits[i] in pos[pkey])
                if not cond:
                    ok = False
                    break
            if ok:
                filtered.append(num)
        return filtered

    def _filter_kill(self, numbers, kill):
        filtered = []
        for num in numbers:
            digits = list(num)
            ok = True
            for i, pkey in enumerate(POS_KEYS):
                if digits[i] in kill[pkey]:
                    ok = False
                    break
            if ok:
                filtered.append(num)
        return filtered

    def _filter_dan(self, numbers, dan):
        filtered = []
        for num in numbers:
            digits = list(num)
            ok = True
            for i, pkey in enumerate(POS_KEYS):
                cond = (not dan[pkey]) or (digits[i] in dan[pkey])
                if not cond:
                    ok = False
                    break
            if ok:
                filtered.append(num)
        return filtered

    def _get_two_sums(self, num):
        """5位两两组合的和集合，共C(5,2)=10对"""
        digits = list(map(int, num))
        return {a + b for a, b in itertools.combinations(digits, 2)}

    def _filter_two_sum(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_sums = self._get_two_sums(num)
            if (mode == 1 and num_sums & selected) or (mode == 0 and not num_sums & selected):
                filtered.append(num)
        return filtered

    def _get_two_diffs(self, num):
        """5位两两组合的差集合"""
        digits = list(map(int, num))
        return {abs(a - b) for a, b in itertools.combinations(digits, 2)}

    def _filter_two_diff(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_diffs = self._get_two_diffs(num)
            if (mode == 1 and num_diffs & selected) or (mode == 0 and not num_diffs & selected):
                filtered.append(num)
        return filtered

    def _get_two_codes(self, num):
        """5位两两组合的无序二码集合"""
        digits = list(num)
        return {''.join(sorted(pair)) for pair in itertools.combinations(digits, 2)}

    def _filter_two_code(self, numbers, mode, selected):
        if not selected:
            return numbers
        filtered = []
        for num in numbers:
            num_codes = self._get_two_codes(num)
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
        """5位顺子判定：5个数字排序后连续，或包含特殊 0/9 连号"""
        digits = sorted(map(int, num))
        # 标准顺子：相邻差1
        if all(digits[i + 1] - digits[i] == 1 for i in range(len(digits) - 1)):
            return True
        # 含 0-9 环形连号：0 和 9 视为相连，即排序后形如 [0, 1, 2, 3, 9] 之类
        # 把 9 视作 -1 重新排序判定
        digits_alt = sorted(-1 if d == 9 else d for d in digits)
        if all(digits_alt[i + 1] - digits_alt[i] == 1 for i in range(len(digits_alt) - 1)):
            return True
        return False

    def _is_semi_straight(self, num):
        """5位半顺子判定：存在任意两位数字相差1或9(环形相邻)"""
        digits = list(map(int, num))
        for a, b in itertools.combinations(digits, 2):
            diff = abs(a - b)
            if diff == 1 or diff == 9:
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
        for pos in POS_KEYS:
            for var in self.filter_vars["pos"][pos]:
                var.set(False)

        if self.direct_pos_text:
            self.direct_pos_text.delete(1.0, tk.END)
        self.filter_vars["direct_pos_mode"].set(1)

        if self.non_pos_direct_text:
            self.non_pos_direct_text.delete(1.0, tk.END)
        self.filter_vars["non_pos_direct_mode"].set(1)

        for pos in POS_KEYS:
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

        self.result_text.delete(1.0, tk.END)

    def show_help(self):
        help_text = """
排列5缩水工具使用说明：

【基本玩法】排列5为5位数字直选玩法，每位0-9，共100000注。

1. 定位选择：勾选万/千/百/十/个各位的可选数字，未勾选则不限制该位（每个位置单独全选/取消）

2. 直选定位：多行输入，每行一个组合，格式为「万位,千位,百位,十位,个位」，数字无需空格分隔
   示例：
   13579,24680,13579,24680,13579（万位1/3/5/7/9，千位2/4/6/8/0...）
   01234,56789,01234,56789,01234
   1,2,3,4,5（每位置单个数字）
   模式：
   - 包含选中：仅保留所有行组合内的号码；
   - 排除选中：移除所有行组合内的号码。

3. 非定位直选：每行一个5位数字，匹配该数字的所有排列（顺序不限）
   示例：12345（匹配全部120种排列）
         11234（含重复数字，匹配60种）

4. 杀号过滤：勾选需要排除的数字（该位不会出现勾选数字）

5. 胆码过滤：勾选必须包含的数字（该位必须是勾选数字）

6. 二码和过滤：5位两两组合(C(5,2)=10对)求和，目标和值范围0-18
   二码差过滤：5位两两组合求绝对差，目标差范围0-9
   二码过滤：5位两两组合生成无序二码(00-99)，匹配勾选二码

7. 012路：每位数字%3的余数组合（0/1/2），5位共3^5=243种形态

8. 和值：五位数字之和（0-45），和尾：和值的个位数（0-9）

9. 跨度：最大数-最小数（0-9）

10. 大中小：小=0-2，中=3-6，大=7-9，5位共3^5=243种形态
    大小：小=0-4，大=5-9，5位共2^5=32种形态

11. 奇偶：奇=13579，偶=02468，5位共2^5=32种形态
    质合：质=12357，合=04689，5位共2^5=32种形态

12. 顺子过滤：
    顺子=5位数排序后连续连号（如12345、01239 视为环形连号）
    半顺子=任意两位数相差1或9（如12578）

13. 号码组：最多5组，每组勾选胆码，输入需要出现的次数（0-5）

注意事项：
- 排列5总注数达100000注，过滤条件较多时可显著缩小范围
- 彩票开奖为随机事件，本工具仅为号码筛选，不保证中奖
- 输入非法内容会自动忽略，请按提示格式输入
        """
        showinfo("使用说明", help_text)
