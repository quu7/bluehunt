#!/usr/bin/env python3

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.upload_problem, name="upload-problem"),
]
