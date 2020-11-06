from . import views
from django.urls import path

urlpatterns = [
    path('orders', views.AddorderView.as_view()),
    path('orders', views.AddorderView.as_view()),
    path('orders/[int:order_id]/status', views.OrderStatus.as_view()),
    path('orders/[int:order_id]/comment', views.OrderComment.as_view()),
]