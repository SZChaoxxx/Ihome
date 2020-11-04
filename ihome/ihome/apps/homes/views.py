from django.views import View
from homes.models import Area
from django.db import DatabaseError
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

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
