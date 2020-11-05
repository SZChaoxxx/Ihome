from django.shortcuts import render
from django_redis import get_redis_connection
from django.views import View
import json, time
from django.http import JsonResponse
from django.shortcuts import render
from homes.models import House
from .models import Order
# Create your views here.



class AddorderView(View):

# 定义POST方法
    # TODO: 带验证
    def post(self, request):
        user = request.user
        data = json.loads(request.body.decode())
        house_id = data.get('house_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # 提取参数
        # 校验参数
        # 查询房屋表中所有信息
        house = House.objects.all()
        # 判断下单用户是否为房主
        # 下订单的用户编号　不能等于　房屋主人的用户编号　
        if user.id == house.user:
            return JsonResponse({'errno': '4105', 'errmsg': '用户身份错误'})
        if not all([house_id, start_date, end_date]):
            return JsonResponse({'errno': '4103', 'errmsg': '参数错误'})

        # 业务处理
        # 判断用户是否登陆
        if user.is_authenticated:
            # 登陆查询５号库
            conn = get_redis_connection('order_information')
            redis_orders = conn.hgetall('orders_%s' % user.id)
            # 判断用户所选房屋是否重复
            if str(house_id).encode() in redis_orders or str(start_date).encode() in redis_orders:
                return JsonResponse({'errno': '4003', 'errmsg': '数据已存在'})

            else:

                # 写入数据库
                conn.hset('orders_%s' % user.id, house_id, start_date, end_date)

            return JsonResponse({
                "data": {
                    "order_id": 'orders_%s' % user.id
                },
                "errno": '0',
                "errmsg": "下单成功"
            })
        else:
            return JsonResponse({"errno": '4101',
                                 "errmsg": "用户未登录"})


    def get(self, request):
        # 提取参数
        user = request.user
        role = request.GET.get('role')
        # 校验参数
        if not role:
            return JsonResponse({'errno': '4103', 'errmsg': '参数错误'})
        # 定义一个空字典用
        oder_dict = {}
        # 判断用户是否登陆
        if user.is_authenticated:
            # 读取数据库缓存
            conn = get_redis_connection('order_information')
            redis_order = conn.hgetall('orders_%s' % user.id)
            # 便利添加字典
            for k, v, v1 in redis_order.items():
                house_id = int(k)
                start_date = int(v)
                end_date = int(v1)
                # 把便利结果存入字典
                oder_dict[house_id] = {'start_date': start_date, 'end_date': end_date}
        else:
            return JsonResponse({"errno": '4101',
                                 "errmsg": "用户未登录"})
        # 构建响应列表
        orders = []

        ord_ids = oder_dict.keys()
        # 便利并向列表中添加数据
        for ord_id in ord_ids:
            ord = Order.objects.get(pk=ord_id)
            house = House.objects.get(user=ord_id)
            orders.append({
                'amount': ord.amount,
                'comment': ord.comment,
                'ctime': ord.create_time,
                'days': ord.days,
                "end_date": ord.end_date,
                # TODO: 要换成七牛云
                "img_url": "http://oyucyko3w.bkt.clouddn.com/FhgvJiGF9Wfjse8ZhAXb_pYObECQ",
                "order_id": 'orders_%s' % user.id,
                "start_date": ord.begin_date,
                "status": ord.status,
                "title": house.title
            })
        return JsonResponse({
            "data": orders,
            "errmsg": 'ok',
            "errno": '0'
        })
#todo 带验证
class OrderStatus(View):
    def put(self, request, order_id):
        # 1 提取参数
        data = json.loads(request.body.decode())
        action = data.get('action')
        reason = data.get('reason')

        # 2 校验参数
        if not action:
            return JsonResponse({"errno": "4103", "errmsg": "参数错误，缺少必要参数"})

        # 3 业务处理
        order = Order.objects.get(pk=order_id)
        if action == "accept":
            try:
                order.status = 1  # 状态为１(待支付)　表示房东已经接单
                order.save()
            except Exception as e:
                return JsonResponse({"errno": "4001", "errmsg": "数据库写入错误"})
        elif action == "reject":
            if not reason:
                return JsonResponse({"errno": "4103", "errmsg": "参数错误，缺少必要参数"})
            try:
                order.status = 6  # 状态为6(已拒单)  表示房东已经拒单
                order.comment = reason
                order.save()
            except Exception as e:
                return JsonResponse({"errno": "4001", "errmsg": "数据库写入错误"})
        # 4 构建响应
        return JsonResponse({
            "errno": "0",
            "errmsg": "操作成功"
        })
#todo 带验证
class OrderComment(View):
    def put(self, request, order_id):
        data = json.loads(request.body.decode())
        comment = data.get('comment')
        if not comment:
            return JsonResponse({"errno": "4103", "errmsg": "参数错误，缺少必要参数"})
        try:
            order = Order.objects.get(pk=order_id)
            order.comment = comment
            order.status = 4
            order.save()
        except Exception as e:
            return JsonResponse({"errno": "4001", "errmsg": "数据库写入错误"})
        # 4 构建响应
        return JsonResponse({
            "errno": "0",
            "errmsg": "评论成功"
        })


