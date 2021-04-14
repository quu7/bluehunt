#!/usr/bin/env python3

import numpy as np
import scipy as sp
import pandas as pd

def define_intervals(crit_values, crit_monot, a_split):
    """Define value intervals of criteria, given the monotonicity, and the
    number of points to split each interval.
    Parameters
    ----------
    crit_values: pandas DataFrame
            Table whose columns correspond to the criteria and rows that
            correspond to the values of the alternatives on those criteria.
    crit_monot: array
            An array with boolean values, whose number is equal to that of the
            criteria, defining whether each criterion is increasing (True) or
            decreasing (False).
    a_split: array
            Specifies the number of subintervals into which to split each
            criterion's interval.
    """
    # columns of DataFrame: criteria, rows: [min, max]
    interval_extrema = crit_values.agg(['min', 'max'])


def utastar(multicrit_tbl, crit_monot):
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

    pass
