from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .forms import ProblemForm
from .models import Problem

# Create your views here.


def index(request):
    return HttpResponse("Hello! You're at the minora app index.")


def upload_problem(request):
    if request.method == "POST":
        form = ProblemForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            problem = form.save()
            return HttpResponseRedirect(reverse("minora:details", args=(problem.id,)))
    else:
        form = ProblemForm()
    return render(request, "minora/upload_problem.html", {"form": form})


def details(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)

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
