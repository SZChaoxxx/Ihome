from django.urls import path
from . import views

urlpatterns = [
    # TODO: 自定义转换器匹配uuid和pre 或者直接匹配后做参数校验
    path('imagecode/', views.ImageCodeView.as_view()),
    # 短信验证码
    path('sms/<mobile:mobile>/', views.SMSCodeView.as_view()),

]