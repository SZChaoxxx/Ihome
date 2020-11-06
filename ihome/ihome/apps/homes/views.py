from django.views import View
from django.db import DatabaseError
from django.core.cache import cache
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import json, re
from random import sample
from .models import House, Area, Facility, HouseImage
from users.models import User
from qiniu import Auth, put_data, etag
from datetime import datetime


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


class HouseHandleView(View):
    """
    房屋处理视图
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

        except DatabaseError as e:
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

    def get(self, request):
        """
        搜索
        """
        # 1.获取参数
        aid = request.GET.get('aid')  # 区域id
        sd = request.GET.get('sd')  # 开始日期
        ed = request.GET.get('ed')  # 结束时间
        sk = request.GET.get('sk')  # 排序方式
        # booking 入住最多， new： 最新上线，price-inc：价格低到高， price-des：价格高到低
        p = request.GET.get('p')  # 页数，不传为1
        # 2.校验参数 (不需要)
        # 3.业务逻辑处理
        try:
            data = House.objects.all()
        except DatabaseError:
            return JsonResponse({
                "errno": "4001",
                "errmsg": "数据库查询错误"
            })

        # 地区数据过滤
        if aid != "" or (aid is not None):
            data = data.filter(area_id=aid)

        # 入住时间过滤
        if (sd != "" or (sd is not None)) and (ed != "" or (ed is not None)):
            FMT = '%Y-%M-%d'
            tdelta = (datetime.strptime(ed, FMT) - datetime.strptime(sd, FMT)).days
            data = data.filter(min_days__lte=tdelta)
            data = data.filter(Q(max_days__gte=tdelta)|Q(max_days=0))

        # 根据sk排序
        if sk == "booking":
            data = data.order_by('order_count')
        elif sk == "new":
            data = data.order_by("-create_time")
        elif sk == "price-inc":
            data = data.order_by("price")
        elif sk == "price-des":
            data = data.order_by("-price")

        # 根据页数过滤显示内容
        # 参数校验
        try:
            p = int(p)
        except TypeError:
            return JsonResponse({
                "errno": "4004",
                "errmsg": "页数数据格式错误"
            })

        paginator = Paginator(data, settings.MAX_PAGE)
        # 获取每页数据
        try:
            page_data = paginator.page(p)
        except EmptyPage:
            # 如果page_num不正确，默认返回400
            return JsonResponse({
                "errno": "4004",
                "errmsg": "超出最大页数限制"
            })

        # 获取列表页总页数
        total_page = paginator.num_pages
        # 定义列表
        data_list = []
        # 整理格式
        for datum in page_data:
            data_list.append({
                "address": datum.address,
                "area_name": Area.objects.get(id=datum.area_id).name,
                "ctime": datum.create_time,
                "house_id": datum.id,
                "img_url": "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % datum.index_image_url,
                "order_count": datum.order_count,
                "price": datum.price,
                "room_count": datum.room_count,
                "title": datum.title,
                "user_avatar": "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % User.objects.get(id=datum.user_id).avatar,
            })

        return JsonResponse({
            "data": {
                "houses": data_list,
                "total_page": total_page,
            },
            "errno": "0",
            "errmsg": "请求成功"
        })


class UploadHouseImage(View):
    def post(self, request, house_id):
        file_obj = request.FILES.get('house_image')
        if not file_obj:
            return JsonResponse({
                "errno": "4002",
                "errmsg": "获取图片失败"
            })
        # 构建鉴权对象
        q = Auth(settings.ACCESS_KEY, settings.SECRET_KEY)
        key = None
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(settings.BUCKET_NAME, key, 3600)
        print(type(file_obj))
        ret, info = put_data(token, key, file_obj)
        # 房屋图片传入数据库
        try:
            house = House.objects.get(id=house_id)
            if house.index_image_url is None or house.facility.all() == "":
                house.index_image_url = ret['key']
            houseImage = HouseImage(house_id=house.id, url=ret['key'])
            houseImage.save()
            house.save()
        except Exception as e:
            return JsonResponse({
                "errno": "4001",
                "errmsg": "数据库查询错误"
            })
        return JsonResponse({
            "data":
                {
                    "url": "http://qj9kppiiy.hn-bkt.clouddn.com/" + ret['key'],
                },
            "errno": "0",
            "errmsg": "图片上传成功"
        })


class HomePageRecommendView(View):
    def get(self, request):
        try:
            house_querySet = House.objects.all()
        except DatabaseError:
            return JsonResponse({
                "errno": "4001",
                "errmsg": "数据库查询错误"
            })
        house_list = []
        for house in house_querySet:
             house_list.append({
                 "house_id": house.id,
                 "img_url": "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % house.index_image_url,
                 "title": house.title
             })
        if len(house_list) >= 5:
            house_list = sample(house_list, 5)
        return JsonResponse({
            "data": house_list,
            "errmsg": "ok",
            "errno": "0"
        })


class HouseDetailView(View):
    def get(self, request, house_id):
        # 1.获取参数
        user_id = -1
        user = request.user
        # 判断用户是否登陆
        if user:
           user_id = user.id
        try:
            house = House.objects.get(id=house_id)
        except DatabaseError:
            return JsonResponse({
                "errno": "4001",
                "errmsg": "数据库查询失败"
            })
        # 整理数据
        facility_list = []
        for item in house.facility.all():
            facility_list.append(item.id)
        house_image_list = []
        for item in HouseImage.objects.filter(house_id=house_id):
            house_image_list.append("http://qj9kppiiy.hn-bkt.clouddn.com/%s" % item.url)
        data = {
                "acreage": house.acreage,
                "address": house.address,
                "beds": house.beds,
                "capacity": house.capacity,
                "comments": {},  # TODO
                "deposit": house.deposit,
                "facilities": facility_list,
                "hid": house.id,
                "img_urls": house_image_list,
                "max_days": house.max_days,
                "min_days": house.min_days,
                "price": house.price,
                "room_count": house.room_count,
                "title": house.title,
                "unit": house.unit,
                "user_avatar": "http://qj9kppiiy.hn-bkt.clouddn.com/%s" % User.objects.get(id=house.user_id).avatar,
                "user_name": User.objects.get(id=house.user_id).username,
            }

        return JsonResponse({
            "data": {
                "house": data,
                "user_id": user_id,
                },
            "errno": "0",
            "errmsg": "ok"
        })
