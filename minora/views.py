from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .forms import UploadProblemForm, ProblemParameterForm
from .models import Problem

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

# Create your views here.


class IndexView(generic.ListView):
    template_name = "minora/index.html"
    context_object_name = "problem_list"

    def get_queryset(self):
        """Return all Problems."""
        return Problem.objects.all()


def upload_problem(request):
    if request.method == "POST":
        form = UploadProblemForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            problem = form.save()
            return HttpResponseRedirect(reverse("minora:details", args=(problem.id,)))
    else:
        form = UploadProblemForm()
    return render(request, "minora/upload_problem.html", {"form": form})


def details(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    if request.method == "POST":
        form = ProblemParameterForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("minora:results", args=(problem.id,)))

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
