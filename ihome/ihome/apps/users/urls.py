from . import views
from django.urls import path, re_path

urlpatterns = [
    path('user/',views.UsernameCountView.as_view()),
]