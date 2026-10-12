import unittest

import numpy as np
import pandas as pd

from src import evaluation as ev


class TopKTests(unittest.TestCase):
    def test_perfect_score_reaches_all_churners_within_capacity(self):
        y = np.array([1] * 10 + [0] * 90)
        result = ev.topk_metrics(y, y.astype(float), fractions=(0.10, 0.20)).set_index('capacity')
        self.assertEqual(result.loc[0.10, 'precision'], 1.0)
        self.assertEqual(result.loc[0.10, 'recall'], 1.0)
        self.assertAlmostEqual(result.loc[0.10, 'lift'], 10.0)
        self.assertAlmostEqual(result.loc[0.20, 'precision'], 0.5)

    def test_random_scores_have_lift_near_one(self):
        rng = np.random.default_rng(1)
        y = (rng.random(20000) < 0.1).astype(int)
        result = ev.topk_metrics(y, rng.random(20000), fractions=(0.10,))
        self.assertAlmostEqual(result.loc[0, 'lift'], 1.0, delta=0.15)

    def test_ties_are_broken_randomly_but_reproducibly(self):
        score = np.array([1.0] * 50 + [0.0] * 50)
        first, second = ev.select_top(score, 0.1, seed=3), ev.select_top(score, 0.1, seed=3)
        self.assertTrue((first == second).all())
        self.assertEqual(first.sum(), 10)
        self.assertTrue(score[first].min() == 1.0)          # only flagged users are selected

    def test_selection_size_is_not_inflated_by_float_rounding(self):
        self.assertEqual(ev.select_top(np.arange(30.0), 0.1).sum(), 3)      # 0.1 * 30 is 3.0000000000000004

    def test_selection_size_rounds_up(self):
        self.assertEqual(ev.select_top(np.arange(11.0), 0.05).sum(), 1)

    def test_band_metrics(self):
        y = np.array([1, 0, 1, 0, 1, 0])
        score = np.array([6, 5, 4, 3, 2, 1.0])
        band = np.array(['a', 'a', 'a', 'b', 'b', 'b'])
        result = ev.band_metrics(y, score, band, 0.5).set_index('band')
        self.assertEqual(result.loc['a', 'selected'], 3)
        self.assertAlmostEqual(result.loc['a', 'precision'], 2 / 3)
        self.assertEqual(result.loc['b', 'selected'], 0)


class ProbabilityTests(unittest.TestCase):
    def test_auc_and_brier(self):
        y = [0, 0, 1, 1]
        self.assertEqual(ev.auc(y, [0.1, 0.2, 0.8, 0.9]), 1.0)
        self.assertTrue(np.isnan(ev.auc([0, 0], [0.1, 0.2])))
        self.assertAlmostEqual(ev.brier([1, 0], [1.0, 0.0]), 0.0)

    def test_calibration_table_bins(self):
        rng = np.random.default_rng(0)
        p = rng.random(10000)
        y = (rng.random(10000) < p).astype(int)
        table = ev.calibration_table(y, p, bins=10)
        self.assertEqual(len(table), 10)
        self.assertTrue(((table.mean_predicted - table.observed_rate).abs() < 0.05).all())


if __name__ == '__main__':
    unittest.main()
