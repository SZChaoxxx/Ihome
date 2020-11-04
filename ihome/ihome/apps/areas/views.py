from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from ihome.ihome.apps.homes.models import Area
from django.core.cache import cache


# Create your views here.


class AreasView(View):
    """提供地区数据"""

    def get(self, request):
        """ 1.查询地区数据
            2.序列化数据
            3.响应数据
        """
        try:
            # 缓存回填
            Data = cache.get("Data")
            if Data:
                return JsonResponse(
                    {
                        'errno': 0,
                        'errmsg': "'获取成功'缓存找到数据",
                        'Data': Data
                    }, status=0
                )
            # .查询数据
            DataList = Area.objects.filter(parent=None)

            # 提取数据
            Data = []
            for data in DataList:
                Data.append: ({
                    'aid': data.aid,
                    'aname': data.aname,
                })
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '省份数据错误'
            })
            # 软一致
        cache.set("Data", Data, 4500)

        # 构建响应
        return JsonResponse({
            'errrno': 0,
            'errmsg': '获取成功',
            'Data': Data
        })
