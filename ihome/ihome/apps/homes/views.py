from django.views import View
from django.db import DatabaseError
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
import json, re
from .models import House, Area, Facility


class AreaView(View):
    """
    提供地区数据
    """

    def get(self, request):
        # 1.查询地区数据
        # ========(1)、通读策略之"先读缓存，读到则直接构建响应"========
        data = cache.get('data')  # 如果缓存数据存在返回列表，否则返回None
        if data:
            return JsonResponse({
                "errno": 0,
                "errmsg": "ok",
                "data": data
            })

        # ========(2)、通读策略之"读mysql"========
        # 2.序列化数据
        try:
            # 1.查询数据
            area_model_list = Area.objects.all()
            # 2.整理省级数据
            data = []
            for area_model in area_model_list:
                data.append({
                    "aid": area_model.id,
                    "aname": area_model.name
                })
        except DatabaseError:
            return JsonResponse({
                "errno": 4001,
                "errmsg": "数据库查询错误"
            })
        # ========(3)、通读策略之"缓存回填"========
        # 3.响应数据
        # 缓存时间设置为3600秒，目的：一定程度上可以实现"缓存弱一致"
        cache.set('data', data, 3600)
        # 3.返回整理好后的数据
        return JsonResponse({
            "errmsg": "获取成功",
            "errno": "0",
            "data": data
        })


class PublishHouse(View):
    """
    发布新房源
    """

    def post(self, request):
        """
        处理房源发布请求
        """

        # 1获取参数
        user = request.user
        data = json.loads(request.body.decode())
        title = data.get('title')
        price = data.get('price')
        area_id = data.get('area_id')
        address = data.get('address')
        room_count = data.get('room_count')
        acreage = data.get('acreage')
        unit = data.get('unit')
        capacity = data.get('capacity')
        beds = data.get('beds')
        deposit = data.get('deposit')
        min_days = data.get('min_days')
        max_days = data.get('max_days')
        facility = data.get('facility')

        # 校验参数
        # 必要性校验
        if not all(
                [title, price, area_id, address,
                 room_count, acreage, unit, capacity,
                 beds, deposit, min_days, max_days,
                 facility]):
            return JsonResponse({
                "errno": "4103",
                "errmsg": "参数错误: 缺少必要参数",
            })
        # 约束性校验
        # 标题
        if not re.match(r'^.*$', title):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "标题数据错误",
            })
        if not re.match(r'^([1-9]\d*(\.\d{1,2})?$)|(^0\.\d{1,2})?$', price):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "价格数据错误",
            })
        if not re.match(r'^[1-9]{1,}$', area_id):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "区域号数据错误",
            })
        if not re.match(r'^.*$', address):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "地址数据错误",
            })
        if not re.match(r'^\d{1,}$', room_count):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "房间数数据错误"
            })
        if not re.match(r'^(\d+.\d{1,4}|\d+)$', acreage):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "面积数据错误",
            })
        if not re.match(r'^.*$', unit):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "单元数据错误",
            })
        if not re.match(r'^\d{1,20}$', capacity):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "容量数据错误",
            })
        if not re.match(r'^.*$', beds):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "床数据错误",
            })
        if not re.match(r'^([1-9]\d*(\.\d{1,2})?$)|(^0\.\d{1,2})?$', deposit):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "定金数据错误",
            })
        if not re.match(r'^\d{1,}$', min_days):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "最小天数数据错误",
            })
        if not re.match(r'^\d{1,}$', max_days):
            return JsonResponse({
                "errno": "4004",
                "errmsg": "最大大天数数据错误",
            })
        # 设备业务校验
        facility_ids = []
        for i in Facility.objects.all():
            facility_ids.append(str(i.id))
        for item in facility:
            if item not in facility_ids:
                return JsonResponse({
                    "errno": "4004",
                    "errmsg": "设备数据错误",
                })

        # 3、业务数据处理 —— 新建House模型类对象保存数据库
        try:
            house = House(
                user=user,
                area_id=area_id,
                # area = Area.objects.get(pk=area_id),
                title=title,
                price=price,
                address=address,
                room_count=room_count,
                acreage=acreage,
                unit=unit,
                capacity=capacity,
                beds=beds,
                deposit=deposit,
                min_days=min_days,
                max_days=max_days,
            )
            house.save()
            # 房屋对象新建完成之后，去新建关联的设备（多）
            house.facility.set(facility)

        except Exception as e:
            return JsonResponse({
                "errno": "4500",
                "errmsg": "内部错误"
            })
        return JsonResponse({
            "errno": "0",
            "errmsg": "发布成功",
            "data": {
                "house_id": house.id
            }
        })
