#!/usr/bin/env python3

from django.forms import ModelForm
from .models import Problem


class ProblemForm(ModelForm):
    class Meta:
        model = Problem
        fields = ["name", "problem_file"]
