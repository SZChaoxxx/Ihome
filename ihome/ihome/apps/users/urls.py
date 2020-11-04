from . import views
from django.urls import path

urlpatterns = [

    path('users',views.RegisterView.as_view()),
    path('session',views.LoginView.as_view()),
]