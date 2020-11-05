from sysconfig import get_path

from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from ihome.utils.views import LoginRequiredJsonMixin
from users.models import User
from homes.models import House, Area
from django.shortcuts import render
from django.http import JsonResponse
# Create your views here.
from django.views import View
import json,re
from qiniu import Auth, put_data, etag


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
                'errno':"4103",
                'errmsg':'缺少必要参数'
            })
        # 2,2,约束性校验
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return JsonResponse({
                'errno':"4103",
                'errmsg':'手机号格式有误'
            })
        if not re.match(r'^\d{6}$', phonecode):
            return JsonResponse({
                'errno': "4103",
                'errmsg': '短信验证码格式有误'
            })
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$',password):
            return JsonResponse({
                'errno':"4106",
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
                'errno':"4103",
                'errmsg':'数据库写入失败'
            })
        # 状态保持 —— 使用session机制，把用户数据写入redis
        login(request,user,backend='django.contrib.auth.backends.ModelBackend')

        # 4,构建响应
        response = JsonResponse({
            'errno':"0",
            'errmsg':'注册成功'
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
                'errno': "4103",
                'errmsg': '缺少参数'
            })
        # 2.2 约束性校验
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return JsonResponse({
                'errno':"4103",
                'errmsg':'手机号格式有误'
            })
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({
                'errno': "4103",
                'errmsg': '密码格式有误',
            })
        # ３,业务数据处理
        # 3.验证是否能够登录
        user = authenticate(request,username=mobile, password=password)

        # 判断是否为空,如果为空,返回
        if not user:
            return JsonResponse({
                'errno': "4103",
                'errmsg': '手机号或者密码错误'
            })
        #状态保持
        login(request, user)
        # 4、构建响应
        response = JsonResponse({
            'errno': "0",
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
        response = JsonResponse({'errno': 0, 'errmsg': '已登出'})
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
                    'user_id': user.id,
                    'name':user.username  #用户名
                }

            })
        else:
            # 未登录：
            return JsonResponse({
                "errno": "4101",
                "errmsg": "未登录"
            })


# 个人中心
class UsernameCountView(LoginRequiredJsonMixin,View):
    def get(self,request):
        user = request.user
        data = {
            "avatar_url":"http://qj9kppiiy.hn-bkt.clouddn.com/%s"%user.avatar,
            "create_time":user.date_joined,
            "mobile":user.mobile,
            "name":user.username,
            "user_id":user.id
        }
        if data['avatar_url'] == "http://qj9kppiiy.hn-bkt.clouddn.com/":
            data['avatar_url'] = 'http://qj9kppiiy.hn-bkt.clouddn.com/FhQqgJcMQX4F0aE4XNodk3IAOPQZ'
        return JsonResponse({
            'data':data,
            'errmsg':"OK",
            'errno':"0"
        })


# 修改个人头像
class UpdateAvatar(LoginRequiredJsonMixin,View):
    def post(self,request):
        user = request.user
        file_obj = request.FILES.get('avatar', None)
        if not file_obj:
            return JsonResponse({
                "errno": "4002",
                "errmsg": "无数据"
            })
        # 需要填写你的 Access Key 和 Secret Key
        # access_key = 'BnfVoZAdZUyn4PhhwV6BOSb00fQi9G7QIXkGvdcX'
        # secret_key = 'ox0JfWx5Yu6zX1lB7hOvRaW1gFEAhPXgKn_TJFzB'
        # 构建鉴权对象
        q = Auth(settings.ACCESS_KEY,settings.SECRET_KEY)
        # 要上传的空间
        # bucket_name = 'ihomesz40'
        # 上传后保存的文件名
        key = None
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(settings.BUCKET_NAME, key, 3600)
        print(type(file_obj))
        ret, info = put_data(token,key,file_obj)
        print(ret['key'])
        try:
            user.avatar = ret['key']
            user.save()
        except Exception as e:
            return JsonResponse({
                "errno": "4001",
                "errmsg": "数据库查询错误"
            })
        return JsonResponse({
            "data": {
                "avatar_url": "http://qj9kppiiy.hn-bkt.clouddn.com/" + ret['key']
            },
            "errno": "0",
            "errmsg": "头像上传成功"
        })


# 修改用户名
class UpdateName(LoginRequiredJsonMixin,View):
    def put(self,request):
        user = request.user
        data = json.loads(request.body.decode())
        username = data.get('name')
        # 必要性校验
        if not username:
            return JsonResponse({
                    "errno": "4002",
                    "errmsg": "无数据"
            })
        # 校验名字是否重复
        if username == user.username:
            return JsonResponse({
                "errno": "4003",
                "errmsg": "数据已存在"
            })
        try:
            user.username = username
            user.save()
        except Exception as e:
            return JsonResponse({
                "errno": "4001",
                "errmsg": "数据库查询错误"
            })
        return JsonResponse({
                "errno": "0",
                "errmsg": "修改成功"
            })


# 实名认证
class RealName(LoginRequiredJsonMixin,View):
    def post(self,request):
        user = request.user
        data = json.loads(request.body.decode())
        real_name = data.get('real_name')
        id_card = data.get('id_card')
        #检查必要性参数
        if not all([real_name,id_card]):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "数据错误"

            })
        if not re.match(r'[\u4e00-\u9fa5]',real_name):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "数据错误"
            })
        if not re.match(r'^[1-9]\d{5}(18|19|20|(3\d))\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$',id_card):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "数据错误"
            })
        try:
            user.real_name = real_name
            user.id_card = id_card
            user.save()
        except Exception as e:
            return JsonResponse({
                "errno": "4001",
                "errmsg": "数据库查询错误"
            })
        return JsonResponse({
                "errno": "0",
                "errmsg": "认证信息保存成功"
            })

    def get(self, request):
        # 1. 提取参数
        user = request.user
        # 2. 业务逻辑处理
        if not all([user.real_name, user.id_card]):
            return JsonResponse({
                "errno": "0",
                "errmsg": "用户未实名认证"
            })

        return JsonResponse({
            "errno": "0",
            "errmsg": "ok",
            "data": {
                "real_name": user.real_name,
                "id_card": user.id_card,
            }
        })


class MyHousesView(LoginRequiredJsonMixin,View):
    """
    返回我发布的房源列表
    """
    def get(self, request):
        user = request.user
        house_queryset = House.objects.filter(user_id=user.id)
        house_list = []
        for house in house_queryset:
            house_list.append({
                "address": house.address,
                "area_name": Area.objects.get(id=house.area_id).name,
                "ctime": house.create_time,
                "house_id": house.id,
                "img_url": "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % house.index_image_url,
                "order_count": house.order_count,
                "price": house.price,
                "room_count": house.room_count,
                "title": house.title,
                "user_avatar": "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % user.avatar,
            })
        return JsonResponse({
            "data": {
                "houses": house_list,
            },
            "errno": "0",
            "errmsg": "ok",
        })
