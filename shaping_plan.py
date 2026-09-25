"""对称减针行程规划：逐行安排左右相同的减针数。

模型（偏差用分数精确计算，不用浮点）：
  第 i 行单侧减针数 d_i ∈ {0..M}（M 为每个减针行单侧最多减针数，1 或 2），
  左右两侧各减 d_i 针，本行共减 2·d_i 针；
  减针行（d_i > 0）之间至少隔一行平织，即相邻两行不能同时减针；
  末行余针须等于目标针数：Σ 2·d_i = 起针数 − 目标针数（故差值须为偶数）。

  在满足约束的方案中，最小化各行累计减针数与线性目标进度的平方偏差之和：
      Σ_{i=1..R} (C_i − D·i/R)²
  其中 R 为总行数，C_i = Σ_{j≤i} d_j 为第 i 行后的累计单侧减针数，
  D = Σ d_i 为单侧总减针数，D·i/R 为线性目标进度（末行二者相等，偏差
  恒为 0）。同分取逐行单侧减针数组 (d_1..d_R) 字典序最小的方案。

动态规划：按（已安排行数, 累计单侧减针数, 上一行是否减针）记录
（最小偏差和, 字典序最小前缀数组）。每行的偏差贡献只取决于当前累计值，
约束只依赖上一行是否减针，故同一状态的最优前缀可独立优化：代价更小者
拼接任意共同后缀后总代价仍更小；代价相同则前缀字典序更小者整体字典序
也更小。容量剪枝：剩余行按“减针行之间至少隔一行平织”能提供的最大
减针量不足以达到 D 时，不再扩展该状态。
"""

from fractions import Fraction


def solve_shaping(start, target, rows, max_decrease):
    """求解对称减针行程。

    参数（调用方已完成校验）：
      start        起针数，int，> 0
      target       目标针数，int，0 ≤ target ≤ start
      rows         总行数，int，> 0
      max_decrease 每个减针行单侧最多减针数，int，1 或 2

    可行时返回：
      {"ok": True,
       "decreases": [d_1, ..., d_R]   逐行单侧减针数（左右相同）,
       "deviation": Fraction           平方偏差之和（精确分数）,
       "decrease_rows": 减针行数量,
       "max_decrease_rows": 行数约束下最多可安排的减针行数,
       "max_total_decrease": 行数与单侧上限约束下最多可减的总针数}
    无可行方案时返回：
      {"ok": False,
       "reason": "odd"          差值为奇数，左右对称减针无法恰好凑出
                | "insufficient" 行数与单侧上限约束下减针量不足,
       "need_decrease": 需要减去的总针数,
       "decrease_rows_needed": 至少需要的减针行数（reason 为 insufficient 时）,
       "max_decrease_rows": ..., "max_total_decrease": ...}
    """
    need = start - target                     # 需要减去的总针数（双侧）
    max_dec_rows = (rows + 1) // 2            # 减针行最多数量：第 1、3、5…行
    max_total = 2 * max_decrease * max_dec_rows
    if need % 2 == 1:
        return {
            "ok": False,
            "reason": "odd",
            "need_decrease": need,
            "max_decrease_rows": max_dec_rows,
            "max_total_decrease": max_total,
        }
    total_side = need // 2                    # 单侧总减针数 D
    if total_side > max_decrease * max_dec_rows:
        return {
            "ok": False,
            "reason": "insufficient",
            "need_decrease": need,
            "decrease_rows_needed": -(-total_side // max_decrease),  # 向上取整
            "max_decrease_rows": max_dec_rows,
            "max_total_decrease": max_total,
        }

    # dp[(累计单侧减针数, 上一行是否减针)] = (前 i 行最小偏差和, 字典序最小前缀)
    dp = {(0, False): (Fraction(0), ())}
    for i in range(1, rows + 1):
        progress = Fraction(total_side * i, rows)   # 线性目标进度 D·i/R
        rest = rows - i                             # 本行之后的剩余行数
        nxt = {}
        for (cum, prev_dec), (cost, plan) in dp.items():
            for d in range(max_decrease + 1):
                if d and prev_dec:
                    continue            # 减针行之间至少隔一行平织
                ncum = cum + d
                if ncum > total_side:
                    continue
                # 容量剪枝：剩余行能提供的最大单侧减针量不足以达到 D 时跳过
                if d:
                    future = rest // 2          # 下一行强制平织
                else:
                    future = (rest + 1) // 2
                if ncum + max_decrease * future < total_side:
                    continue
                ncost = cost + (Fraction(ncum) - progress) ** 2
                nplan = plan + (d,)
                key = (ncum, bool(d))
                old = nxt.get(key)
                if old is None or (ncost, nplan) < old:
                    nxt[key] = (ncost, nplan)
        dp = nxt

    # 可行性已在上面保证（total_side ≤ max_decrease × max_dec_rows），必有解
    best = None
    for (cum, _prev_dec), entry in dp.items():
        if cum != total_side:
            continue
        if best is None or entry < best:
            best = entry
    deviation, decreases = best
    return {
        "ok": True,
        "decreases": list(decreases),
        "deviation": deviation,
        "decrease_rows": sum(1 for d in decreases if d),
        "max_decrease_rows": max_dec_rows,
        "max_total_decrease": max_total,
    }
