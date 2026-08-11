"""
统计工具层 - 3D 彩票数据分析的基础工具
所有函数纯函数式,不依赖 UI/不读写文件,可独立测试
"""
from collections import Counter
from typing import List, Dict, Tuple, Optional
import math


# ========== 基础特征 ==========

def extract_number(record: dict) -> str:
    """从历史记录中提取开奖号码(3位字符串)"""
    return str(record.get("number", "")).zfill(3)


def extract_position(record: dict, pos: int) -> int:
    """提取某位的数字 (pos: 0=百, 1=十, 2=个)"""
    num = extract_number(record)
    if len(num) < 3:
        return -1
    return int(num[pos])


def ac_value(number: str) -> int:
    """
    AC 值(算术复杂度) - 不同两个数之差的绝对值集合,去掉 0,数量减 1
    例如 "123" -> 差值 |1-2|=1, |1-3|=2, |2-3|=1, 去重 {1,2}, AC=2-1=1
    """
    digits = [int(c) for c in str(number).zfill(3)]
    diffs = set()
    for i in range(3):
        for j in range(i + 1, 3):
            diffs.add(abs(digits[i] - digits[j]))
    diffs.discard(0)
    return len(diffs) - 1 if len(diffs) > 0 else 0


def o12_type(number: str) -> str:
    """012 路:每位数字对 3 取余,生成 3位 0/1/2 字符串"""
    return "".join(str(int(c) % 3) for c in str(number).zfill(3))


def span(number: str) -> int:
    """跨度 = max - min"""
    digits = [int(c) for c in str(number).zfill(3)]
    return max(digits) - min(digits)


def sum_value(number: str) -> int:
    """和值"""
    return sum(int(c) for c in str(number).zfill(3))


def is_zuxuan(number: str) -> bool:
    """判断是否组三(两个相同)或组六(三不同)"""
    digits = [int(c) for c in str(number).zfill(3)]
    if len(set(digits)) == 3:
        return True  # 组六
    if len(set(digits)) == 2:
        return True  # 组三
    return False  # 豹子


# ========== 频率/冷热统计 ==========

def position_frequency(records: List[dict], pos: int) -> Dict[int, int]:
    """
    某位置 0-9 的出现次数
    pos: 0=百, 1=十, 2=个
    """
    counter = Counter()
    for r in records:
        n = extract_position(r, pos)
        if 0 <= n <= 9:
            counter[n] += 1
    # 补全 0-9
    return {d: counter.get(d, 0) for d in range(10)}


def position_frequency_weighted(records: List[dict], pos: int,
                               decay: float = 0.95) -> Dict[int, float]:
    """
    某位置 0-9 的指数衰减加权频率
    records 假定按时间升序(旧->新),最近的权重 = 1.0
    decay 越小,越偏重近期
    """
    if not records:
        return {d: 0.0 for d in range(10)}

    weights = [decay ** (len(records) - 1 - i) for i in range(len(records))]
    freq = {d: 0.0 for d in range(10)}

    for r, w in zip(records, weights):
        n = extract_position(r, pos)
        if 0 <= n <= 9:
            freq[n] += w
    return freq


def cold_hot_numbers(records: List[dict], pos: int, window: int = 20,
                     top_n: int = 5) -> Tuple[List[int], List[int]]:
    """
    冷热号:最近 window 期内出现次数 top_n 为热号,出现次数最少的 top_n 为冷号
    返回 (hot_list, cold_list)
    """
    recent = records[-window:] if len(records) > window else records
    freq = position_frequency(recent, pos)
    sorted_items = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    hot = [d for d, _ in sorted_items[:top_n]]
    cold = [d for d, _ in sorted_items[-top_n:]]
    return hot, cold


def sum_distribution(records: List[dict]) -> Dict[int, int]:
    """和值 0-27 的分布"""
    counter = Counter()
    for r in records:
        s = sum_value(extract_number(r))
        if 0 <= s <= 27:
            counter[s] += 1
    return {s: counter.get(s, 0) for s in range(28)}


def span_distribution(records: List[dict]) -> Dict[int, int]:
    """跨度 0-9 的分布"""
    counter = Counter()
    for r in records:
        s = span(extract_number(r))
        if 0 <= s <= 9:
            counter[s] += 1
    return {s: counter.get(s, 0) for s in range(10)}


def o12_distribution(records: List[dict]) -> Dict[str, int]:
    """012 路 27 种组合的分布"""
    counter = Counter()
    for r in records:
        t = o12_type(extract_number(r))
        counter[t] += 1
    # 补全所有 27 种
    all_types = [f"{a}{b}{c}" for a in range(3) for b in range(3) for c in range(3)]
    return {t: counter.get(t, 0) for t in all_types}


def ac_distribution(records: List[dict]) -> Dict[int, int]:
    """AC 值分布(0-?, 实际 0-3)"""
    counter = Counter()
    for r in records:
        ac = ac_value(extract_number(r))
        counter[ac] += 1
    # AC 值理论 0-3
    return {a: counter.get(a, 0) for a in range(4)}


def repeat_rate(records: List[dict], pos: int, window: int = 5) -> float:
    """
    重号率:最近 window 期内,某位出现与上一期相同的比例
    (用于估算"重号"概率)
    """
    if len(records) < 2:
        return 0.0
    recent = records[-window - 1:] if len(records) > window + 1 else records
    hits = 0
    total = 0
    for i in range(1, len(recent)):
        if extract_position(recent[i], pos) == extract_position(recent[i - 1], pos):
            hits += 1
        total += 1
    return hits / total if total > 0 else 0.0


# ========== 概率分布/平滑 ==========

def laplace_smooth(freq: Dict[int, int], alpha: float = 1.0) -> Dict[int, float]:
    """
    拉普拉斯平滑:每个数加 alpha,避免 0 概率
    返回归一化后的概率
    """
    total = sum(freq.values()) + alpha * len(freq)
    return {k: (v + alpha) / total for k, v in freq.items()}


def normalize(distribution: Dict[int, float]) -> Dict[int, float]:
    """归一化概率分布"""
    total = sum(distribution.values())
    if total <= 0:
        return {k: 1.0 / len(distribution) for k in distribution}
    return {k: v / total for k, v in distribution.items()}


def top_n_keys(distribution: Dict[int, float], n: int) -> List[int]:
    """取概率最高的 n 个 key(数字)"""
    sorted_items = sorted(distribution.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in sorted_items[:n]]


# ========== 滚动切分 ==========

def walk_forward_split(records: List[dict], train_size: int = 100,
                       test_size: int = 30, step: int = 1
                       ) -> List[Tuple[List[dict], List[dict]]]:
    """
    滚动窗口划分(用于回测)
    返回 [(train, test), (train, test), ...] 列表
    records 必须按时间升序
    """
    if not records or train_size <= 0 or test_size <= 0:
        return []

    splits = []
    n = len(records)
    # 至少需要 train_size + test_size 才跑一轮
    start = 0
    while start + train_size + test_size <= n:
        train = records[start:start + train_size]
        test = records[start + train_size:start + train_size + test_size]
        splits.append((train, test))
        start += step
    return splits


# ========== 评估指标 ==========

def evaluate_prediction(predicted: Dict[str, List[int]], actual: str) -> Dict:
    """
    评估一次预测
    predicted: {"bai": [0,1,2], "shi": [...], "ge": [...]}
    actual: 实际开奖号,如 "923"
    返回:
      - hit_count: 命中位数 (0-3)
      - hit_pos: 命中的位置 ["百", "十", "个"]
      - is_zhixuan: 是否直选命中(三位全中)
    """
    actual = str(actual).zfill(3)
    hit_pos = []
    pos_map = {0: "百", 1: "十", 2: "个"}
    pos_keys = ["bai", "shi", "ge"]
    for i, key in enumerate(pos_keys):
        if int(actual[i]) in predicted.get(key, []):
            hit_pos.append(pos_map[i])
    return {
        "hit_count": len(hit_pos),
        "hit_pos": hit_pos,
        "is_zhixuan": len(hit_pos) == 3,
        "actual": actual,
    }


def aggregate_metrics(results: List[Dict]) -> Dict:
    """
    汇总多次回测结果
    results: 每期评估结果列表
    返回:
      - total: 总期数
      - avg_hit: 平均命中位数
      - hit_distribution: 0/1/2/3 位的分布
      - pos_rates: 百/十/个 各自的命中率
      - zhixuan_count / rate: 直选全中数/率
    """
    if not results:
        return {}

    total = len(results)
    hit_dist = Counter()
    pos_hits = {"百": 0, "十": 0, "个": 0}
    zhixuan = 0

    for r in results:
        hit_dist[r["hit_count"]] += 1
        for p in r.get("hit_pos", []):
            pos_hits[p] += 1
        if r["is_zhixuan"]:
            zhixuan += 1

    return {
        "total": total,
        "avg_hit": sum(hit_dist[k] * k for k in hit_dist) / total,
        "hit_distribution": {k: hit_dist.get(k, 0) for k in range(4)},
        "hit_distribution_rate": {k: hit_dist.get(k, 0) / total for k in range(4)},
        "pos_rates": {p: pos_hits[p] / total for p in pos_hits},
        "zhixuan_count": zhixuan,
        "zhixuan_rate": zhixuan / total,
    }


def expected_hit_by_random(n_per_pos: int) -> float:
    """
    理论期望命中位数(随机选 n_per_pos 个号/位)
    每次选 1/n_per_pos 概率命中,3 位独立
    """
    p = n_per_pos / 10.0
    return 3 * p  # 期望 = 3 * 单次命中概率
