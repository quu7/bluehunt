#!/usr/bin/env python3

import numpy as np
import pandas as pd
from scipy.optimize import linprog


class LinearProgramError(Exception):
    pass


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
        """Calculate marginal utility of this criterion from an alternative's value.

        Parameters
        ----------
        value : float
            Alternative's value in this Criterion.

        Returns
        -------
        weights_array : tuple
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

    def w(self):
        return [1] * len(self.interval)

    def e(self):
        return [0] * len(self.interval)


class Criteria(object):
    "Object containing Criterion objects."

    def __init__(self, criteria):
        if not isinstance(criteria, (tuple, list)):
            raise TypeError("Criterion objects must be provided in a tuple or list.")
        for item in criteria:
            if not isinstance(item, Criterion):
                raise TypeError(
                    "Provided objects must be instances of Criterion class."
                )

        self.criteria = tuple(criteria)

    def __len__(self):
        return len(self.criteria)

    def __iter__(self):
        return self.criteria.__iter__()

    def __next__(self):
        return self.criteria.__len__()

    def weight_array(self, criterion_name):
        array = []
        for index, item in enumerate(self.criteria):
            if item.name == criterion_name:
                array.extend(item.w())
            else:
                array.extend(item.e())
        return array


def utastar(multicrit_tbl, crit_monot, a_split, delta, epsilon):
    """Run UTASTAR on given data.

    Parameters
    ----------
    multicrit_tbl : pandas DataFrame
        The 1st column lists the alternatives (and is the index of the
        DataFrame), the 2nd contains the user-provided rank of alternatives, and
        the following ones contain the names and values of the decision criteria.
    crit_monot : dict
        A dictionary with criteria names and boolean values, whose number is
        equal to that of the criteria, defining whether each criterion is
        increasing (True) or decreasing (False).
    a_split : dict
        A dictionary with names of criteria as keys and values the number of
        subintervals desired for each criterion's interval segmentation.
    delta : float
        The preference threshold.
    epsilon : float
        Small positive float used in determining weights in final preference model.

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
    # Create Criteria object from list of criteria
    criteria = Criteria(criteria)

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

    # Part of linear program constraints relating to double error function (σ+
    # and σ- )
    error_array = np.zeros([len(differences), len(alternatives) * 2])
    for difference, i in zip(error_array, range(0, len(differences) * 2, 2)):
        difference[i] = 1
        difference[i + 1] = -1
        difference[i + 2] = -1
        difference[i + 3] = 1

    # Separate linear program's constraints into inequality and equality
    # constraints and append them to the apropriate array
    lp_constraints = np.concatenate((differences, error_array), axis=1)

    A_ub = []
    A_eq = []
    b_ub = []
    b_eq = []
    for i, row in enumerate(lp_constraints):
        if multicrit_tbl.iat[i, 0] < multicrit_tbl.iat[i + 1, 0]:
            A_ub.append(row)
            b_ub.append(delta)
        else:
            A_eq.append(row)
            b_eq.append(0)

    # Append constraint that ensures all w_ij subinterval variable values sum up
    # to 1
    A_eq.append([1] * sum(a_split.values()) + [0] * len(alternatives) * 2)
    b_eq.append(1)

    c = [0] * sum(a_split.values()) + [1] * len(alternatives) * 2

    A_ub = np.array(A_ub)
    A_eq = np.array(A_eq)
    b_ub = np.array(b_ub)
    b_eq = np.array(b_eq)
    c = np.array(c)

    # Invert A_ub and b_eq to conform to <= inequalities, instead of >=
    A_ub = -A_ub
    b_ub = -b_ub

    print("A_ub")
    print(A_ub)
    print("b_ub")
    print(b_ub)
    print("A_eq")
    print(A_eq)
    print("b_eq")
    print(b_eq)
    print("c")
    print(c)

    # Solve linear program using simplex
    lp_res = linprog(c, A_ub, b_ub, A_eq, b_eq, method="revised simplex")
    if not lp_res.success:
        raise LinearProgramError("Linear program could not be solved.")

    # if not lp_res.fun == 0:
    if lp_res.fun == 0:
        results = []
        for criterion in criteria:
            error_array = np.zeros([len(differences), len(alternatives) * 2])
            lp_constraints = np.concatenate((differences, error_array), axis=1)
            A_ub = []
            A_eq = []
            b_ub = []
            b_eq = []
            for i, row in enumerate(lp_constraints):
                if multicrit_tbl.iat[i, 0] < multicrit_tbl.iat[i + 1, 0]:
                    A_ub.append(row)
                    b_ub.append(delta)
                else:
                    A_eq.append(row)
                    b_eq.append(0)

            # Append constraint that ensures all w_ij subinterval variable values sum up
            # to 1
            A_eq.append([1] * sum(a_split.values()) + [0] * len(alternatives) * 2)
            b_eq.append(1)
            # Add constraint that ensures sum of errors is less than the value
            # of the objective function of original linear program plus epsilon.
            A_ub.append([0] * sum(a_split.values()) + [-1] * len(alternatives) * 2)
            b_ub.append(-(lp_res.fun + epsilon))

            c = criteria.weight_array(criterion.name) + [0] * len(alternatives) * 2

            A_ub = np.array(A_ub)
            A_eq = np.array(A_eq)
            b_ub = np.array(b_ub)
            b_eq = np.array(b_eq)
            c = np.array(c)

            # Invert A_ub and b_eq to conform to <= inequalities, instead of >=
            A_ub = -A_ub
            b_ub = -b_ub

            # Solve LPs using original LP's optimal solution as Basic Feasible Solution.
            res = linprog(
                c, A_ub, b_ub, A_eq, b_eq, method="revised simplex", x0=lp_res.x
            )
            if res.success:
                results.append(res)
                print(res.x)
            else:
                print(res.message)

        weights = np.array([x.x for x in results])
        print(f"Weights: {weights}")
        avg_results = np.average(weights, axis=1)
        print("Average weights: ", avg_results[: sum(a_split.values())])

    w_values = lp_res.x[: sum(a_split.values())]
    print(w_values)

    utilities = np.dot(alternatives, w_values)
    print(utilities)
    # return lp_res
    return weights
