from django.contrib.auth import login, authenticate, logout
from users.models import User
from django.shortcuts import render
from django.http import JsonResponse
# Create your views here.
from django.views import View
import json,re


# 用户注册
class RegisterView(View):
    def post(self,request):
        # １,提取参数
        data = json.loads(request.body.decode())

        mobile = data.get('mobile')#手机号
        phonecode = data.get('phonecode')#短信验证码
        password = data.get('password')#密码
        # 2、校验参数
        # 2.1、必要性校验
        if not all([mobile,phonecode,password]):
            return JsonResponse({
                'code':4103,
                'errmsg':'缺少必要参数'
            })
        # 2,2,约束性校验
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return JsonResponse({
                'code':4103,
                'errmsg':'手机号格式有误'
            })
        if not re.match(r'^\d{6}$', phonecode):
            return JsonResponse({
                'code': 4103,
                'errmsg': '短信验证码格式有误'
            })
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$',password):
            return JsonResponse({
                'code':4106,
                'errmsg':'密码格式有误',

            })
        # 3、业务数据处理 —— 新建User模型类对象保存数据库,注册的核心逻辑 - 保存到数据库(mobile,phonecode,password)
        try:
            user = User.objects.create_user(username=mobile,
                                            mobile=mobile,
                                            password=password)
        except Exception as e:
            print(e)
            return JsonResponse({
                'code':4103,
                'errmsg':'数据库写入失败'
            })
        # TODO: 状态保持 —— 使用session机制，把用户数据写入redis
        login(request,user,backend='django.contrib.auth.backends.ModelBackend')

        # 4,构建响应
        response = JsonResponse({
            'code':0,
            'errmsg':'ok'
        })
        return response

# 用户登陆
class LoginView(View):

    def post(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        mobile = data.get('mobile')
        password = data.get('password')
        # 2、校验参数
        # 2.1、必要性校验
        if not all([mobile, password]):
            return JsonResponse({
                'code': 4103,
                'errmsg': '缺少参数'
            })
        # 2.2 约束性校验
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return JsonResponse({
                'code':4103,
                'errmsg':'手机号格式有误'
            })
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({
                'code': 4103,
                'errmsg': '密码格式有误',
            })
        # ３,业务数据处理
        # 3.验证是否能够登录
        user = authenticate(request,username=mobile, password=password)

        # 判断是否为空,如果为空,返回
        if not user:
            return JsonResponse({
                'code': 4103,
                'errmsg': '手机号或者密码错误'
            })
        #状态保持
        login(request, user)
        # 4、构建响应
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.set_cookie('username', user.username, max_age=3600*24*14)
        return response


    def delete(self, request):
        """
         退出登陆
        """
        # １,删除该用户的session登陆数据，清除该用户的登陆状态
        logout(request) # 通过request对象获取用户信息，然后在去清除session数据
        response = JsonResponse({'code': 0, 'errmsg': '已登出'})
        response.delete_cookie('username')
        return response


    def get(self,request):
        """
        判断是否登陆
        :param request:
        :return:
        """
        user = request.user
        if user:
            return JsonResponse({
                'errno':0,
                'errmsg':'已登陆',
                'data':{
                    'name':'user'#用户名
                }

            })
        else:
            # 未登录：
            return JsonResponse({
                "errno": "4101",
                "errmsg": "未登录"
            })






