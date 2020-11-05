from . import views
from django.urls import path,re_path

urlpatterns = [

    path('users',views.RegisterView.as_view()),
    path('session',views.LoginView.as_view()),
    re_path(r'^user$',views.UsernameCountView.as_view()),
    re_path(r'^user/avatar$',views.UpdateAvatar.as_view()),
    re_path(r'^user/name$',views.UpdateName.as_view()),
    re_path(r'^user/auth$',views.RealName.as_view()),

]