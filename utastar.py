#!/usr/bin/env python3

import numpy as np
import pandas as pd

# import scipy as sp


def define_intervals(crit_values, crit_monot, a_split):
    """Define value intervals of criteria, given the monotonicity, and the
    number of points to split each criterion's interval.
    Parameters
    ----------
    crit_values: pandas DataFrame
            Table whose columns correspond to the criteria and rows that
            correspond to the values of the alternatives on those criteria.
    crit_monot: array
            An array with boolean values, whose number is equal to that of the
            criteria, defining whether each criterion is increasing (True) or
            decreasing (False).
    a_split: numpy ndarray
            Specifies the number of subintervals into which to split each
            criterion's interval.
    Returns
    -------
    intervals: list
            List of numpy arrays with the points of subintervals into which each
            criterion's value interval was split.
    """
    if not np.all(a_split > 0):
        raise ValueError("Number of subintervals must be positive.")
    # columns of DataFrame: criteria, rows: [min, max]
    interval_extrema = crit_values.agg(["min", "max"])

    crit_num = interval_extrema.shape[1]
    intervals = []
    for i in range(crit_num):
        if crit_monot[i]:
            intervals.append(
                np.linspace(
                    interval_extrema.iat[0, i],
                    interval_extrema.iat[1, i],
                    a_split[i] + 1,
                )
            )
        elif not crit_monot[i]:
            intervals.append(
                np.linspace(
                    interval_extrema.iat[1, i],
                    interval_extrema.iat[0, i],
                    a_split[i] + 1,
                )
            )
    return intervals


def calc_partial_utility(crit_values, crit_intervals):
    """Calculate partial utility for each criterion
    Parameters
    ----------
    crit_values: pandas DataFrame
            Table whose columns correspond to the criteria and rows that
            correspond to the values of the alternatives on those criteria.
    crit_intervals: list
            List of numpy arrays with the points of subintervals into which each
            criterion's value interval was split.
    Returns
    -------
    """


def utastar(multicrit_tbl, crit_monot, a_split):
    """Run UTASTAR on given data.
    Parameters
    ----------
    multicrit_tbl: pandas DataFrame
            The 1st column lists the alternatives, the 2nd contains the
            user-provided rank of alternatives, and the following ones contain
            the names and values of the decision criteria.
    crit_monot: array
            An array with boolean values, whose number is equal to that of the
            criteria, defining whether each criterion is increasing (True) or
            decreasing (False).
    Returns
    -------

    """

    crit_intervals = define_intervals(multicrit_tbl.iloc[:, 2:], crit_monot, a_split)
