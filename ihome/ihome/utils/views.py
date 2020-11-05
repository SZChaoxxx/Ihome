"""
自定义登陆验证视图拓展类
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

class LoginRequiredJsonMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        return JsonResponse({
            'code':4101,
            'errmsg':'用户未登录'
        })