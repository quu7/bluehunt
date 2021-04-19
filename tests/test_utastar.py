#!/usr/bin/env python3

import numpy as np
from numpy.testing import assert_allclose

# import scipy as sp
import pandas as pd
from utastar import *


def test_subinterval_creation():
    multicrit_tbl = pd.read_csv("public_transport.csv")
    crit_monot = [False, False, True]
    a_split = np.array([2, 3, 3])
    crit_values = multicrit_tbl.iloc[:, 2:]
    intervals = define_intervals(crit_values, crit_monot, a_split)
    test_intervals = [
        np.array([30.0, 16.0, 2.0]),
        np.array([40.0, 30.0, 20.0, 10.0]),
        np.array([0.0, 1.0, 2.0, 3.0]),
    ]
    for interval_array, test_array in zip(intervals, test_intervals):
        assert_allclose(interval_array, test_array)
