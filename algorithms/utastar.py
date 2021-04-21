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
        if not isinstance(interval, Interval):
            raise TypeError(f"{interval} must be an Interval object.")
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
            # If value is left edge of first subinterval then its utility is 0
            # and the coefficients of weights should be 0 as well.
            if index == 0 and subinterval.left == value:
                break
            elif subinterval.isedge(value):
                for i in range(index + 1):
                    weights_array[i] = 1
                break
            elif value in subinterval:
                for i in range(index):
                    weights_array[i] = 1
                weights_array[index] = (value - subinterval.left) / (
                    subinterval.right - subinterval.left
                )
                break
        return weights_array


def utastar(multicrit_tbl, crit_monot, a_split, delta):
    """Run UTASTAR on given data.
    Parameters
    ----------
    multicrit_tbl: pandas DataFrame
        The 1st column lists the alternatives (and is the index of the
        DataFrame), the 2nd contains the user-provided rank of alternatives, and
        the following ones contain the names and values of the decision
        criteria.
    crit_monot: dict
        A dictionary with criteria names and boolean values, whose number is
        equal to that of the criteria, defining whether each criterion is
        increasing (True) or decreasing (False).
    a_split: dict
        A dictionary with names of criteria as keys and values the number of
        subintervals desired for each criterion's interval segmentation.
    delta: float
        The preference threshold.
    Returns
    -------

    """
    crit_values = multicrit_tbl.iloc[:, 1:]
    interval_extrema = crit_values.agg(["min", "max"])

    # List length = number of crit_values's columns
    criteria = []
    for criterion in crit_values:
        if criterion in crit_monot and criterion in a_split:
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

    # Calculate each alternative's utility
    alternatives = []
    for alternative in multicrit_tbl.index:
        weights = []
        for value, criterion in zip(crit_values.loc[alternative], criteria):
            weights.extend(criterion.getvalue(value))
        alternatives.append(weights)

    alternatives = np.array(alternatives)

    # Calculate differences between each successive pair of alternatives
    differences = []
    for i in range(len(alternatives) - 1):
        differences.append(alternatives[i] - alternatives[i + 1])

    differences = np.array(differences)

    return differences
