from django.conf import settings
from django.shortcuts import render, redirect
# 导包
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, QueryDict, Http404
from labapp.models import *
from django.core.serializers import serialize
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views import View
import json
# 导入上传文件夹配置
from lab_django.settings import UPLOAD_ROOT
import os
# 导入公共目录变量
from lab_django.settings import BASE_DIR
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, InvalidPage
# 导包
from django.db.models import Q, F, Avg, Max, Min
from labapp.labser import *
from rest_framework_jwt.utils import jwt_decode_handler
import random
import redis
import datetime
from dateutil.relativedelta import relativedelta
from jieba.analyse import ChineseAnalyzer

# 推荐算法包
from collections import Counter

# 定义ip地址和端口
host = "120.26.175.79"
port = 6379

# 链接对象
r = redis.Redis(host=host, port=port, decode_responses=True)
# r1 活动秒杀库
r1 = redis.Redis(host=host, port=port, decode_responses=True, db= 1)

RESULTS_PER_PAGE = getattr(settings, 'HAYSTACK_SEARCH_RESULTS_PER_PAGE', 20)
from haystack.forms import  ModelSearchForm
from haystack.query import EmptySearchQuerySet


def basic_search(request, load_all=True, form_class=ModelSearchForm, searchqueryset=None, extra_context=None, results_per_page=None):
    query = ''
    results = EmptySearchQuerySet()
    if request.GET.get('q'):
        form = form_class(
            request.GET, searchqueryset=searchqueryset, load_all=load_all)

        if form.is_valid():
            query = form.cleaned_data['q']
            results = form.search()
    else:
        form = form_class(searchqueryset=searchqueryset, load_all=load_all)

    paginator = Paginator(results, results_per_page or RESULTS_PER_PAGE)
    try:
        page = paginator.page(int(request.GET.get('page', 1)))
    except InvalidPage:
        result = {"code": 404, "msg": 'No file found！', "data": []}
        return HttpResponse(json.dumps(result), content_type="application/json")

    context = {
        'form': form,
        'page': page,
        'paginator': paginator,
        'query': query,
        'suggestion': None,
    }
    if results.query.backend.include_spelling:
        context['suggestion'] = form.get_suggestion()

    if extra_context:
        context.update(extra_context)

    jsondata = []
    print(len(page.object_list))
    for result in page.object_list:
        data = {
            'pk': result.object.pk,
            'name': result.object.name,
            'desc': result.object.desc,
            'img': result.object.img,
            'category': result.object.category,
        }
        jsondata.append(data)
    result = {"code": 200, "msg": 'Search successfully！', "data": jsondata}
    return JsonResponse(result, content_type="application/json")

# 展示报告
class ReportList(APIView):
    def get(self,request):
        # 获取课程id
        cid = request.GET.get('cid',None)
        reportlist = Report.objects.filter(cid=int(cid))
        reportser = ReportSer(reportlist,many=True).data
        # 查询所有课程
        course = Course.objects.all()
        courseser = CourseSer(course,many=True).data
        # 遍历
        for i in reportser:
            # 当报告uid与用户id相同时
            user = User.objects.get(id=int(i['uid']))
            # 将用户信息添加到报告列表中
            i['username'] = user.username
            i['photo'] = user.photo
            i['exper'] = user.experience
            # 遍历所有课程
            for j in courseser:
                # 当报告中cid与课程id相同时
                if i['cid'] == j['id']:
                    # 将课程name添加到报告列表中
                    i['name'] = j['name']
        return Response({'code':200,'reportlist':reportser})

# 发表报告
class AddReport(APIView):
    def post(self,request):
        # 获取参数
        cid = request.data.get('cid',None)
        sid = request.data.get('sid',None)
        content = request.data.get('content',None)
        jwt_token = request.data.get('token',None)
        user = jwt_decode_handler(jwt_token)
        user_id = user.get('user_id')
        # 判断是否登录
        if not user_id:
            return Response({'code':405,'message':'请先登录'})
        # 将课程id。章节id。报告人id。报告内容。存入到数据库中
        Report.objects.create(cid=cid,sid=sid,uid=user_id,content=content)
        return Response({'code':200,'message':'发布成功'})

# 课程推荐
class RecoCourse(APIView):
    def get(self,request):
        # 获取课程id
        cid = request.GET.get('cid',None)
        print(cid)
        # 查询该课程已学过的用户
        learn = Learn.objects.filter(cid=int(cid))
        learn_ser = LearnSer(learn,many=True).data
        data = []
        # 遍历取出已学过的用户id
        for i in learn_ser:
            uid = i['uid']
            # 查询学过此课程的用户学过的其它课程
            learn1 = Learn.objects.filter(uid=int(uid))
            learn_ser1 = LearnSer(learn1, many=True).data
            # 遍历将这些用户学过的课程id存入到空列表中
            for j in learn_ser1:
                # 当课程id与从前端获取的课程id相同时，不再添加列表中
                if j['cid'] != int(cid):
                    data.append(j['cid'])
        #  计算出现课程次数较高的前三课程
        counts = Counter(data)
        CountsNum = counts.most_common(3)
        course_data = []
        # 遍历
        for i in CountsNum:
            resp = {}
            # 查询前三课程的课程信息
            course = Course.objects.get(id=int(i[0]))
            courseser = CourseSer(course).data
            # 取出有用信息已字典形式存入到空列表中
            resp['id'] = courseser.get('id')
            resp['name'] = courseser.get('name')
            resp['img'] = courseser.get('img')
            course_data.append(resp)
        print(course_data)
        return Response({'code':200,'course_data':course_data})

# 新活动入库
class SeckillAdmin(APIView):
    def post(self, request):
        res = {}
        print(request.data)
        form = request.data.get('form')
        title = form.get('name')
        courses = form.get('courses')

        img = form.get('img')
        time = form.get('pick_date')
        start_time = time[0].split('T')[0] + ' 00:00:00'
        end_time = time[1].split('T')[0] + ' 00:00:00'
        # 获取课程详细信息
        course_info = Course.objects.filter(id__in= courses)
        c_ser = CourseSer(course_info, many= True)

        c_str_info = json.dumps(c_ser.data)

        # 存入活动信息
        seckill = Seckill(title= title, img= img, start_time= start_time, end_time= end_time)
        seckill.save()
        # 存入课程信息
        for course_id in courses:
            sec_course = SecCourse(sid= seckill.id, cid= course_id)
            sec_course.save()

        # 存入redis
        r_key = 's_%d' %seckill.id
        r1.hset(r_key, 'title', title)
        r1.hset(r_key, 'time', (start_time + ' ~ '+ end_time))
        r1.hset(r_key, 'courses', c_str_info)

        # 设置生命周期
        now = timezone.now()
        end = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        exp = end - now

        r1.expire(r_key, exp.seconds)


        return Response(res)


# 训练营修改库存
class SetStock(APIView):
    def post(self, request):
        res = {}
        cid = request.data.get('id', 'null')
        stock = request.data.get('stock', 'null')

        r1.hset('bootcamp', cid, stock)

        res['code'] = 200
        res['message'] = '修改成功'
        return Response(res)


# 秒杀课程数据
class SeckillData(APIView):
    def get(self,request):
        res = {}
        # 获取redis库中所有信息
        seckill = r1.keys()
        print(seckill)
        res['data'] = []

        if not 'bootcamp' in seckill:
            seckill.append('bootcamp')
        info = []
        stock = {}
        for i in seckill:
            sec = {}
            data = r1.hgetall(i)
            if i != 'bootcamp' and i != 'lock':
                sec['title'] = data['title']
                sec['time'] = data['time']
                sec['courses'] = json.loads(data['courses'])
                info.append(sec)
            else:
                stock = data

        # 数据拼接
        for i in info:
            print(i)
            courses = i.get('courses')
            for c in courses:
                if stock.get(str(c.get('id'))):
                    c['stock'] = stock.get(str(c.get('id')))

                else:
                    c['stock'] = 100
                    r1.hset('bootcamp', str(c.get('id')), 100)
            res['data'] = info
        return Response(res)

# 训练营课程
class DrillCourse(APIView):
    def get(self, request):
        res = {}
        course_list = Course.objects.filter(category="训练营")
        print(course_list)
        course_ser = CourseSer(course_list, many=True)
        for i in course_ser.data:
            stock = r1.hget('bootcamp', i['id'])
            if stock:
                i['stock'] = stock
            else:
                i['stock'] = 100
                r1.hset('bootcamp', i['id'], 100)
        res['data'] = course_ser.data
        return Response(res)


# 获取实验豆数量
class GetBlan(APIView):
    def get(self, request):
        jwt_token = request.GET.get('token', None)
        user = jwt_decode_handler(jwt_token)
        user_id = user.get('user_id')
        if not user_id:
            return Response({'code': 405, 'message': '请先登录'})
        user = User.objects.get(id=int(user_id))
        bean = UserSer(user).data
        return Response({'code': 200, 'bean': bean.get('bean')})


# 获取优惠券
class CouponList(APIView):
    def get(self, request):
        # 获取参数
        jwt_token = request.GET.get('token', None)
        user = jwt_decode_handler(jwt_token)
        user_id = user.get('user_id')
        # 判断用户是否登录
        if not user_id:
            return Response({'code': 405, 'message': '请先登录'})
        # 查询该用户的所有优惠券
        coupon = Coupon.objects.filter(uid=int(user_id))
        # 序列化
        couponlist = CouponSer(coupon, many=True).data
        # 遍历添加是否过期
        for i in couponlist:
            strp = datetime.datetime.strptime(i['end_time'], "%Y-%m-%dT%H:%M:%S.%f")
            end_time = strp - datetime.datetime.now()
            if end_time.days > 0:
                i['state'] = '待使用'
                i['days'] = end_time.days
            else:
                i['state'] = '已过期'
        return Response({'code': 200, 'couponlist': couponlist})


# 优惠券
class CreateCoupon(APIView):
    def get(self, request):
        # 获取参数
        price = request.GET.get('price', None)
        title = request.GET.get('title', None)
        img = request.GET.get('img', None)
        jwt_token = request.GET.get('token', None)
        user = jwt_decode_handler(jwt_token)
        user_id = user.get("user_id")
        # 判断用户是否登录
        if not user_id:
            return Response({'code': 405, 'message': '请登录后领取'})
        # 生成优惠券
        coupon = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(10, 99)))
        print(coupon)
        # 计算过期时间(有效期为一个月)
        end_time = datetime.datetime.now() + relativedelta(months=+1)
        # 处理价格(该价格为实验豆数量1：100)
        price1 = int(price) * 100
        Coupon.objects.create(title=title, price=int(price1), coupon=coupon, img=img, uid=int(user_id),
                              end_time=end_time)
        # 查找当前兑换优惠券用户
        user = User.objects.get(id=int(user_id))
        # 将该用户的实验豆扣除相应数量
        user.bean = user.bean - int(price)
        # 保存
        user.save()
        return Response({'code': 200, 'message': '兑换成功'})


# 实验课程(学过的 & 关注的 & 发布的) & 实验报告 & 实验讨论
class LearnView(APIView):
    def get(self, request):
        uuid = request.GET.get('uid')
        # 获取实验课程 & 实验报告 & 实验讨论
        selected = request.GET.get('selected', None)
        # print(selected)
        # 获取学过的 & 关注的 & 发布的
        type = request.GET.get('type', None)
        # 获取用户token
        jwt_token = request.GET.get('token', None)
        if jwt_token:
            user = jwt_decode_handler(jwt_token)
            uid = user.get("user_id")
            # 判断用户是否登录
            if not uid:
                return Response({'code': '405', 'message': '请先登录'})
            total = Course.objects.all()
            total = CourseSer(total, many=True).data
            courselist = []
            if selected == '实验课程':
                # 实验课程中包含：学过的 & 关注的 & 发布的
                if type == '学过的':
                    learn = Learn.objects.filter(uid=int(uid))
                    learnlist = LearnSer(learn, many=True).data
                    # 遍历
                    for i in learnlist:
                        # 获取课程id
                        cid = i['cid']
                        # 查询此id在课程中对应的信息
                        course = Course.objects.filter(id=int(cid)).first()
                        courseser = CourseSer(course).data
                        # 将此课程信息添加到空列表中
                        courselist.append(courseser)
                    return Response({'code': 200, 'courselist': courselist})
                elif type == '关注的':
                    follow = Follow.objects.filter(uid=int(uid))
                    followlist = FollowSer(follow, many=True).data
                    # 遍历
                    for i in followlist:
                        # 获取课程id
                        cid = i['cid']
                        course = Course.objects.filter(id=int(cid)).first()
                        courseser = CourseSer(course).data
                        # 将此课程信息添加到空列表中
                        courselist.append(courseser)
                    return Response({'code': 200, 'courselist': courselist})
                elif type == '购买的':
                    buy = Buy.objects.filter(uid=int(uid))
                    buylist = BuySer(buy, many=True).data
                    # 遍历
                    for i in buylist:
                        # 获取课程id
                        cid = i['cid']
                        course = Course.objects.filter(id=int(cid)).first()
                        courseser = CourseSer(course).data
                        # 将此课程信息添加到空列表中
                        courselist.append(courseser)
                    return Response({'code': 200, 'courselist': courselist})
                elif type == '发布的':
                    # 查询该用户发布的所有课程
                    course = Course.objects.filter(uid=int(uid))
                    courselist = CourseSer(course, many=True).data
                    return Response({'code': 200, 'courselist': courselist})

            elif selected == '实验报告':
                # 查询该用户的所有报告
                report = Report.objects.filter(uid=int(uid))
                reportser = ReportSer(report, many=True).data
                # 查询所有课程
                course = Course.objects.all()
                courseser = CourseSer(course, many=True).data
                user = User.objects.get(id=int(uid))
                for i in reportser:
                    # 将用户信息存入报告列表中
                    i['username'] = user.username
                    i['photo'] = user.photo
                    i['exper'] = user.experience
                    # 循环遍历(当报告cid与课程id相同时，让课程name添加到报告列表中)
                    for j in courseser:
                        if i['cid'] == int(j['id']):
                            i['name'] = j['name']
                return Response({'code': 200, 'reportlist': reportser})

            elif selected == '实验讨论':
                # 查询改用户发表的帖子
                question = Question.objects.filter(uid=int(uid))
                questionser = QuestionSer(question, many=True).data
                # 遍历(将该帖子下的所有回复，添加到序列化器中，传递给前端)
                for i in questionser:
                    count = Comment.objects.filter(ques_id=int(i['id'])).count()
                    i['count'] = count
                return Response({'code': 200, 'questionlist': questionser})
        else:
            courselist = []
            if selected == '实验课程':
                # 实验课程中包含：学过的 & 关注的 & 发布的
                if type == '学过的':
                    learn = Learn.objects.filter(uid=int(uuid))
                    learnlist = LearnSer(learn, many=True).data
                    # 遍历
                    for i in learnlist:
                        # 获取课程id
                        cid = i['cid']
                        # 查询此id在课程中对应的信息
                        course = Course.objects.filter(id=int(cid)).first()
                        courseser = CourseSer(course).data
                        # 将此课程信息添加到空列表中
                        courselist.append(courseser)
                    return Response({'code': 200, 'courselist': courselist})
                elif type == '关注的':
                    follow = Follow.objects.filter(uid=int(uuid))
                    followlist = FollowSer(follow, many=True).data
                    # 遍历
                    for i in followlist:
                        # 获取课程id
                        cid = i['cid']
                        course = Course.objects.filter(id=int(cid)).first()
                        courseser = CourseSer(course).data
                        # 将此课程信息添加到空列表中
                        courselist.append(courseser)
                    return Response({'code': 200, 'courselist': courselist})
                elif type == '发布的':
                    # 查询该用户发布的所有课程
                    course = Course.objects.filter(uid=int(uuid))
                    courselist = CourseSer(course, many=True).data
                    return Response({'code': 200, 'courselist': courselist})

            elif selected == '实验报告':
                # 查询该用户的所有报告
                report = Report.objects.filter(uid=int(uuid))
                reportser = ReportSer(report, many=True).data
                # 查询所有课程
                course = Course.objects.all()
                courseser = CourseSer(course, many=True).data
                # 循环遍历(当报告cid与课程id相同时，让课程name取代报告的cid)
                for i in reportser:
                    for j in courseser:
                        if i['cid'] == int(j['id']):
                            i['cid'] = j['name']
                return Response({'code': 200, 'reportlist': reportser})

            elif selected == '实验讨论':
                # 查询改用户发表的帖子
                question = Question.objects.filter(uid=int(uuid))
                questionser = QuestionSer(question, many=True).data
                # 遍历(将该帖子下的所有回复，添加到序列化器中，传递给前端)
                for i in questionser:
                    count = Comment.objects.filter(ques_id=int(i['id'])).count()
                    i['count'] = count
                return Response({'code': 200, 'questionlist': questionser})


# 学习记录入库
class CourseRecord(APIView):
    def get(self, request):
        token = request.GET.get('token', '')
        sid = request.GET.get('sid', 0)  # 章节id
        # print(token, sid)

        res = {}

        section = Section.objects.filter(id=sid).first()
        c_id = section.cid

        user = jwt_decode_handler(token)
        # print(type(user))
        uid = user["user_id"]

        course = Learn.objects.filter(uid=uid, cid=c_id, sid=sid)
        if course:
            res['code'] = 401
            res['message'] = "已学习该课程"
            return Response(res)

        learn = Learn(uid=uid, cid=c_id, sid=sid)
        learn.save()

        res['code'] = 200
        res['message'] = "入库成功"
        return Response(res)


# 七牛云
from qiniu import Auth


# 七牛云token
class QiNiu(APIView):
    def get(self, request):
        q = Auth('Kvp7sDywPMlQbylJ62NmrShSd3rO5uaPkeeZ3Us-', 'uGwRXUZfDZPQMNnAQz4DCIxKgJO_LyB1OenOQpuz')
        token = q.upload_token('labcloudstorage')
        return Response({
            'token': token
        })


# 添加课程
class InsertCourse(APIView):
    def get(self, request):
        # 接收参数
        name = request.GET.get("name", 'null')  # 课程名
        uid = request.GET.get("uid", 'null')  # 发布人id
        img = request.GET.get("img", 'null')  # 封面
        # tag = request.GET.get("img",'null')                     # 标签
        desc = request.GET.get("desc", 'null')  # 简介
        category = request.GET.get("category", 'null')  # 所属分类(训练营、会员、高级会员、限免)
        price = request.GET.get("price", 'null')  # 价格（单位：分）
        collect_num = request.GET.get("collect_num", 'null')  # 总收藏数
        is_online = request.GET.get("is_online", 'null')  # 是否上线({0:未上线,1:即将上线})
        # 排重
        course = Course.objects.filter(name=name).first()

        if course:
            res = {}
            res['code'] = 405
            res['message'] = '该课程已存在'
            return Response(res)
        # tag_id_list=tag[1:-1].split(',')
        # 入库
        course = Course(name=name, uid=int(uid), img=img, desc=desc, category=category, price=int(price),
                        collect_num=int(collect_num), is_online=int(is_online))
        course.save()
        res = {}
        res['code'] = 200
        res['message'] = '添加成功'
        return Response(res)


# #更新课程信息
class UpdateCourse(APIView):
    def get(self, request):
        # 接收参数
        id = request.GET.get("id", 0)  # 课程id
        name = request.GET.get("name", 'null')  # 课程名
        uid = request.GET.get("uid", 'null')  # 发布人id
        # tag = request.GET.get("tag", 'null')                    # 标签
        img = request.GET.get("img", 'null')  # 封面
        desc = request.GET.get("desc", 'null')  # 简介
        category = request.GET.get("category ", 'null')  # 所属分类(训练营、会员、高级会员、限免)
        price = request.GET.get("price", 'null')  # 价格（单位：分）
        collect_num = request.GET.get("collect_num", 'null')  # 总收藏数
        is_online = request.GET.get("is_online", 'null')  # 是否上线({0:未上线,1:即将上线})

        # 查询数据
        course = Course.objects.filter(id=int(id)).first()
        course.name = name
        course.uid = uid
        course.img = img
        course.desc = desc
        course.category = category
        course.price = price
        course.collect_num = collect_num
        course.is_online = is_online

        course.save()
        res = {}
        res['code'] = 200
        res['message'] = '恭喜，更新成功'

        return Response(res)


class DeleteCourse(APIView):
    def get(self, request):
        # 接收参数
        id = request.GET.get("id", 0)  # 课程id
        # print(id)
        # 查询数据
        course = Course.objects.filter(id=id).first()
        course.delete()
        res = {}
        res['code'] = 200
        res['message'] = '删除成功'

        return Response(res)


# 课程检索接口
class SearchCourse(APIView):
    def get(self, request):
        # 接收参数
        word = request.GET.get('word', None)

        # 检索  模糊匹配 管道| 表示或者 or     并且&
        # 检索名称或者描述里包含关键词的课程
        courselist = Course.objects.filter(Q(name__icontains=word) | Q(desc__icontains=word))

        # #检索名称或描述里包含关键词，并且规格里也包含的课程
        # goodslist= Goods.objects.filter(Q(parms__icontains=word),Q(name__icontains=word)|Q(desc__icontains=word))

        # 序列化
        course_ser = CourseSer(courselist, many=True)

        return Response(course_ser.data)

    def get(self, request):
        # 当前页
        page = int(request.GET.get("page", 1))
        # 一页有多少条课程
        size = int(request.GET.get("size", 5))


# 全部课程接口
class GetCourses(APIView):
    def get(self, request):
        res = {}

        # 是否是删除？
        is_delete = request.GET.get('is_delete', '0')

        # 当前页
        page = request.GET.get("page", '1')
        # 一页有多少条课程
        size = request.GET.get("size", 'null')

        # 验证参数
        if is_delete.isdigit() and page.isdigit() and size.isdigit():
            is_delete = int(is_delete)
            page = int(page)
            size = int(size)

            # 定义从哪儿开始切
            data_start = (page - 1) * size

            # 定义切到哪儿
            data_end = page * size

            # 查询数据
            courselist = Course.objects.filter(is_delete=is_delete)[data_start:data_end]

            # 查询总数量
            count = Course.objects.count()

            # 序列化操作
            course_ser = CourseSer(courselist, many=True)

            for i in course_ser.data:
                i['author'] = uid_to_user(i['uid']).username
                sections = Section.objects.filter(cid=int(i['id']))
                sections = SectionSer(sections, many=True)
                i['sections'] = sections.data

            data = course_ser.data

            res['code'] = 200
            res['total'] = count
            res['data'] = data

        else:
            courselist = Course.objects.filter(is_delete=is_delete)
            course_ser = CourseSer(courselist, many=True)
            res['code'] = 200
            res['data'] = course_ser.data

        return Response(res)


# 获取标签表
class GetTags(APIView):
    def get(self, request):
        res = {}
        cid = request.GET.get('cid')
        if cid and cid.isdigit():
            cid = int(cid)
            tags = CourseTag.objects.filter(cid=cid)
            tag_ser = CourseTagSer(tags, many=True)
            tag_id_list = []
            for tag in tag_ser.data:
                tag_id_list.append(tag['tid'])
            # print(tag_ser.data)
            res['code'] = 200
            res['data'] = tag_id_list
            return Response(res)

        else:
            tags = Tag.objects.all()

        ser = TagSer(tags, many=True)
        res['code'] = 200
        res['data'] = ser.data
        return Response(res)


# 后台课程增删改查
class CourseAdmin(APIView):
    # 增加一门课程
    def post(self, request):
        res = {}

        course = request.data.get('course')
        section = request.data.get('section').get('sections')
        tags = request.data.get('tags').split(',')
        course.pop('author')
        # # 反序列化入库课程
        course_data = CourseSer(data=course)
        if course_data.is_valid():
            course_data.save()
        # 获取课程id
        course_id = Course.objects.aggregate(Max('id')).get('id__max')
        course_id = int(course_id)
        # 遍历入库章节
        for i in section:
            sec = Section(section_name=i.get('value'), cid=course_id)
            sec.save()
        # 遍历入库标签
        for i in tags:
            t = CourseTag(tid=i, cid=course_id)
            t.save()
        # 课程评论入库
        question = Question(title='', content='', uid=1, cid=course_id, top=0, excellent=0, examine=0, favorite=0,
                            type='comment')
        question.save()
        res['code'] = 200
        res['message'] = '上传成功'

        return Response(res)

    # 修改课程
    def put(self, request):
        res = {}
        # 整理数据
        put = QueryDict(request.body)
        put_str = list(put.items())[0][0]
        put_dict = json.loads(put_str)
        if put_dict != {}:
            id = put_dict.get('id')
            course = Course.objects.get(id=int(id))
            course.create_time = put_dict.get('create_time')
            course.name = put_dict.get('name')
            course.img = put_dict.get('img')
            course.desc = put_dict.get('desc')
            course.is_online = put_dict.get('is_online')
            course.price = put_dict.get('price')
            course.category = put_dict.get('category')
            course.save()

            # 修改标签
            # 获取课程所有标签
            tags_past = CourseTag.objects.filter(cid=int(id))
            tag_list = []
            for i in tags_past:
                tid = i.tid
                tag_list.append(tid)

            tags_now = put_dict.get('tags')
            # 旧表有，新表没有，删除
            for i in tag_list:
                if i not in tags_now:
                    CourseTag.objects.filter(tid=i, cid=id).first().delete()

            # 新表有，旧表没有，增加
            for i in tags_now:
                if i not in tag_list:
                    CourseTag(tid=i, cid=id).save()

            res['code'] = 200
            res['message'] = '修改成功'

            return Response(res)

        res['code'] = 403
        res['message'] = '参数错误'

        return Response(res)

    # 删除课程
    def get(self, request):
        res = {}
        # 整理数据
        id_list = request.GET.get('id_list', '').split(',')
        method = request.GET.get('method', '')
        if method == 'delete':
            is_delete = 1
            message = '删除成功'
        elif method == 'recover':
            is_delete = 0
            message = '恢复成功'
        else:
            res['code'] = 403
            res['message'] = '参数错误'
            return Response(res)
        # print(id_list)
        for id in id_list:
            if id.isdigit():
                id = int(id)
                course = Course.objects.get(id=int(id))
                course.is_delete = is_delete
                course.save()
            else:
                res['code'] = 403
                res['message'] = '参数错误'

                return Response(res)

        res['code'] = 200
        res['message'] = message
        return Response(res)


# 课程章节接口
class SectionInfo(APIView):
    def get(self, request):
        res = {}
        cid = request.GET.get('cid', 0)
        if cid and cid.isdigit():
            cid = int(cid)
            section = Section.objects.filter(cid=cid)
            ser = SectionSer(section, many=True)
            res['code'] = 200
            res['data'] = ser.data
        else:
            res['code'] = 405
            res['message'] = '参数错误'
        return Response(res)


# 单个课程信息类
class CourseInfo(APIView):
    def get(self, request):

        cid = request.GET.get("cid", 0)
        # print(cid)

        # 查询数据
        course = Course.objects.get(id=int(cid))
        if course:
            # 序列化对象
            course_ser = CourseSer(course)
            cid = course.id
            section = Section.objects.filter(cid=cid)
            # print(section)
            if section:
                section_ser = SectionSer(section, many=True)
                data = {'course_ser': course_ser.data, 'section_ser': section_ser.data}
                return Response(data)
            return Response({'course_ser': course_ser.data})
        else:
            return Response({'code': 201, 'message': '没有找到对应课程'})


# 定义上传视图类
class UploadFile(View):
    def post(self, request):
        # 接收参数
        img = request.FILES.get("file")

        # 建立文件流对象
        f = open(os.path.join(UPLOAD_ROOT, '', img.name), 'wb')

        # 写入服务器端
        for chunk in img.chunks():
            f.write(chunk)
        f.close()

        # 定义存储路径
        StoragePath = './static/upload/' + img.name

        # 返回文件名
        return HttpResponse(json.dumps({'filename': img.name}, ensure_ascii=False), content_type='application/json')


# 全部课程接口
class GetCourses1(APIView):
    def get(self, request):
        # 当前页
        page = int(request.GET.get("page", 1))
        # 一页有多少条课程
        size = int(request.GET.get("size", 9))

        free = request.GET.get("free", '')
        tag_id = request.GET.get("tag_id", '')
        online = request.GET.get("online", '')
        sort = request.GET.get("sort", '')

        # print(free)
        # print(online)
        # print(sort)

        # 定义从哪儿开始切
        data_start = (page - 1) * size

        # 定义切到哪儿
        data_end = page * size

        if tag_id == '':
            if sort == '2':
                if free == '' and online == '':
                    courselist = Course.objects.order_by('-collect_num')[data_start:data_end]
                elif free == '' and online != '':
                    courselist = Course.objects.filter(is_online=int(online)).order_by('-collect_num')[
                                 data_start:data_end]
                elif free != '' and online == '':
                    courselist = Course.objects.filter(category=free).order_by('-collect_num')[data_start:data_end]
                else:
                    courselist = Course.objects.filter(category__exact=free, is_online=int(online)).order_by(
                        '-collect_num')[data_start:data_end]
            else:
                if free == '' and online == '':
                    courselist = Course.objects.order_by('-create_time')[data_start:data_end]
                elif free == '' and online != '':
                    courselist = Course.objects.filter(is_online=int(online)).order_by('-create_time')[
                                 data_start:data_end]
                elif free != '' and online == '':
                    courselist = Course.objects.filter(category=free).order_by('-create_time')[data_start:data_end]
                else:
                    courselist = Course.objects.filter(category__exact=free, is_online=int(online)).order_by(
                        '-create_time')[data_start:data_end]
        else:
            tag_id_list = CourseTag.objects.filter(tid=int(tag_id))
            tag_id_ser = CourseTagSer(tag_id_list, many=True)
            cid_list = []
            for i in tag_id_ser.data:
                cid_list.append(i['cid'])
            if sort == '2':
                if free == '' and online == '':  # 1
                    courselist = Course.objects.filter(id__in=cid_list).order_by('-collect_num')[data_start:data_end]
                elif free == 'all' and online != '':  # 1
                    courselist = Course.objects.filter(id__in=cid_list, is_online=int(online)).order_by('-collect_num')[
                                 data_start:data_end]
                elif free != '' and online == '':
                    courselist = Course.objects.filter(id__in=cid_list, category=free).order_by('-collect_num')[
                                 data_start:data_end]
                else:
                    courselist = Course.objects.filter(id__in=cid_list, category__exact=free,
                                                       is_online=int(online)).order_by('-collect_num')[
                                 data_start:data_end]
            else:
                if free == '' and online == '':
                    courselist = Course.objects.filter(id__in=cid_list).order_by('-create_time')[data_start:data_end]
                elif free == '' and online != '':
                    courselist = Course.objects.filter(id__in=cid_list, is_online=int(online)).order_by('-create_time')[
                                 data_start:data_end]
                elif free != '' and online == '':
                    courselist = Course.objects.filter(id__in=cid_list, category=free).order_by('-create_time')[
                                 data_start:data_end]
                else:
                    courselist = Course.objects.filter(id__in=cid_list, category__exact=free,
                                                       is_online=int(online)).order_by('-create_time')[
                                 data_start:data_end]

        # 查询总数量
        count = Course.objects.count()

        # 序列化操作
        course_ser = CourseSer(courselist, many=True)

        data = course_ser.data

        res = {}
        res['code'] = 200
        res['total'] = count
        res['data'] = data
        return Response(res)


class Auth_Info(APIView):
    def get(self, request):
        id = request.GET.get('id', None)
        auth = User.objects.filter(id=id).first()
        if auth:
            auth_ser = UserSer(auth)
            return Response(auth_ser.data)
        else:
            return Response({'code': 201, 'message': '未找到该用户'})


class Course_Count(APIView):
    def get(self, request):
        uid = request.GET.get('id', None)
        if uid:
            course = Course.objects.filter(uid=uid)
            # print(course.count())
            if course:
                return Response({'code': 200, 'message': '数据请求成功', 'course_count': course.count()})
        else:
            return Response({'code': 403, 'message': '数据请求失败'})


class LearnInfo(APIView):
    def get(self, request):
        res = {}
        token = request.GET.get('token', None)
        cid = request.GET.get('cid', None)
        uid = jwt_decode_handler(token).get('user_id')
        hist = Learn.objects.filter(uid=uid, cid=int(cid))
        ser = LearnSer(hist, many=True)
        res['code'] = 200
        res['data'] = ser.data
        return Response(res)


# 添加免费课程
class InsertLearn(APIView):
    def get(self, request):
        # 课程id
        cid = request.GET.get('cid', None)
        # 用户id
        jwt_token = request.GET.get('token', None)
        user = jwt_decode_handler(jwt_token)
        user_id = user.get('user_id')
        if not user_id:
            return Response({'code': 405, 'message': '请先登录'})
        Buy(uid=int(user_id), cid=cid).save()
        return Response({'code': 200, 'message': '课程添加成功'})


# 后台课程章节视频
class SectionVideo(APIView):
    # 添加视频
    def post(self, request):
        # 获取参数
        sid = request.data.get('sid')
        vkey = request.data.get('key')
        # 数据库查询
        section = Section.objects.filter(id=sid).first()
        if section:
            section.video = vkey
            section.save()
            res = {}
            res['code'] = 200
            res['msg'] = '上传成功'
            return Response(res)
        else:

            res = {}
            res['code'] = 405
            res['msg'] = '上传失败'
            return Response(res)

    # 获取视频
    def get(self, request):
        # 获取参数
        sid = request.GET.get('sid')
        # 数据库查询
        section = Section.objects.filter(id=sid).first()
        print(section)
        res = {}
        res['video'] = section.video

        return Response(res)


# 后台课程头图
class SectionImg(APIView):
    # 添加头图
    def post(self, request):
        # 获取参数
        sid = request.data.get('sid')
        key = request.data.get('imgkey')
        # 数据库查询
        section = Section.objects.filter(id=sid).first()
        if section:
            section.video = key
            section.save()
            res = {}
            res['code'] = 200
            res['msg'] = '上传成功'
            return Response(res)
        else:

            res = {}
            res['code'] = 405
            res['msg'] = '上传失败'
            return Response(res)

    # 获取视频
    def get(self, request):
        # 获取参数
        sid = request.GET.get('sid')
        # 数据库查询
        section = Section.objects.filter(id=sid).first()
        print(section)
        res = {}
        res['video'] = section.video

        return Response(res)


# 根据id查用户
def uid_to_user(uid):
    user = User.objects.filter(id=int(uid)).first()
    if user:
        return user
    else:
        return User.objects.get(id=1)


class GetCoursePay(APIView):
    def get(self, request):
        resp = {}
        # 获取token
        jwt_token = request.GET.get("token", None)
        if not jwt_token:
            return Response({"code": 405, "message": "用户未登录"})
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


import uuid
import time
class Purchase(APIView):

    def get(self, request):
        cid = request.GET.get('cid')
        res = {}
        res['code'] = 200
        res['message'] = '请求成功'
        res['data'] = self.sale(cid)
        return Response(res)

    def sale(self, cid):
        print(cid)
        while True:
            lock = self.acquire_lock('lock')
            if not lock: # 持锁失败
                continue
            p = r1.pipeline()
            try:
                p.watch('bootcamp')
                p.multi()
                stock = p.hget('bootcamp', cid)
                print(stock)
                if stock == 0:
                    p.unwatch()
                    return '您来晚了，课程已销售一空'
                else:
                    p.hincrby('bootcamp', cid, -1)
                    p.execute()  # 执行事务
                    p.unwatch()
                    return '秒杀成功！'
            except Exception as e:  # 当出现watch监听值出现修改时，WatchError异常抛出
                print('[Error]: %s' % e)
                error_message = '[Error]: %s' % e
                continue  # 继续尝试执行
            finally:

                res = self.release_lock('lock', lock)
                #释放锁成功，
                if res:
                    print("删除锁成功")
                #释放锁失败，强制删除
                else:
                    print("删除锁失败,强制删除锁")
                    res = r1.delete('lock')
                    print(res)
            # break

    def acquire_lock(self, lock_name, expire_time=10):
        '''
        rs: 连接对象
        lock_name: 锁标识
        acquire_time: 过期超时时间
        return -> False 获锁失败 or True 获锁成功
        '''
        identifier = str(uuid.uuid4())
        end = time.time() + expire_time
        while time.time() < end:
            # 当获取锁的行为超过有效时间，则退出循环，本次取锁失败，返回False
            if r1.setnx(lock_name, identifier): # 尝试取得锁
                return identifier
            # time.sleep(.001)
            return False

    # 3. 释放锁
    def release_lock(self, lockname, identifier):
        '''
        rs: 连接对象
        lockname: 锁标识
        identifier: 锁的value值，用来校验
        '''


        if r1.get(lockname) == identifier:  # 防止其他进程同名锁被误删
            r1.delete(lockname)
            return True            # 删除锁
        else:
            return False           # 删除失败

    #有过期时间的锁
    def acquire_expire_lock(self, lock_name, expire_time=10, locked_time=10):
        '''
        rs: 连接对象
        lock_name: 锁标识
        acquire_time: 过期超时时间
        locked_time: 锁的有效时间
        return -> False 获锁失败 or True 获锁成功
        '''
        identifier = str(uuid.uuid4())
        end = time.time() + expire_time
        while time.time() < end:
            # 当获取锁的行为超过有效时间，则退出循环，本次取锁失败，返回False
            if r1.setnx(lock_name, identifier): # 尝试取得锁
                print('锁已设置: %s' % identifier)
                r1.expire(lock_name, locked_time)
                return identifier
            time.sleep(.001)
        return False
