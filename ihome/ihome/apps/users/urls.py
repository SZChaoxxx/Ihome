from . import views
from django.urls import path

urlpatterns = [
    path('users',views.RegisterView.as_view()),
    path('session',views.LoginView.as_view()),
    path('user/avatar',views.UpdateAvatar.as_view()),
    path('user/name',views.UpdateName.as_view()),
    path('user/auth',views.RealName.as_view()),
    path('user/houses', views.MyHousesView.as_view()),
    path('user',views.UsernameCountView.as_view()),
]