import itertools
import random
import unittest
from fractions import Fraction

from shaping_plan import solve_shaping


def brute_force(start, target, rows, max_decrease):
    """暴力枚举所有满足约束的逐行单侧减针数组。

    返回 (最小平方偏差和, 字典序最小数组)；无可行方案时返回 None。
    """
    need = start - target
    if need % 2 == 1:
        return None
    total_side = need // 2
    best = None
    for combo in itertools.product(range(max_decrease + 1), repeat=rows):
        if sum(combo) != total_side:
            continue
        if any(combo[i] and combo[i + 1] for i in range(rows - 1)):
            continue
        cost = sum(
            (Fraction(sum(combo[:i + 1])) - Fraction(total_side * (i + 1), rows)) ** 2
            for i in range(rows))
        key = (cost, combo)
        if best is None or key < best:
            best = key
    return best


class TestSolveShaping(unittest.TestCase):
    def test_basic_unique_plan(self):
        # 40→20 共减 20 针（单侧 10），10 行最多 5 个减针行、每行单侧最多 2，
        # 容量恰好用尽：只能隔行各减 2；两种排法同分，取字典序最小
        result = solve_shaping(40, 20, 10, 2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['decreases'], [0, 2, 0, 2, 0, 2, 0, 2, 0, 2])
        self.assertEqual(result['decrease_rows'], 5)
        self.assertEqual(result['deviation'], 5)

    def test_tie_breaks_to_lexicographically_smallest(self):
        # (1,0,1,0)、(1,0,0,1)、(0,1,0,1) 偏差同为 1/2，取字典序最小的 (0,1,0,1)
        result = solve_shaping(4, 0, 4, 1)
        self.assertTrue(result['ok'])
        self.assertEqual(result['decreases'], [0, 1, 0, 1])
        self.assertEqual(result['deviation'], Fraction(1, 2))

    def test_decrease_rows_never_adjacent(self):
        result = solve_shaping(30, 10, 9, 2)
        self.assertTrue(result['ok'])
        d = result['decreases']
        self.assertTrue(all(not (d[i] and d[i + 1]) for i in range(len(d) - 1)))
        self.assertEqual(2 * sum(d), 30 - 10)

    def test_zero_decrease_when_target_equals_start(self):
        result = solve_shaping(10, 10, 5, 2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['decreases'], [0, 0, 0, 0, 0])
        self.assertEqual(result['deviation'], 0)
        self.assertEqual(result['decrease_rows'], 0)

    def test_single_row(self):
        result = solve_shaping(4, 0, 1, 2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['decreases'], [2])
        self.assertEqual(result['deviation'], 0)

    def test_single_row_limit_one(self):
        result = solve_shaping(4, 2, 1, 1)
        self.assertTrue(result['ok'])
        self.assertEqual(result['decreases'], [1])

    def test_odd_difference_infeasible(self):
        # 差值 21 为奇数：左右对称减针每次减偶数针，无法恰好减到目标
        result = solve_shaping(41, 20, 10, 2)
        self.assertFalse(result['ok'])
        self.assertEqual(result['reason'], 'odd')
        self.assertEqual(result['need_decrease'], 21)
        self.assertEqual(result['max_decrease_rows'], 5)
        self.assertEqual(result['max_total_decrease'], 20)

    def test_insufficient_rows_infeasible(self):
        # 需减 8 针（单侧 4），6 行最多 3 个减针行 × 单侧 1 → 最多减 6 针
        result = solve_shaping(12, 4, 6, 1)
        self.assertFalse(result['ok'])
        self.assertEqual(result['reason'], 'insufficient')
        self.assertEqual(result['need_decrease'], 8)
        self.assertEqual(result['decrease_rows_needed'], 4)
        self.assertEqual(result['max_decrease_rows'], 3)
        self.assertEqual(result['max_total_decrease'], 6)

    def test_max_total_decrease_reflects_limit(self):
        # 单侧上限 2 时容量翻倍：同一差值从不可行变为可行
        self.assertFalse(solve_shaping(12, 4, 6, 1)['ok'])
        result = solve_shaping(12, 4, 6, 2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['max_total_decrease'], 12)

    def test_exact_fit_forces_every_other_row(self):
        # 单侧 4、减针行最多 4、每行最多 1：唯一方案 (1,0,1,0,1,0,1)
        result = solve_shaping(12, 4, 7, 1)
        self.assertTrue(result['ok'])
        self.assertEqual(result['decreases'], [1, 0, 1, 0, 1, 0, 1])

    def test_random_against_brute_force(self):
        # 随机小参数与暴力枚举对照：可行性、偏差与减针数组都必须一致
        rng = random.Random(20260925)
        for _ in range(300):
            start = rng.randint(1, 24)
            target = rng.randint(0, start)
            rows = rng.randint(1, 9)
            max_decrease = rng.randint(1, 2)
            result = solve_shaping(start, target, rows, max_decrease)
            best = brute_force(start, target, rows, max_decrease)
            msg = '参数 start={} target={} rows={} max_decrease={}'.format(
                start, target, rows, max_decrease)
            if best is None:
                self.assertFalse(result['ok'], msg=msg)
                self.assertEqual(
                    result['max_total_decrease'],
                    2 * max_decrease * ((rows + 1) // 2), msg=msg)
            else:
                self.assertTrue(result['ok'], msg=msg)
                self.assertEqual(result['deviation'], best[0], msg=msg)
                self.assertEqual(tuple(result['decreases']), best[1], msg=msg)
                # 末行余针等于目标针数，减针行互不相邻
                d = result['decreases']
                self.assertEqual(start - 2 * sum(d), target, msg=msg)
                self.assertTrue(
                    all(not (d[i] and d[i + 1]) for i in range(rows - 1)), msg=msg)


if __name__ == '__main__':
    unittest.main()
