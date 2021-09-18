from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.urls import reverse
from django.views import generic
from .forms import ProblemFileForm, ProblemParameterForm
from .models import Problem

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import pandas as pd

# Create your views here.


class IndexView(generic.ListView):
    template_name = "minora/index.html"
    context_object_name = "problem_list"

    def get_queryset(self):
        """Return all Problems."""
        return Problem.objects.all()


def upload_problem(request):
    if request.method == "POST":
        form = ProblemFileForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            problem = form.save()
            return redirect("minora:details", problem.id)
    else:
        form = ProblemFileForm()
    return render(request, "minora/upload_problem.html", {"form": form})


def replace_problem_file(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    if request.method == "POST":
        form = ProblemFileForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            new_problem = form.save()
            return redirect("minora:delete", problem.id, new_problem.id)
    else:
        form = ProblemFileForm()
    return render(
        request,
        "minora/replace_problem_file.html",
        {
            "problem": problem,
            "form": form,
        },
    )


def details(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    if request.method == "POST":
        form = ProblemParameterForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            return redirect("minora:results", problem.id)

    multicrit_tbl, crit_params = problem.get_dataframe()
    multicrit_tbl_html = multicrit_tbl.to_html(
        justify="inherit",
        index_names=False,
        classes=[
            "table",
            "table-hover",
        ],
    )

    crit_params_html = crit_params.to_html(
        justify="inherit",
        index_names=False,
        classes=[
            "table",
            "table-hover",
        ],
    )

    return render(
        request,
        "minora/details.html",
        {
            "multicrit_tbl": multicrit_tbl_html,
            "crit_params": crit_params_html,
            "problem": problem,
        },
    )


def results(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    result = problem.run_utastar()

    multicrit_tbl = result.table.to_html(
        justify="inherit",
        index_names=False,
        classes=[
            "table",
            "table-hover",
        ],
    )

    graphs = []
    for criterion, values in zip(result.criteria, result.w_values.values()):
        points = criterion.interval.points
        # Insert missing 0 for first point of interval with 0 partial
        # utility.
        values = np.concatenate(([0], values))
        # To get marginal utility values for each criterion we need to sum w_ij
        # values to the index of that subinterval.
        values = np.cumsum(values)

        # Normalize values
        values = values / values.max()

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(points, values, "-bo")
        ax.xaxis.set_ticks(points)
        ax.set_title(criterion.name)

        filelike = io.BytesIO()
        fig.savefig(filelike)
        encoded_fig = base64.b64encode(filelike.getvalue()).decode()
        graphs.append(encoded_fig)

    return render(
        request,
        "minora/results.html",
        {
            "result": result,
            "problem": problem,
            "image_list": graphs,
            "multicrit_tbl": multicrit_tbl,
        },
    )


def evaluate_alternative(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)

    multicrit_tbl, crit_params = problem.get_dataframe()
    criteria = multicrit_tbl.columns[1:]

    if request.method == "POST":
        try:
            if not request.POST["name"]:
                raise KeyError("Please fill in the alternative's name.")

            alt_values = []
            for criterion in criteria:
                if request.POST[criterion]:
                    alt_values.append(float(request.POST[criterion]))
                else:
                    raise ValueError(f"Invalid value for criterion {criterion}.")

            result = problem.run_utastar()

            utility = result.get_utility(alt_values)

            row = [""]
            row.extend(alt_values)
            row.append(utility)

            result.table.loc[request.POST["name"]] = row
            # Sort new table to show new alternative's ranking to
            # original alternatives.
            result.table.sort_values("Utilities", ascending=False, inplace=True)
            multicrit_tbl_html = result.table.to_html(
                justify="inherit",
                index_names=False,
                classes=[
                    "table",
                    "table-hover",
                ],
            )

            return render(
                request,
                "minora/evaluate_alternative.html",
                {
                    "problem": problem,
                    "criteria": criteria,
                    "multicrit_tbl": multicrit_tbl_html,
                },
            )

        except (KeyError, ValueError) as e:
            error_message = getattr(e, "message", str(e))
            return render(
                request,
                "minora/evaluate_alternative.html",
                {
                    "problem": problem,
                    "criteria": criteria,
                    "error_message": error_message,
                },
            )

    multicrit_tbl_html = multicrit_tbl.to_html(
        justify="inherit",
        index_names=False,
        classes=[
            "table",
            "table-hover",
        ],
    )

    return render(
        request,
        "minora/evaluate_alternative.html",
        {
            "problem": problem,
            "criteria": criteria,
            "multicrit_tbl": multicrit_tbl_html,
        },
    )


def download_model(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    result = problem.run_utastar()

    weights = {}
    for criterion, weight in zip(result.criteria, result.weights):
        weights[criterion.name] = weight

    w_values_df = pd.DataFrame.from_dict(result.w_values, orient="index", dtype="float")
    weights_df = pd.DataFrame.from_dict(weights, orient="index", dtype="float")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        weights_df.to_excel(writer, sheet_name="Weights")
        w_values_df.to_excel(writer, sheet_name="w_ij")

    buffer.seek(0)
    return FileResponse(
        buffer, as_attachment=True, filename=f"{problem.name} results.xlsx"
    )


def delete_problem(request, old_problem_id, new_problem_id):
    old_problem = get_object_or_404(Problem, pk=old_problem_id)

    # Delete problem_file from storage
    old_problem.problem_file.delete(save=False)
    # and then delete the instance of Problem.
    old_problem.delete()

    if new_problem_id == 0:
        return redirect("minora:index")

    return redirect("minora:details", new_problem_id)
