from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("schools/<str:school_slug>/", views.school_dashboard, name="school_dashboard"),
]
