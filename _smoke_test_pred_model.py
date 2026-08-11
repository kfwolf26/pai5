"""
预测模型 5 位改造冒烟测试
1) 验证 utils.statistics 支持 5 位(分布/评估)
2) 验证 PredictionModel 可实例化 + 位置键为 5 个
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
root = tk.Tk()
root.withdraw()

from utils.statistics import (
    DIGIT_COUNT, POS_KEYS_LIST, POS_LABELS_DICT,
    sum_value, span, o12_type, ac_value,
    sum_distribution, o12_distribution, ac_distribution,
    evaluate_prediction, aggregate_metrics, expected_hit_by_random,
    extract_number,
)
from modules.prediction_model import PredictionModel, PM_POS_KEYS, PM_POS_LABELS, PM_POS_SHORT

print("=" * 60)
print("【1】utils.statistics 基础常量")
print("=" * 60)
assert DIGIT_COUNT == 5, f"DIGIT_COUNT 应为 5,实际 {DIGIT_COUNT}"
assert POS_KEYS_LIST == ["w", "q", "b", "s", "g"], f"POS_KEYS_LIST={POS_KEYS_LIST}"
assert POS_LABELS_DICT == {0: "万", 1: "千", 2: "百", 3: "十", 4: "个"}
print(f"✓ DIGIT_COUNT={DIGIT_COUNT}")
print(f"✓ POS_KEYS_LIST={POS_KEYS_LIST}")

# 基础特征
assert sum_value("12345") == 15
assert span("12345") == 4
assert o12_type("12345") == "12012"
print(f"✓ sum_value(12345)={sum_value('12345')}, span={span('12345')}, 012={o12_type('12345')}")

ac = ac_value("12345")
print(f"✓ ac_value(12345)={ac}")

# 分布
dist = sum_distribution([{"number": "12345"}, {"number": "00000"}, {"number": "99999"}])
assert dist[15] == 1 and dist[0] == 1 and dist[45] == 1
assert min(dist.keys()) == 0 and max(dist.keys()) == 45
print(f"✓ sum_distribution 范围 {min(dist.keys())}-{max(dist.keys())} 共 {len(dist)} 项")

odist = o12_distribution([{"number": "01201"}])
assert len(odist) == 243, f"012 路应有 243 种,实际 {len(odist)}"
print(f"✓ o12_distribution {len(odist)} 项")

adist = ac_distribution([{"number": "12345"}])
assert len(adist) >= 10, f"ac_distribution 数量 {len(adist)}"
print(f"✓ ac_distribution {len(adist)} 项")

# 评估
predicted = {"w": [1, 2], "q": [2, 3], "b": [3, 4], "s": [4, 5], "g": [5, 6]}
result = "12345"
ev = evaluate_prediction(predicted, result)
assert ev["hit_count"] == 5, f"应5位全中,实际 {ev['hit_count']}"
assert ev["is_zhixuan"] is True
print(f"✓ evaluate_prediction w/q/b/s/g 全中 result=12345 => {ev}")

predicted2 = {"w": [9], "q": [8], "b": [7], "s": [6], "g": [5]}
ev2 = evaluate_prediction(predicted2, result)
assert ev2["hit_count"] == 1  # 个位中 5
print(f"✓ 评估(部分命): hit_count={ev2['hit_count']}, hit_pos={ev2['hit_pos']}")

# 聚合
agg = aggregate_metrics([ev, ev2])
assert agg["total"] == 2
assert agg["hit_distribution"][5] == 1
print(f"✓ aggregate_metrics: total={agg['total']}, avg_hit={agg['avg_hit']}, 5命中={agg['hit_distribution'][5]}")

exp = expected_hit_by_random(3)
assert abs(exp - 1.5) < 1e-9, f"期望应为 1.5,实际 {exp}"
print(f"✓ expected_hit_by_random(3)={exp}")

# 兼容老结构(bai/shi/ge)
predicted_old = {"bai": [1], "shi": [2], "ge": [3]}
ev_old = evaluate_prediction(predicted_old, "12345")
assert ev_old["hit_count"] == 3, f"老结构3位全中应有3,实际 {ev_old['hit_count']}"
print(f"✓ evaluate_prediction 兼容 bai/shi/ge => 命中 {ev_old['hit_count']} 位")

print("\n" + "=" * 60)
print("【2】PredictionModel 常量 + 实例化")
print("=" * 60)
assert PM_POS_KEYS == ["w", "q", "b", "s", "g"]
assert PM_POS_LABELS["w"] == "万位" and PM_POS_SHORT["g"] == "个"
print(f"✓ PM_POS_KEYS={PM_POS_KEYS}")

parent = tk.Frame(root)
# 构造 PredictionModel 前,把 history.json 备份一份并改为空,避免加载3位数据时误导
pm = PredictionModel(parent)
print("✓ PredictionModel 实例化成功")

assert set(pm.kill_trees.keys()) == set(PM_POS_KEYS), f"kill_trees 键应为5个,实际 {list(pm.kill_trees.keys())}"
print(f"✓ kill_trees 5 列 OK: {list(pm.kill_trees.keys())}")
assert set(pm.remain_labels.keys()) == set(PM_POS_KEYS)
print("✓ remain_labels 5 列 OK")
assert set(pm.remain_texts.keys()) == set(PM_POS_KEYS)
print("✓ remain_texts 5 列 OK")

# 检查 query_tree 列数
cols = pm.query_tree.cget("columns")
print(f"✓ query_tree columns({len(cols)})={cols}")
assert "w_pred" in cols and "g_pred" in cols

print("\n🎉 预测模型 5 位改造冒烟测试全部通过")
root.destroy()
