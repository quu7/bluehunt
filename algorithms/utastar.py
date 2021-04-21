#!/usr/bin/env python3

import numpy as np
import pandas as pd

# import scipy as sp


class Subinterval(object):
    """Represent a subinterval of a criterion's interval of valid values."""

    def __init__(self, left, right):
        if left == right:
            raise ValueError("Edges of subinterval cannot be the same.")
        self.validate(left)
        self.validate(right)
        self.left = left
        self.right = right
        if right > left:
            self.monotonicity = True
        else:
            self.monotonicity = False

    def __contains__(self, item):
        if self.monotonicity:
            return self.left <= item <= self.right
        elif not self.monotonicity:
            return self.left >= item >= self.right

    def __repr__(self):
        return f"[{self.left}, {self.right}]"

    def isedge(self, item):
        return self.left == item or self.right == item

    def validate(self, num):
        if not isinstance(num, (int, float, np.integer, np.single, np.double)):
            raise TypeError(f"{num} must be integer or float.")


class Interval(Subinterval):
    """Interval of valid values that a criterion can take"""

    def __init__(self, left, right, num_of_subintervals):
        self.validate(left)
        self.validate(right)
        if not isinstance(num_of_subintervals, (int, np.integer)):
            raise TypeError(
                f"num_of_subintervals, {num_of_subintervals}, must be an integer."
            )
        if not num_of_subintervals > 0:
            raise ValueError("Number of subintervals must be positive.")

        self.left = left
        self.right = right
        if right > left:
            self.monotonicity = True
        else:
            self.monotonicity = False
        array = np.linspace(start=left, stop=right, num=num_of_subintervals + 1)
        subintervals = [0] * num_of_subintervals
        for i in range(len(array)):
            if not array[i] == self.right:
                subintervals[i] = Subinterval(array[i], array[i + 1])
        self.subintervals = tuple(subintervals)

    def __len__(self):
        return len(self.subintervals)

    def __iter__(self):
        return self.subintervals.__iter__()

    def __next__(self):
        return self.subintervals.__next__()


class Criterion(object):
    """Stores criterion's value interval and other related attributes."""

    def __init__(self, name, interval):
        self.name = name
        self.interval = interval

    def __repr__(self):
        if self.interval.monotonicity:
            monotonicity = "ascending"
        elif not self.interval.monotonicity:
            monotonicity = "descending"
        return f"Name: {self.name}\nMonotonicity: {monotonicity}\nInterval: {self.interval}"

    def getvalue(self, value):
        """Calculate marginal utility of this criterion from an alternative's value
        Parameters
        ----------
        value: int or float
            Alternative's value in this Criterion.
        Returns
        -------
        weights_array: tuple
            Coefficients of subinterval weights (w_ij)
        """
        if not isinstance(value, (int, float, np.integer, np.single, np.double)):
            raise TypeError(f"{value} must be integer or float.")
        if not value >= 0:
            raise ValueError("Provided value must be non negative.")

        weights_array = [0] * len(self.interval)
        for index, subinterval in enumerate(self.interval):
            if subinterval.isedge(value):
                for i in range(index + 1):
                    weights_array[i] = 1
                break
            elif value in subinterval:
                for i in range(index):
                    weights_array[i] = 1
                weights_array[index] = (value - subinterval.left) / (
                    subinterval.right - subinterval.left
                )
        return weights_array


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
                    start=interval_extrema.iat[0, i],
                    stop=interval_extrema.iat[1, i],
                    num=a_split[i] + 1,
                )
            )
        elif not crit_monot[i]:
            intervals.append(
                np.linspace(
                    start=interval_extrema.iat[1, i],
                    stop=interval_extrema.iat[0, i],
                    num=a_split[i] + 1,
                )
            )
    return intervals


def utastar(multicrit_tbl, crit_monot, a_split):
    """Run UTASTAR on given data.
    Parameters
    ----------
    multicrit_tbl: pandas DataFrame
        The 1st column lists the alternatives, the 2nd contains the
        user-provided rank of alternatives, and the following ones contain
        the names and values of the decision criteria.
    crit_monot: dict
        A dictionary with criteria names and boolean values, whose number is
        equal to that of the criteria, defining whether each criterion is
        increasing (True) or decreasing (False).
    a_split: dict
        A dictionary with names of criteria as keys and values th number of
        subintervals desired for each criterion's interval segmentation.
    Returns
    -------

    """
    crit_values = multicrit_tbl.iloc[:, 2:]
    interval_extrema = crit_values.agg(["min", "max"])

    # List length = number of crit_values's columns
    criteria = []
    for criterion in crit_values:
        if criterion in crit_monot:
            if crit_monot[criterion]:
                criteria.append(
                    Criterion(
                        name=criterion,
                        interval=Interval(
                            interval_extrema.at["min", criterion],
                            interval_extrema.at["max", criterion],
                            a_split[criterion],
                        ),
                    )
                )
            elif not crit_monot[criterion]:
                criteria.append(
                    Criterion(
                        name=criterion,
                        interval=Interval(
                            interval_extrema.at["max", criterion],
                            interval_extrema.at["min", criterion],
                            a_split[criterion],
                        ),
                    )
                )

    for i in criteria:
        print(i)
        print("---")
