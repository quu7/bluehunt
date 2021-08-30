from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .forms import UploadProblemForm, ProblemParameterForm
from .models import Problem

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


def results(request, problem_id):

    return render(
        request,
        "minora/results.html",
    )
