"""
回测引擎 - 验证预测策略在历史数据上的真实表现

设计:
- BaseStrategy: 统一策略接口
- 多个具体策略: Random/Frequency/DecayWeighted/Smoothed/ColdHot
- BacktestEngine: 跑回测 + 汇总指标
- BacktestTab: Tkinter UI
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import threading
import os
import json
from typing import List, Dict, Tuple, Optional

from utils.statistics import (
    position_frequency,
    position_frequency_weighted,
    cold_hot_numbers,
    laplace_smooth,
    top_n_keys,
    evaluate_prediction,
    aggregate_metrics,
    extract_number,
    walk_forward_split,
)
from utils.history_manager import HistoryManager


# ========== 策略定义 ==========

class BaseStrategy:
    """策略基类"""
    name = "Base"
    description = ""

    def predict(self, train_data: List[dict], top_n: int) -> Dict[str, List[int]]:
        """
        输入: 训练数据 + 每位置选号数
        输出: {"bai": [0,1,2], "shi": [...], "ge": [...]}
        """
        raise NotImplementedError


class RandomStrategy(BaseStrategy):
    """随机基准 - 用于对照实验"""
    name = "随机基准"
    description = "每个位置随机选 top_n 个号,纯随机"

    def predict(self, train_data, top_n):
        n = min(top_n, 10)
        return {
            "bai": sorted(random.sample(range(10), n)),
            "shi": sorted(random.sample(range(10), n)),
            "ge": sorted(random.sample(range(10), n)),
        }


class FrequencyStrategy(BaseStrategy):
    """简单频率 - 选历史出现次数最多的号"""
    name = "简单频率"
    description = "选历史出现次数最多的 top_n 个号"

    def predict(self, train_data, top_n):
        result = {}
        for pos, key in enumerate(["bai", "shi", "ge"]):
            freq = position_frequency(train_data, pos)
            top = top_n_keys(freq, top_n)
            result[key] = sorted(top)
        return result


class SmoothedFrequencyStrategy(BaseStrategy):
    """带拉普拉斯平滑的频率 - 避免 0 概率偏向"""
    name = "平滑频率"
    description = "频率 + 拉普拉斯平滑,样本少时更稳"

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha

    def predict(self, train_data, top_n):
        result = {}
        for pos, key in enumerate(["bai", "shi", "ge"]):
            freq = position_frequency(train_data, pos)
            prob = laplace_smooth(freq, self.alpha)
            top = top_n_keys(prob, top_n)
            result[key] = sorted(top)
        return result


class DecayWeightedStrategy(BaseStrategy):
    """指数衰减加权 - 近期数据权重大"""
    name = "衰减加权"
    description = "近期出现频率权重大,适合抓短期趋势"

    def __init__(self, decay: float = 0.95):
        self.decay = decay

    def predict(self, train_data, top_n):
        result = {}
        for pos, key in enumerate(["bai", "shi", "ge"]):
            freq = position_frequency_weighted(train_data, pos, self.decay)
            top = top_n_keys(freq, top_n)
            result[key] = sorted(top)
        return result


class ColdHotStrategy(BaseStrategy):
    """冷热号策略 - 只看最近 window 期"""
    name = "冷热号"
    description = "只统计最近 window 期的热号,完全忽略更早数据"

    def __init__(self, recent_window: int = 20):
        self.recent_window = recent_window

    def predict(self, train_data, top_n):
        result = {}
        for pos, key in enumerate(["bai", "shi", "ge"]):
            hot, _ = cold_hot_numbers(train_data, pos, self.recent_window, top_n)
            result[key] = sorted(hot)
        return result


# 策略注册表
STRATEGY_REGISTRY = {
    "随机基准": lambda: RandomStrategy(),
    "简单频率": lambda: FrequencyStrategy(),
    "平滑频率(α=1)": lambda: SmoothedFrequencyStrategy(1.0),
    "平滑频率(α=0.5)": lambda: SmoothedFrequencyStrategy(0.5),
    "衰减加权(d=0.9)": lambda: DecayWeightedStrategy(0.9),
    "衰减加权(d=0.95)": lambda: DecayWeightedStrategy(0.95),
    "衰减加权(d=0.98)": lambda: DecayWeightedStrategy(0.98),
    "冷热号(w=10)": lambda: ColdHotStrategy(10),
    "冷热号(w=20)": lambda: ColdHotStrategy(20),
    "冷热号(w=50)": lambda: ColdHotStrategy(50),
}


# ========== 回测引擎 ==========

class BacktestEngine:
    """
    滚动窗口回测引擎
    输入: 历史数据 + 策略 + 窗口参数
    输出: 每期预测结果 + 汇总指标
    """

    def __init__(self, history: List[dict]):
        # 按 issue 升序(旧->新)
        self.history = sorted(history, key=lambda x: str(x.get("issue", "")))
        self._filter_valid()

    def _filter_valid(self):
        """过滤掉 number 字段不合法(空/非数字)的记录"""
        valid = []
        for r in self.history:
            num = str(r.get("number", "")).strip()
            if len(num) == 3 and num.isdigit():
                valid.append(r)
        self.history = valid

    def run(self, strategy: BaseStrategy, top_n: int = 5,
            train_size: int = 100, test_size: int = 30,
            step: int = 1, max_periods: int = None) -> Dict:
        """
        跑回测
        train_size: 训练窗口(用前 N 期训练)
        test_size: 每轮测试多少期
        step: 滑动步长
        max_periods: 最多跑多少个测试窗口
        """
        results = []
        n = len(self.history)
        if n < train_size + 1:
            return {
                "results": results,
                "metrics": aggregate_metrics(results),
                "strategy": strategy.name,
                "top_n": top_n,
                "train_size": train_size,
                "test_size": test_size,
                "warning": f"历史数据不足({n}期),需至少 {train_size + 1} 期",
            }

        start = 0
        window_count = 0
        while start + train_size + test_size <= n:
            train = self.history[start:start + train_size]
            test = self.history[start + train_size:start + train_size + test_size]

            for record in test:
                pred = strategy.predict(train, top_n)
                eval_result = evaluate_prediction(pred, extract_number(record))
                eval_result["issue"] = str(record.get("issue", ""))
                eval_result["predicted"] = {
                    "bai": pred["bai"],
                    "shi": pred["shi"],
                    "ge": pred["ge"],
                }
                results.append(eval_result)

            start += step
            window_count += 1
            if max_periods and window_count >= max_periods:
                break

        return {
            "results": results,
            "metrics": aggregate_metrics(results),
            "strategy": strategy.name,
            "top_n": top_n,
            "train_size": train_size,
            "test_size": test_size,
            "window_count": window_count,
        }

    def compare(self, strategy_names: List[str], **kwargs) -> Dict[str, Dict]:
        """跑多个策略,返回对比结果"""
        comparison = {}
        for name in strategy_names:
            if name not in STRATEGY_REGISTRY:
                comparison[name] = {"error": "未知策略"}
                continue
            strategy = STRATEGY_REGISTRY[name]()
            try:
                comparison[name] = self.run(strategy, **kwargs)
            except Exception as e:
                comparison[name] = {"error": str(e)}
        return comparison

    def predict_next(self, strategy: BaseStrategy, top_n: int = 5,
                     train_size: int = None) -> Optional[Dict]:
        """
        用策略对下一期做预测
        train_size: 用最近 N 期做训练(None=用全部)
        返回: {"issue": "2026185", "predicted": {...}, "is_prediction": True, ...}
        """
        if not self.history:
            return None
        n = len(self.history)
        if n < 10:
            return None

        train = self.history[-train_size:] if train_size else self.history
        pred = strategy.predict(train, top_n)

        # 算下一期号
        last_issue = str(self.history[-1].get("issue", ""))
        if not last_issue or len(last_issue) < 7:
            return None
        try:
            year = int(last_issue[:4])
            num = int(last_issue[4:])
            num += 1
            if num > 999:
                num = 1
                year += 1
            next_issue = f"{year}{num:03d}"
        except (ValueError, IndexError):
            return None

        return {
            "issue": next_issue,
            "predicted": {
                "bai": pred["bai"],
                "shi": pred["shi"],
                "ge": pred["ge"],
            },
            "actual": "",
            "hit_count": -1,
            "hit_pos": [],
            "is_prediction": True,
        }


# ========== UI Tab ==========

class BacktestTab:
    """回测中心 Tab"""

    def __init__(self, parent):
        self.parent = parent
        self.history_manager = HistoryManager()
        self.engine = None
        self._last_result = None
        self._last_comparison = None
        self._next_prediction = None
        # 历史归档 - 与 saved_predictions.json 共享同一份数据
        self.archive_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "saved_predictions.json")
        self.archive_data: List[Dict] = []
        self._load_archive()
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.parent)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # === 参数设置 ===
        param = ttk.LabelFrame(main, text="回测参数", padding=10)
        param.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(param)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="策略:").pack(side=tk.LEFT, padx=(0, 4))
        self.strategy_var = tk.StringVar(value="平滑频率(α=1)")
        strategy_combo = ttk.Combobox(row1, textvariable=self.strategy_var,
                                      values=list(STRATEGY_REGISTRY.keys()),
                                      state="readonly", width=20)
        strategy_combo.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="Top-N(每位置):").pack(side=tk.LEFT, padx=(0, 4))
        self.topn_var = tk.StringVar(value="5")
        ttk.Entry(row1, textvariable=self.topn_var, width=6).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="训练窗口:").pack(side=tk.LEFT, padx=(0, 4))
        self.train_var = tk.StringVar(value="100")
        ttk.Entry(row1, textvariable=self.train_var, width=6).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row1, text="期").pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="测试窗口:").pack(side=tk.LEFT, padx=(0, 4))
        self.test_var = tk.StringVar(value="30")
        ttk.Entry(row1, textvariable=self.test_var, width=6).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row1, text="期").pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="滑动步长:").pack(side=tk.LEFT, padx=(0, 4))
        self.step_var = tk.StringVar(value="1")
        ttk.Entry(row1, textvariable=self.step_var, width=6).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row1, text="期").pack(side=tk.LEFT, padx=(0, 12))

        row2 = ttk.Frame(param)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="数据信息:").pack(side=tk.LEFT, padx=(0, 4))
        self.info_label = ttk.Label(row2, text="点击「刷新数据」加载", foreground="gray")
        self.info_label.pack(side=tk.LEFT, padx=(0, 12))
        self.archive_label = ttk.Label(row2, text="已归档: ? 条", foreground="#1976d2",
                                       font=("微软雅黑", 9, "bold"))
        self.archive_label.pack(side=tk.LEFT, padx=(0, 12))
        self._refresh_archive_label()

        tk.Button(row2, text="  🔄 刷新数据  ", bg="#5bc0de", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._load_data).pack(side=tk.LEFT, padx=4)
        tk.Button(row2, text="  🚀 跑回测  ", bg="#5cb85c", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9, "bold"),
                  command=self._run_backtest).pack(side=tk.LEFT, padx=4)
        tk.Button(row2, text="  ⚔️ 策略对比  ", bg="#d9534f", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9, "bold"),
                  command=self._run_comparison).pack(side=tk.LEFT, padx=4)
        tk.Button(row2, text="  🗑 清空结果  ", bg="#f0ad4e", fg="white",
                  relief=tk.RAISED, padx=5, pady=3, font=("微软雅黑", 9),
                  command=self._clear).pack(side=tk.RIGHT, padx=4)

        # === 状态条 ===
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main, textvariable=self.status_var, foreground="blue",
                  font=("微软雅黑", 9)).pack(fill=tk.X, pady=(0, 4))

        # === 结果区 ===
        result_frame = ttk.LabelFrame(main, text="回测报告", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.result_notebook = ttk.Notebook(result_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)

        self._build_summary_tab()
        self._build_comparison_tab()
        self._build_detail_tab()
        self._build_analysis_tab()

    def _build_summary_tab(self):
        tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(tab, text="  📊 总览指标  ")

        self.summary_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD,
                                                     font=("微软雅黑", 10),
                                                     state=tk.DISABLED)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _build_comparison_tab(self):
        tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(tab, text="  ⚔️ 策略对比  ")

        columns = ("策略", "总期数", "平均命中位", "0位占比", "1位占比",
                   "2位占比", "3位全中", "百位命中", "十位命中", "个位命中")
        self.compare_tree = ttk.Treeview(tab, columns=columns, show="headings", height=12)
        widths = {"策略": 140, "总期数": 70, "平均命中位": 90, "0位占比": 70,
                  "1位占比": 70, "2位占比": 70, "3位全中": 80, "百位命中": 80,
                  "十位命中": 80, "个位命中": 80}
        for c in columns:
            self.compare_tree.heading(c, text=c)
            self.compare_tree.column(c, width=widths.get(c, 80), anchor=tk.CENTER)
        self.compare_tree.tag_configure("baseline", foreground="#999")
        self.compare_tree.tag_configure("best", foreground="#d32f2f",
                                       font=("微软雅黑", 9, "bold"))

        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.compare_tree.yview)
        self.compare_tree.configure(yscrollcommand=scrollbar.set)
        self.compare_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

    def _build_detail_tab(self):
        tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(tab, text="  📋 详细记录  ")

        # 顶部工具条:控制显示条数
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill=tk.X, padx=4, pady=(4, 2))
        ttk.Label(toolbar, text="显示条数:").pack(side=tk.LEFT, padx=(0, 4))
        self.detail_limit_var = tk.StringVar(value="500")
        ttk.Entry(toolbar, textvariable=self.detail_limit_var, width=8).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(toolbar, text="  🔄 刷新  ", bg="#5bc0de", fg="white",
                  relief=tk.RAISED, padx=5, pady=2, font=("微软雅黑", 9),
                  command=self._refresh_detail_view).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="  全部(可能慢)  ", bg="#f0ad4e", fg="white",
                  relief=tk.RAISED, padx=5, pady=2, font=("微软雅黑", 9),
                  command=self._show_all_detail).pack(side=tk.LEFT, padx=2)
        self.detail_status_label = ttk.Label(toolbar, text="尚未跑回测", foreground="gray")
        self.detail_status_label.pack(side=tk.LEFT, padx=12)

        columns = ("期号", "开奖号", "百位选号", "十位选号", "个位选号",
                   "命中位", "详情")
        self.detail_tree = ttk.Treeview(tab, columns=columns, show="headings", height=18)
        widths = {"期号": 90, "开奖号": 70, "百位选号": 130, "十位选号": 130,
                  "个位选号": 130, "命中位": 70, "详情": 200}
        for c in columns:
            self.detail_tree.heading(c, text=c)
            self.detail_tree.column(c, width=widths.get(c, 80), anchor=tk.CENTER)
        self.detail_tree.tag_configure("hit0", foreground="#999")
        self.detail_tree.tag_configure("hit1", foreground="#666")
        self.detail_tree.tag_configure("hit2", foreground="#f57c00",
                                       font=("微软雅黑", 9, "bold"))
        self.detail_tree.tag_configure("hit3", foreground="#d32f2f",
                                       font=("微软雅黑", 9, "bold"))
        self.detail_tree.tag_configure("prediction", foreground="#1976d2",
                                       font=("微软雅黑", 10, "bold"),
                                       background="#fff8e1")

        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=scrollbar.set)
        self.detail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

    def _build_analysis_tab(self):
        tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(tab, text="  🔢 冷热分析  ")

        self.analysis_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD,
                                                      font=("微软雅黑", 10),
                                                      state=tk.DISABLED)
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    # ========== 业务方法 ==========

    def _load_archive(self) -> List[Dict]:
        """从 saved_predictions.json 加载历史归档"""
        if not os.path.exists(self.archive_file):
            self.archive_data = []
            return self.archive_data
        try:
            with open(self.archive_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.archive_data = data
                else:
                    self.archive_data = []
        except (json.JSONDecodeError, OSError):
            self.archive_data = []
        return self.archive_data

    def _save_archive(self) -> bool:
        """保存归档到 saved_predictions.json(原子写)"""
        try:
            tmp = self.archive_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.archive_data, f, ensure_ascii=False, indent=2)
            # 原子替换,防止写到一半崩溃损坏文件
            if os.path.exists(self.archive_file):
                os.remove(self.archive_file)
            os.rename(tmp, self.archive_file)
            return True
        except OSError:
            return False

    def _archive_format(self, result_item: Dict) -> Optional[Dict]:
        """把回测单期结果转成 saved_predictions.json 的归档格式"""
        if not result_item.get("actual"):
            return None  # 没开奖结果的不归档
        if result_item.get("is_prediction"):
            return None  # 预测行不归档
        pred = result_item.get("predicted", {})
        return {
            "issue": result_item.get("issue", ""),
            "bai_remain": pred.get("bai", []),
            "shi_remain": pred.get("shi", []),
            "ge_remain": pred.get("ge", []),
            "result": result_item.get("actual", ""),
            "hit_pos": result_item.get("hit_pos", []),
            "source": "backtest",  # 标记来源,区分 prediction_model 的人工录入
        }

    def _archive_results(self, result: Dict) -> Dict:
        """
        归档回测结果到 saved_predictions.json
        返回 {"added": X, "updated": Y, "skipped": Z}
        """
        existing = {r.get("issue"): r for r in self.archive_data}
        added, updated, skipped = 0, 0, 0

        for item in result.get("results", []):
            archive_item = self._archive_format(item)
            if not archive_item:
                skipped += 1
                continue
            issue = archive_item["issue"]
            if issue in existing:
                # 已有但 result 为空 -> 这次补上
                if not existing[issue].get("result") and archive_item.get("result"):
                    existing[issue].update(archive_item)
                    updated += 1
                else:
                    skipped += 1
            else:
                self.archive_data.append(archive_item)
                added += 1

        if added > 0 or updated > 0:
            self._save_archive()

        return {"added": added, "updated": updated, "skipped": skipped}

    def _refresh_archive_label(self):
        """刷新顶部归档数量显示"""
        if hasattr(self, "archive_label"):
            n = len(self.archive_data)
            self.archive_label.config(text=f"已归档: {n} 条")

    def _load_data(self):
        history = self.history_manager.get_all()
        if not history:
            self.info_label.config(text="⚠️ 历史数据为空,请先在「历史查询」中添加", foreground="red")
            return
        self.engine = BacktestEngine(history)
        n = len(self.engine.history)
        if n < 30:
            self.info_label.config(
                text=f"⚠️ 有效数据 {n} 期,建议至少 100 期才有统计意义",
                foreground="orange")
        else:
            first = self.engine.history[0].get("issue", "")
            last = self.engine.history[-1].get("issue", "")
            self.info_label.config(
                text=f"✅ 已加载 {n} 期 ({first} ~ {last})",
                foreground="green")
        self.status_var.set(f"已加载 {n} 期历史数据")

    def _parse_params(self) -> Tuple[str, int, int, int, int]:
        try:
            strategy = self.strategy_var.get()
            top_n = int(self.topn_var.get())
            train_size = int(self.train_var.get())
            test_size = int(self.test_var.get())
            step = int(self.step_var.get())
            assert 1 <= top_n <= 10
            assert train_size >= 10
            assert test_size >= 1
            assert step >= 1
            return strategy, top_n, train_size, test_size, step
        except (ValueError, AssertionError) as e:
            messagebox.showerror("参数错误",
                                 f"请检查参数:Top-N(1-10),训练窗口(>=10),测试窗口(>=1)\n{e}")
            return None

    def _run_backtest(self):
        if self.engine is None:
            self._load_data()
            if self.engine is None:
                return

        params = self._parse_params()
        if not params:
            return
        strategy_name, top_n, train_size, test_size, step = params

        if strategy_name not in STRATEGY_REGISTRY:
            messagebox.showerror("错误", f"未知策略: {strategy_name}")
            return

        # 取 detail 显示条数
        try:
            detail_limit = int(self.detail_limit_var.get())
            if detail_limit < 0:
                detail_limit = 0
        except ValueError:
            detail_limit = 500

        self.status_var.set(f"⏳ 正在跑回测: {strategy_name} ...")
        self.result_notebook.select(0)  # 切到总览

        def do_run():
            try:
                strategy = STRATEGY_REGISTRY[strategy_name]()
                result = self.engine.run(strategy, top_n, train_size, test_size, step)
                self._last_result = result
                # 同步生成下一期预测(基于全部历史训练)
                try:
                    self._next_prediction = self.engine.predict_next(
                        strategy, top_n, train_size=None)
                except Exception:
                    self._next_prediction = None
                # 自动归档到 saved_predictions.json
                archive_stats = self._archive_results(result)
                self.parent.after(0, self._refresh_archive_label)
                self.parent.after(0, lambda: self._render_summary(result))
                self.parent.after(0, lambda: self._render_detail(result, limit=detail_limit))
                self.parent.after(0,
                    lambda: self._render_analysis(strategy_name, top_n, train_size))
                next_msg = ""
                if self._next_prediction:
                    next_issue = self._next_prediction["issue"]
                    next_msg = f" · 下一期 {next_issue} 预测已生成"
                archive_msg = ""
                if archive_stats["added"] or archive_stats["updated"]:
                    archive_msg = (f" · 归档 +{archive_stats['added']}/"
                                   f"~{archive_stats['updated']} 条")
                self.parent.after(0,
                    lambda: self.status_var.set(
                        f"✅ 完成:{strategy_name} Top-{top_n},共 {result['metrics'].get('total', 0)} 期"
                        f"{next_msg}{archive_msg}"))
            except Exception as e:
                self.parent.after(0,
                    lambda: messagebox.showerror("回测失败", str(e)))
                self.parent.after(0, lambda: self.status_var.set("❌ 回测失败"))

        threading.Thread(target=do_run, daemon=True).start()

    def _run_comparison(self):
        if self.engine is None:
            self._load_data()
            if self.engine is None:
                return

        params = self._parse_params()
        if not params:
            return
        _, top_n, train_size, test_size, step = params

        self.status_var.set("⏳ 正在跑多策略对比 ...")
        self.result_notebook.select(1)  # 切到对比

        def do_run():
            try:
                names = list(STRATEGY_REGISTRY.keys())
                comparison = self.engine.compare(
                    names, top_n=top_n, train_size=train_size,
                    test_size=test_size, step=step)
                self._last_comparison = comparison
                self.parent.after(0, lambda: self._render_comparison(comparison, top_n))
                self.parent.after(0,
                    lambda: self.status_var.set(
                        f"✅ 对比完成,共 {len(comparison)} 个策略"))
            except Exception as e:
                self.parent.after(0,
                    lambda: messagebox.showerror("对比失败", str(e)))
                self.parent.after(0, lambda: self.status_var.set("❌ 对比失败"))

        threading.Thread(target=do_run, daemon=True).start()

    def _clear(self):
        self._last_result = None
        self._last_comparison = None
        self._next_prediction = None
        for txt in [self.summary_text, self.analysis_text]:
            txt.config(state=tk.NORMAL)
            txt.delete("1.0", tk.END)
            txt.config(state=tk.DISABLED)
        for tree in [self.compare_tree, self.detail_tree]:
            for item in tree.get_children():
                tree.delete(item)
        if hasattr(self, "detail_status_label"):
            self.detail_status_label.config(text="尚未跑回测")
        self.status_var.set("已清空")

    # ========== 渲染 ==========

    def _render_summary(self, result: Dict):
        m = result.get("metrics", {})
        if not m:
            warning = result.get("warning", "无数据")
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert(tk.END, f"⚠️ {warning}")
            self.summary_text.config(state=tk.DISABLED)
            return

        from utils.statistics import expected_hit_by_random
        top_n = result.get("top_n", 5)
        expected = expected_hit_by_random(top_n)
        actual_avg = m.get("avg_hit", 0)

        diff = actual_avg - expected
        diff_pct = (diff / expected * 100) if expected > 0 else 0

        verdict = "持平"
        if diff_pct > 5:
            verdict = "📈 略优于随机"
        elif diff_pct > 15:
            verdict = "🔥 明显优于随机"
        elif diff_pct < -5:
            verdict = "📉 略差于随机"
        elif diff_pct < -15:
            verdict = "❄️ 明显差于随机"

        lines = [
            "=" * 60,
            f"策略: {result.get('strategy', '?')}",
            f"参数: Top-{top_n}/位 | 训练窗口 {result.get('train_size')} 期 | "
            f"测试窗口 {result.get('test_size')} 期 | 滑动步长 {result.get('step', 1)}",
            f"测试轮次: {result.get('window_count', '?')} 个滚动窗口",
            "=" * 60,
            "",
            f"📊 总览",
            f"  总测试期数:  {m.get('total', 0)} 期",
            f"  平均命中位数:  {actual_avg:.3f} 位 (理论随机期望: {expected:.3f} 位)",
            f"  相对随机的优势:  {diff:+.3f} 位 ({diff_pct:+.1f}%)",
            f"  评估结论:  {verdict}",
            "",
            f"🎯 命中位数分布",
            f"  0 位(全错):  {m['hit_distribution'].get(0, 0):>5} 期 "
            f"({m['hit_distribution_rate'].get(0, 0)*100:>5.1f}%)",
            f"  1 位命中:    {m['hit_distribution'].get(1, 0):>5} 期 "
            f"({m['hit_distribution_rate'].get(1, 0)*100:>5.1f}%)",
            f"  2 位命中:    {m['hit_distribution'].get(2, 0):>5} 期 "
            f"({m['hit_distribution_rate'].get(2, 0)*100:>5.1f}%)",
            f"  3 位全中:    {m['hit_distribution'].get(3, 0):>5} 期 "
            f"({m['hit_distribution_rate'].get(3, 0)*100:>5.1f}%)",
            "",
            f"📍 各位置命中率",
            f"  百位命中:  {m['pos_rates']['百']*100:.1f}% (随机期望: {top_n*10:.0f}%)",
            f"  十位命中:  {m['pos_rates']['十']*100:.1f}% (随机期望: {top_n*10:.0f}%)",
            f"  个位命中:  {m['pos_rates']['个']*100:.1f}% (随机期望: {top_n*10:.0f}%)",
            "",
            f"🏆 直选命中(3位全中)",
            f"  命中数:  {m.get('zhixuan_count', 0)} / {m.get('total', 0)}",
            f"  命中率:  {m.get('zhixuan_rate', 0)*100:.4f}% "
            f"(随机期望: {(top_n/10)**3*100:.4f}%)",
            "",
            "=" * 60,
            "💡 解读:",
            f"  - Top-{top_n} 即每位保留 {top_n} 个号,理论随机命中 1 位的概率 ~{top_n*10:.0f}%",
            f"  - 3位全中(直选)理论概率 {(top_n/10)**3*100:.4f}%,需长期跟踪才有意义",
            f"  - 如果'平均命中位'接近 {expected:.2f},说明策略等价于随机",
            f"  - 显著高于 {expected:.2f} 才说明有可观测的预测能力",
            "=" * 60,
        ]
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "\n".join(lines))
        self.summary_text.config(state=tk.DISABLED)

    def _render_comparison(self, comparison: Dict, top_n: int):
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)

        rows = []
        for name, result in comparison.items():
            if "error" in result:
                rows.append((name, 0, 0, "错误", "", "", "", "", "", ""))
                continue
            m = result.get("metrics", {})
            if not m:
                continue
            rows.append((
                name,
                m.get("total", 0),
                f"{m.get('avg_hit', 0):.3f}",
                f"{m['hit_distribution_rate'].get(0, 0)*100:.1f}%",
                f"{m['hit_distribution_rate'].get(1, 0)*100:.1f}%",
                f"{m['hit_distribution_rate'].get(2, 0)*100:.1f}%",
                f"{m['zhixuan_count']} ({m['zhixuan_rate']*100:.2f}%)",
                f"{m['pos_rates']['百']*100:.1f}%",
                f"{m['pos_rates']['十']*100:.1f}%",
                f"{m['pos_rates']['个']*100:.1f}%",
            ))

        # 找平均命中最高的
        best_avg = -1
        for r in rows:
            try:
                avg = float(r[2])
                if avg > best_avg:
                    best_avg = avg
            except (ValueError, TypeError):
                pass

        for r in rows:
            tags = ()
            if "随机" in r[0] or "Random" in r[0].lower():
                tags = ("baseline",)
            try:
                if float(r[2]) == best_avg and best_avg > 0:
                    tags = ("best",)
            except (ValueError, TypeError):
                pass
            self.compare_tree.insert("", tk.END, values=r, tags=tags)

    def _render_detail(self, result: Dict, limit: int = 500):
        """渲染详细记录。limit=0 表示全部,否则只显示最近 limit 条(倒序,最新在最上)
        顶部插入一条下一期预测(如有)"""
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        all_results = result.get("results", [])
        total_history = len(all_results)
        # 倒序:最新在最上
        history_rows = list(reversed(all_results))

        next_pred = getattr(self, "_next_prediction", None)
        has_pred = next_pred is not None

        if limit and limit > 0:
            # 限制总显示:预测占 1 条,剩下的给历史
            hist_limit = max(0, limit - (1 if has_pred else 0))
            history_rows = history_rows[:hist_limit]
            rows_to_show = ([next_pred] if has_pred else []) + history_rows
            shown = len(rows_to_show)
            if has_pred:
                status = f"🔮 1 条预测 + 最近 {shown - 1} 期 / 共 {total_history} 期历史"
            else:
                status = f"显示最近 {shown} / 共 {total_history} 期(倒序)"
        else:
            rows_to_show = ([next_pred] if has_pred else []) + history_rows
            shown = len(rows_to_show)
            if has_pred:
                status = f"🔮 1 条预测 + 全部 {total_history} 期历史(倒序)"
            else:
                status = f"显示全部 {total_history} 期(倒序)"

        for r in rows_to_show:
            self._insert_detail_row(r)

        if hasattr(self, "detail_status_label"):
            self.detail_status_label.config(text=status)

    def _insert_detail_row(self, r: Dict):
        """向 detail_tree 插入单行(预测行或历史行)"""
        is_pred = r.get("is_prediction", False)
        pred = r.get("predicted", {})
        actual = r.get("actual", "")

        bai_str = " ".join(str(x) for x in pred.get("bai", []))
        shi_str = " ".join(str(x) for x in pred.get("shi", []))
        ge_str = " ".join(str(x) for x in pred.get("ge", []))

        if is_pred:
            self.detail_tree.insert("", tk.END, values=(
                f"🔮 {r.get('issue', '')} (预测)",
                "—",
                bai_str,
                shi_str,
                ge_str,
                "待开奖",
                "下一期预测 · 基于全部历史训练",
            ), tags=("prediction",))
        else:
            hit_count = r.get("hit_count", 0)
            tags = (f"hit{hit_count}",)
            detail_parts = []
            for i, key in enumerate(["bai", "shi", "ge"]):
                pos_name = ["百", "十", "个"][i]
                hit = int(actual[i]) in pred.get(key, [])
                detail_parts.append(f"{pos_name}={'✓' if hit else '✗'}")
            self.detail_tree.insert("", tk.END, values=(
                r.get("issue", ""),
                actual,
                bai_str,
                shi_str,
                ge_str,
                f"{hit_count}位",
                " ".join(detail_parts),
            ), tags=tags)

    def _refresh_detail_view(self):
        """根据当前 limit 输入框刷新 detail 视图"""
        if not self._last_result:
            messagebox.showinfo("提示", "请先跑回测")
            return
        try:
            limit = int(self.detail_limit_var.get())
            if limit < 0:
                limit = 0
        except ValueError:
            limit = 500
            self.detail_limit_var.set("500")
        self._render_detail(self._last_result, limit=limit)

    def _show_all_detail(self):
        """显示全部(可能让 UI 卡住几秒,大量数据时慎用)"""
        if not self._last_result:
            messagebox.showinfo("提示", "请先跑回测")
            return
        total = len(self._last_result.get("results", []))
        if total > 2000:
            if not messagebox.askyesno("确认",
                                       f"将插入 {total} 条记录,可能需要几秒到几十秒,继续?"):
                return
        self.status_var.set(f"⏳ 正在渲染 {total} 条...")
        self.detail_limit_var.set("0")
        # 分批插入避免完全冻结
        self._render_detail_chunked(self._last_result, batch_size=200)

    def _render_detail_chunked(self, result: Dict, batch_size: int = 200):
        """分批插入 detail,每批之间释放主线程。倒序 + 顶部预测行"""
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
        all_results = result.get("results", [])
        history_rows = list(reversed(all_results))  # 倒序
        next_pred = getattr(self, "_next_prediction", None)
        rows = ([next_pred] if next_pred else []) + history_rows
        total = len(rows)
        self._chunked_idx = 0

        def insert_batch():
            end = min(self._chunked_idx + batch_size, total)
            for r in rows[self._chunked_idx:end]:
                self._insert_detail_row(r)
            self._chunked_idx = end
            if self.detail_status_label:
                has_pred = next_pred is not None
                pred_done = "🔮✓ " if (has_pred and self._chunked_idx > 0) else (
                    "" if not has_pred else "🔮⏳ ")
                self.detail_status_label.config(
                    text=f"{pred_done}已渲染 {end}/{total} 条(倒序)")
            if end < total:
                self.parent.after(20, insert_batch)
            else:
                self.status_var.set(f"✅ 全部 {total} 条渲染完成(倒序)")
                if self.detail_status_label:
                    if next_pred:
                        self.detail_status_label.config(
                            text=f"🔮 1 条预测 + 全部 {total - 1} 期历史(倒序)")
                    else:
                        self.detail_status_label.config(
                            text=f"显示全部 {total} 期(倒序)")

        insert_batch()

    def _render_analysis(self, strategy_name: str, top_n: int, train_size: int):
        """冷热分析:用当前策略的参数,统计训练窗口对应的最近 train_size 期的号码热度"""
        if not self.engine or not self.engine.history:
            return
        train_data = self.engine.history[-train_size:] \
            if len(self.engine.history) >= train_size else self.engine.history
        from utils.statistics import (
            position_frequency, sum_distribution, span_distribution,
            ac_distribution, o12_distribution,
        )

        lines = [
            f"🔢 冷热分析(基于最近 {len(train_data)} 期训练数据)",
            "=" * 60,
            "",
        ]

        pos_names = ["百位", "十位", "个位"]
        for pos, name in enumerate(pos_names):
            freq = position_frequency(train_data, pos)
            total = sum(freq.values())
            sorted_freq = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
            hot = [k for k, v in sorted_freq[:5]]
            cold = [k for k, v in sorted_freq[-3:]]
            lines.append(f"📍 {name} (共 {total} 次):")
            lines.append(f"  热号 Top-5: {hot}  "
                         f"({', '.join(f'{k}({v}次)' for k, v in sorted_freq[:5])})")
            lines.append(f"  冷号 Top-3: {cold}")
            for d in range(10):
                v = freq[d]
                pct = v / total * 100 if total > 0 else 0
                bar = "█" * int(pct * 2)
                lines.append(f"    {d}: {v:>4} 次 ({pct:>5.1f}%) {bar}")
            lines.append("")

        # 和值/跨度/AC 值/012 路
        sum_d = sum_distribution(train_data)
        span_d = span_distribution(train_data)
        ac_d = ac_distribution(train_data)
        o12_d = o12_distribution(train_data)

        lines.append("📈 和值分布:")
        total_sum = sum(sum_d.values()) or 1
        sorted_sum = sorted(sum_d.items(), key=lambda x: -x[1])[:5]
        lines.append(f"  Top-5 高频和值: "
                     f"{', '.join(f'{k}({v})' for k, v in sorted_sum)}")
        lines.append("")

        lines.append("📐 跨度分布:")
        total_span = sum(span_d.values()) or 1
        for s in range(10):
            v = span_d[s]
            pct = v / total_span * 100
            lines.append(f"  跨度 {s}: {v:>4} 次 ({pct:>5.1f}%)")
        lines.append("")

        lines.append("🔢 AC 值分布:")
        total_ac = sum(ac_d.values()) or 1
        for a in range(4):
            v = ac_d[a]
            pct = v / total_ac * 100
            lines.append(f"  AC={a}: {v:>4} 次 ({pct:>5.1f}%)")
        lines.append("")

        lines.append("🎯 012 路 Top-5:")
        sorted_o12 = sorted(o12_d.items(), key=lambda x: -x[1])[:5]
        lines.append(f"  {', '.join(f'{k}({v})' for k, v in sorted_o12)}")
        lines.append("")

        lines.append("=" * 60)
        lines.append(f"💡 解读:用这些分布可估算每个号/形态的先验概率")
        lines.append(f"   比如百位热号 {hot[:3]},策略更倾向选它们")

        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, "\n".join(lines))
        self.analysis_text.config(state=tk.DISABLED)
