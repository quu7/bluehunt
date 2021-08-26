from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .forms import ProblemForm

# Create your views here.


def index(request):
    return HttpResponse("Hello! You're at the minora app index.")


def upload_problem(request):
    if request.method == "POST":
        form = ProblemForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            form.save()
            return HttpResponseRedirect(reverse("minora:index"))
    else:
        form = ProblemForm()
    return render(request, "minora/upload_problem.html", {"form": form})
