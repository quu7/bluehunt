#!/usr/bin/env python3

from django.urls import path

from . import views

app_name = "minora"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("upload/", views.upload_problem, name="upload-problem"),
    path("details/<int:problem_id>/", views.details, name="details"),
]
