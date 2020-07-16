from django.contrib import admin

from labapp.user import *
# 正则
import re
# 导入jwt
from labapp.serializer import *

# 导入rest_framework
from rest_framework.views import APIView

# 导包
from django.db.models import Q, F

# 导入response模块
from rest_framework.response import Response

# 导入序列化
from labapp.labser import *

# 导入django自带验证模块
from django.contrib.auth import authenticate
# 邮箱使用包
from django.shortcuts import loader


# 用户列表
class UserList(APIView):
    # 获取用户列表
    def get(self, request):
        resp = {}
        # 将数据库中所有会员等级取出
        vip = VIP.objects.all()
        # 序列化会员等级信息
        vipser = VIPSer(vip, many=True).data

        # 当前页面
        page = int(request.GET.get("page", 1))
        # 定义一页多少条数据
        size = int(request.GET.get("size", 10))
        # 定义从哪开始切片
        data_start = (page - 1) * size
        # 定义切到哪
        data_end = page * size

        search = request.GET.get("search", None)
        if search:
            user = User.objects.filter(Q(is_delete=0), Q(username__contains=search) | Q(phone__contains=search) |
                                       Q(email__contains=search) | Q(sign__contains=search)).order_by("-date_joined")[
                   data_start:data_end]
            # 查询一共有多少条数据
            count = user.count()

            # 序列化用户信息
            userser = UserSer(user, many=True).data
            resp["code"] = 200
            resp["count"] = count
            resp["userlist"] = userser
            resp["viplist"] = vipser
            return Response(resp)
        else:

            # 将数据库中所有用户取出
            user = User.objects.filter(is_delete=0).order_by("-date_joined")[data_start:data_end]
            # 查询一共有多少条数据
            count = User.objects.count()

            # 序列化用户信息
            userser = UserSer(user, many=True).data

        resp["code"] = 200
        resp["count"] = count
        resp["userlist"] = userser
        resp["viplist"] = vipser

        return Response(resp)

    # 添加用户信息
    def post(self, request):
        # 获取参数
        data = request.data
        # 正则匹配用户名、密码、邮箱、手机号是否符合规范
        username = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", data["username"])
        password = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", data["password"])
        email = re.findall("^\w+((.\w+)|(-\w+))@[A-Za-z0-9]+((.|-)[A-Za-z0-9]+).[A-Za-z0-9]+$", data["email"])
        phone = re.findall("^(13[0-9]{9})|(15[0-9][0-9]{8})|(18[0-9][0-9]{8})$", data["phone"])
        if not [username, password, email, phone]:
            return Response({"code": 405, "message": "信息错误"})
        # 排重
        user = User.objects.filter(username=data["username"]).first()
        if user:
            return Response({"code": 405, "message": "该用户已存在"})
        # 将数据写入数据库中
        User.objects.create_user(username=data["username"], password=data["password"], email=data["email"],
                                 phone=data["phone"], occupation=data["occupation"], school=data["school"],
                                 vid=int(data["vid"]), sign=data["sign"], balance=data["balance"], bean=data["bean"],
                                 experience=data["experience"], code=data["code"]
                                 )
        return Response({"code": 200, "message": "添加成功"})

    # 修改用户信息
    def put(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        email = request.data.get("email", None)
        phone = request.data.get("phone", None)
        occupation = request.data.get("occupation", None)
        school = request.data.get("school", None)
        vid = int(request.data.get("vid", None))
        balance = int(request.data.get("balance", None))
        bean = int(request.data.get("bean", None))
        experience = int(request.data.get("experience", None))
        code = request.data.get("code", None)
        sign = request.data.get("sign", None)
        # 正则匹配用户名、密码、邮箱、手机号是否符合规范
        user_name = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", username)
        pass_word = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", username)
        em_ail = re.findall("^\w+((.\w+)|(-\w+))@[A-Za-z0-9]+((.|-)[A-Za-z0-9]+).[A-Za-z0-9]+$", email)
        ph_one = re.findall("^(13[0-9]{9})|(15[0-9][0-9]{8})|(18[0-9][0-9]{8})$", phone)
        if not [user_name, pass_word, em_ail, ph_one]:
            return Response({"code": 405, "message": "数据错误"})
        user = User.objects.filter(username=username).first()
        if user:
            # 将数据写入数据库中
            user.username = username
            user.set_password(password)
            user.email = email
            user.phone = phone
            user.occupation = occupation
            user.school = school
            user.vid = vid
            user.balance = balance
            user.bean = bean
            user.experience = experience
            user.code = code
            user.sign = sign
            user.save()
            return Response({"code": 200, "message": "修改成功"})
        else:

            return Response({"code": 405, "message": "数据错误"})

    def delete(self, request):
        resp = {}
        uid = request.GET.get("uid", None)
        id_list = request.GET.get("id_list", None)
        # 单个删除
        if uid:
            user = User.objects.get(id=int(uid))
            user.is_delete = 1
            resp["code"] = 200
            resp["message"] = "删除成功"
            user.save()
        # 判断获取的id字符串是否存在
        if id_list:
            # 将获取到的id字符串进行切片
            id_list = id_list.split(",")
            # 循环遍历
            for i in id_list:
                # 循环查询然后删除
                user = User.objects.get(id=int(i))
                user.is_delete = 1
                user.save()
            resp["code"] = 200
            resp["message"] = "批量删除成功"
        return Response(resp)


# 管理员邮箱登录
class EmailLogin(APIView):
    def post(self, request):
        resp = {}
        # 获取数据
        # username = request.data.get("username",None)
        email = request.data.get("email", None)
        password = request.data.get("password", None)
        code = request.data.get("code", None)
        print(code)
        if [email, password]:
            try:
                # 判断邮箱及密码是否正确
                user = authenticate(email=email, password=password)
                # 查询该邮箱是否在一分钟内获取过验证码、和验证码是否正确
                token = r.get(email)
                print(token)
                if token == code:
                    # 生成登录token
                    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                    payload = jwt_payload_handler(user)
                    token = jwt_encode_handler(payload)

                    resp["code"] = 200
                    resp["token"] = token
                    resp["uid"] = user.id
                    resp["username"] = user.username
                    resp["message"] = "登陆成功"

            except Exception as e:
                # 用户名或密码错误
                resp["code"] = 405
                resp["message"] = "邮箱、或密码错误"
                return Response(resp)
        # 用户名或密码错误
        resp["code"] = 405
        resp["message"] = "验证码错误"
        return Response(resp)


# 管理员登录
class AdminLogin(APIView):
    def post(self, request):
        resp = {}
        # 获取参数
        # username = request.data.get()
        # print(username)
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        # 判断是否为空数据
        if [username, password]:
            user_name = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", username)
            pass_word = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", password)
            if user_name and pass_word:
                try:
                    user = authenticate(username=username, password=password)

                    if user:
                        # 生成登录token
                        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                        payload = jwt_payload_handler(user)
                        token = jwt_encode_handler(payload)

                        resp["code"] = 200
                        resp["token"] = token
                        resp["uid"] = user.id
                        resp["username"] = user.username
                        resp["message"] = "登陆成功"
                        return Response(resp)
                except Exception as e:
                    resp["code"] = 405
                    resp["message"] = "帐号或密码错误"
                    return Response(resp)
            else:
                resp["code"] = 405
                resp["message"] = "用户名或密码格式不正确"
                return Response(resp)
        resp["code"] = 405
        resp["message"] = "帐号或密码错误"
        return Response(resp)


# 管理员注册
class AdminRegister(APIView):
    def post(self, request):
        resp = {}
        # 获取参数
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        email = request.data.get("email", None)
        phone = request.data.get("phone", None)
        # 判断是否为空数据
        if username and password and email and phone:
            user_name = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", username)
            pass_word = re.findall("^([a-zA-Z])[a-zA-Z0-9]{5,16}$", password)
            if user_name and pass_word:
                # 将数据写入数据库中
                user = User.objects.create_user(username=username, password=password, email=email, phone=phone)
                resp["code"] = 200
                resp["uid"] = user.id
                resp["username"] = user.username
                return Response(resp)
            else:
                resp["code"] = 405
                resp["message"] = "用户名或密码格式不正确"
                return Response(resp)
        else:
            resp["code"] = 405
            resp["message"] = "数据不全，请重新填写"
            return Response(resp)
