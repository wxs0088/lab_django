from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.contrib.auth.backends import ModelBackend  # 验证基类
from rest_framework_jwt.settings import api_settings
from rest_framework.views import APIView
from django.views import View
from rest_framework.response import Response
from django.http import HttpResponse
from .models import *
from django.contrib.auth import authenticate
from .serializer import UserSerializer
from rest_framework_jwt.utils import jwt_decode_handler
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.permissions import BasePermission
from django.contrib.auth import authenticate
from .labser import *
import hashlib
import random
from django.core.mail import send_mail  # 用来发送用
from django.http import JsonResponse, HttpRequest
from lab_django.settings import EMAIL_HOST_USER
from lab_django.settings import DEFAULT_FROM_EMAIL

# 沙箱支付
from alipay import AliPay
import datetime
# 悲观锁
from django.db import transaction

# 阿里云短信
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

# 三方登陆
import redis
import json
import requests
import time
import hmac
import base64
from hashlib import sha256
import urllib

# 定义ip地址和端口
host = "120.26.175.79"
port = 6379

# 链接对象
r = redis.Redis(host=host, port=port, decode_responses=True)
# r2: 最近访客库
r2 = redis.Redis(host=host, port=port, decode_responses=True,db=2)


# 访客添加
class Visitor(APIView):
    def post(self,request):
        uid = request.data.get("uid", None)  # 被访问人的id
        token = request.data.get("token", None)  # 访问者的
        user_id = jwt_decode_handler(token).get('user_id')
        if str(uid) == str(user_id):
            return Response()
        times = str(time.strftime('%Y-%m-%d %H:%M:%S'))
        r2.hset(uid,user_id,times)
        return Response({'code:200'})

    def get(self,request):
        vid = request.GET.get("uid", None)  # 被访问人的id
        ret = r2.hgetall(vid)
        a = sorted(ret.items(), key=lambda x: str(x[1]), reverse=True)
        b = map(lambda x: {'id':x[0], 'time': x[1]}, a)
        user_data = []
        for i in b:
            id = i['id']
            user = User.objects.filter(id=int(id)).first()
            i['username'] = user.username
            i['img'] = user.photo
            i['exp'] = user.experience
            user_data.append(i)
        res = {}
        res['msg'] = '刷新成功'
        res['code'] = 200
        res['data'] = user_data
        return Response(res)



# 沙箱支付---读取私钥及公钥
app_private_key_string = open("pay/private.txt").read()
alipay_public_key_string = open("pay/public.txt").read()


# 用户详情
class GetUser(APIView):
    def get(self,request):
        res = {}
        uid = request.GET.get('uid')
        if uid:
            user = User.objects.filter(id=uid).first()
            res['img'] = user.photo
            return Response(res)
        else:
            res['code'] = 405
            return Response(res)

# 支付回调
class Get_Alipy(APIView):
    def get(self, request):
        # 购买课程id
        cid = request.GET.get('cid',None)
        # 订单号
        order = request.GET.get("order", None)
        # 获取token
        jwt_token = request.GET.get("token", None)
        user_json = jwt_decode_handler(jwt_token)
        # 获取token中的uid
        user_id = user_json.get("user_id")

        # 判断是否登录
        if not user_id:
            return Response({"code": 405, "message": "用户信息已失效，请重新登录"})
            # 查询订单是否存在，或订单是否已经支付过
        order_id = Order.objects.filter(order=order, uid=int(user_id)).first()
        if not order_id or order_id.is_succeed == 1:
            return Response({"code": 405, "message": "订单不存在或已付款，请刷新后查看"})

        alipay = AliPay(
            appid="2016102400753303",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        # 此为支付宝交易查询接口
        response = alipay.api_alipay_trade_query(order)

        if response.get("code") != "10000" or response.get("trade_status") != "TRADE_SUCCESS":
            return Response({"code": 405, "message": "开通失败"})
        order_id = Order.objects.filter(order=order, uid=int(user_id)).first()
        # 将支付状态修改为已支付

        order_id.is_succeed = 1
        order_id.save()
        if not cid:
            # 查询开通的会员级别
            vip = VIP.objects.filter(grade=order_id.behoof).first()

            # 修改对应用户的vip级别
            user = User.objects.get(id=int(user_id))
            user.vid = vip.id

            user.vip_start_time = datetime.datetime.now()
            # 提交所有修改
            user.save()
            return Response({"code": 200, "message": "恭喜您，会员开通成功"})
        else:
            Buy.objects.create(uid=int(user_id),cid=int(cid))
            return Response({"code": 200, "message": "恭喜您，购买成功"})


# 生成订单
class Create_Order(APIView):
    def get(self, request):
        resp = {}
        # 获取token
        jwt_token = request.GET.get("token", None)
        if not jwt_token:
            return Response({"code":405,"message":"用户未登录"})
        user_json = jwt_decode_handler(jwt_token)
        # 获取token中的uid
        user_id = user_json.get("user_id")
        # 判断是否登录
        if user_id:
            order = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(10, 99)))
            r.set("order" + str(user_id), order)
            resp["code"] = 200
            resp["order"] = order
            return Response(resp)
        resp["code"] = 405
        resp["message"] = "用户信息获取失败，请重新登录"
        return Response(resp)


# 沙箱支付
class Alipay(APIView):
    def get(self, request):
        # 获取订单号
        order = request.GET.get("order", None)
        # 获取支付价格
        price = request.GET.get("price", None)
        # 获取token
        jwt_token = request.GET.get("token", None)
        user_json = jwt_decode_handler(jwt_token)
        # 获取token中的uid
        user_id = user_json.get("user_id")
        # 判断是否登录
        if not user_id:
            return Response({"code": 405, "message": "用户信息已失效，请重新登录"})

        alipay = AliPay(
            appid="2016102400753303",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_str = alipay.api_alipay_trade_page_pay(
            subject="实验楼消费",
            notify_url=None,
            out_trade_no=order,  # 订单号
            total_amount=price,  # 订单价格
            return_url="http://127.0.0.1:8080/vip/"
        )

        request_url = 'https://openapi.alipaydev.com/gateway.do?' + order_str

        return Response({
            "code": 200,
            "msg": "请求成功，跳转支付页面",
            "data": request_url
        })

    # 订单入库
    def post(self, request):
        resp = {}
        jwt_token = request.data.get("token", None)  # 用户信息
        order = request.data.get("order", None)  # 订单号

        price = request.data.get("price", None)  # 价格
        record = request.data.get("record", None)  # 消费记录
        user_json = jwt_decode_handler(jwt_token)
        user_id = user_json.get("user_id")

        # 判断用户是否登录及本地订单与传过来的订单是否一致
        if not user_id or order != r.get("order" + str(user_id)):
            resp["code"] = 405
            resp["message"] = "请求失败，请刷新页面重试"
            return Response(resp)
        order_id = Order.objects.filter(order=order).first()
        if order_id:
            resp["code"] = 405
            resp["message"] = "该订单已存在，请确认后再次提交"
            return Response(resp)
        # 将订单入库
        price = int(price) * 100        # 将价格单位改为分
        Order.objects.create(uid=user_id, order=order, price=price, behoof=record)
        resp["code"] = 200
        resp["message"] = "订单已生成，请继续完成支付"
        return Response(resp)


# 获取所有vip
class Vip_List(APIView):
    def get(self, request):
        resp = {}
        vip_list = VIP.objects.all()
        vipser = VIPSer(vip_list, many=True).data
        resp["code"] = 200
        resp["vip_list"] = vipser
        return Response(resp)


# 构造钉钉回调方法
def ding_back(request):
    # 获取code
    code = request.GET.get("code")

    t = time.time()
    # 时间戳
    timestamp = str((int(round(t * 1000))))
    appSecret = 'Fcah25vIw-koApCVN0mGonFwT2nSze14cEe6Fre8i269LqMNvrAdku4HRI2Mu9VK'
    # 构造签名
    signature = base64.b64encode(
        hmac.new(appSecret.encode('utf-8'), timestamp.encode('utf-8'), digestmod=sha256).digest())
    # 请求接口，换取钉钉用户名
    payload = {'tmp_auth_code': code}
    headers = {'Content-Type': 'application/json'}
    res = requests.post('https://oapi.dingtalk.com/sns/getuserinfo_bycode?signature=' + urllib.parse.quote(
        signature.decode("utf-8")) + "&timestamp=" + timestamp + "&accessKey=dingoajf8cqgyemqarekhr",
                        data=json.dumps(payload), headers=headers)

    res_dict = json.loads(res.text)
    unid = res_dict['user_info']['unionid']
    usern = '游客' + unid[0:8]
    user = User.objects.filter(username=str(usern)).first()

    if user:
        # 生成jwt
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        username = user.username
        jwt = token
        img = user.photo
        uid = user.id

        return HttpResponseRedirect('http://localhost:8080/?jwt=%s&username=%s&img=%s&uid=%s' % (jwt,username,img,uid))

    else:
        user = User(username=str(usern), password='')
        user.save()
        u = User.objects.filter(username=str(usern)).first()
        # 生成jwt
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(u)
        token = jwt_encode_handler(payload)
        jwt = token
        uid = u.id

        return HttpResponseRedirect('http://localhost:8080/tripalogin/?jwt=%s&type=%s' % (jwt,1))


# 三方登陆(微博)
def wb_back(request):
    # 获取code
    code = request.GET.get('code')
    # 定义微博认证地址
    access_token_url = "https://api.weibo.com/oauth2/access_token"
    # 参数
    res = requests.post(
        access_token_url,
        data={
            "client_id": '156528899',
            "client_secret": "ed2ea49411d3ee0dbd4500f6495e36dc",
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://127.0.0.1:8000/weibo/"
        }
    )
    # 转化类型
    usern = '游客' + json.loads(res.text)['uid']

    user = User.objects.filter(username=str(usern)).first()

    if user:
        # 生成jwt
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        username = user.username
        jwt = token
        img = user.photo
        uid = user.id

        return HttpResponseRedirect('http://localhost:8080/?jwt=%s&username=%s&img=%s&uid=%s' % (jwt,username,img,uid))
    else:
        user = User(username=str(usern), password='')
        user.save()
        u = User.objects.filter(username=str(usern)).first()
        # 生成jwt
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(u)
        token = jwt_encode_handler(payload)
        jwt = token
        uid = u.id

        return HttpResponseRedirect('http://localhost:8080/tripalogin/?jwt=%s&type=%s' % (jwt,2))



# 三方登陆手机号验证

class Verif(APIView):
    def post(self, request):
        jwt = request.data.get('jwt')
        phone = request.data.get('phone')
        code = request.data.get('code')
        type = request.data.get('type')
        uid = jwt_decode_handler(jwt).get('user_id')
        user = User.objects.get(id=uid)
        p_user = User.objects.filter(phone=phone).first()

        if user and type == str(1) and p_user:

            p_user.dingding = user.id

            user.phone = phone
            user.save()
            p_user.save()

            # 再次查询
            use = User.objects.filter(id=uid).first()

            res = {}
            res['code'] = 200
            res['msg'] = '验证通过'
            res['img'] = use.photo
            res['uid'] = use.id
            res['username'] = use.username
            return Response(res)

        if user and type == str(2) and p_user:
            p_user.weibo = user.id
            user.phone = phone
            user.save()
            p_user.save()
            
            # 再次查询
            use = User.objects.filter(id=uid).first()

            res = {}
            res['code'] = 200
            res['msg'] = '验证通过'
            res['img'] = use.photo
            res['uid'] = use.id
            res['username'] = use.username
            return Response(res)


        # elif user:

        #     user.phone = phone
        #     user.save()
            
        #     # 再次查询
        #     use = User.objects.filter(id=uid).first()

        #     res = {}
        #     res['code'] = 200
        #     res['msg'] = '验证通过'
        #     res['img'] = use.photo
        #     res['uid'] = use.id
        #     res['username'] = use.username
        #     return Response(res)
        

        else:

            res = {}
            res['code'] = 405
            res['msg'] = '验证码错误'
            return Response(res)
        


# 邮箱
def get_pass(str_):
    s = hashlib.sha1()
    s.update(str_.encode())
    return s.hexdigest()


# 生成随机验证码
def get_random_str():
    # 验证码是由 字母a~z  A~Z 数字 0~9 组成
    # 在 ascii 码中 小写a的起点是97 大写A起点是65
    a_ = [chr(var) for var in range(97, 123)]  # 小写a的列表推导式
    A_ = [chr(var) for var in range(65, 91)]  # 大写A的列表推导式
    num_ = [str(var) for var in range(0, 9)]  # 数字的
    # 使用sample 在列表中随机生成6个任意字母数字
    return ''.join(random.sample(a_ + A_ + num_, 6))


class EmailVerify(View):
    # 邮件验证码请求的接口
    '''
    1.先检查 对应邮件是否在redis里已经存在了验证码
    2.发现没有存在，那么需要生成6位随机字符
    3. 存储入到redis里，并设置60s的过期时间
         key:value:time  ==  email:6位随机字符:60s
    '''

    def post(self, request):
        email = request.POST.get('email')  # 接收到用户发来的邮箱
        print(email)
        token = r.get(email)
        # token = '123456'
        res = {}
        if token:  # 去redis 中查看 是否这个邮箱
            res['code'] = 401
            res['message'] = "请一分钟后再次发送"
            return JsonResponse(res)

        else:
            # 发送给
            token = get_random_str()  # 生成验证码
            print(token)
            subject = '亲！欢迎你来到实验楼哦'
            message = '你的验证码是:%s' % token
            r.set(email, token)  # 存储到redis
            # 设置访问周期为60秒
            r.expire(email, 60)
            send_mail(subject, message, DEFAULT_FROM_EMAIL,
                      [email])  # 把邮件发过去

            res['code'] = 200
            res['message'] = "验证码已发送"
            return JsonResponse(res)


# 阿里云发送验证码
class SendAlysms(APIView):
    def post(self, request):
        phone = request.data.get('phone')  # 接收到用户发来的验证码
        res = {}
        token = r.get(phone)
        # token = '123456'

        if token:  # 去redis 中查看 是否这个手机号
            res['code'] = 401
            res['message'] = "请一分钟后再次发送"
            return JsonResponse(res)


        else:
            token = get_random_str()  # 生成验证码
            AK = "LTAI4G7emXUN3dnGVK2p1duM"
            SK = "ZgekQkkT1cZZ4hCyhSquxOwwnjyfLo"

            # 登录阿里云客户端
            client = AcsClient(AK, SK, 'cn-hangzhou')

            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_method('POST')
            request.set_protocol_type('https')  # https | http
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')

            request.add_query_param('RegionId', "cn-hangzhou")
            # 这个手机号可以从前端获取
            request.add_query_param('PhoneNumbers', str(phone))
            request.add_query_param('SignName', "美多商场")
            request.add_query_param('TemplateCode', "SMS_189015076")
            # 验证码可以随机获取
            request.add_query_param('TemplateParam', str({'code': token}))
            r.set(phone, token)  # 存储到redis
            # 设置访问周期为60秒
            r.expire(phone, 60)

            response = client.do_action(request)
            print(str(response, encoding='utf-8'))
            res['code'] = 200
            res['message'] = "验证码已发送"
            # res['token'] = phone
            return JsonResponse(res)
            # return


# 查询用户是否存在
def check_user(username):
    user = User.objects.filter(username= username).first()
    if user:
        return user
    else:
        return User.objects.get(id= 1)

# 查询用户是否存在视图
class CheckUsername(APIView):
    def post(self, request):
        res = {}
        username = request.data.get('username')
        user = check_user(username)
        if user.id == 1:
            res['code'] = 403
            res['message'] = '该用户不存在'
        else:
            res['code'] = 200
            res['uid'] = user.id
        return Response(res)


# 登录
class Login(APIView):

    def post(self, request):
        # 获取用户名
        username = request.data.get('username', 'null')
        # 获取密码
        password = request.data.get('password', 'null')

        # 验证信息是否正确
        try:
            user = authenticate(username=username, password=password)
        except:
            # 如果错误
            res = {}
            res['code'] = 405
            res['message'] = "信息错误"
            return Response(res)

        # 如果信息正确
        if user:
            res = {}

            # 生成jwt
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            res['code'] = 200
            res['message'] = "登陆成功"
            res['username'] = user.username
            res['uid'] = user.id
            res['jwt'] = token
            res['img'] = user.photo
            return Response(res)


# 注册
class Register(APIView):
    def post(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        phone = request.data.get('phone', None)
        email = request.data.get('email', None)

        code = request.data.get('code', None)  # 验证码

        res = {}

        if username and password and code and (phone or email):

            # 如果传入的是电话
            if phone:
                token = r.get(phone)
                # 在数据库中取出对应的验证码
                if token and token == code:
                    res['code'] = 200
                    res['message'] = "注册成功"
                    User.objects.create_user(
                        username=username, password=password, phone=phone)
                    return Response(res)

                else:
                    res['code'] = 403
                    res['message'] = "验证码错误"
                    return Response(res)






            # 如果传入的是邮箱
            else:

                token = r.get(email)
                # 在数据库中取出对应的验证码
                if token and token == code:
                    res['code'] = 200
                    res['message'] = "注册成功"
                    User.objects.create_user(
                        username=username, password=password, email=email)
                    return Response(res)

                else:
                    res['code'] = 403
                    res['message'] = "验证码错误"
                    return Response(res)

                # # mycode = r.get()
                # User.objects.create_user(username=username, password=password, email= email)
                # res['code'] = 200
                # res['message'] = "注册成功"

        else:

            res['code'] = 405
            res['message'] = "数据不全"

        return Response(res)


def jwt_response_payload_handler(token, user=None, request=None):
    '''
    :param token: jwt生成的token值
    :param user: User对象
    :param request: 请求
    '''
    print('*' * 100)
    return {
        'token': token,
        'user': user.id,
        # 'user': UserSerializer(user, context={'request': request}).data
        # 'userid': user.id,
        # 'userphone':user.phone
    }


class DecodeView(APIView):
    def post(self, request):
        token = request.data.get("token", "")
        # print(token)
        result = jwt_decode_handler(token)
        return Response({"code": 200})


# 为登录增加手机登录和邮箱登录
class UsernameMobileAuthBackend(ModelBackend):
    # 重写验证方式
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = User.objects.get(Q(username=username) | Q(phone=username) | Q(email=username))
        if user is not None and user.check_password(password):
            return user


# 用户信息类
class UserInfo(APIView):
    # 展示信息
    def get(self, request):
        res = {}
        uid = request.GET.get("uid", None)
        client_jwt = request.GET.get("token", None)
        if client_jwt:
            try:
                user_json = jwt_decode_handler(client_jwt)
                user_id = user_json['user_id']
                # 查询数据
                user = User.objects.get(id=int(user_id))
                # 序列化对象
                user_ser = UserSer(user)
                res['code'] = 200
                res['data'] = user_ser.data
                return Response(res)
            except Exception as e:
                res['code'] = 405
                res['message'] = 'token验证错误，请重新登录！'
                return Response(res)
            
        else:
            # 查询数据
                user = User.objects.get(id=int(uid))
                # 序列化对象
                user_ser = UserSer(user)
                res['code'] = 200
                res['data'] = user_ser.data
                return Response(res)

    # 修改信息
    def post(self, request):
        res = {}
        token = request.data.get("token", None)
        username = request.data.get("username", None)
        occupation = request.data.get("occupation", None)
        school = request.data.get("school", None)
        img = request.data.get('img', None)

        uid = jwt_decode_handler(token).get('user_id')

        # 用户名排重
        user_double = User.objects.filter(username=username)

        user = User.objects.get(id=int(uid))

        if username != user.username and user_double:
            res['code'] = 405
            res['message'] = '用户名已存在'

        # 验证是否有修改
        if username:
            user.username = username
        if occupation:
            user.occupation = occupation
        if school:
            user.school = school
        if img:
            user.photo = img

        user.save()
        res['code'] = 200
        res['message'] = '个人信息修改成功'
        return Response(res)


# 上传图片更新并保存用户头像
class UpdateUserImg(APIView):

    def get(self, request):
        photo = request.GET.get("photo")

        uid = request.GET.get("uid")
        # 查询数据
        user = User.objects.get(id=int(uid))
        user.photo = photo

        user.save()

        return Response({'code': 200, 'message': '更新成功'})

class GetVid(APIView):
    def get(self, request):
        uid = request.GET.get('uid', None)
        user = User.objects.filter(id=uid).first()
        if user:
            return Response({'code': 200, 'message': '获取成功', 'vid': user.vid})
        else: 
            return Response({"code": 301, 'message': '用户信息错误,请重新登录'})

