from django.views import View
from verifications.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse,JsonResponse


class ImageCodeView(View):
    """
    图形验证处理视图
    """
    def get(self, request):
        """
        实现图形验证码逻辑
        :param uuid cur, pre
        :return image.jpg
        """
        # 1.获取参数
        cur = request.GET.get('cur')
        pre = request.GET.get('pre')
        # 2. 参数校验 TODO
        # 3. 业务逻辑处理
        # 生成图形验证码
        text, image = captcha.generate_captcha()
        # 保存图形验证码
        # 使用配置的redis数据库别名，创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')
        # 使用连接到redis的对象去操作数据存储到redis
        # 图形验证码必须要有有效期
        redis_conn.setex('img_%s'%cur, 300, text)
        # 响应图形验证码
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    """
    短信验证码
    """
    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return JSON
        """
        # 1. 接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        # 2.校验参数
        if not all([image_code_client, uuid]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要参数'
            },status=400)
        # 3.创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')
        # 从redis数据库获取存入的数据
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 判断该数据是否存在，如果存在意味着用户发送短信间隔不超过60s，直接返回
        if send_flag:
            return JsonResponse({
                'code': 400,
                'errmsg': '发送短信过于频繁'
            },status=400)

        # 4. 提取图形验证码
        image_code_server = redis_conn.get('img_%s'%uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({
                'code': 400,
                'errmsg': '图形验证码失效'
            },status=400)

        # 5. 删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('ims_%s' %uuid)
        except Exception as e:
            logger.error(e)

        # 6. 对比图形验证码
        # bytes 转字符串
        image_code_server = image_code_server.decode()
        # 转小写后比较
        if image_code_client.lower() != image_code_server.lower():
            return JsonResponse({
                'code': 400,
                'errmsg':'输入图形验证码有误'
            },status=400)

        # 7. 生成短信验证码： 生成6位数字验证码
        sms_code = "%06d" % random.randint(0, 999999)
        logger.info(sms_code)

        # 8. 保存短信验证码
        # 短信验证码有效期，单位：300秒
        redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        # 往redis中存入一个数据有效期为60s避免用户频繁发送短信
        redis_conn.setex('send_flag_%s' % mobile, 60, 1)

        # 9. 发送短信验证码
        # 短信模版
        # CCP().send_template_sms(mobile,[sms_code, 5], 1)
        ccp_send_sms_code.delay(mobile, sms_code)
        print('短信验证码: ', sms_code)

        # 10. 响应结果
        return JsonResponse({
            'code': 0,
            'errmsg': '发送短信成功'
        })
