"""
定位定胆 + 回测模块 5 位改造冒烟测试
1) LocationDingDan 实例化,Tab 数 = 6,位置键 = w/q/b/s/g
2) BacktestTab 实例化 + 引擎跑一遍 5 位回测
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
root = tk.Tk()
root.withdraw()

# ---- LocationDingDan ----
from modules.location_dingdan import LocationDingDan, LD_POS_KEYS, LD_POS_TAB_NAMES

print("=" * 60)
print("【1】LocationDingDan")
print("=" * 60)
assert LD_POS_KEYS == ["w", "q", "b", "s", "g"]
assert set(LD_POS_TAB_NAMES.keys()) == set(LD_POS_KEYS)
print(f"✓ LD_POS_KEYS={LD_POS_KEYS}")
print(f"✓ LD_POS_TAB_NAMES={LD_POS_TAB_NAMES}")

parent = tk.Frame(root)
ldd = LocationDingDan(parent)
print("✓ LocationDingDan 实例化成功")

# Tab 数应为 6(不定位 + 5 位)
tab_count = len(ldd.notebook.tabs())
assert tab_count == 6, f"Tab 数应为 6,实际 {tab_count}"
print(f"✓ Tab 数 = {tab_count} (不定位 + 万/千/百/十/个)")

# predictors 应有 6 个 key
assert set(ldd.predictors.keys()) == {"unpositioned"} | set(LD_POS_KEYS), \
    f"predictors 键应为 6 个,实际 {list(ldd.predictors.keys())}"
print(f"✓ predictors 键: {sorted(ldd.predictors.keys())}")

# canvas_frames 同
assert set(ldd.canvas_frames.keys()) == {"unpositioned"} | set(LD_POS_KEYS)
print(f"✓ canvas_frames 6 列 OK")

# 测 _generate_predictors_for_period
# 不定位:对 12345,5 位都参与集合判断
preds = ldd._generate_predictors_for_period("unpositioned", "12345")
assert len(preds) == 10
# 每个预测者:hit_numbers 应是 numbers 与 {1,2,3,4,5} 的交集
for p in preds:
    expected_hit = [n for n in p["numbers"] if str(n) in set("12345")]
    assert p["hit_numbers"] == expected_hit, f"不定位 hit 错: {p}"
print(f"✓ 不定位 _generate_predictors_for_period(12345) OK")

# 万位 tab:对 12345,目标位=0(万位)=1
preds = ldd._generate_predictors_for_period("w", "12345")
for p in preds:
    expected_hit = [n for n in p["numbers"] if str(n) == "1"]
    assert p["hit_numbers"] == expected_hit, f"万位 hit 错: {p}"
print("✓ 万位(_generate_predictors_for_period) OK")

# 个位 tab:目标位=4(个位)=5
preds = ldd._generate_predictors_for_period("g", "12345")
for p in preds:
    expected_hit = [n for n in p["numbers"] if str(n) == "5"]
    assert p["hit_numbers"] == expected_hit, f"个位 hit 错: {p}"
print("✓ 个位(_generate_predictors_for_period) OK")

# 空 result_num 时 hit_numbers 应为空
preds = ldd._generate_predictors_for_period("w", "")
assert all(p["hit_numbers"] == [] for p in preds)
print("✓ 空 result_num 时 hit_numbers 为空")

# ---- BacktestTab ----
print("\n" + "=" * 60)
print("【2】BacktestTab + BacktestEngine")
print("=" * 60)
from modules.backtest import (
    BacktestTab, BacktestEngine, BT_POS_KEYS, BT_POS_NAMES,
    RandomStrategy, FrequencyStrategy, STRATEGY_REGISTRY,
)

assert BT_POS_KEYS == ["w", "q", "b", "s", "g"]
assert BT_POS_NAMES == ["万", "千", "百", "十", "个"]
print(f"✓ BT_POS_KEYS={BT_POS_KEYS}, BT_POS_NAMES={BT_POS_NAMES}")

# 策略 predict 必须返回 5 个键
random_strategy = RandomStrategy()
pred = random_strategy.predict([], 5)
assert set(pred.keys()) == set(BT_POS_KEYS), f"Random 策略返回键错: {list(pred.keys())}"
for pk in BT_POS_KEYS:
    assert len(pred[pk]) == 5
print(f"✓ RandomStrategy.predict → 5 键,每键 5 号: {pred}")

# 构造 5 位假历史,跑回测引擎
fake_history = []
for i in range(120):
    issue = f"2026{i + 1:03d}"
    n1 = (i) % 10
    n2 = (i + 1) % 10
    n3 = (i + 2) % 10
    n4 = (i + 3) % 10
    n5 = (i + 4) % 10
    fake_history.append({"issue": issue, "number": f"{n1}{n2}{n3}{n4}{n5}"})

engine = BacktestEngine(fake_history)
assert len(engine.history) == 120, f"过滤后应有 120 期,实际 {len(engine.history)}"
print(f"✓ BacktestEngine 加载 5 位历史 120 期")

# 跑回测
result = engine.run(FrequencyStrategy(), top_n=5, train_size=50, test_size=20, step=20)
assert "metrics" in result
m = result["metrics"]
print(f"✓ 回测完成: total={m['total']} 期, avg_hit={m['avg_hit']:.3f}")
print(f"  hit_distribution={m['hit_distribution']}")
print(f"  pos_rates={m['pos_rates']}")

# 检查 results 中每条都有 5 个 predicted 键
for r in result["results"]:
    assert set(r["predicted"].keys()) == set(BT_POS_KEYS)
    assert 0 <= r["hit_count"] <= 5
print(f"✓ results 中每条 predicted 5 键 + hit_count ∈ [0,5]")

# 测 predict_next
next_pred = engine.predict_next(FrequencyStrategy(), top_n=5)
assert next_pred is not None
assert set(next_pred["predicted"].keys()) == set(BT_POS_KEYS)
assert next_pred["is_prediction"] is True
print(f"✓ predict_next: issue={next_pred['issue']}, predicted 5 键 OK")

# BacktestTab 实例化
parent2 = tk.Frame(root)
bt_tab = BacktestTab(parent2)
print("✓ BacktestTab 实例化成功")

# 检查 detail_tree 列(应为 期号/开奖号 + 5 位选号 + 命中位 + 详情 = 9 列)
detail_cols = list(bt_tab.detail_tree.cget("columns"))
assert "万位选号" in detail_cols and "个位选号" in detail_cols
assert len(detail_cols) == 9, f"detail_tree 应有 9 列,实际 {len(detail_cols)}"
print(f"✓ detail_tree columns({len(detail_cols)})={detail_cols}")

# 检查 compare_tree 列
cmp_cols = list(bt_tab.compare_tree.cget("columns"))
assert "5位全中" in cmp_cols
assert "万位命中" in cmp_cols and "个位命中" in cmp_cols
print(f"✓ compare_tree columns({len(cmp_cols)})={cmp_cols}")

# 测 _archive_format 生成新结构(remains)
fake_result_item = {
    "actual": "12345",
    "is_prediction": False,
    "issue": "2026200",
    "predicted": {"w": [1, 2], "q": [3], "b": [4, 5], "s": [6], "g": [7, 8]},
    "hit_pos": ["万", "千"],
}
archived = bt_tab._archive_format(fake_result_item)
assert archived is not None
assert "remains" in archived
assert set(archived["remains"].keys()) == set(BT_POS_KEYS)
assert archived["remains"]["w"] == [1, 2]
assert "bai_remain" not in archived  # 不应再有老结构
print(f"✓ _archive_format 新结构: {archived}")

print("\n" + "=" * 60)
print("🎉 定位定胆 + 回测模块 5 位改造冒烟测试全部通过")
print("=" * 60)

root.destroy()
