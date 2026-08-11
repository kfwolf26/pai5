"""
历史查询 号码标准化 冒烟测试
覆盖：_normalize_pl5_number + 单条添加 / 批量导入 / 搜索 的号码处理逻辑（不启动 GUI 的主循环）
"""
import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
root = tk.Tk()
root.withdraw()

from modules.history_query import HistoryQuery

parent = tk.Frame(root)
hq = HistoryQuery(parent)

print("=" * 60)
print("【1】_normalize_pl5_number 号码标准化")
print("=" * 60)

cases = [
    # (输入, 期望号码, 期望是否有 warn, 描述)
    ("01234", "01234", False, "完整 5 位，前导 0"),
    ("00000", "00000", False, "5 个 0"),
    ("00001", "00001", False, "前 4 个 0，末位 1"),
    ("1234",  "01234", True,  "4 位 → 补 0"),
    ("123",   "00123", True,  "3 位 → 补两个 0"),
    ("12",    "00012", True,  "2 位 → 补 3 个 0"),
    ("1",     "00001", True,  "1 位 → 补 4 个 0"),
    ("0",     "00000", True,  "单个 0 → 00000"),
    ("12345", "12345", False, "5 位完整，无前导 0"),
    (" 012 ", "00012", True,  "含空格的 3 位，补 0"),
    ("",       None,   False, "空号码应拒绝"),
    ("abc",    None,   False, "非数字应拒绝"),
    ("123456", None,   False, "6 位应拒绝"),
]

all_ok = True
for raw, expected_num, should_warn, desc in cases:
    got_num, got_warn = hq._normalize_pl5_number(raw)
    if expected_num is None:
        # 非法情况:只要求号码为 None + warn 有错误提示字符串
        ok = got_num is None and bool(got_warn)
    else:
        ok = got_num == expected_num and (bool(got_warn) == should_warn)
    status = "✓" if ok else "✗"
    if not ok: all_ok = False
    print(f"{status} {desc}: 输入={raw!r} → 号码={got_num!r}, warn={got_warn!r}"
          + (f"  (期望 num={expected_num!r}, warn_present={should_warn})" if not ok else ""))

assert all_ok, "至少一条 _normalize 失败"
print("✓ 号码标准化全部 OK")

print("\n" + "=" * 60)
print("【2】单条添加（写入一个临时 history.json）")
print("=" * 60)

# 替换 history.json 的路径到临时文件，避免污染用户数据
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
json.dump([], tmp)
tmp.close()

# 重建实例，然后直接替换内部 history_manager.history_file 路径
hq2 = HistoryQuery(parent)
hq2.history_manager.history_file = tmp.name
hq2.history_manager.history_data = None  # 清缓存，下次调用自动从新路径加载

add_cases = [
    ("2026001", "01234", "2026-01-01"),  # 完整 5 位 + 前导 0
    ("2026002", "1234",  "2026-01-02"),  # 4 位 → 01234（会弹 info，我们只验证实际写入）
    ("2026003", "0",     "2026-01-03"),  # 单 0 → 00000
    ("2026004", "12",    "2026-01-04"),  # 2 位 → 00012
]

success_issues = []
for issue, num, date in add_cases:
    hq2.history_issue_var.set(issue)
    hq2.history_number_var.set(num)
    hq2.history_date_var.set(date)
    before_count = len(hq2.history_manager.get_all())
    # 直接调用，避免 messagebox 阻塞
    try:
        # 拦截 showinfo / showwarning，不让弹窗中断
        import modules.history_query as hq_mod
        orig_info = hq_mod.showinfo
        orig_warn = hq_mod.showwarning
        hq_mod.showinfo = lambda *a, **k: None
        hq_mod.showwarning = lambda *a, **k: None
        try:
            hq2._add_history_record()
        finally:
            hq_mod.showinfo = orig_info
            hq_mod.showwarning = orig_warn
    except Exception as e:
        print(f"  ✗ 添加 {issue}/{num} 异常: {e}")
        continue
    after_count = len(hq2.history_manager.get_all())
    ok = after_count == before_count + 1
    print(f"{'✓' if ok else '✗'} 添加期号 {issue} 号码 {num!r}: count {before_count}→{after_count}")
    if ok:
        success_issues.append(issue)

all_data = hq2.history_manager.get_all()
print(f"最终历史列表（{len(all_data)} 条）:")
for rec in all_data:
    print(f"  issue={rec['issue']}  number={rec['number']!r}  sum={rec['sum']}  span={rec['span']}  type={rec['type']}")

# 校验具体号码
checks = {
    "2026001": "01234",
    "2026002": "01234",
    "2026003": "00000",
    "2026004": "00012",
}
for issue, expected_number in checks.items():
    actual = next((r["number"] for r in all_data if r["issue"] == issue), None)
    ok = actual == expected_number
    print(f"{'✓' if ok else '✗'} 期号 {issue} 号码应为 {expected_number!r} 实际 {actual!r}")
    assert ok

print("✓ 单条添加 + 号码标准化全部 OK")

print("\n" + "=" * 60)
print("【3】搜索号码逻辑（短数字 / 前导0 / 组选 / 子串）")
print("=" * 60)

def mock_search(term):
    """模拟 _search_history 的号码匹配部分，返回匹配到的 issue 列表"""
    matched = []
    for record in all_data:
        match = True
        sn = term.strip()
        if sn.isdigit() and len(sn) <= 5:
            exact = sn.zfill(5)
            if record["number"] == exact:
                pass
            else:
                sorted_search = ''.join(sorted(exact))
                sorted_record = ''.join(sorted(record["number"]))
                if sorted_search == sorted_record:
                    pass
                else:
                    if sn not in record["number"] and exact not in record["number"]:
                        match = False
        else:
            if sn not in record["number"]:
                match = False
        if match:
            matched.append(record["issue"])
    return matched

# 精确匹配(含前导0)
r = mock_search("01234")
assert "2026001" in r and "2026002" in r, f"01234 精确匹配不到: {r}"
print(f"✓ 搜索 01234 命中 {r}")

# 短数字补 0：1234 → exact=01234
r = mock_search("1234")
assert "2026001" in r and "2026002" in r, f"1234 补0后匹配不到: {r}"
print(f"✓ 搜索 1234 (补 0 → 01234) 命中 {r}")

# 单个 0 → 00000
r = mock_search("0")
# exact=00000, 且 "0" 是子串，所以全部都中
assert "2026003" in r, f"搜索 0 应命中 2026003: {r}"
print(f"✓ 搜索 0 (补 0 → 00000) 命中 {r}")

# 组选匹配：01234 的组选是 04321
r = mock_search("04321")
assert "2026001" in r and "2026002" in r, f"组选 04321 匹配不到: {r}"
print(f"✓ 搜索 04321(组选 01234) 命中 {r}")

# 子串模糊：12 → 2026004(00012) 含 "12"、以及所有含"12"的（01234 有子串 12）
r = mock_search("12")
assert "2026004" in r, f"搜索 12 应命中 00012 (2026004): {r}"
print(f"✓ 搜索 12（子串模糊）命中 {r}")

# 子串：000 → 2026003(00000) / 2026004(00012)
r = mock_search("000")
assert "2026003" in r and "2026004" in r, f"搜索 000 应命中 00000 / 00012: {r}"
print(f"✓ 搜索 000（子串模糊）命中 {r}")

print("✓ 搜索全部 OK")

# 清理临时文件
try:
    os.unlink(tmp.name)
except Exception:
    pass

print("\n🎉 历史查询号码标准化（含前导0）全部通过")
root.destroy()
