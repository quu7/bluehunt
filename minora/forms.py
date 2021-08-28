#!/usr/bin/env python3

from django.forms import ModelForm
from .models import Problem


class UploadProblemForm(ModelForm):
    class Meta:
        model = Problem
        fields = ["name", "problem_file"]


class ProblemParameterForm(ModelForm):
    class Meta:
        model = Problem
        fields = ["delta", "epsilon"]
