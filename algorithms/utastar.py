#!/usr/bin/env python3

import numpy as np
import pandas as pd
from itertools import chain
from scipy.optimize import linprog
from scipy.stats import kendalltau
import logging

# Get module's name for logging
logger = logging.getLogger(__name__)


class LinearProgramError(Exception):
    pass


class Subinterval:
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
        self.points = np.linspace(start=left, stop=right, num=num_of_subintervals + 1)
        subintervals = [0] * num_of_subintervals
        for i in range(len(self.points)):
            if not self.points[i] == self.right:
                subintervals[i] = Subinterval(self.points[i], self.points[i + 1])
        self.subintervals = tuple(subintervals)

    def __len__(self):
        return len(self.subintervals)

    def __iter__(self):
        return self.subintervals.__iter__()

    def __next__(self):
        return self.subintervals.__next__()

    def __getitem__(self, key):
        if isinstance(key, int):
            if key >= 0 and key < len(self.subintervals):
                return self.subintervals[key]
            else:
                raise IndexError("index out of range")
        else:
            return TypeError("key must be of type int")


class Criterion:
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

    def __iter__(self):
        return self.interval.__iter__()

    def get_value(self, value):
        """Calculate marginal utility of this criterion from an alternative's value.

        Parameters
        ----------
        value : float
            Alternative's value in this Criterion.

        Returns
        -------
        weights_array : list
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


class Criteria:
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

    def __getitem__(self, key):
        if isinstance(key, str):
            for criterion in self.criteria:
                if key == criterion.name:
                    return criterion
            raise KeyError(f"'{key}'")
        elif isinstance(key, int):
            if key >= 0 and key < len(self.criteria):
                return self.criteria[key]
            else:
                raise IndexError("index out of range")
        else:
            raise TypeError("key must be of type str or int")

    def __contains__(self, item):
        if isinstance(item, str):
            try:
                if self[item]:
                    return True
            except KeyError:
                return False
        else:
            raise TypeError("item must be of type str")

    def weight_array(self, criterion_name):
        array = []
        for criterion in self.criteria:
            if criterion_name == criterion.name:
                array.extend(criterion.w())
            else:
                array.extend(criterion.e())
        return array


class UtastarResult:
    """Contain results from a UTASTAR run.

    Parameters
    ----------
    criteria : Criteria iterable
        Object containing Criterion objects representing the problem's criteria.
    w_values : iterable
        Marginal weights used in calculating an alternative's marginal utility
        for each criterion.
    tau : float
        Kendall's tau statistic calculated on both rankings of alternatives.
    multicrit_tbl : pandas.DataFrame
        Multicriteria table of the problem with the last column containing total
        utilities of alternatives.
    first_sol : list
        List with 2 elements. The first is a w_values array and the second is an
        error array, twice as long as the number of alternatives in the problem.
        It's used to construct a child UtastarResult object representing the
        original solution.
    sa_sol : list
        List with 2 elements. The first is a w_values array and the second is an
        error array, twice as long as the number of alternatives in the problem.
        Each array has as many rows as the number of criteria and represent the
        solutions of linear programs during sensitivity analysis. The list is
        used to construct child UtastarResult objects representing each
        criterion's LP in sensitivity analysis.
    """

    def __init__(
        self, criteria, w_values, alternatives, error_array, multicrit_tbl, **kwargs
    ):
        # A Criteria object representing the problem's criteria.
        self.criteria = criteria

        pointer = 0
        weights = []
        w_values_dict = {}
        partial_utilities_dict = {}
        for criterion in criteria:
            # w_values
            crit_w_values = w_values[pointer : pointer + len(criterion.interval)]
            w_values_dict[criterion.name] = tuple(crit_w_values)
            # Partial utilities
            partial_utilities_dict[criterion.name] = tuple(np.cumsum(crit_w_values))
            # Weights
            weight = sum(crit_w_values)
            weights.append(weight)
            pointer += len(criterion.interval)
        # The resulting model's weights.
        # NOTE: This is a list containing the coeffiecients of the sum of
        # partial values of an alternative's criteria values.
        self.weights = tuple(weights)

        # The w_ij values used in calculating each alternative's marginal
        # utilities for each criterion.
        # self.w_values = tuple(w_values)
        self.w_values = w_values_dict

        # Criterion's partial utilities calculated by adding w_ij values together.
        self.partial_util = partial_utilities_dict

        self.num_of_criteria = len(criteria)

        # Calculate utilities
        utilities = np.dot(alternatives, w_values)

        # Kendall's tau coefficient calculated between the original and
        # resulting rankings of alternatives (correlation of rankings).
        instance_tbl = multicrit_tbl.copy()
        instance_tbl["Utilities"] = utilities
        sorted_by_utilities = instance_tbl.sort_values("Utilities", ascending=False)
        tau_c, tau_p = kendalltau(instance_tbl.index, sorted_by_utilities.index)

        self.tau = tau_c

        self.table = sorted_by_utilities

        self.errors = error_array

        # if kwargs["first_sol"] and kwargs["sa_sol"]:
        if "first_sol" in kwargs and "sa_sol" in kwargs:
            self.first_sol = UtastarResult(
                criteria,
                kwargs["first_sol"][0],
                alternatives,
                kwargs["first_sol"][1],
                multicrit_tbl,
            )
            sa_sol_list = []
            for i in range(len(criteria)):
                sa_sol_list.append(
                    UtastarResult(
                        criteria,
                        kwargs["sa_sol"][0][i],
                        alternatives,
                        kwargs["sa_sol"][1][i],
                        multicrit_tbl,
                    )
                )
            self.sa_sol = tuple(sa_sol_list)

    def get_utility(self, alt_values):
        "Calculate utility of a new alternative"
        weights = []
        for value, criterion in zip(alt_values, self.criteria):
            weights.extend(criterion.get_value(value))
        return np.dot(weights, tuple(chain(*self.w_values.values())))

    def get_crit_weights(self, crit_name):
        "Return marginal weights for each subinterval in crit_name."
        return self.w_values[crit_name]


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
    UtastarResult : UtastarResult
        Contains the resulting utilities, weights, w_values and criteria array,
        among other helper methods, of a utastar() run.
    """

    logger.info("Applying UTASTAR!")

    # Sort alternatives by their original ranking.
    multicrit_tbl.sort_values(multicrit_tbl.columns[0], ascending=True, inplace=True)
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
            weights.extend(criterion.get_value(value))
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

    logger.debug("A_ub is\n%s", A_ub)
    logger.debug("b_ub is %s", b_ub)
    logger.debug("A_eq is\n%s", A_eq)
    logger.debug("b_eq is %s", b_eq)
    logger.debug("c is %s", c)

    # Solve linear program
    lp_res = linprog(c, A_ub, b_ub, A_eq, b_eq, method="revised simplex")
    if not lp_res.success:
        raise LinearProgramError("Linear program could not be solved.")

    # Check for solution multiplicity
    # If the objective function's optimal value is 0 then multiple optimal
    # solutions may be present, and in that case we solve LPs to maximize the
    # weights of each criterion.
    logger.debug("Linear program objective function's optimal value: %s", lp_res.fun)

    if np.isclose(lp_res.fun, 0):
        results = []
        logger.debug(
            "Calculating multiple LPs to optimize w_values for each criterion."
        )
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
            c = -c
            logger.debug("c:\n%s", c)
            res = linprog(c, A_ub, b_ub, A_eq, b_eq, method="revised simplex")

            if res.success:
                results.append(res)
                logger.debug("x:\n%s", res.x)
            else:
                logger.debug("Cannot solve LP: %s", res.message)

        lp_x_array = np.array([result.x for result in results])
        logger.debug("w_values of LPs:\n%s", lp_x_array)
        sa_w_array = lp_x_array[:, : sum(a_split.values())]
        w_values = np.average(sa_w_array, axis=0)
        # w_values = avg_results[: sum(a_split.values())]
        logger.debug("Average w_values:\n%s", w_values)

        sa_error_array = lp_x_array[:, sum(a_split.values()) :]
        error_array = np.average(sa_error_array, axis=0)

        first_solution = [
            lp_res.x[: sum(a_split.values())],
            lp_res.x[sum(a_split.values()) :],
        ]
        sa_solutions = [sa_w_array, sa_error_array]

        utilities = np.dot(alternatives, w_values)
        logger.info("Utilities of alternatives: %s", utilities)

        logger.info("Done!")
        return UtastarResult(
            criteria,
            w_values,
            alternatives,
            error_array,
            multicrit_tbl,
            first_sol=first_solution,
            sa_sol=sa_solutions,
        )

    else:
        w_values = lp_res.x[: sum(a_split.values())]
        logger.debug("w_values:\n%s", w_values)

        error_array = lp_res.x[sum(a_split.values()) :]

        utilities = np.dot(alternatives, w_values)
        logger.info("Utilities of alternatives: %s", utilities)

        logger.info("Done!")
        return UtastarResult(
            criteria, w_values, alternatives, error_array, multicrit_tbl
        )
