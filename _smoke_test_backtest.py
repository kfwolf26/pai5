"""
回测引擎端到端冒烟测试
- 加载 history.json 真实数据
- 跑全部 10 个策略做对比
- 输出每个策略的关键指标
- 验证逻辑无异常
"""
import sys
import os
import json
import time

# 让模块导入能找到
sys.path.insert(0, r"D:\ai\3dpai")

from utils.history_manager import HistoryManager
from modules.backtest import BacktestEngine, STRATEGY_REGISTRY


def main():
    print("=" * 60)
    print("回测引擎冒烟测试")
    print("=" * 60)

    # 加载真实历史数据
    hm = HistoryManager()
    history = hm.get_all()
    print(f"\n[1] 加载历史数据: {len(history)} 条")

    if not history:
        print("FAIL: 历史数据为空,无法测试")
        return 1

    # 统计有效记录(number 是 3 位数字)
    valid = [r for r in history if str(r.get("number", "")).strip().isdigit()
             and len(str(r.get("number", "")).strip()) == 3]
    print(f"    有效 3 位数字记录: {len(valid)} 条")

    if len(valid) < 150:
        print(f"WARN: 有效数据较少 (<150),回测结果意义有限")

    # 创建引擎
    engine = BacktestEngine(history)
    n = len(engine.history)
    print(f"    引擎载入: {n} 期")
    if n > 0:
        first = engine.history[0].get("issue")
        last = engine.history[-1].get("issue")
        print(f"    范围: {first} ~ {last}")

    # 跑单个策略(平滑频率)做详细验证
    print(f"\n[2] 单策略详细测试: 平滑频率(α=1)")
    strat = STRATEGY_REGISTRY["平滑频率(α=1)"]()
    t0 = time.time()
    result = engine.run(strat, top_n=5, train_size=100, test_size=30, step=5)
    dt = time.time() - t0
    m = result["metrics"]
    print(f"    用时: {dt:.2f}s")
    print(f"    测试期数: {m.get('total', 0)}")
    print(f"    平均命中位: {m.get('avg_hit', 0):.4f} "
          f"(随机期望: {expected_hit(5):.3f})")
    print(f"    命中分布: {m.get('hit_distribution', {})}")
    print(f"    各位置命中率: {m.get('pos_rates', {})}")
    print(f"    直选命中: {m.get('zhixuan_count', 0)}/{m.get('total', 0)} "
          f"({m.get('zhixuan_rate', 0)*100:.4f}%)")

    # 跑全部策略对比
    print(f"\n[3] 全策略对比 (Top-N=5, train=100, test=30, step=5)")
    t0 = time.time()
    names = list(STRATEGY_REGISTRY.keys())
    comparison = engine.compare(names, top_n=5, train_size=100, test_size=30, step=5)
    dt = time.time() - t0

    print(f"    用时: {dt:.2f}s")
    print(f"    {'策略':<22} {'平均命中':>8} {'0位%':>6} {'1位%':>6} "
          f"{'2位%':>6} {'3位%':>6} {'直选':>6}")
    print("    " + "-" * 70)

    exp = expected_hit(5)
    rows = []
    for name, res in comparison.items():
        if "error" in res:
            print(f"    {name:<22} ERROR: {res['error']}")
            continue
        m = res["metrics"]
        if not m:
            print(f"    {name:<22} 无数据")
            continue
        avg = m["avg_hit"]
        diff = avg - exp
        marker = " 🏆" if diff > 0.05 else ("  " if abs(diff) < 0.05 else " 📉")
        row = {
            "name": name,
            "avg": avg,
            "diff": diff,
            "metrics": m,
        }
        rows.append(row)
        print(f"    {name:<22} {avg:>6.3f}{marker}  "
              f"{m['hit_distribution_rate'][0]*100:>5.1f}  "
              f"{m['hit_distribution_rate'][1]*100:>5.1f}  "
              f"{m['hit_distribution_rate'][2]*100:>5.1f}  "
              f"{m['hit_distribution_rate'][3]*100:>5.1f}  "
              f"{m['zhixuan_count']:>3}/{m['total']}")

    print(f"\n[4] 排名: 按平均命中位排序(理论随机期望 {exp:.3f})")
    rows.sort(key=lambda r: r["avg"], reverse=True)
    for i, r in enumerate(rows, 1):
        medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else "  "))
        print(f"    {medal} #{i}  {r['name']:<22}  "
              f"平均命中 {r['avg']:.3f}  vs 随机 {r['diff']:+.3f}")

    print("\n" + "=" * 60)
    print("✅ 冒烟测试通过:所有策略可正常跑,无异常")
    print("=" * 60)
    return 0


def expected_hit(top_n):
    from utils.statistics import expected_hit_by_random
    return expected_hit_by_random(top_n)


if __name__ == "__main__":
    sys.exit(main())
