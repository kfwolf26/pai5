import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.messagebox import showwarning, showinfo, askyesno
from datetime import datetime
from utils.history_manager import HistoryManager


class HistoryQuery:
    def __init__(self, parent):
        self.parent = parent
        self.history_manager = HistoryManager()

        self._build_ui()

    def _build_ui(self):
        add_frame = ttk.LabelFrame(self.parent, text="添加开奖记录", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=10)

        row1 = ttk.Frame(add_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="期号：").pack(side=tk.LEFT, padx=5)
        self.history_issue_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.history_issue_var, width=15).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="开奖号码：").pack(side=tk.LEFT, padx=5)
        self.history_number_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.history_number_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="(五位数字，如 12345)").pack(side=tk.LEFT)

        ttk.Label(row1, text="日期：").pack(side=tk.LEFT, padx=5)
        self.history_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(row1, textvariable=self.history_date_var, width=12).pack(side=tk.LEFT, padx=5)

        btn_row = ttk.Frame(add_frame)
        btn_row.pack(fill=tk.X, pady=5)
        tk.Button(btn_row, text="  ➕ 添加记录  ", bg="#5cb85c", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._add_history_record).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_row, text="  📥 批量导入  ", bg="#5bc0de", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._batch_import_history).pack(side=tk.LEFT, padx=6)

        search_frame = ttk.LabelFrame(self.parent, text="搜索查询", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X, pady=5)

        ttk.Label(search_row, text="搜索号码：").pack(side=tk.LEFT, padx=5)
        self.search_number_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.search_number_var, width=10).pack(side=tk.LEFT, padx=5)

        ttk.Label(search_row, text="期号范围：").pack(side=tk.LEFT, padx=5)
        self.search_issue_start_var = tk.StringVar()
        self.search_issue_end_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.search_issue_start_var, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(search_row, text="-").pack(side=tk.LEFT)
        ttk.Entry(search_row, textvariable=self.search_issue_end_var, width=10).pack(side=tk.LEFT, padx=2)

        ttk.Label(search_row, text="按年查询：").pack(side=tk.LEFT, padx=5)
        self.search_year_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.search_year_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(search_row, text="(如 2024)").pack(side=tk.LEFT)

        tk.Button(search_row, text="  🔍 搜索  ", bg="#337ab7", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._search_history).pack(side=tk.LEFT, padx=10)
        tk.Button(search_row, text="  📋 显示全部  ", bg="#f0ad4e", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._show_all_history).pack(side=tk.LEFT, padx=6)
        tk.Button(search_row, text="  📊 统计分析  ", bg="#5bc0de", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._analyze_history).pack(side=tk.LEFT, padx=6)

        list_frame = ttk.LabelFrame(self.parent, text="历史记录", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("期号", "开奖号码", "日期", "和值", "跨度", "形态")
        self.history_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100, anchor="center")

        self.history_tree.column("期号", width=120)
        self.history_tree.column("开奖号码", width=120)
        self.history_tree.column("日期", width=120)

        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=tree_scroll.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        del_btn_frame = ttk.Frame(list_frame)
        del_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(del_btn_frame, text="  🗑 删除选中  ", bg="#d9534f", fg="white",
                  relief=tk.RAISED, padx=5, pady=2, font=("微软雅黑", 9),
                  command=self._delete_history_record).pack(side=tk.LEFT, padx=6)
        tk.Button(del_btn_frame, text="  ⚠ 清空全部  ", bg="#777", fg="white",
                  relief=tk.RAISED, padx=5, pady=2, font=("微软雅黑", 9),
                  command=self._clear_all_history).pack(side=tk.LEFT, padx=6)

        self._refresh_history_list()

    def _get_number_form(self, digits):
        """
        排列5 形态分类（按数字重复结构）。
        digits: list[int]，长度5
        返回形如 "五同"、"四同+单"、"葫芦(3+2)"、"三同+单+单"、"两对+单"、"一对+三单"、"五不同" 的形态名
        """
        from collections import Counter
        counts = sorted(Counter(digits).values(), reverse=True)
        if counts == [5]:
            return "五同"
        if counts == [4, 1]:
            return "四同+单"
        if counts == [3, 2]:
            return "葫芦(3+2)"
        if counts == [3, 1, 1]:
            return "三同+单+单"
        if counts == [2, 2, 1]:
            return "两对+单"
        if counts == [2, 1, 1, 1]:
            return "一对+三单"
        if counts == [1, 1, 1, 1, 1]:
            return "五不同"
        return "其他"

    def _normalize_pl5_number(self, raw_number: str):
        """
        排列5 号码标准化（解决前导0、短数字、全非数字问题）。
        规则：
          1. 去两端空格
          2. 必须全部为数字
          3. 长度 1-5 → 左补 0 到 5 位（自动补前导0，用户输入 1234 → 01234、1 → 00001）
          4. 长度 > 5 → 非法
        返回 (normalized_number: str | None, warn_msg: str | None)
        """
        n = (raw_number or "").strip()
        if not n:
            return None, "请输入开奖号码"
        if not n.isdigit():
            return None, "开奖号码必须是数字"
        if len(n) > 5:
            return None, "开奖号码最多 5 位数字"
        normalized = n.zfill(5)
        warn = None
        if len(n) < 5:
            warn = f"输入 {len(n)} 位数字，已自动左补 0 为 {normalized}"
        return normalized, warn

    def _add_history_record(self):
        issue = self.history_issue_var.get().strip()
        raw_number = self.history_number_var.get()
        date = self.history_date_var.get().strip()

        if not issue:
            showwarning("提示", "请输入期号")
            return

        number, warn = self._normalize_pl5_number(raw_number)
        if number is None:
            showwarning("提示", warn or "请输入有效的开奖号码")
            return

        digits = list(map(int, number))
        sum_val = sum(digits)
        span = max(digits) - min(digits)
        num_type = self._get_number_form(digits)

        record = {
            "issue": issue,
            "number": number,
            "date": date,
            "sum": sum_val,
            "span": span,
            "type": num_type
        }

        success, msg = self.history_manager.add_record(record)
        if success:
            self._refresh_history_list()
            self.history_issue_var.set("")
            self.history_number_var.set("")
            tip = f"已添加期号 {issue} 的开奖记录：{number}"
            if warn:
                tip = f"[注意] {warn}\n{tip}"
                showinfo("成功（已自动补前导0）", tip)
            else:
                showinfo("成功", tip)
        else:
            showwarning("提示", msg)

    def _batch_import_history(self):
        import_window = tk.Toplevel(self.parent)
        import_window.title("批量导入开奖历史")
        import_window.geometry("500x400")

        ttk.Label(import_window, text="请输入多行开奖记录，每行格式：期号,号码,日期", font=("Arial", 10)).pack(pady=10)
        ttk.Label(import_window, text="示例：2024001,12345,2024-01-01 或 2024002,01234", foreground="gray").pack()
        ttk.Label(import_window, text="排列5每位0-9独立，号码不足5位会自动左补0（如 123 → 00123）",
                  foreground="#1976d2").pack()

        import_text = scrolledtext.ScrolledText(import_window, width=50, height=15, font=("Arial", 10))
        import_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def do_import():
            content = import_text.get(1.0, tk.END).strip()
            if not content:
                showwarning("提示", "请输入要导入的记录")
                return

            lines = content.splitlines()
            records = []
            padded_count = 0
            invalid_count = 0
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    issue = parts[0].strip()
                    raw_number = parts[1].strip()
                    date = parts[2].strip() if len(parts) > 2 else datetime.now().strftime("%Y-%m-%d")
                    number, warn = self._normalize_pl5_number(raw_number)
                    if number is None:
                        invalid_count += 1
                        continue
                    if warn:
                        padded_count += 1
                    digits = list(map(int, number))
                    record = {
                        "issue": issue,
                        "number": number,
                        "date": date,
                        "sum": sum(digits),
                        "span": max(digits) - min(digits),
                        "type": self._get_number_form(digits)
                    }
                    records.append(record)

            added_count = self.history_manager.batch_add(records)
            if added_count > 0:
                self._refresh_history_list()
                msg = f"成功导入 {added_count} 条记录"
                if padded_count or invalid_count:
                    msg += f"\n其中自动补前导0：{padded_count} 条；忽略无效号码：{invalid_count} 条"
                showinfo("成功", msg)
                import_window.destroy()
            else:
                msg = "没有有效记录被导入"
                if padded_count or invalid_count:
                    msg += f"（自动补前导0：{padded_count} 条；无效号码：{invalid_count} 条）"
                showwarning("提示", msg)

        ttk.Button(import_window, text="导入", command=do_import).pack(pady=10)

    def _delete_history_record(self):
        selected = self.history_tree.selection()
        if not selected:
            showwarning("提示", "请先选中要删除的记录")
            return

        if askyesno("确认", "确定要删除选中的记录吗？"):
            for item in selected:
                issue = self.history_tree.item(item)["values"][0]
                self.history_manager.delete_record(issue)
            self._refresh_history_list()
            showinfo("成功", "已删除选中记录")

    def _clear_all_history(self):
        if not self.history_manager.get_all():
            showwarning("提示", "历史记录已为空")
            return

        if askyesno("确认", "确定要清空全部历史记录吗？此操作不可恢复！"):
            self.history_manager.clear_all()
            self._refresh_history_list()
            showinfo("成功", "已清空全部历史记录")

    def _search_history(self):
        search_number = self.search_number_var.get().strip()
        issue_start = self.search_issue_start_var.get().strip()
        issue_end = self.search_issue_end_var.get().strip()
        search_year = self.search_year_var.get().strip()

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for record in self.history_manager.get_all():
            match = True

            if search_number:
                # 搜索号码标准化：如果是纯数字 1-5 位，自动 zfill(5) 先做精确/组选匹配；
                # 若不是纯数字或>5位，按"包含子串"模糊匹配（用户可输入 012、01 这样的片段）。
                sn = search_number
                if sn.isdigit() and len(sn) <= 5:
                    exact = sn.zfill(5)
                    if record["number"] == exact:
                        pass  # 精确匹配命中
                    else:
                        sorted_search = ''.join(sorted(exact))
                        sorted_record = ''.join(sorted(record["number"]))
                        if sorted_search == sorted_record:
                            pass  # 组选匹配命中（数字集合相同，顺序不同）
                        else:
                            # 最后降级：包含子串（比如 1234 搜 01234）
                            if sn not in record["number"] and exact not in record["number"]:
                                match = False
                else:
                    # 非纯数字搜索：作为字符串子串包含匹配
                    if sn not in record["number"]:
                        match = False

            if issue_start and record["issue"] < issue_start:
                match = False
            if issue_end and record["issue"] > issue_end:
                match = False

            if search_year:
                issue_year = record["issue"][:4]
                if issue_year != search_year:
                    match = False

            if match:
                self.history_tree.insert("", tk.END, values=(
                    record["issue"],
                    record["number"],
                    record["date"],
                    record["sum"],
                    record["span"],
                    record["type"]
                ))

    def _show_all_history(self):
        self.search_number_var.set("")
        self.search_issue_start_var.set("")
        self.search_issue_end_var.set("")
        self.search_year_var.set("")
        self._refresh_history_list()

    def _refresh_history_list(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for record in self.history_manager.get_all():
            self.history_tree.insert("", tk.END, values=(
                record["issue"],
                record["number"],
                record["date"],
                record["sum"],
                record["span"],
                record["type"]
            ))

    def _analyze_history(self):
        if not self.history_manager.get_all():
            showwarning("提示", "暂无历史数据，请先添加开奖记录")
            return

        analyze_window = tk.Toplevel(self.parent)
        analyze_window.title("历史数据分析")
        analyze_window.geometry("650x600")

        range_frame = ttk.LabelFrame(analyze_window, text="统计范围", padding=10)
        range_frame.pack(fill=tk.X, padx=10, pady=10)

        range_row = ttk.Frame(range_frame)
        range_row.pack(fill=tk.X, pady=5)

        ttk.Label(range_row, text="期号范围：").pack(side=tk.LEFT, padx=5)
        analyze_issue_start_var = tk.StringVar()
        analyze_issue_end_var = tk.StringVar()
        ttk.Entry(range_row, textvariable=analyze_issue_start_var, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(range_row, text="-").pack(side=tk.LEFT)
        ttk.Entry(range_row, textvariable=analyze_issue_end_var, width=12).pack(side=tk.LEFT, padx=2)

        ttk.Label(range_row, text="按年统计：").pack(side=tk.LEFT, padx=10)
        analyze_year_var = tk.StringVar()
        ttk.Entry(range_row, textvariable=analyze_year_var, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(range_row, text="(如 2024)").pack(side=tk.LEFT)

        def do_analyze():
            issue_start = analyze_issue_start_var.get().strip()
            issue_end = analyze_issue_end_var.get().strip()
            analyze_year = analyze_year_var.get().strip()

            filtered_data = self.history_manager.get_all().copy()

            if issue_start:
                filtered_data = [r for r in filtered_data if r["issue"] >= issue_start]
            if issue_end:
                filtered_data = [r for r in filtered_data if r["issue"] <= issue_end]
            if analyze_year:
                filtered_data = [r for r in filtered_data if r["issue"][:4] == analyze_year]

            if not filtered_data:
                showwarning("提示", "没有符合条件的数据")
                return

            total_count = len(filtered_data)

            pos_names = ["万位", "千位", "百位", "十位", "个位"]
            pos_freqs = [{str(i): 0 for i in range(10)} for _ in range(5)]

            sum_freq = {}
            span_freq = {}
            type_freq = {}
            num_freq = {}

            for record in filtered_data:
                number = record["number"]
                for i in range(5):
                    d = number[i]
                    pos_freqs[i][d] = pos_freqs[i].get(d, 0) + 1

                sum_val = record["sum"]
                sum_freq[sum_val] = sum_freq.get(sum_val, 0) + 1

                span_val = record["span"]
                span_freq[span_val] = span_freq.get(span_val, 0) + 1

                t = record["type"]
                type_freq[t] = type_freq.get(t, 0) + 1

                num_freq[number] = num_freq.get(number, 0) + 1

            result_text.delete(1.0, tk.END)

            result_text.insert(tk.END, "=" * 60 + "\n")
            range_desc = "全部"
            if issue_start or issue_end:
                range_desc = f"{issue_start or '开始'} ~ {issue_end or '结束'}"
            if analyze_year:
                range_desc = f"{analyze_year}年"
            result_text.insert(tk.END, f"历史数据统计分析（范围：{range_desc}，共 {total_count} 期）\n")
            result_text.insert(tk.END, "=" * 60 + "\n\n")

            result_text.insert(tk.END, "【各位数字出现频率】\n")
            for i, name in enumerate(pos_names):
                result_text.insert(tk.END, f"{name}：")
                for d in range(10):
                    pct = pos_freqs[i][str(d)] / total_count * 100 if total_count > 0 else 0
                    result_text.insert(tk.END, f"{d}({pct:.1f}%) ")
                result_text.insert(tk.END, "\n")
            result_text.insert(tk.END, "\n")

            result_text.insert(tk.END, "【号码形态统计】\n")
            for t, count in sorted(type_freq.items(), key=lambda x: -x[1]):
                pct = count / total_count * 100 if total_count > 0 else 0
                result_text.insert(tk.END, f"{t}：{count} 次 ({pct:.1f}%)\n")
            result_text.insert(tk.END, "\n")

            result_text.insert(tk.END, "【和值分布（前10高频）】\n")
            sorted_sum = sorted(sum_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            for sum_val, count in sorted_sum:
                pct = count / total_count * 100 if total_count > 0 else 0
                result_text.insert(tk.END, f"和值 {sum_val}：{count} 次 ({pct:.1f}%)\n")
            result_text.insert(tk.END, "\n")

            result_text.insert(tk.END, "【跨度分布】\n")
            for span_val in range(10):
                count = span_freq.get(span_val, 0)
                pct = count / total_count * 100 if total_count > 0 else 0
                result_text.insert(tk.END, f"跨度 {span_val}：{count} 次 ({pct:.1f}%)\n")
            result_text.insert(tk.END, "\n")

            result_text.insert(tk.END, "【热门号码（出现次数≥2）】\n")
            hot_nums = sorted(num_freq.items(), key=lambda x: x[1], reverse=True)
            hot_nums = [x for x in hot_nums if x[1] >= 2]
            if hot_nums:
                for num, count in hot_nums[:20]:
                    result_text.insert(tk.END, f"{num}：{count} 次\n")
            else:
                result_text.insert(tk.END, "暂无重复出现的号码\n")

            result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
            result_text.insert(tk.END, "分析完成！\n")

        ttk.Button(range_row, text="开始统计", command=do_analyze).pack(side=tk.RIGHT, padx=10)

        result_frame = ttk.Frame(analyze_window, padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        result_text = scrolledtext.ScrolledText(result_frame, width=75, height=28, font=("Arial", 10))
        result_text.pack(fill=tk.BOTH, expand=True)

        do_analyze()
