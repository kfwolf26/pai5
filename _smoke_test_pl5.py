"""
排列5 改造冒烟测试 - 验证 filter_tool.py 和 history_query.py 核心逻辑
不启动 GUI，只测试纯逻辑函数
"""
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建一个隐藏的 tk root 用于初始化 tk 变量
import tkinter as tk
root = tk.Tk()
root.withdraw()

from modules.filter_tool import FilterTool, POS_KEYS, SIZE_TYPES, OE_TYPES, PC_TYPES, O12_TYPES, SMS_TYPES
from modules.history_query import HistoryQuery

# ============ 1. 常量校验 ============
print("=" * 60)
print("【1】常量校验")
print("=" * 60)
assert len(POS_KEYS) == 5, f"POS_KEYS 应有5个,实际 {len(POS_KEYS)}"
print(f"✓ POS_KEYS = {POS_KEYS}")
assert len(SIZE_TYPES) == 32, f"大小形态应有32种,实际 {len(SIZE_TYPES)}"
print(f"✓ SIZE_TYPES 共 {len(SIZE_TYPES)} 种")
assert len(OE_TYPES) == 32, f"奇偶形态应有32种,实际 {len(OE_TYPES)}"
print(f"✓ OE_TYPES 共 {len(OE_TYPES)} 种")
assert len(PC_TYPES) == 32, f"质合形态应有32种,实际 {len(PC_TYPES)}"
print(f"✓ PC_TYPES 共 {len(PC_TYPES)} 种")
assert len(O12_TYPES) == 243, f"012路形态应有243种,实际 {len(O12_TYPES)}"
print(f"✓ O12_TYPES 共 {len(O12_TYPES)} 种")
assert len(SMS_TYPES) == 243, f"大中小形态应有243种,实际 {len(SMS_TYPES)}"
print(f"✓ SMS_TYPES 共 {len(SMS_TYPES)} 种")

# ============ 2. 初始化 FilterTool 实例 ============
print("\n" + "=" * 60)
print("【2】FilterTool 初始化")
print("=" * 60)
parent = tk.Frame(root)
ft = FilterTool(parent)
print("✓ FilterTool 实例化成功")

# 验证变量结构
assert set(ft.filter_vars["pos"].keys()) == set(POS_KEYS), "pos 键应为 5 位"
assert set(ft.filter_vars["kill"].keys()) == set(POS_KEYS), "kill 键应为 5 位"
assert set(ft.filter_vars["dan"].keys()) == set(POS_KEYS), "dan 键应为 5 位"
print(f"✓ pos/kill/dan 各有 {len(POS_KEYS)} 个位置")

assert len(ft.filter_vars["sum_val"]) == 46, f"和值应有46个选项,实际 {len(ft.filter_vars['sum_val'])}"
print(f"✓ 和值范围 0-45,共 {len(ft.filter_vars['sum_val'])} 个")

assert len(ft.filter_vars["size"]) == 32, f"大小形态应有32个,实际 {len(ft.filter_vars['size'])}"
print(f"✓ 大小形态 {len(ft.filter_vars['size'])} 个")

# ============ 3. 全量生成 ============
print("\n" + "=" * 60)
print("【3】全量号码生成")
print("=" * 60)
all_nums = ft._generate_all_direct()
assert len(all_nums) == 100000, f"全量应有100000注,实际 {len(all_nums)}"
assert all_nums[0] == "00000", f"首注应为00000,实际 {all_nums[0]}"
assert all_nums[-1] == "99999", f"末注应为99999,实际 {all_nums[-1]}"
print(f"✓ 全量生成 {len(all_nums)} 注(00000-99999)")

# ============ 4. 形态判定函数 ============
print("\n" + "=" * 60)
print("【4】形态判定")
print("=" * 60)
assert ft._get_size_type("01234") == "小小小小小", f"大小判定错: {ft._get_size_type('01234')}"
assert ft._get_size_type("56789") == "大大大大大", f"大小判定错: {ft._get_size_type('56789')}"
assert ft._get_size_type("01289") == "小小小大大"
print(f"✓ 大小: 01234 -> {ft._get_size_type('01234')}, 56789 -> {ft._get_size_type('56789')}")

assert ft._get_oe_type("13579") == "奇奇奇奇奇"
assert ft._get_oe_type("02468") == "偶偶偶偶偶"
print(f"✓ 奇偶: 13579 -> {ft._get_oe_type('13579')}, 02468 -> {ft._get_oe_type('02468')}")

assert ft._get_pc_type("12357") == "质质质质质"
assert ft._get_pc_type("04689") == "合合合合合"
print(f"✓ 质合: 12357 -> {ft._get_pc_type('12357')}, 04689 -> {ft._get_pc_type('04689')}")

assert ft._get_012_type("00000") == "00000"
assert ft._get_012_type("12345") == "12012"
print(f"✓ 012路: 12345 -> {ft._get_012_type('12345')}")

assert ft._get_sms_type("01234") == "小小小中中"
assert ft._get_sms_type("78901") == "大大大小小"
print(f"✓ 大中小: 01234 -> {ft._get_sms_type('01234')}, 78901 -> {ft._get_sms_type('78901')}")

assert ft._get_sum("12345") == 15
assert ft._get_sum("99999") == 45
print(f"✓ 和值: 12345 -> {ft._get_sum('12345')}, 99999 -> {ft._get_sum('99999')}")

assert ft._get_span("12345") == 4
assert ft._get_span("09999") == 9
print(f"✓ 跨度: 12345 -> {ft._get_span('12345')}, 09999 -> {ft._get_span('09999')}")

# ============ 5. 二码组合 ============
print("\n" + "=" * 60)
print("【5】二码组合(C(5,2)=10对)")
print("=" * 60)
sums = ft._get_two_sums("12345")
assert sums == {3, 4, 5, 6, 7, 8, 9}, f"12345 二码和集合应为3-9,实际 {sums}"
print(f"✓ 12345 二码和集合(去重7个): {sorted(sums)}")

diffs = ft._get_two_diffs("12345")
assert diffs == {1, 2, 3, 4}, f"12345 二码差集合应为1-4,实际 {diffs}"
print(f"✓ 12345 二码差集合: {sorted(diffs)}")

codes = ft._get_two_codes("12345")
assert len(codes) == 10, f"二码应有10对(无序),实际 {len(codes)}"
print(f"✓ 12345 二码集合(10个无序对): {sorted(codes)}")

# ============ 6. 顺子判定 ============
print("\n" + "=" * 60)
print("【6】顺子/半顺子判定")
print("=" * 60)
assert ft._is_straight("12345") == True, "12345 应为顺子"
assert ft._is_straight("56789") == True, "56789 应为顺子"
assert ft._is_straight("01239") == True, "01239 应为环形顺子(0-9相连)"
assert ft._is_straight("13579") == False, "13579 不应为顺子"
print("✓ 顺子: 12345 / 56789 / 01239(环形) 均判定正确")

assert ft._is_semi_straight("13579") == False, "13579 不应有半顺子"
assert ft._is_semi_straight("13578") == True, "13578 应有半顺子(7和8)"
assert ft._is_semi_straight("19023") == True, "19023 应有半顺子(0和9)"
print("✓ 半顺子: 13579(无) / 13578(有) / 19023(0-9) 均判定正确")

# ============ 7. 定位过滤 ============
print("\n" + "=" * 60)
print("【7】定位/杀号/胆码过滤")
print("=" * 60)
test_nums = ["12345", "67890", "13579", "24680"]
pos = {"w": {"1"}, "q": set(), "b": set(), "s": set(), "g": set()}
filtered = ft._filter_position(test_nums, pos)
assert "12345" in filtered, "12345 万位=1 应通过"
assert "67890" not in filtered, "67890 万位=6 应被过滤"
print(f"✓ 定位: 万位=1,从{len(test_nums)}注筛出{len(filtered)}注: {filtered}")

kill = {"w": {"1"}, "q": set(), "b": set(), "s": set(), "g": set()}
filtered = ft._filter_kill(test_nums, kill)
assert "12345" not in filtered, "12345 万位=1 应被杀号"
assert "67890" in filtered
print(f"✓ 杀号: 万位杀1,筛出{len(filtered)}注: {filtered}")

dan = {"w": {"1", "2"}, "q": set(), "b": set(), "s": set(), "g": set()}
filtered = ft._filter_dan(test_nums, dan)
assert "12345" in filtered, "12345 万位=1 应通过胆码"
assert "67890" not in filtered
print(f"✓ 胆码: 万位胆1/2,筛出{len(filtered)}注: {filtered}")

# ============ 8. 直选定位解析 ============
print("\n" + "=" * 60)
print("【8】直选定位解析")
print("=" * 60)
combines = ft._parse_direct_pos_single("13,24,57,68,9")
assert "124689" not in combines  # 不应出现,因为每位单独取
assert "14569" in combines, f"应包含 14569,实际 {combines[:5]}"
assert len(combines) == 2 * 2 * 2 * 2 * 1, f"应有 16 种组合,实际 {len(combines)}"
print(f"✓ '13,24,57,68,9' 解析为 {len(combines)} 种组合")

# 错误格式
bad = ft._parse_direct_pos_single("1,2,3")
assert bad == [], "3 段格式应返回空"
print("✓ '1,2,3' (3段) 正确返回空")

# ============ 9. 非定位直选解析 ============
print("\n" + "=" * 60)
print("【9】非定位直选解析")
print("=" * 60)
perms = ft._parse_non_pos_direct_single("12345")
assert len(perms) == 120, f"5个不同数字应有120种排列,实际 {len(perms)}"
print(f"✓ '12345' 生成 {len(perms)} 种排列")

perms = ft._parse_non_pos_direct_single("11234")
assert len(perms) == 60, f"含1对重复应有60种排列(5!/2!),实际 {len(perms)}"
print(f"✓ '11234' 生成 {len(perms)} 种排列(含1对重复)")

perms = ft._parse_non_pos_direct_single("11123")
assert len(perms) == 20, f"含3个1应有20种排列(5!/3!),实际 {len(perms)}"
print(f"✓ '11123' 生成 {len(perms)} 种排列(含3个1)")

bad = ft._parse_non_pos_direct_single("1234")
assert len(bad) == 0, "4位数字应返回空"
print("✓ '1234' (4位) 正确返回空")

# ============ 10. HistoryQuery 形态判定 ============
print("\n" + "=" * 60)
print("【10】HistoryQuery 形态判定")
print("=" * 60)
hq = HistoryQuery(parent)
print("✓ HistoryQuery 实例化成功")

assert hq._get_number_form([1, 1, 1, 1, 1]) == "五同"
assert hq._get_number_form([1, 1, 1, 1, 2]) == "四同+单"
assert hq._get_number_form([1, 1, 1, 2, 2]) == "葫芦(3+2)"
assert hq._get_number_form([1, 1, 1, 2, 3]) == "三同+单+单"
assert hq._get_number_form([1, 1, 2, 2, 3]) == "两对+单"
assert hq._get_number_form([1, 1, 2, 3, 4]) == "一对+三单"
assert hq._get_number_form([1, 2, 3, 4, 5]) == "五不同"
print("✓ 7种形态判定全部正确")
print("  五同/四同+单/葫芦(3+2)/三同+单+单/两对+单/一对+三单/五不同")

# ============ 11. 号码组过滤 ============
print("\n" + "=" * 60)
print("【11】号码组过滤(5位)")
print("=" * 60)
groups = [({"1", "2"}, 2)]  # 数字1或2出现2次
filtered = ft._filter_number_group(test_nums, groups)
assert "12345" in filtered, "12345 含1和2各一次,共2次,应通过"
assert "67890" not in filtered
print(f"✓ 号码组(1/2出现2次),筛出: {filtered}")

groups = [({"1", "2"}, 3)]
filtered = ft._filter_number_group(test_nums, groups)
assert "12345" not in filtered, "12345 只出现2次,要求3次应被过滤"
print(f"✓ 号码组(1/2出现3次),筛出: {filtered}")

# ============ 12. 完整过滤流程(小样本) ============
print("\n" + "=" * 60)
print("【12】完整过滤流程验证")
print("=" * 60)
# 设置一个简单条件:万位=1
for i, var in enumerate(ft.filter_vars["pos"]["w"]):
    if i == 1:
        var.set(True)
# 解析并过滤
filters = ft._parse_filters()
nums = ft._generate_all_direct()
nums = ft._filter_position(nums, filters["pos"])
assert len(nums) == 10000, f"万位=1 应有10000注,实际 {len(nums)}"
assert all(n[0] == "1" for n in nums[:100]), "前100注应都以1开头"
print(f"✓ 万位=1 过滤后剩余 {len(nums)} 注(应为10000)")

# 加和值过滤:和值=15
for i, var in enumerate(ft.filter_vars["sum_val"]):
    if i == 15:
        var.set(True)
filters = ft._parse_filters()
nums2 = ft._filter_sum(nums, filters["sum_mode"], filters["sum_val"])
assert all(ft._get_sum(n) == 15 for n in nums2[:50]), "和值都应为15"
print(f"✓ 万位=1 且 和值=15 过滤后剩余 {len(nums2)} 注")

# 清空
ft.clear_all()
filters = ft._parse_filters()
assert not filters["pos"]["w"], "清空后 pos[w] 应为空"
print("✓ clear_all 正常工作")

print("\n" + "=" * 60)
print("🎉 全部冒烟测试通过！")
print("=" * 60)
print("改造总结:")
print("- filter_tool.py: 5位数字过滤,删除组三/组六/豹子,扩展和值(0-45)/形态(32/243种)")
print("- history_query.py: 5位历史查询,形态分类按重复结构(7种)")
print("- main.py: 标题改为'体彩排列5过滤工具'")

root.destroy()
