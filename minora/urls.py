#!/usr/bin/env python3

from django.urls import path

from . import views

app_name = "minora"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("upload/", views.upload_problem, name="upload-problem"),
    path("details/<int:problem_id>/", views.details, name="details"),
    path("results/<int:problem_id>/", views.results, name="results"),
    path(
        "evaluate-alternative/<int:problem_id>/",
        views.evaluate_alternative,
        name="evaluate-alternative",
    ),
    path(
        "download-model/<int:problem_id>/", views.download_model, name="download-model"
    ),
]
