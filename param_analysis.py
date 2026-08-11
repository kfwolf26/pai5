"""
排列5参数优化分析脚本
目标：找到最优参数设置，使得过滤后每个位置剩余3-5个号码
"""
import json
import os
import sys
import itertools
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.statistics import (
    position_frequency,
    position_frequency_weighted,
    cold_hot_numbers,
    laplace_smooth,
    top_n_keys,
    evaluate_prediction,
    aggregate_metrics,
    extract_number,
    expected_hit_by_random,
)
from utils.history_manager import HistoryManager
from modules.backtest import (
    BacktestEngine,
    STRATEGY_REGISTRY,
    BT_POS_KEYS,
    BT_POS_NAMES,
)

POS_NAMES_CN = ["万位", "千位", "百位", "十位", "个位"]


def load_history():
    """加载历史数据"""
    hm = HistoryManager()
    history = hm.get_all()
    if not history:
        print("⚠️  未找到历史数据，使用模拟数据进行理论分析")
        return []
    history = sorted(history, key=lambda x: str(x.get("issue", "")))
    # 过滤有效数据
    valid = []
    for r in history:
        num = str(r.get("number", "")).strip()
        if len(num) == 5 and num.isdigit():
            valid.append(r)
    print(f"✅ 加载历史数据: {len(valid)} 期有效记录")
    if valid:
        print(f"   期号范围: {valid[0].get('issue')} ~ {valid[-1].get('issue')}")
    return valid


def theoretical_analysis():
    """
    理论计算分析：
    1. 仅使用定位选择时，每位置选N个的总注数
    2. 叠加其他过滤条件后的预期剩余注数
    """
    print("\n" + "=" * 70)
    print("📐 第一部分：理论计算分析")
    print("=" * 70)

    # 1. 定位选择分析
    print("\n📍 【1.1 定位选择 - 每位置选N个号码】")
    print("-" * 70)
    print(f"{'每位选号数':>10} | {'总注数':>10} | {'占总注数比例':>12} | {'理论5位全中概率':>16}")
    print("-" * 70)
    for n in range(1, 11):
        total = n ** 5
        ratio = total / 100000 * 100
        zhixuan_prob = (n / 10) ** 5 * 100
        marker = " ← 目标范围(3-5)" if 3 <= n <= 5 else ""
        print(f"{n:>10d} | {total:>10d} | {ratio:>11.2f}% | {zhixuan_prob:>15.4f}%{marker}")

    # 2. 常用过滤条件的过滤力度估算
    print("\n🔍 【1.2 常用过滤条件的单独过滤力度】")
    print("-" * 70)

    # 生成全部100000注
    all_nums = [f"{i:05d}" for i in range(100000)]

    # 和值过滤（中间范围）
    def filter_sum(nums, low, high):
        return [n for n in nums if low <= sum(map(int, n)) <= high]

    sum_ranges = [
        ("和值 15-30 (常用中间段)", 15, 30),
        ("和值 18-27 (更集中)", 18, 27),
        ("和值 20-25 (核心区间)", 20, 25),
    ]
    print(f"\n{'和值过滤条件':<25} | {'剩余注数':>10} | {'过滤力度':>10}")
    print("-" * 70)
    for name, low, high in sum_ranges:
        remaining = len(filter_sum(all_nums, low, high))
        power = (1 - remaining / 100000) * 100
        print(f"{name:<25} | {remaining:>10d} | {power:>9.2f}%")

    # 跨度过滤
    def filter_span(nums, low, high):
        return [n for n in nums if low <= (max(map(int, n)) - min(map(int, n))) <= high]

    span_ranges = [
        ("跨度 3-9 (排除极窄)", 3, 9),
        ("跨度 4-8 (常用区间)", 4, 8),
        ("跨度 5-7 (集中区间)", 5, 7),
    ]
    print(f"\n{'跨度过滤条件':<25} | {'剩余注数':>10} | {'过滤力度':>10}")
    print("-" * 70)
    for name, low, high in span_ranges:
        remaining = len(filter_span(all_nums, low, high))
        power = (1 - remaining / 100000) * 100
        print(f"{name:<25} | {remaining:>10d} | {power:>9.2f}%")

    # 3. 组合过滤策略分析（定位 + 形态过滤）
    print("\n🎯 【1.3 组合过滤策略 - 目标：每位置剩余3-5个，总注300-3000】")
    print("-" * 70)

    strategies = [
        ("仅定位：每位置5个", lambda: 5**5),
        ("仅定位：每位置4个", lambda: 4**5),
        ("仅定位：每位置3个", lambda: 3**5),
        ("定位3个 + 和值15-30", lambda: int(3**5 * (len(filter_sum(all_nums, 15, 30)) / 100000))),
        ("定位4个 + 和值18-27", lambda: int(4**5 * (len(filter_sum(all_nums, 18, 27)) / 100000))),
        ("定位4个 + 跨度4-8", lambda: int(4**5 * (len(filter_span(all_nums, 4, 8)) / 100000))),
        ("定位5个 + 和值20-25 + 跨度5-7",
         lambda: int(5**5 * (len(filter_sum(all_nums, 20, 25)) / 100000) * (len(filter_span(all_nums, 5, 7)) / 100000))),
        ("定位3个 + 和值20-25", lambda: int(3**5 * (len(filter_sum(all_nums, 20, 25)) / 100000))),
    ]

    print(f"{'策略':<35} | {'预期总注数':>12} | {'评估':<20}")
    print("-" * 70)
    for name, calc_fn in strategies:
        count = calc_fn()
        if count < 100:
            eval_str = "⚠️  太少(可能过杀)"
        elif count < 300:
            eval_str = "🔻 偏少(风险高)"
        elif count <= 3000:
            eval_str = "✅ 合适范围"
        elif count <= 10000:
            eval_str = "🔺 偏多(成本高)"
        else:
            eval_str = "⚠️  太多(过滤不足)"
        print(f"{name:<35} | {count:>12d} | {eval_str:<20}")


def historical_statistics_analysis(history):
    """
    基于历史数据的统计分析
    """
    print("\n" + "=" * 70)
    print("📊 第二部分：历史数据统计分析")
    print("=" * 70)

    if not history:
        print("⚠️  无历史数据，跳过统计分析")
        return {}

    n = len(history)

    # 1. 各位置频率分析
    print("\n📍 【2.1 各位置号码出现频率统计】")
    print("-" * 70)

    pos_top_n = {}  # 记录每个位置的top3, top4, top5号码

    for pos_idx, pos_name in enumerate(POS_NAMES_CN):
        freq = position_frequency(history, pos_idx)
        total = sum(freq.values())
        sorted_freq = sorted(freq.items(), key=lambda x: (-x[1], x[0]))

        print(f"\n{pos_name} (共 {total} 期):")
        print(f"  {'号码':<6} {'次数':<6} {'频率':<8} {'累积频率':<10}")
        cum_pct = 0
        top_numbers = []
        for rank, (num, count) in enumerate(sorted_freq):
            pct = count / total * 100
            cum_pct += pct
            marker = ""
            if rank < 3:
                marker = " ★Top3"
                top_numbers.append(num)
            elif rank < 5:
                marker = " ☆Top5"
                top_numbers.append(num)
            print(f"  {num:<6} {count:<6} {pct:<7.2f}% {cum_pct:<9.2f}%{marker}")

        pos_top_n[pos_idx] = {
            "top3": sorted([x[0] for x in sorted_freq[:3]]),
            "top4": sorted([x[0] for x in sorted_freq[:4]]),
            "top5": sorted([x[0] for x in sorted_freq[:5]]),
            "freq_all": sorted_freq,
        }

    # 2. 推荐每位置选号方案
    print("\n🎯 【2.2 基于历史频率的推荐选号方案】")
    print("-" * 70)

    for scheme_name, n_per_pos in [("保守方案(Top-5)", 5), ("均衡方案(Top-4)", 4), ("激进方案(Top-3)", 3)]:
        print(f"\n🔹 {scheme_name} (每位置{n_per_pos}个):")
        scheme = {}
        for pos_idx, pos_name in enumerate(POS_NAMES_CN):
            top_nums = pos_top_n[pos_idx][f"top{n_per_pos}"]
            scheme[BT_POS_KEYS[pos_idx]] = top_nums
            nums_str = " ".join(str(x) for x in top_nums)
            # 计算累积频率
            freq = pos_top_n[pos_idx]["freq_all"]
            top_freq_items = freq[:n_per_pos]
            cum_freq = sum(c for _, c in top_freq_items)
            pct = cum_freq / n * 100
            print(f"   {pos_name}: {nums_str:<15} (覆盖频率: {pct:.1f}%)")

        total = n_per_pos ** 5
        coverage = 1
        for pos_idx in range(5):
            freq = pos_top_n[pos_idx]["freq_all"]
            top_freq_items = freq[:n_per_pos]
            cum_freq = sum(c for _, c in top_freq_items)
            coverage *= (cum_freq / n)
        print(f"   → 总注数: {total} 注 | 理论5位覆盖率: {coverage*100:.2f}%")

    # 3. 和值/跨度分布
    print("\n📈 【2.3 历史和值/跨度分布】")
    print("-" * 70)

    # 和值分布
    sum_counter = Counter()
    span_counter = Counter()
    for r in history:
        num = extract_number(r)
        s = sum(map(int, num))
        span_val = max(map(int, num)) - min(map(int, num))
        sum_counter[s] += 1
        span_counter[span_val] += 1

    print("\n和值分布 Top-10:")
    for s, cnt in sum_counter.most_common(10):
        pct = cnt / n * 100
        bar = "█" * int(pct * 3)
        print(f"  和值={s:>2}: {cnt:>4}次 ({pct:>5.1f}%) {bar}")

    print("\n跨度分布:")
    for s in range(10):
        cnt = span_counter.get(s, 0)
        pct = cnt / n * 100
        bar = "█" * int(pct * 5)
        marker = " ← 高频" if 5 <= s <= 8 else ""
        print(f"  跨度={s}: {cnt:>4}次 ({pct:>5.1f}%) {bar}{marker}")

    # 4. 冷热号分析（最近30期 vs 全部历史）
    print("\n🔥 【2.4 冷热号分析 - 最近30期 vs 全部历史】")
    print("-" * 70)

    recent_30 = history[-30:] if len(history) >= 30 else history
    for pos_idx, pos_name in enumerate(POS_NAMES_CN):
        hot_recent, cold_recent = cold_hot_numbers(history, pos_idx, window=30, top_n=5)
        hot_all, cold_all = cold_hot_numbers(history, pos_idx, window=len(history), top_n=5)

        # 找交集（稳定热号）
        stable_hot = set(hot_recent) & set(hot_all)
        print(f"\n{pos_name}:")
        print(f"  最近30期热号: {sorted(hot_recent)}")
        print(f"  全部历史热号: {sorted(hot_all)}")
        print(f"  ★ 稳定热号(交集): {sorted(stable_hot)}")

    return pos_top_n


def backtest_analysis(history):
    """
    回测分析：不同策略 + 不同Top-N的表现
    """
    print("\n" + "=" * 70)
    print("⚔️  第三部分：回测分析 - 不同策略参数的真实表现")
    print("=" * 70)

    if len(history) < 130:
        print(f"⚠️  历史数据不足({len(history)}期)，建议至少130期(100训练+30测试)")
        print("   将使用当前可用数据运行")

    engine = BacktestEngine(history)
    n = len(engine.history)

    # 回测参数
    train_size = min(100, max(20, n - 20))
    test_size = min(30, max(5, n - train_size))

    print(f"\n回测配置: 训练={train_size}期, 测试={test_size}期, 总数据={n}期")

    # 1. Top-N扫描：固定策略，测试Top-N=3,4,5的表现
    print("\n📍 【3.1 Top-N扫描 (平滑频率策略)】")
    print("-" * 70)

    strategy = STRATEGY_REGISTRY["平滑频率(α=1)"]()

    header = f"{'Top-N':<8} | {'平均命中':>8} | {'0位':>6} | {'1位':>6} | {'2位':>6} | {'3位':>6} | {'4位':>6} | {'5位全中':>8} | {'评价':<10}"
    print(header)
    print("-" * len(header))

    top_n_results = {}
    for top_n in [3, 4, 5, 6, 7]:
        result = engine.run(strategy, top_n=top_n, train_size=train_size,
                           test_size=test_size, step=1)
        metrics = result.get("metrics", {})
        if not metrics:
            continue

        avg_hit = metrics.get("avg_hit", 0)
        expected = expected_hit_by_random(top_n)
        diff = (avg_hit - expected) / expected * 100 if expected > 0 else 0

        dist = metrics.get("hit_distribution_rate", {})
        total = metrics.get("total", 0)
        zx_count = metrics.get("zhixuan_count", 0)
        zx_rate = metrics.get("zhixuan_rate", 0) * 100

        # 评价
        if diff > 10:
            eval_str = "🔥 优秀"
        elif diff > 0:
            eval_str = "✅ 良好"
        elif diff > -10:
            eval_str = "➖ 一般"
        else:
            eval_str = "❌ 较差"

        marker = " ← 目标" if 3 <= top_n <= 5 else ""
        print(f"Top-{top_n:<4} | {avg_hit:>7.3f} | {dist.get(0,0)*100:>5.1f}% | {dist.get(1,0)*100:>5.1f}% | "
              f"{dist.get(2,0)*100:>5.1f}% | {dist.get(3,0)*100:>5.1f}% | {dist.get(4,0)*100:>5.1f}% | "
              f"{zx_count}/{total}({zx_rate:>4.2f}%) | {eval_str:<8}{marker}")

        top_n_results[top_n] = result

    # 2. 策略对比：固定Top-N=4，对比所有策略
    print("\n⚔️  【3.2 策略对比 (固定Top-4/位)】")
    print("-" * 70)

    header = f"{'策略':<22} | {'平均命中':>8} | {'随机期望':>8} | {'差值%':>7} | {'3位+命中':>8} | {'5位全中':>8}"
    print(header)
    print("-" * len(header))

    comparison = engine.compare(list(STRATEGY_REGISTRY.keys()),
                               top_n=4, train_size=train_size,
                               test_size=test_size, step=1)

    best_strategy = None
    best_avg = -1
    for name, result in sorted(comparison.items()):
        if "error" in result:
            print(f"{name:<22} | 错误: {result['error']}")
            continue
        metrics = result.get("metrics", {})
        if not metrics:
            continue

        avg_hit = metrics.get("avg_hit", 0)
        expected = expected_hit_by_random(4)
        diff = (avg_hit - expected) / expected * 100 if expected > 0 else 0

        dist = metrics.get("hit_distribution_rate", {})
        hit3plus = sum(dist.get(k, 0) for k in [3, 4, 5]) * 100
        total = metrics.get("total", 0)
        zx_count = metrics.get("zhixuan_count", 0)

        if avg_hit > best_avg:
            best_avg = avg_hit
            best_strategy = name

        marker = " 👑" if name == best_strategy and avg_hit > expected else ""
        print(f"{name:<22} | {avg_hit:>7.3f} | {expected:>7.3f} | {diff:>+6.1f}% | "
              f"{hit3plus:>7.1f}% | {zx_count}/{total}{marker}")

    # 3. 策略×Top-N组合热力图（文字版）
    print("\n🔥 【3.3 策略×Top-N 组合效果热力图】")
    print("-" * 70)
    print("(数值=平均命中位-随机期望，正=优于随机，负=差于随机)")

    test_topns = [3, 4, 5]
    strategy_names = list(STRATEGY_REGISTRY.keys())

    header = f"{'策略':<22}" + "".join(f" |  Top-{n:>2}" for n in test_topns)
    print(header)
    print("-" * len(header))

    best_combo = None
    best_combo_val = -999

    combo_results = {}

    for sname in strategy_names:
        if sname not in STRATEGY_REGISTRY:
            continue
        row = f"{sname:<22}"
        for tn in test_topns:
            try:
                strat = STRATEGY_REGISTRY[sname]()
                result = engine.run(strat, top_n=tn, train_size=train_size,
                                   test_size=test_size, step=1)
                metrics = result.get("metrics", {})
                avg_hit = metrics.get("avg_hit", 0)
                expected = expected_hit_by_random(tn)
                diff = avg_hit - expected
                combo_results[(sname, tn)] = {
                    "avg_hit": avg_hit,
                    "diff": diff,
                    "metrics": metrics,
                }
                if diff > best_combo_val:
                    best_combo_val = diff
                    best_combo = (sname, tn)

                if diff > 0.3:
                    cell = f" | 🟢{diff:>+5.2f}"
                elif diff > 0:
                    cell = f" | 🟡{diff:>+5.2f}"
                elif diff > -0.3:
                    cell = f" | 🟠{diff:>+5.2f}"
                else:
                    cell = f" | 🔴{diff:>+5.2f}"
            except Exception as e:
                cell = f" |  ERROR"
            row += cell
        print(row)

    if best_combo:
        print(f"\n🏆 最佳组合: {best_combo[0]} + Top-{best_combo[1]}")
        best = combo_results[best_combo]
        print(f"   平均命中位: {best['avg_hit']:.3f} (超出随机 {best['diff']:+.3f})")
        m = best['metrics']
        dist = m.get('hit_distribution_rate', {})
        print(f"   命中分布: ", end="")
        for k in range(6):
            print(f"{k}位={dist.get(k,0)*100:.1f}% ", end="")
        print()

    return best_combo, combo_results


def optimized_filter_recommendation(history, best_combo=None):
    """
    生成最终的优化过滤建议
    """
    print("\n" + "=" * 70)
    print("🎯 第四部分：最优参数设置方案推荐")
    print("=" * 70)

    if not history:
        print("⚠️  无历史数据，仅给出通用建议")
        history = []

    n = len(history)

    # 方案一：纯定位选号
    print("\n📋 方案A：纯定位选号（最简单，直接每位置选3-5个）")
    print("-" * 70)

    if history:
        # 基于历史频率
        print("\n基于历史频率的推荐（热号优先）：")
        for pos_idx, pos_name in enumerate(POS_NAMES_CN):
            freq = position_frequency(history, pos_idx)
            sorted_freq = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
            top3 = [x[0] for x in sorted_freq[:3]]
            top4 = [x[0] for x in sorted_freq[:4]]
            top5 = [x[0] for x in sorted_freq[:5]]
            print(f"  {pos_name}: Top3={sorted(top3)}, Top4={sorted(top4)}, Top5={sorted(top5)}")
    else:
        print("\n通用建议（无历史数据时）：")
        print("  可使用随机、或根据直觉/走势图选号")

    # 方案二：定位 + 形态过滤叠加
    print("\n📋 方案B：定位 + 形态过滤组合（推荐，更精准）")
    print("-" * 70)

    print("""
  推荐组合（总注数控制在 300-3000 注）：
  ┌─────────────────────────────────────────────────────────┐
  │ 1. 定位选择：每位置选 Top-4 个号码                        │
  │    → 基础注数：4^5 = 1024 注                             │
  │                                                         │
  │ 2. 和值过滤：保留 18-27（中间高频区间）                    │
  │    → 约过滤掉 50%，剩余 ~500 注                          │
  │    (配合Top-5定位的话约 3125 × 50% ≈ 1500 注)             │
  │                                                         │
  │ 3. 跨度过滤：保留 4-8（排除极端跨度）                      │
  │    → 再过滤掉约 30%，剩余 ~350 注                        │
  │                                                         │
  │ 4. (可选) 大小/奇偶形态：排除极端形态                      │
  │    → 排除 5大0小 / 0大5小 / 5奇0偶 / 0奇5偶              │
  └─────────────────────────────────────────────────────────┘
    """)

    # 方案三：基于回测最优策略
    if best_combo:
        print(f"\n📋 方案C：基于回测最优策略 ({best_combo[0]} + Top-{best_combo[1]})")
        print("-" * 70)
        print(f"""
  使用步骤：
  1. 打开「回测中心」Tab
  2. 策略选择：{best_combo[0]}
  3. Top-N设置：{best_combo[1]}（每位置剩余 {best_combo[1]} 个）
  4. 训练窗口：100期（数据不足时用50-80期）
  5. 点击「跑回测」验证效果
  6. 跑完后在「详细记录」最上方找到下一期预测
        """)

    # 参数微调建议
    print("\n🔧 第五部分：参数微调指南")
    print("=" * 70)

    print("""
  如果结果不在 3-5 个/位置 的范围内，可按以下方法调整：

  📌 【剩余号码 > 5个/位置 → 需要加强过滤】
     1. 减少定位选择的号码数（5→4→3）
     2. 增加杀号：每位杀 2-3 个冷号
     3. 缩小和值区间（如 20-25 代替 15-30）
     4. 缩小跨度区间（如 5-7 代替 3-9）
     5. 添加 012 路 / 大小奇偶 形态过滤

  📌 【剩余号码 < 3个/位置 → 需要放宽条件】
     1. 增加定位选择的号码数（3→4→5）
     2. 减少杀号或胆码限制
     3. 扩大和值区间（如 15-30 代替 20-25）
     4. 扩大跨度区间（如 3-9 代替 5-7）
     5. 取消部分形态过滤条件

  📌 【调整目标】
     • 稳健型：每位置 5 个（5^5=3125注）→ 命中概率高，成本高
     • 均衡型：每位置 4 个（4^5=1024注）→ 推荐平衡点
     • 激进型：每位置 3 个（3^5=243注）  → 命中概率低，成本低
    """)


def main():
    print("🎰 排列5参数优化分析工具")
    print("目标：分析最优参数设置 → 每位置剩余 3-5 个号码")

    # 加载历史数据
    history = load_history()

    # 1. 理论分析
    theoretical_analysis()

    # 2. 历史统计分析
    pos_top_n = historical_statistics_analysis(history)

    # 3. 回测分析
    best_combo = None
    if history:
        best_combo, _ = backtest_analysis(history)

    # 4. 最终推荐
    optimized_filter_recommendation(history, best_combo)


if __name__ == "__main__":
    main()
