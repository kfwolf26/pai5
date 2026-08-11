import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import random
import threading
from utils.history_manager import HistoryManager


class PredictionModel:
    def __init__(self, parent):
        self.parent = parent
        self.root = parent.winfo_toplevel()
        self.history_manager = HistoryManager()
        self.prediction_data = {}
        self.prediction_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prediction_data.json"
        )
        self.saved_predictions_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "saved_predictions.json"
        )
        self.saved_predictions = []
        self.status_var = tk.StringVar(value="")
        
        self._load_prediction_data()
        self._load_saved_predictions()
        self._build_ui()
    
    def _load_prediction_data(self):
        if os.path.exists(self.prediction_file):
            try:
                with open(self.prediction_file, 'r', encoding='utf-8') as f:
                    self.prediction_data = json.load(f)
            except:
                self.prediction_data = {}
    
    def _save_prediction_data(self):
        try:
            with open(self.prediction_file, 'w', encoding='utf-8') as f:
                json.dump(self.prediction_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
    
    def _load_saved_predictions(self):
        if os.path.exists(self.saved_predictions_file):
            try:
                with open(self.saved_predictions_file, 'r', encoding='utf-8') as f:
                    self.saved_predictions = json.load(f)
            except:
                self.saved_predictions = []
        else:
            self.saved_predictions = []
    
    def _save_saved_predictions(self):
        try:
            with open(self.saved_predictions_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_predictions, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
    
    def _refresh_saved_list(self):
        total = len(self.saved_predictions)
        opened = len([r for r in self.saved_predictions if r.get("result")])
        pending = total - opened
        self.stats_label.config(text=f"已保存 {total} 期预测记录（已开奖 {opened} 期，待开奖 {pending} 期），点击\"预测对错统计\"查看详情")
    
    def _save_remain_numbers(self):
        issue = self.save_issue_var.get().strip()
        if not issue:
            messagebox.showerror("错误", "请输入期号")
            return
        
        predictions = self.prediction_data.get("predictions", {})
        params = self.prediction_data.get("params", {})
        next_issue = params.get("next_issue", "")
        
        bai_remain = []
        shi_remain = []
        ge_remain = []
        
        if next_issue and next_issue in predictions:
            positions = [("bai", 0), ("shi", 1), ("ge", 2)]
            pos_names = {"bai": "百", "shi": "十", "ge": "个"}
            kill_sets = {"bai": set(), "shi": set(), "ge": set()}
            
            min_streak = params.get("min_streak", 3)
            predictor_count = params.get("predictor_count", 0)
            predict_count = params.get("predict_count", 1)
            history_issues = sorted([k for k in predictions.keys() if k != next_issue], reverse=True)
            
            for pos_key, _ in positions:
                for pid in range(predictor_count):
                    for seq in range(predict_count):
                        streak = 0
                        for hist_issue in history_issues:
                            pred_data = predictions[hist_issue]
                            result_num = pred_data["result"]
                            predictors = pred_data["predictors"]
                            if pid < len(predictors):
                                pred = predictors[pid]
                                if seq < len(pred[pos_key]):
                                    pred_num = pred[pos_key][seq]
                                    result_pos = int(result_num[0]) if pos_key == "bai" else int(result_num[1]) if pos_key == "shi" else int(result_num[2])
                                    if pred_num == result_pos:
                                        streak += 1
                                    else:
                                        break
                                else:
                                    break
                            else:
                                break
                        if streak >= min_streak:
                            next_predictors = predictions[next_issue]["predictors"]
                            if pid < len(next_predictors):
                                next_pred = next_predictors[pid]
                                if seq < len(next_pred[pos_key]):
                                    kill_sets[pos_key].add(next_pred[pos_key][seq])
            
            bai_remain = sorted(set(range(10)) - kill_sets["bai"])
            shi_remain = sorted(set(range(10)) - kill_sets["shi"])
            ge_remain = sorted(set(range(10)) - kill_sets["ge"])
        else:
            bai_remain = list(range(10))
            shi_remain = list(range(10))
            ge_remain = list(range(10))
        
        history = self.history_manager.get_all()
        history_map = {str(h["issue"]): h["number"] for h in history}
        result = history_map.get(issue, "")
        
        hit_pos = []
        if result:
            bai_result = int(result[0])
            shi_result = int(result[1])
            ge_result = int(result[2])
            if bai_result in bai_remain:
                hit_pos.append("百")
            if shi_result in shi_remain:
                hit_pos.append("十")
            if ge_result in ge_remain:
                hit_pos.append("个")
        
        for rec in self.saved_predictions:
            if rec["issue"] == issue:
                messagebox.showwarning("提示", f"期号 {issue} 已存在，请勿重复保存")
                return
        
        new_record = {
            "issue": issue,
            "bai_remain": bai_remain,
            "shi_remain": shi_remain,
            "ge_remain": ge_remain,
            "result": result,
            "hit_pos": hit_pos
        }
        self.saved_predictions.append(new_record)
        self.saved_predictions.sort(key=lambda x: x["issue"])
        self._save_saved_predictions()
        self._refresh_saved_list()
        messagebox.showinfo("成功", f"期号 {issue} 的剩余号码已保存")
    
    def _refresh_results(self):
        if not self.saved_predictions:
            messagebox.showinfo("提示", "暂无保存的预测记录")
            return
        
        history = self.history_manager.get_all()
        history_map = {str(h["issue"]): h["number"] for h in history}
        
        updated_count = 0
        for rec in self.saved_predictions:
            issue = rec["issue"]
            old_result = rec.get("result", "")
            new_result = history_map.get(issue, "")
            
            bai_remain = rec.get("bai_remain", [])
            shi_remain = rec.get("shi_remain", [])
            ge_remain = rec.get("ge_remain", [])
            
            if not new_result:
                if old_result:
                    rec["result"] = ""
                    rec["hit_pos"] = []
                    updated_count += 1
            elif old_result != new_result:
                rec["result"] = new_result
                hit_pos = []
                bai_result = int(new_result[0])
                shi_result = int(new_result[1])
                ge_result = int(new_result[2])
                if bai_result in bai_remain:
                    hit_pos.append("百")
                if shi_result in shi_remain:
                    hit_pos.append("十")
                if ge_result in ge_remain:
                    hit_pos.append("个")
                rec["hit_pos"] = hit_pos
                updated_count += 1
            elif not old_result and new_result:
                rec["result"] = new_result
                hit_pos = []
                bai_result = int(new_result[0])
                shi_result = int(new_result[1])
                ge_result = int(new_result[2])
                if bai_result in bai_remain:
                    hit_pos.append("百")
                if shi_result in shi_remain:
                    hit_pos.append("十")
                if ge_result in ge_remain:
                    hit_pos.append("个")
                rec["hit_pos"] = hit_pos
                updated_count += 1
        
        predictions_updated = 0
        if self.prediction_data and "predictions" in self.prediction_data:
            predictions = self.prediction_data["predictions"]
            for issue, pred_data in predictions.items():
                if pred_data.get("result", "") == "" and issue in history_map:
                    pred_data["result"] = history_map[issue]
                    predictions_updated += 1
            if predictions_updated > 0:
                self._save_prediction_data()
        
        if updated_count > 0:
            self._save_saved_predictions()
            self._refresh_saved_list()
            messagebox.showinfo("成功", f"已同步 {updated_count} 条记录（预测数据同步 {predictions_updated} 条）")
        else:
            messagebox.showinfo("提示", "数据已是最新，无需更新")
    
    def _calc_prediction_stats(self):
        if not self.saved_predictions:
            messagebox.showinfo("提示", "暂无保存的预测记录")
            return
        
        total = len([r for r in self.saved_predictions if r.get("result")])
        if total == 0:
            messagebox.showinfo("提示", "暂无已开奖的预测记录")
            return
        
        bai_hit = 0
        shi_hit = 0
        ge_hit = 0
        all_hit = 0
        two_hit = 0
        none_hit = 0
        
        for rec in self.saved_predictions:
            result = rec.get("result", "")
            if not result:
                continue
            hit_pos = rec.get("hit_pos", [])
            if "百" in hit_pos:
                bai_hit += 1
            if "十" in hit_pos:
                shi_hit += 1
            if "个" in hit_pos:
                ge_hit += 1
            if len(hit_pos) == 3:
                all_hit += 1
            elif len(hit_pos) == 2:
                two_hit += 1
            elif len(hit_pos) == 0:
                none_hit += 1
        
        bai_rate = f"{bai_hit/total*100:.1f}%"
        shi_rate = f"{shi_hit/total*100:.1f}%"
        ge_rate = f"{ge_hit/total*100:.1f}%"
        all_rate = f"{all_hit/total*100:.1f}%"
        two_rate = f"{two_hit/total*100:.1f}%"
        none_rate = f"{none_hit/total*100:.1f}%"
        
        stats_text = (f"已开奖 {total} 期 | "
                      f"百位命中 {bai_hit}/{total} ({bai_rate}) | "
                      f"十位命中 {shi_hit}/{total} ({shi_rate}) | "
                      f"个位命中 {ge_hit}/{total} ({ge_rate}) | "
                      f"三位全中 {all_hit}/{total} ({all_rate}) | "
                      f"两位命中 {two_hit}/{total} ({two_rate}) | "
                      f"全未中 {none_hit}/{total} ({none_rate})")
        self.stats_label.config(text=stats_text)
        
        top = tk.Toplevel(self.parent)
        top.title("预测对错统计")
        top.geometry("900x600")
        top.transient(self.parent)
        top.grab_set()
        
        summary_frame = ttk.LabelFrame(top, text="对错总览", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        row1 = ttk.Frame(summary_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text=f"总开奖期数：{total} 期", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Label(row1, text=f"三位全中：{all_hit} 期 ({all_rate})", foreground="#d32f2f", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Label(row1, text=f"两位命中：{two_hit} 期 ({two_rate})", foreground="#f57c00", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Label(row1, text=f"全未中：{none_hit} 期 ({none_rate})", foreground="#388e3c", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT, padx=10)
        
        row2 = ttk.Frame(summary_frame)
        row2.pack(fill=tk.X, pady=(8, 2))
        ttk.Label(row2, text=f"百位命中：{bai_hit}/{total} ({bai_rate})", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)
        ttk.Label(row2, text=f"十位命中：{shi_hit}/{total} ({shi_rate})", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)
        ttk.Label(row2, text=f"个位命中：{ge_hit}/{total} ({ge_rate})", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)
        
        list_frame = ttk.LabelFrame(top, text="详细记录", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ("issue", "bai_remain", "shi_remain", "ge_remain", "result", "bai", "shi", "ge")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        tree.heading("issue", text="期号")
        tree.heading("bai_remain", text="百位剩余")
        tree.heading("shi_remain", text="十位剩余")
        tree.heading("ge_remain", text="个位剩余")
        tree.heading("result", text="开奖号")
        tree.heading("bai", text="百")
        tree.heading("shi", text="十")
        tree.heading("ge", text="个")
        tree.column("issue", width=80, anchor=tk.CENTER)
        tree.column("bai_remain", width=100, anchor=tk.CENTER)
        tree.column("shi_remain", width=100, anchor=tk.CENTER)
        tree.column("ge_remain", width=100, anchor=tk.CENTER)
        tree.column("result", width=70, anchor=tk.CENTER)
        tree.column("bai", width=50, anchor=tk.CENTER)
        tree.column("shi", width=50, anchor=tk.CENTER)
        tree.column("ge", width=50, anchor=tk.CENTER)
        
        tree.tag_configure("all_hit", foreground="#d32f2f", font=("", 10, "bold"))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for rec in reversed(self.saved_predictions):
            issue = rec.get("issue", "")
            bai_remain = rec.get("bai_remain", [])
            shi_remain = rec.get("shi_remain", [])
            ge_remain = rec.get("ge_remain", [])
            result = rec.get("result", "待开奖")
            hit_pos = rec.get("hit_pos", [])
            
            tags = ()
            if result and result != "待开奖" and len(hit_pos) == 3:
                tags = ("all_hit",)
            
            bai_hit = "中" if "百" in hit_pos else ("错" if result and result != "待开奖" else "")
            shi_hit = "中" if "十" in hit_pos else ("错" if result and result != "待开奖" else "")
            ge_hit = "中" if "个" in hit_pos else ("错" if result and result != "待开奖" else "")
            
            tree.insert("", tk.END, values=(
                issue,
                " ".join(str(n) for n in bai_remain),
                " ".join(str(n) for n in shi_remain),
                " ".join(str(n) for n in ge_remain),
                result,
                bai_hit,
                shi_hit,
                ge_hit
            ), tags=tags)
    
    def _build_ui(self):
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        param_frame = ttk.LabelFrame(main_frame, text="参数设置", padding=8)
        param_frame.pack(fill=tk.X, pady=(0, 8))
        
        param_row = ttk.Frame(param_frame)
        param_row.pack(fill=tk.X)
        
        ttk.Label(param_row, text="预测者数量：").pack(side=tk.LEFT, padx=(5, 2), pady=5)
        self.predictor_count_var = tk.StringVar(value="5000")
        ttk.Entry(param_row, textvariable=self.predictor_count_var, width=10).pack(side=tk.LEFT, padx=(2, 10), pady=5)
        
        ttk.Label(param_row, text="每位置预测号码数：").pack(side=tk.LEFT, padx=2, pady=5)
        self.predict_count_var = tk.StringVar(value="1")
        ttk.Entry(param_row, textvariable=self.predict_count_var, width=8).pack(side=tk.LEFT, padx=(2, 10), pady=5)
        
        ttk.Label(param_row, text="最小连续命中期数：").pack(side=tk.LEFT, padx=2, pady=5)
        self.min_streak_var = tk.StringVar(value="3")
        ttk.Entry(param_row, textvariable=self.min_streak_var, width=8).pack(side=tk.LEFT, padx=(2, 10), pady=5)
        
        ttk.Label(param_row, text="预测期数：").pack(side=tk.LEFT, padx=2, pady=5)
        self.predict_periods_var = tk.StringVar(value="30")
        ttk.Entry(param_row, textvariable=self.predict_periods_var, width=8).pack(side=tk.LEFT, padx=(2, 10), pady=5)
        
        tk.Button(param_row, text="  🔄 应用参数并生成预测数据  ", bg="#5bc0de", fg="white",
                   relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                   command=self._generate_predictions).pack(side=tk.LEFT, padx=6, pady=8)

        self.btn_add_predict = tk.Button(param_row, text="  ➕ 补齐预测  ", bg="#f0ad4e", fg="white",
                   relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                   command=self._add_predictions)
        self.btn_add_predict.pack(side=tk.LEFT, padx=6, pady=8)
        
        query_frame = ttk.LabelFrame(main_frame, text="查询预测数据", padding=8)
        query_frame.pack(fill=tk.X, pady=(0, 8))
        
        query_row = ttk.Frame(query_frame)
        query_row.pack(fill=tk.X)
        
        ttk.Label(query_row, text="预测者ID：").pack(side=tk.LEFT, padx=(5, 2), pady=5)
        self.query_pid_var = tk.StringVar(value="1")
        ttk.Entry(query_row, textvariable=self.query_pid_var, width=10).pack(side=tk.LEFT, padx=(2, 10), pady=5)
        
        tk.Button(query_row, text="  🔍 查询该预测者所有期预测数据  ", bg="#5cb85c", fg="white",
                   relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                   command=self._query_predictor_data).pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Button(query_row, text="  🔄 刷新开奖结果  ", bg="#f0ad4e", fg="white",
                   relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                   command=self._refresh_results).pack(side=tk.LEFT, padx=6, pady=5)
        
        self.btn_calc_kill = tk.Button(query_row, text="  ⚡ 计算杀号  ", bg="#d9534f", fg="white",
                   relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9, "bold"),
                   command=self._calculate_kill_numbers)
        self.btn_calc_kill.pack(side=tk.LEFT, padx=6, pady=5)
        
        self.query_result_frame = ttk.LabelFrame(main_frame, text="预测者历史数据", padding=5)
        self.query_result_frame.pack(fill=tk.X, pady=(0, 8))
        
        query_columns = ("issue", "result", "bai_pred", "shi_pred", "ge_pred")
        self.query_tree = ttk.Treeview(self.query_result_frame, columns=query_columns, show="headings", height=8)
        self.query_tree.heading("issue", text="期号")
        self.query_tree.heading("result", text="开奖号")
        self.query_tree.heading("bai_pred", text="百位预测")
        self.query_tree.heading("shi_pred", text="十位预测")
        self.query_tree.heading("ge_pred", text="个位预测")
        self.query_tree.column("issue", width=80, anchor=tk.CENTER)
        self.query_tree.column("result", width=70, anchor=tk.CENTER)
        self.query_tree.column("bai_pred", width=120, anchor=tk.CENTER)
        self.query_tree.column("shi_pred", width=120, anchor=tk.CENTER)
        self.query_tree.column("ge_pred", width=120, anchor=tk.CENTER)
        
        self.query_tree.tag_configure("hit_row", foreground="#d32f2f")
        self.query_tree.tag_configure("pending", foreground="#999999")
        self.query_tree.tag_configure("result_blue", foreground="#1976d2")
        
        query_scrollbar = ttk.Scrollbar(self.query_result_frame, orient=tk.VERTICAL, command=self.query_tree.yview)
        self.query_tree.configure(yscrollcommand=query_scrollbar.set)
        self.query_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        query_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.kill_trees = {}
        self.kill_labels = {}
        self.remain_labels = {}
        self.remain_texts = {}
        
        positions = [("bai", "位置1（百位）"), ("shi", "位置2（十位）"), ("ge", "位置3（个位）")]
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        
        for i, (pos_key, pos_name) in enumerate(positions):
            col_frame = ttk.Frame(content_frame)
            col_frame.grid(row=0, column=i, sticky="nsew", padx=3)
            
            kill_frame = ttk.LabelFrame(col_frame, text=f"{pos_name}杀号结果", padding=5)
            kill_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            
            info_label = ttk.Label(kill_frame, 
                                   text=f"{pos_name.split('（')[0]}杀号对应预测期数：- | 杀号数量：0 | 去重后杀号数量：0")
            info_label.pack(anchor=tk.W, pady=(0, 5))
            self.kill_labels[pos_key] = info_label
            
            columns = ("predictor_id", "seq", "kill_num", "streak", "hit_rate")
            tree = ttk.Treeview(kill_frame, columns=columns, show="headings", height=8)
            tree.heading("predictor_id", text="预测者ID")
            tree.heading("seq", text="序号")
            tree.heading("kill_num", text="杀号")
            tree.heading("streak", text="连续中奖期数")
            tree.heading("hit_rate", text="历史中奖概率")
            tree.column("predictor_id", width=70, anchor=tk.CENTER)
            tree.column("seq", width=50, anchor=tk.CENTER)
            tree.column("kill_num", width=50, anchor=tk.CENTER)
            tree.column("streak", width=80, anchor=tk.CENTER)
            tree.column("hit_rate", width=80, anchor=tk.CENTER)
            
            scrollbar_kill = ttk.Scrollbar(kill_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar_kill.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_kill.pack(side=tk.RIGHT, fill=tk.Y)
            self.kill_trees[pos_key] = tree
            
            remain_frame = ttk.LabelFrame(col_frame, text=f"{pos_name}剩余号码", padding=5)
            remain_frame.pack(fill=tk.X)
            
            count_label = ttk.Label(remain_frame, text=f"{pos_name.split('（')[0]}剩余号码总数：10")
            count_label.pack(anchor=tk.W, pady=(0, 5))
            self.remain_labels[pos_key] = count_label
            
            remain_text = tk.Text(remain_frame, height=2, bg="white", relief=tk.SUNKEN, font=("微软雅黑", 10))
            remain_text.pack(fill=tk.X)
            remain_text.insert(tk.END, "0 1 2 3 4 5 6 7 8 9")
            remain_text.config(state=tk.DISABLED)
            self.remain_texts[pos_key] = remain_text
        
        save_frame = ttk.LabelFrame(main_frame, text="保存剩余号码与统计", padding=8)
        save_frame.pack(fill=tk.X, pady=(8, 0))
        
        save_row1 = ttk.Frame(save_frame)
        save_row1.pack(fill=tk.X)
        
        ttk.Label(save_row1, text="期号：").pack(side=tk.LEFT, padx=(5, 2), pady=5)
        self.save_issue_var = tk.StringVar()
        ttk.Entry(save_row1, textvariable=self.save_issue_var, width=12).pack(side=tk.LEFT, padx=(2, 15), pady=5)
        
        tk.Button(save_row1, text="  💾 保存当前剩余号码  ", bg="#5bc0de", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._save_remain_numbers).pack(side=tk.LEFT, padx=6, pady=5)
        
        tk.Button(save_row1, text="   预测对错统计  ", bg="#337ab7", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._calc_prediction_stats).pack(side=tk.LEFT, padx=6, pady=5)
        
        stats_frame = ttk.Frame(save_frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="点击\"预测对错统计\"按钮查看详细统计和记录")
        self.stats_label.pack(anchor=tk.W, padx=5)
        
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(fill=tk.X, pady=(5, 0))
        
        self._refresh_saved_list()
        self._set_default_issue()
    
    def _get_next_issue(self):
        history = self.history_manager.get_all()
        if not history:
            return ""
        return str(history[0]["issue"])
    
    def _set_default_issue(self):
        next_issue = self._get_next_issue()
        if next_issue:
            self.save_issue_var.set(next_issue)
    
    def _generate_predictions(self):
        try:
            predictor_count = int(self.predictor_count_var.get())
            predict_count = int(self.predict_count_var.get())
            predict_periods = int(self.predict_periods_var.get())
            
            if predictor_count <= 0 or predict_count <= 0 or predict_periods <= 0:
                messagebox.showerror("错误", "参数必须大于0")
                return
            if predict_count > 10:
                messagebox.showerror("错误", "每位置预测号码数不能超过10")
                return
            
            history = self.history_manager.get_all()
            history.sort(key=lambda x: str(x["issue"]))
            recent_history = history[-predict_periods:] if len(history) > predict_periods else history
            
            if not recent_history:
                messagebox.showerror("错误", "历史数据为空，请先在历史查询中添加开奖记录")
                return
            
            latest_issue = str(recent_history[-1]["issue"])
            year = int(latest_issue[:4])
            period_num = int(latest_issue[4:])
            next_period = period_num + 1
            next_issue = f"{year}{next_period:03d}"
            
            total = predict_periods + 1
            
            def do_gen():
                predictions = {}
                for i, record in enumerate(recent_history):
                    issue = str(record["issue"])
                    result_num = record["number"]
                    predictions[issue] = {
                        "result": result_num,
                        "predictors": []
                    }
                    
                    for pid in range(predictor_count):
                        predictor_pred = {
                            "predictor_id": pid + 1,
                            "bai": random.sample(range(10), min(predict_count, 10)),
                            "shi": random.sample(range(10), min(predict_count, 10)),
                            "ge": random.sample(range(10), min(predict_count, 10))
                        }
                        predictions[issue]["predictors"].append(predictor_pred)
                    
                    if (i + 1) % 5 == 0 or i == len(recent_history) - 1:
                        self.root.after(0, lambda p=i+1, t=total: self.status_var.set(f"正在生成预测数据... {p}/{t}"))
                
                predictions[next_issue] = {
                    "result": "",
                    "predictors": []
                }
                for pid in range(predictor_count):
                    predictor_pred = {
                        "predictor_id": pid + 1,
                        "bai": random.sample(range(10), min(predict_count, 10)),
                        "shi": random.sample(range(10), min(predict_count, 10)),
                        "ge": random.sample(range(10), min(predict_count, 10))
                    }
                    predictions[next_issue]["predictors"].append(predictor_pred)
                
                self.prediction_data = {
                    "params": {
                        "predictor_count": predictor_count,
                        "predict_count": predict_count,
                        "min_streak": int(self.min_streak_var.get()),
                        "predict_periods": predict_periods,
                        "next_issue": next_issue
                    },
                    "predictions": predictions
                }
                
                self._save_prediction_data()
                self.root.after(0, lambda: messagebox.showinfo("成功", f"已生成{predictor_count}个预测者，{len(recent_history)}期历史预测 + 1期新预测（{next_issue}）"))
                self.root.after(0, lambda: self.status_var.set(f"已生成 {total} 期预测数据"))
            
            self.status_var.set(f"正在生成预测数据... 0/{total}")
            threading.Thread(target=do_gen, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def _add_predictions(self):
        if not self.prediction_data or "predictions" not in self.prediction_data:
            messagebox.showerror("错误", "请先生成预测数据后再补齐")
            return

        history = self.history_manager.get_all()
        if not history:
            messagebox.showerror("错误", "历史数据为空")
            return

        predictions = self.prediction_data["predictions"]
        history_sorted = sorted(history, key=lambda x: str(x["issue"]))
        history_issues = [str(h["issue"]) for h in history_sorted]
        history_map = {str(h["issue"]): h["number"] for h in history_sorted}
        predicted_issues_set = set(predictions.keys())
        
        if not predicted_issues_set:
            messagebox.showerror("错误", "预测数据为空，请先生成预测数据")
            return
        
        max_history_issue = history_issues[-1]
        max_history_year = int(max_history_issue[:4])
        max_history_num = int(max_history_issue[4:])
        
        max_pred_issue = max(predicted_issues_set)
        max_pred_year = int(max_pred_issue[:4])
        max_pred_num = int(max_pred_issue[4:])
        
        all_issues = []
        current_year = max_pred_year
        current_num = max_pred_num
        
        while True:
            issue = f"{current_year}{current_num:03d}"
            
            if current_year > max_history_year or (current_year == max_history_year and current_num > max_history_num):
                break
            
            if current_year == max_pred_year and current_num == max_pred_num:
                current_num += 1
                if current_num > 999:
                    current_num = 1
                    current_year += 1
                continue
            
            all_issues.append(issue)
            
            current_num += 1
            if current_num > 999:
                current_num = 1
                current_year += 1
        
        missing_issues = all_issues
        
        next_year = max_history_year
        next_num = max_history_num + 1
        if next_num > 999:
            next_num = 1
            next_year += 1
        next_issue_new = f"{next_year}{next_num:03d}"
        
        need_add_next = next_issue_new not in predicted_issues_set
        
        if not missing_issues and not need_add_next:
            messagebox.showinfo("提示", "所有历史期号和新一期都已预测，无需补齐")
            return
        
        params = self.prediction_data.get("params", {})
        predictor_count = params.get("predictor_count", 0)
        predict_count = params.get("predict_count", 1)
        
        total_issues = len(missing_issues) + (1 if need_add_next else 0)
        current_progress = 0
        
        def do_add():
            nonlocal current_progress
            try:
                added_count = 0
                
                def generate_predictors(issue_name):
                    new_predictors = []
                    for pid in range(predictor_count):
                        predictor_pred = {
                            "predictor_id": pid + 1,
                            "bai": random.sample(range(10), min(predict_count, 10)),
                            "shi": random.sample(range(10), min(predict_count, 10)),
                            "ge": random.sample(range(10), min(predict_count, 10))
                        }
                        new_predictors.append(predictor_pred)
                        
                        if (pid + 1) % 500 == 0:
                            progress_in_issue = int((pid + 1) / predictor_count * 100)
                            self.root.after(0, lambda p=current_progress, t=total_issues, i=issue_name, pi=progress_in_issue: self.status_var.set(f"正在补齐预测... {p}/{t} ({i}: {pi}%)"))
                    return new_predictors
                
                for issue in missing_issues:
                    predictions[issue] = {
                        "result": history_map.get(issue, ""),
                        "predictors": generate_predictors(issue)
                    }
                    added_count += 1
                    current_progress += 1
                    
                    if current_progress % 5 == 0 or current_progress == total_issues:
                        self.root.after(0, lambda p=current_progress, t=total_issues: self.status_var.set(f"正在补齐预测... {p}/{t}"))
                
                if need_add_next:
                    predictions[next_issue_new] = {
                        "result": "",
                        "predictors": generate_predictors(next_issue_new)
                    }
                    added_count += 1
                    current_progress += 1
                    
                    self.root.after(0, lambda p=current_progress, t=total_issues: self.status_var.set(f"正在补齐预测... {p}/{t}"))
                    self.prediction_data["params"]["next_issue"] = next_issue_new
                
                self._save_prediction_data()
                
                msg = f"已补齐 {added_count} 期预测数据"
                if need_add_next:
                    msg += f"（含新一期 {next_issue_new}）"
                self.root.after(0, lambda m=msg: messagebox.showinfo("成功", m))
                self.root.after(0, lambda: self.status_var.set(f"已补齐 {added_count} 期"))
                self.root.after(0, self._refresh_saved_list)
            except Exception as e:
                self.root.after(0, lambda err=str(e): messagebox.showerror("补齐预测错误", f"错误信息：{err}"))
                self.root.after(0, lambda: self.status_var.set("补齐预测失败"))
        
        self.status_var.set(f"正在补齐预测... 0/{total_issues}")
        threading.Thread(target=do_add, daemon=True).start()

    def _query_predictor_data(self):
        if not self.prediction_data or "predictions" not in self.prediction_data:
            messagebox.showerror("错误", "请先生成预测数据")
            return
        
        try:
            pid = int(self.query_pid_var.get()) - 1
        except ValueError:
            messagebox.showerror("错误", "请输入有效的预测者ID")
            return
        
        params = self.prediction_data.get("params", {})
        predictor_count = params.get("predictor_count", 0)
        
        if pid < 0 or pid >= predictor_count:
            messagebox.showerror("错误", f"预测者ID必须在1-{predictor_count}之间")
            return
        
        predictions = self.prediction_data["predictions"]
        issues = sorted(predictions.keys(), reverse=True)
        
        for item in self.query_tree.get_children():
            self.query_tree.delete(item)
        
        for issue in issues:
            pred_data = predictions[issue]
            result_num = pred_data.get("result", "")
            predictors = pred_data["predictors"]
            
            if pid < len(predictors):
                pred = predictors[pid]
                bai_pred_list = pred["bai"]
                shi_pred_list = pred["shi"]
                ge_pred_list = pred["ge"]
                
                bai_result = result_num[0] if result_num else ""
                shi_result = result_num[1] if result_num else ""
                ge_result = result_num[2] if result_num else ""
                
                bai_pred_str = ",".join(
                    (str(num) + "★") if (result_num and str(num) == bai_result) else str(num)
                    for num in bai_pred_list
                )
                shi_pred_str = ",".join(
                    (str(num) + "★") if (result_num and str(num) == shi_result) else str(num)
                    for num in shi_pred_list
                )
                ge_pred_str = ",".join(
                    (str(num) + "★") if (result_num and str(num) == ge_result) else str(num)
                    for num in ge_pred_list
                )
                
                display_result = result_num if result_num else "待开奖"
                tags = ()
                if not result_num:
                    tags = ("pending",)
                else:
                    bai_hit = any(str(num) == bai_result for num in bai_pred_list)
                    shi_hit = any(str(num) == shi_result for num in shi_pred_list)
                    ge_hit = any(str(num) == ge_result for num in ge_pred_list)
                    if bai_hit and shi_hit and ge_hit:
                        tags = ("hit_row",)
                
                self.query_tree.insert("", tk.END, values=(
                    issue, display_result, bai_pred_str, shi_pred_str, ge_pred_str
                ), tags=tags)
    
    def _calculate_kill_numbers(self):
        if not self.prediction_data or "predictions" not in self.prediction_data:
            messagebox.showerror("错误", "请先生成预测数据")
            return
        
        try:
            min_streak = int(self.min_streak_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的连续中奖期数")
            return
        
        predictions = self.prediction_data["predictions"]
        params = self.prediction_data.get("params", {})
        predictor_count = params.get("predictor_count", 0)
        predict_count = params.get("predict_count", 3)
        next_issue = params.get("next_issue", "")
        
        if not next_issue or next_issue not in predictions:
            messagebox.showerror("错误", "未找到下一期预测数据")
            return
        
        next_pred_data = predictions[next_issue]
        next_predictors = next_pred_data["predictors"]
        
        history_issues = sorted([k for k in predictions.keys() if k != next_issue and predictions[k].get("result", "")], reverse=True)
        total_periods = len(history_issues)
        
        if total_periods == 0:
            messagebox.showerror("错误", "没有可用的历史预测数据用于计算")
            return
        
        positions = [("bai", "位置1"), ("shi", "位置2"), ("ge", "位置3")]
        
        def do_calc():
            total_hit_counts = {}
            for pos_key, pos_name in positions:
                total_hit_counts[pos_key] = {}
                for pid in range(predictor_count):
                    total_hits = 0
                    for issue in history_issues:
                        pred_data = predictions[issue]
                        result_num = pred_data["result"]
                        predictors = pred_data["predictors"]
                        if pid < len(predictors):
                            pred = predictors[pid]
                            result_pos_num = int(result_num[0]) if pos_key=="bai" else int(result_num[1]) if pos_key=="shi" else int(result_num[2])
                            if result_pos_num in pred[pos_key]:
                                total_hits += 1
                    total_hit_counts[pos_key][pid] = total_hits
            
            all_kill_details = {}
            all_kill_sets = {}
            all_remain_nums = {}
            
            for pos_idx, (pos_key, pos_name) in enumerate(positions):
                kill_details = []
                kill_set = set()
                
                for pid in range(predictor_count):
                    for seq in range(predict_count):
                        streak = 0
                        
                        for issue in history_issues:
                            pred_data = predictions[issue]
                            result_num = pred_data["result"]
                            predictors = pred_data["predictors"]
                            
                            if pid < len(predictors):
                                pred = predictors[pid]
                                if seq < len(pred[pos_key]):
                                    pred_num = pred[pos_key][seq]
                                    result_pos_num = int(result_num[0]) if pos_key=="bai" else int(result_num[1]) if pos_key=="shi" else int(result_num[2])
                                    
                                    if pred_num == result_pos_num:
                                        streak += 1
                                    else:
                                        break
                                else:
                                    break
                            else:
                                break
                        
                        if streak >= min_streak:
                            if pid < len(next_predictors):
                                next_pred = next_predictors[pid]
                                if seq < len(next_pred[pos_key]):
                                    kill_num = next_pred[pos_key][seq]
                                    kill_set.add(kill_num)
                                    total_hits = total_hit_counts[pos_key].get(pid, 0)
                                    hit_rate = f"{total_hits}/{total_periods}"
                                    kill_details.append((pid + 1, seq + 1, kill_num, streak, hit_rate))
                
                kill_details.sort(key=lambda x: (-x[3], x[0], x[1]))
                all_kill_details[pos_key] = kill_details
                all_kill_sets[pos_key] = kill_set
                all_remain_nums[pos_key] = sorted(set(range(10)) - kill_set)
                
                self.root.after(0, lambda p=pos_idx+1, t=3: self.status_var.set(f"正在计算杀号... {p}/{t}"))
            
            def update_ui():
                for pos_key, pos_name in positions:
                    kill_details = all_kill_details[pos_key]
                    kill_set = all_kill_sets[pos_key]
                    remain_nums = all_remain_nums[pos_key]
                    
                    for item in self.kill_trees[pos_key].get_children():
                        self.kill_trees[pos_key].delete(item)
                    
                    for detail in kill_details:
                        self.kill_trees[pos_key].insert("", tk.END, values=detail)
                    
                    self.kill_labels[pos_key].config(
                        text=f"{pos_name}杀号对应预测期数：{total_periods}期历史 + {next_issue}期新预测 | 杀号数量：{len(kill_details)} | 去重后：{len(kill_set)}"
                    )
                    
                    self.remain_labels[pos_key].config(
                        text=f"{pos_name}剩余号码总数：{len(remain_nums)}"
                    )
                    self.remain_texts[pos_key].config(state=tk.NORMAL)
                    self.remain_texts[pos_key].delete(1.0, tk.END)
                    self.remain_texts[pos_key].insert(tk.END, " ".join(str(n) for n in remain_nums))
                    self.remain_texts[pos_key].config(state=tk.DISABLED)
                
                self.status_var.set(f"杀号计算完成")
                messagebox.showinfo("成功", "杀号计算完成")
            
            self.root.after(0, update_ui)
        
        self.status_var.set("正在计算杀号... 0/3")
        threading.Thread(target=do_calc, daemon=True).start()
