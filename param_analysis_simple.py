"""
排列5参数优化分析脚本 (简化版)
目标：找到最优参数设置，使得过滤后每个位置剩余3-5个号码
"""
import json
import os
import sys
import itertools
from collections import Counter

POS_NAMES_CN = ["万位", "千位", "百位", "十位", "个位"]
POS_KEYS = ["w", "q", "b", "s", "g"]


def load_history_json():
    """直接从JSON加载历史数据，避免UI相关导入"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
    if not os.path.exists(path):
        print("⚠️  history.json 不存在")
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️  读取 history.json 失败: {e}")
        return []
    # 过滤有效数据
    valid = []
    for r in data:
        num = str(r.get("number", "")).strip()
        if len(num) == 5 and num.isdigit():
            valid.append(r)
    valid.sort(key=lambda x: str(x.get("issue", "")))
    return valid


# ========== 统计工具函数 ==========

def position_frequency(records, pos):
    counter = Counter()
    for r in records:
        num = str(r.get("number", "")).zfill(5)
        n = int(num[pos])
        if 0 <= n <= 9:
            counter[n] += 1
    return {d: counter.get(d, 0) for d in range(10)}


def position_frequency_weighted(records, pos, decay=0.95):
    if not records:
        return {d: 0.0 for d in range(10)}
    weights = [decay ** (len(records) - 1 - i) for i in range(len(records))]
    freq = {d: 0.0 for d in range(10)}
    for r, w in zip(records, weights):
        num = str(r.get("number", "")).zfill(5)
        n = int(num[pos])
        if 0 <= n <= 9:
            freq[n] += w
    return freq


def laplace_smooth(freq, alpha=1.0):
    total = sum(freq.values()) + alpha * len(freq)
    return {k: (v + alpha) / total for k, v in freq.items()}


def top_n_keys(dist, n):
    sorted_items = sorted(dist.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in sorted_items[:n]]


def cold_hot_numbers(records, pos, window=20, top_n=5):
    recent = records[-window:] if len(records) > window else records
    freq = position_frequency(recent, pos)
    sorted_items = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    hot = [d for d, _ in sorted_items[:top_n]]
    cold = [d for d, _ in sorted_items[-top_n:]]
    return hot, cold


# ========== 策略函数 ==========

def strategy_random(train_data, top_n):
    import random
    n = min(top_n, 10)
    return {pk: sorted(random.sample(range(10), n)) for pk in POS_KEYS}


def strategy_frequency(train_data, top_n):
    result = {}
    for pos, key in enumerate(POS_KEYS):
        freq = position_frequency(train_data, pos)
        top = top_n_keys(freq, top_n)
        result[key] = sorted(top)
    return result


def strategy_smoothed(train_data, top_n, alpha=1.0):
    result = {}
    for pos, key in enumerate(POS_KEYS):
        freq = position_frequency(train_data, pos)
        prob = laplace_smooth(freq, alpha)
        top = top_n_keys(prob, top_n)
        result[key] = sorted(top)
    return result


def strategy_decay(train_data, top_n, decay=0.95):
    result = {}
    for pos, key in enumerate(POS_KEYS):
        freq = position_frequency_weighted(train_data, pos, decay)
        top = top_n_keys(freq, top_n)
        result[key] = sorted(top)
    return result


def strategy_coldhot(train_data, top_n, window=20):
    result = {}
    for pos, key in enumerate(POS_KEYS):
        hot, _ = cold_hot_numbers(train_data, pos, window, top_n)
        result[key] = sorted(hot)
    return result


# ========== 回测引擎 ==========

def evaluate_prediction(predicted, actual):
    actual = str(actual).zfill(5)
    hit_pos = []
    for i, key in enumerate(POS_KEYS):
        if i >= len(actual):
            break
        if int(actual[i]) in predicted.get(key, []):
            hit_pos.append(POS_NAMES_CN[i])
    return {
        "hit_count": len(hit_pos),
        "hit_pos": hit_pos,
        "is_zhixuan": len(hit_pos) == 5,
    }


def run_backtest(history, strategy_fn, top_n, train_size=100, test_size=30, step=1):
    """简单回测"""
    results = []
    n = len(history)
    if n < train_size + 1:
        return {"error": f"数据不足，需要至少{train_size+1}期"}

    start = 0
    while start + train_size + 1 <= n:
        train = history[start:start + train_size]
        end_test = min(start + train_size + test_size, n)
        test = history[start + train_size:end_test]

        for record in test:
            pred = strategy_fn(train, top_n)
            num = str(record.get("number", "")).zfill(5)
            eval_r = evaluate_prediction(pred, num)
            results.append(eval_r)

        start += step
        if len(results) >= 500:  # 限制结果数，避免太慢
            break

    if not results:
        return {"error": "无结果"}

    total = len(results)
    hit_dist = Counter()
    pos_hits = Counter()
    zhixuan = 0

    for r in results:
        hc = r["hit_count"]
        hit_dist[hc] += 1
        for p in r["hit_pos"]:
            pos_hits[p] += 1
        if r["is_zhixuan"]:
            zhixuan += 1

    return {
        "total": total,
        "avg_hit": sum(hit_dist[k] * k for k in hit_dist) / total,
        "hit_distribution": {k: hit_dist.get(k, 0) for k in range(6)},
        "hit_distribution_rate": {k: hit_dist.get(k, 0) / total for k in range(6)},
        "pos_rates": {p: pos_hits[p] / total for p in POS_NAMES_CN},
        "zhixuan_count": zhixuan,
        "zhixuan_rate": zhixuan / total,
    }


# ========== 主分析流程 ==========

def main():
    print("🎰 排列5参数优化分析工具")
    print("=" * 70)
    print("目标：分析最优参数设置 → 每位置剩余 3-5 个号码")

    history = load_history_json()
    print(f"\n📂 历史数据: {len(history)} 期有效")
    if history:
        print(f"   期号范围: {history[0].get('issue')} ~ {history[-1].get('issue')}")

    # ========== 第一部分：理论计算 ==========
    print("\n" + "=" * 70)
    print("📐 第一部分：理论计算分析")
    print("=" * 70)

    print("\n📍 【1.1 定位选择 - 每位置选N个号码的总注数】")
    print("-" * 80)
    header = f"{'每位选号':>8} | {'总注数':>10} | {'占比':>10} | {'5位全中概率':>14} | 说明"
    print(header)
    print("-" * 80)
    for n in range(1, 11):
        total = n ** 5
        ratio = total / 100000 * 100
        zhixuan_prob = (n / 10) ** 5 * 100
        if 3 <= n <= 5:
            if n == 3:
                note = "← 激进(243注)"
            elif n == 4:
                note = "← 均衡推荐(1024注) ⭐"
            else:
                note = "← 保守(3125注)"
        else:
            note = ""
        print(f"{n:>8d} | {total:>10d} | {ratio:>9.2f}% | {zhixuan_prob:>13.4f}% | {note}")

    # 生成100000注用于过滤力度计算
    print("\n🔍 【1.2 形态过滤单独力度估算】")
    all_nums = [f"{i:05d}" for i in range(100000)]

    # 和值过滤
    def filter_sum(nums, low, high):
        return [n for n in nums if low <= sum(map(int, n)) <= high]

    print(f"\n{'和值过滤':<22} | {'剩余注数':>10} | {'过滤比例':>10}")
    print("-" * 60)
    for name, low, high in [
        ("15-30 (常用区间)", 15, 30),
        ("18-27 (中间段)", 18, 27),
        ("20-25 (核心区)", 20, 25),
    ]:
        cnt = len(filter_sum(all_nums, low, high))
        print(f"{name:<22} | {cnt:>10d} | {(1-cnt/100000)*100:>9.2f}%")

    # 跨度过滤
    def filter_span(nums, low, high):
        return [n for n in nums if low <= (max(map(int, n)) - min(map(int, n))) <= high]

    print(f"\n{'跨度过滤':<22} | {'剩余注数':>10} | {'过滤比例':>10}")
    print("-" * 60)
    for name, low, high in [
        ("3-9 (排除极窄)", 3, 9),
        ("4-8 (常用区间)", 4, 8),
        ("5-7 (集中区)", 5, 7),
    ]:
        cnt = len(filter_span(all_nums, low, high))
        print(f"{name:<22} | {cnt:>10d} | {(1-cnt/100000)*100:>9.2f}%")

    # 组合策略估算
    print("\n🎯 【1.3 组合策略推荐 - 目标：300-3000注】")
    print("-" * 80)
    strategies = [
        ("Top-4 定位(4^5)", 4**5),
        ("Top-4 + 和值18-27", int(4**5 * (len(filter_sum(all_nums, 18, 27)) / 100000))),
        ("Top-4 + 和值18-27 + 跨度4-8",
         int(4**5 * (len(filter_sum(all_nums, 18, 27)) / 100000) * (len(filter_span(all_nums, 4, 8)) / 100000))),
        ("Top-5 定位(5^5)", 5**5),
        ("Top-5 + 和值20-25", int(5**5 * (len(filter_sum(all_nums, 20, 25)) / 100000))),
        ("Top-3 定位(3^5)", 3**5),
        ("Top-3 + 和值15-30", int(3**5 * (len(filter_sum(all_nums, 15, 30)) / 100000))),
    ]
    header = f"{'策略':<35} | {'预期注数':>10} | {'建议':<20}"
    print(header)
    print("-" * 80)
    for name, count in strategies:
        if count < 100:
            sug = "⚠️ 过少(易过杀)"
        elif count < 300:
            sug = "🔻偏少(激进)"
        elif count <= 3000:
            sug = "✅ 合适范围 ⭐"
        elif count <= 10000:
            sug = "🔺偏多"
        else:
            sug = "⚠️过多"
        print(f"{name:<35} | {count:>10d} | {sug:<20}")

    # ========== 第二部分：历史数据统计 ==========
    if history:
        print("\n" + "=" * 70)
        print("📊 第二部分：历史数据统计分析")
        print("=" * 70)

        n = len(history)

        print("\n📍 【2.1 各位置频率 Top-5】")
        print("-" * 80)

        pos_recommend = {}
        for pos_idx, pos_name in enumerate(POS_NAMES_CN):
            freq = position_frequency(history, pos_idx)
            total = sum(freq.values())
            sorted_freq = sorted(freq.items(), key=lambda x: (-x[1], x[0]))

            print(f"\n{pos_name}:")
            print(f"  {'排名':<4} {'号码':<4} {'次数':<6} {'频率':<8} {'累积'}")
            cum = 0
            for rank, (num, count) in enumerate(sorted_freq[:7]):
                pct = count / total * 100
                cum += pct
                star = " ★" if rank < 3 else (" ☆" if rank < 5 else "")
                print(f"  {rank+1:<4} {num:<4} {count:<6} {pct:<7.2f}% {cum:.1f}%{star}")

            pos_recommend[pos_idx] = {
                "top3": sorted([x[0] for x in sorted_freq[:3]]),
                "top4": sorted([x[0] for x in sorted_freq[:4]]),
                "top5": sorted([x[0] for x in sorted_freq[:5]]),
            }

        print("\n🎯 【2.2 基于历史频率的三套推荐方案】")
        print("-" * 80)

        for scheme_name, key_n in [("激进(Top-3/位)", "top3"), ("均衡(Top-4/位)⭐", "top4"), ("保守(Top-5/位)", "top5")]:
            n_per = 3 if key_n == "top3" else (4 if key_n == "top4" else 5)
            print(f"\n🔹 {scheme_name}")
            total_coverage = 1
            for pos_idx, pos_name in enumerate(POS_NAMES_CN):
                nums = pos_recommend[pos_idx][key_n]
                freq = position_frequency(history, pos_idx)
                total_f = sum(freq.values())
                cov = sum(freq[x] for x in nums) / total_f * 100
                total_coverage *= cov / 100
                nums_str = " ".join(str(x) for x in nums)
                print(f"   {pos_name}: {nums_str:<14} 单覆盖={cov:.1f}%")
            print(f"   → 总注数: {n_per**5} 注 | 预期5位同中覆盖率: {total_coverage*100:.2f}%")

        # 冷热号对比
        print("\n🔥 【2.3 稳定热号 (近30期 ∩ 全部历史)】")
        print("-" * 80)
        for pos_idx, pos_name in enumerate(POS_NAMES_CN):
            hot_30, _ = cold_hot_numbers(history, pos_idx, window=min(30, len(history)), top_n=5)
            hot_all, _ = cold_hot_numbers(history, pos_idx, window=len(history), top_n=5)
            stable = sorted(set(hot_30) & set(hot_all))
            print(f"  {pos_name}: 近30期热{sorted(hot_30)} ∩ 全期热{sorted(hot_all)} = 稳定热号{stable}")

        # 和值/跨度分布
        print("\n📈 【2.4 历史高频和值与跨度】")
        print("-" * 80)
        sum_counter = Counter()
        span_counter = Counter()
        for r in history:
            num = str(r.get("number", "")).zfill(5)
            s = sum(map(int, num))
            sp = max(map(int, num)) - min(map(int, num))
            sum_counter[s] += 1
            span_counter[sp] += 1

        print(f"\n高频和值 Top-5: ", end="")
        for s, c in sum_counter.most_common(5):
            print(f"{s}({c}次) ", end="")
        print()
        print(f"建议和值区间: 18-27 (中间高频段)")

        print(f"\n跨度频率: ", end="")
        for s in range(10):
            c = span_counter.get(s, 0)
            print(f"{s}:{c} ", end="")
        print()
        print(f"建议跨度区间: 4-8 (高频跨度)")

    # ========== 第三部分：回测分析 ==========
    if history and len(history) >= 30:
        print("\n" + "=" * 70)
        print("⚔️  第三部分：回测分析")
        print("=" * 70)

        train_sz = min(100, max(15, len(history) - 15))
        test_sz = min(20, max(5, len(history) - train_sz))
        print(f"\n回测配置: 训练={train_sz}期, 测试≈{test_sz}期, 数据={len(history)}期")
        print("(注: 数据较少时回测仅供参考)\n")

        # 策略定义
        strategies = [
            ("随机基准", lambda t, n: strategy_random(t, n)),
            ("简单频率", lambda t, n: strategy_frequency(t, n)),
            ("平滑频率α=1", lambda t, n: strategy_smoothed(t, n, 1.0)),
            ("衰减加权d=0.95", lambda t, n: strategy_decay(t, n, 0.95)),
            ("冷热号w=20", lambda t, n: strategy_coldhot(t, n, min(20, len(t)))),
        ]

        # Top-N扫描 (用平滑频率)
        print("📍 【3.1 每位置选N个号码 - 回测命中率 (平滑频率策略)】")
        print("-" * 90)
        header = f"{'每位置N':>8} | {'平均命中':>8} | {'随机期望':>8} | {'0位':>6} | {'2位+':>6} | {'3位+':>6} | {'5位全中':>10}"
        print(header)
        print("-" * 90)

        for top_n in [3, 4, 5]:
            r = run_backtest(history, lambda t, n=top_n: strategy_smoothed(t, n, 1.0),
                            top_n, train_size=train_sz, test_size=test_sz, step=5)
            if "error" in r:
                print(f"Top-{top_n:<4} | 错误: {r['error']}")
                continue
            avg = r["avg_hit"]
            expected = 5 * top_n / 10
            dist = r["hit_distribution_rate"]
            hit2plus = sum(dist.get(k, 0) for k in [2, 3, 4, 5]) * 100
            hit3plus = sum(dist.get(k, 0) for k in [3, 4, 5]) * 100
            zx = f"{r['zhixuan_count']}/{r['total']}"
            marker = " ← 目标范围" if 3 <= top_n <= 5 else ""
            print(f"Top-{top_n:<4} | {avg:>7.3f} | {expected:>7.3f} | "
                  f"{dist.get(0,0)*100:>5.1f}% | {hit2plus:>5.1f}% | {hit3plus:>5.1f}% | {zx:>9}{marker}")

        # 策略对比 (固定Top-4)
        print(f"\n⚔️  【3.2 策略对比 (固定 Top-4/位)】")
        print("-" * 90)
        header = f"{'策略':<20} | {'平均命中':>8} | {'超随机':>7} | {'3位+命中':>8} | {'5位全中':>10}"
        print(header)
        print("-" * 90)

        best_sname = None
        best_avg = -1
        for sname, sfn in strategies:
            r = run_backtest(history, lambda t, sfn=sfn: sfn(t, 4), 4,
                            train_size=train_sz, test_size=test_sz, step=5)
            if "error" in r:
                continue
            avg = r["avg_hit"]
            expected = 5 * 4 / 10
            diff = (avg - expected) / expected * 100 if expected > 0 else 0
            dist = r["hit_distribution_rate"]
            hit3plus = sum(dist.get(k, 0) for k in [3, 4, 5]) * 100
            zx = f"{r['zhixuan_count']}/{r['total']}"
            if avg > best_avg:
                best_avg = avg
                best_sname = sname
            marker = " 👑" if sname == best_sname and avg > expected else ""
            print(f"{sname:<20} | {avg:>7.3f} | {diff:>+6.1f}% | {hit3plus:>7.1f}% | {zx:>9}{marker}")

        # 组合热力图
        print(f"\n🔥 【3.3 策略×选号数 效果矩阵 (数值=平均命中位-随机期望)】")
        print("-" * 70)
        header = f"{'策略':<20}" + "".join(f" |  Top-{n:>2}" for n in [3, 4, 5])
        print(header)
        print("-" * 70)

        best_combo_name = None
        best_combo_diff = -999
        for sname, sfn in strategies:
            row = f"{sname:<20}"
            for tn in [3, 4, 5]:
                r = run_backtest(history, lambda t, sfn=sfn, tn=tn: sfn(t, tn), tn,
                                train_size=train_sz, test_size=test_sz, step=8)
                if "error" in r:
                    row += " |   ERR"
                    continue
                avg = r["avg_hit"]
                expected = 5 * tn / 10
                diff = avg - expected
                if diff > best_combo_diff:
                    best_combo_diff = diff
                    best_combo_name = (sname, tn)
                if diff > 0.3:
                    cell = f" | 🟢{diff:>+5.2f}"
                elif diff > 0:
                    cell = f" | 🟡{diff:>+5.2f}"
                elif diff > -0.3:
                    cell = f" | 🟠{diff:>+5.2f}"
                else:
                    cell = f" | 🔴{diff:>+5.2f}"
                row += cell
            print(row)

        if best_combo_name:
            print(f"\n🏆 回测最佳: {best_combo_name[0]} + 每位置{best_combo_name[1]}个号")

    # ========== 第四部分：最终推荐 ==========
    print("\n" + "=" * 70)
    print("🎯 第四部分：最优参数设置总结")
    print("=" * 70)

    print("""
┌──────────────────────────────────────────────────────────────────────┐
│                    ✨ 推荐参数配置方案 ✨                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🅰️  最简单方案：纯定位选号 (无需叠加其他过滤)                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  均衡推荐 ⭐⭐⭐ : 每位置选 Top-4 个号码                     │     │
│  │    · 总注数: 4^5 = 1024 注 (适中范围)                       │     │
│  │    · 单位置命中概率: ~40% (随机理论)                        │     │
│  │    · 成本与命中率的最佳平衡点                               │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  保守方案: 每位置选 Top-5 个号码                            │     │
│  │    · 总注数: 5^5 = 3125 注 (成本较高)                       │     │
│  │    · 单位置命中概率: 50%                                    │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  激进方案: 每位置选 Top-3 个号码                            │     │
│  │    · 总注数: 3^5 = 243 注 (成本低，风险高)                  │     │
│  │    · 单位置命中概率: 30%                                    │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  🅱️  推荐方案：定位 + 形态过滤组合 (更精准)                          │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  1️⃣ 定位选择: 每位置 Top-5 (或 Top-4)                       │     │
│  │  2️⃣ 和值过滤: 保留 18-27 (中间高频区间，约过滤50%)           │     │
│  │  3️⃣ 跨度过滤: 保留 4-8 (高频跨度，约再过滤25%)              │     │
│  │  4️⃣ (可选) 排除极端形态: 5大/5小/5奇/5偶/5质/5合            │     │
│  │  → 预期结果: Top-5组合约 3125×50%×75% ≈ 1172 注            │     │
│  │             Top-4组合约 1024×50%×75% ≈ 384 注              │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  🅲️  数据驱动方案：使用「回测中心」                                  │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  1. 录入至少 100+ 期历史数据 (「历史查询」Tab)              │     │
│  │  2. 进入「回测中心」Tab                                      │     │
│  │  3. 策略选择: 平滑频率(α=1) 或 衰减加权(d=0.95)             │     │
│  │  4. Top-N 设置: 4 (每位置4个) 或 5 (每位置5个)              │     │
│  │  5. 点击「跑回测」验证各策略表现                             │     │
│  │  6. 跑完后「详细记录」顶部会显示下一期预测号码               │     │
│  │  7. 不满意可换策略/参数重跑，或用「⚔️ 策略对比」一键跑全部   │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  🔧 微调技巧:                                                         │
│  · 结果太多 (>5个/位): 减少定位号数 / 缩小和值跨度区间 / 加杀号     │
│  · 结果太少 (<3个/位): 增加定位号数 / 放宽和值跨度区间 / 去限制     │
│  · 冷热号选号可参考「定位定胆」Tab 的统计结果                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    main()
