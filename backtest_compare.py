"""回测策略对比部分 - 修复版"""
import json
import os
import itertools
from collections import Counter

POS_NAMES_CN = ["万位", "千位", "百位", "十位", "个位"]
POS_KEYS = ["w", "q", "b", "s", "g"]

def load_history():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    valid = []
    for r in data:
        num = str(r.get("number", "")).strip()
        if len(num) == 5 and num.isdigit():
            valid.append(r)
    valid.sort(key=lambda x: str(x.get("issue", "")))
    return valid

def position_frequency(records, pos):
    c = Counter()
    for r in records:
        n = int(str(r.get("number","")).zfill(5)[pos])
        if 0 <= n <= 9: c[n] += 1
    return {d: c.get(d, 0) for d in range(10)}

def position_frequency_weighted(records, pos, decay=0.95):
    if not records: return {d: 0.0 for d in range(10)}
    w = [decay ** (len(records) - 1 - i) for i in range(len(records))]
    freq = {d: 0.0 for d in range(10)}
    for r, w_ in zip(records, w):
        n = int(str(r.get("number","")).zfill(5)[pos])
        if 0 <= n <= 9: freq[n] += w_
    return freq

def laplace_smooth(freq, alpha=1.0):
    total = sum(freq.values()) + alpha * len(freq)
    return {k: (v + alpha) / total for k, v in freq.items()}

def top_n_keys(d, n):
    return [k for k, _ in sorted(d.items(), key=lambda x: (-x[1], x[0]))[:n]]

def cold_hot(records, pos, window, top_n):
    r = records[-window:] if len(records) > window else records
    f = position_frequency(r, pos)
    s = sorted(f.items(), key=lambda x: (-x[1], x[0]))
    return [d for d, _ in s[:top_n]], [d for d, _ in s[-top_n:]]

def evaluate(pred, actual):
    a = str(actual).zfill(5)
    hits = [POS_NAMES_CN[i] for i, k in enumerate(POS_KEYS) if int(a[i]) in pred.get(k, [])]
    return {"hit_count": len(hits), "hit_pos": hits, "is_zhixuan": len(hits)==5}

def run_bt(history, strat_fn, top_n, train_sz=100, step=8):
    results = []
    n = len(history)
    start = 0
    count = 0
    while start + train_sz + 1 <= n and count < 400:
        train = history[start:start + train_sz]
        test_idx = min(start + train_sz, n - 1)
        record = history[test_idx]
        pred = strat_fn(train, top_n)
        num = str(record.get("number", "")).zfill(5)
        results.append(evaluate(pred, num))
        start += step
        count += 1
    if not results: return {}
    total = len(results)
    hd = Counter(r["hit_count"] for r in results)
    zx = sum(1 for r in results if r["is_zhixuan"])
    return {
        "total": total,
        "avg_hit": sum(r["hit_count"] for r in results) / total,
        "dist_rate": {k: hd.get(k, 0) / total for k in range(6)},
        "zhixuan_count": zx,
    }

def main():
    history = load_history()
    print(f"历史数据: {len(history)} 期")
    train_sz = min(100, len(history) - 10)

    import random

    # 所有策略都返回 dict: {w: [...], q: [...], b: [...], s: [...], g: [...]}
    def s_random(train, n):
        return {k: sorted(random.sample(range(10), n)) for k in POS_KEYS}
    def s_freq(train, n):
        return {POS_KEYS[i]: sorted(top_n_keys(position_frequency(train, i), n)) for i in range(5)}
    def s_smooth(train, n):
        return {POS_KEYS[i]: sorted(top_n_keys(laplace_smooth(position_frequency(train, i)), n)) for i in range(5)}
    def s_decay(train, n):
        return {POS_KEYS[i]: sorted(top_n_keys(position_frequency_weighted(train, i, 0.95), n)) for i in range(5)}
    def s_coldhot(train, n):
        return {POS_KEYS[i]: sorted(cold_hot(train, i, min(20, len(train)), n)[0]) for i in range(5)}

    strategies = [
        ("随机基准", s_random),
        ("简单频率", s_freq),
        ("平滑频率α=1", s_smooth),
        ("衰减加权d=0.95", s_decay),
        ("冷热号w=20", s_coldhot),
    ]

    print("\n" + "="*90)
    print("策略对比 (固定 Top-4/位, 每位置剩余4个号码)")
    print("="*90)
    header = f"{'策略':<20} | {'平均命中':>8} | {'随机期望':>8} | {'超随机%':>8} | {'3位+命中':>8} | {'5位全中':>8}"
    print(header)
    print("-"*90)

    best_name = None
    best_avg = -1
    expected_4 = 5 * 4 / 10.0

    for sname, strat in strategies:
        r = run_bt(history, strat, 4, train_sz=train_sz)
        if not r:
            continue
        avg = r["avg_hit"]
        diff_pct = (avg - expected_4) / expected_4 * 100 if expected_4 > 0 else 0
        dist = r["dist_rate"]
        hit3 = sum(dist.get(k, 0) for k in [3,4,5]) * 100
        zx = f"{r['zhixuan_count']}/{r['total']}"
        if avg > best_avg:
            best_avg = avg
            best_name = sname
        marker = " 👑" if sname == best_name and avg > expected_4 else ""
        print(f"{sname:<20} | {avg:>7.3f} | {expected_4:>7.3f} | {diff_pct:>+7.1f}% | {hit3:>7.1f}% | {zx:>7}{marker}")

    print("\n" + "="*90)
    print("策略 × 选号数 效果矩阵 (每位置选N个)")
    print("="*90)
    header = f"{'策略':<20}"
    for n in [3, 4, 5]:
        header += f" |  Top-{n:>2}"
    print(header)
    print("-"*90)

    best_combo = None
    best_val = -999
    for sname, strat in strategies:
        row = f"{sname:<20}"
        for tn in [3, 4, 5]:
            r = run_bt(history, strat, tn, train_sz=train_sz)
            if not r:
                row += " |   ERR"
                continue
            avg = r["avg_hit"]
            exp = 5 * tn / 10.0
            diff = avg - exp
            if diff > best_val:
                best_val = diff
                best_combo = (sname, tn)
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

    if best_combo:
        print(f"\n🏆 综合最佳组合: {best_combo[0]} 策略 + 每位置选 {best_combo[1]} 个号")

if __name__ == "__main__":
    main()
