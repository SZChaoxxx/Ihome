from django.shortcuts import render
from django_redis import get_redis_connection
from django.views import View
import json, time
from django.http import JsonResponse
from django.shortcuts import render
from homes.models import House
import datetime
from .models import Order
from ihome.utils.views import LoginRequiredJsonMixin
# Create your views here.
from django.db.models import Q


class AddorderView(LoginRequiredJsonMixin,View):

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

        house = House.objects.get(pk=house_id)
        # 判断下单用户是否为房主
        # 下订单的用户编号　不能等于　房屋主人的用户编号　
        if user.id == house.user_id:
            return JsonResponse({'errno': '4105', 'errmsg': '用户身份错误'})
        if not all([house_id, start_date, end_date]):
            return JsonResponse({'errno': '4103', 'errmsg': '参数错误'})

        # 业务处理
        # 判断用户是否登陆
        #
            # 登陆查询５号库
        # conn = get_redis_connection('order_information')
        # redis_orders = conn.hgetall('orders_%s' % user.id)
        order = Order.objects.filter(Q(house_id=house_id)&Q(begin_date=start_date))


        # 判断用户所选房屋是否被预定
        if  order:
            return JsonResponse({'errno': '4003', 'errmsg': '数据已存在'})

        else:

            # 写入数据库
            days = (datetime.datetime.strptime(end_date, '%Y-%m-%d') - datetime.datetime.strptime(start_date, '%Y-%m-%d')).days

            house_price = int(house.price)/(int(house.acreage)/int(house.capacity))
            order = Order(
                user_id=user.id,
                house_id=house_id,
                begin_date=start_date,
                end_date=end_date,
                house_price = house_price,
                days = days,
                amount = house_price*int(days),

            )

            order.save()

            return JsonResponse({
                "data": {
                    "order_id": order.id
                },
                "errno": '0',
                "errmsg": "下单成功"
                })



    def get(self, request):
        # 提取参数
        user = request.user

        role = request.GET.get('role')

        # 校验参数
        if not role:
            return JsonResponse({'errno': '4103', 'errmsg': '参数错误'})
        # 定义一个空字典用

        # 判断用户是否登陆
        # if user.is_authenticated:
        # 构建响应列表
        if role == 'custom':
            orders = []

        # ord_ids = Order.objects.all()
        # 便利并向列表中添加数据
        # for ord_id in ord_ids:
            ord = Order.objects.filter(user_id=user.id)


            for i in ord:
                house = House.objects.get(id=i.house_id)
                orders.append({
                    'amount': i.amount,
                    'comment': i.comment,
                    'ctime': i.create_time.strftime("%Y-%m-%d"),
                    'days': i.days,
                    "end_date": i.end_date,

                    "img_url":  "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % house.index_image_url,
                    "order_id": i.id,
                    "start_date": i.begin_date,
                    "status": Order.ORDER_STATUS_ENUM.get(i.status),
                    "title": house.title
                })
            return JsonResponse({
                "data":{ "orders": orders},
                "errmsg": 'ok',
                "errno": '0'
            })
        if role == 'landlord':
            orders = []

        # ord_ids = Order.objects.all()
        # 便利并向列表中添加数据
        # for ord_id in ord_ids:
            house = House.objects.filter(user_id=user.id)
            for k in house:
                ord=Order.objects.filter(house_id=k.id)
                for i in ord:
                    house = House.objects.get(id=i.house_id)
                    orders.append({
                        'amount': i.amount,
                        'comment': i.comment,
                        'ctime': i.create_time.strftime("%Y-%m-%d"),
                        'days': i.days,
                        "end_date": i.end_date,

                        "img_url":  "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % house.index_image_url,
                        "order_id": i.id,
                        "start_date": i.begin_date,
                        "status": Order.ORDER_STATUS_ENUM.get(i.status),
                        "title": house.title
                        })
            return JsonResponse({
                "data":{ "orders": orders},
                "errmsg": 'ok',
                "errno": '0'
            })


#todo 带验证
class OrderStatus(LoginRequiredJsonMixin,View):
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
                order.status = 3  # 状态为１(待支付)　表示房东已经接单
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
class OrderComment(LoginRequiredJsonMixin,View):
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


