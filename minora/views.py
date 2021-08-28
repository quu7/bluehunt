from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .forms import UploadProblemForm, ProblemParameterForm
from .models import Problem

# Create your views here.


def index(request):
    return HttpResponse("Hello! You're at the minora app index.")


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
            return HttpResponseRedirect(reverse("minora:index"))

    multicrit_tbl, crit_params = problem.get_dataframe()

    return render(
        request,
        "minora/details.html",
        {
            "multicrit_tbl": multicrit_tbl,
            "crit_params": crit_params,
            "problem": problem,
        },
    )
