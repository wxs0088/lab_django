from django.shortcuts import render, redirect
# 导包
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, QueryDict
from labapp.models import *
from django.core.serializers import serialize
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views import View
import requests
import json
# 导入上传文件夹配置
from lab_django.settings import UPLOAD_ROOT
import os
# 导入公共目录变量
from lab_django.settings import BASE_DIR
# 导包
from django.db.models import Q, F, Avg, Max, Min
from labapp.labser import *
from rest_framework_jwt.utils import jwt_decode_handler

def choose_question():
    """
    帖子逻辑
    1，type
        type = comment                 课程评论（不可见主题帖，无内容，仅展示评论）
        type = report                   实验报告
        type = course                   课程问答（实验问答）
        type = sharing                  技术分享
        type=discussion               交流讨论
        type = announcement     站内公告
        课程下：commit, report, course
        讨论区：course, sharing, discussion, announcement
    2，id
        uid     作者      课程评论的作者是1，官方
        cid     课程      
        sid     章节      仅实验报告有此项，其他默认为0或空
    3，其他
        top     置顶
        excellent   精品除课程评论、实验报告
        examine     查看数
        favorite    收藏数
    """
    return Question.objects


# 发表评论
class PublishComment(APIView):
    def post(self,request):
        res = {}
        # 接收参数
        content = request.data.get('content')
        token = request.data.get('token')
        ques_id = request.data.get('ques_id')
        reply = request.data.get('reply', 0)
        if content and token and ques_id:
            try:
                user_id = jwt_decode_handler(token)['user_id']
            except:
                res['data'] = 403
                res['message'] = '验证信息错误'
                return Response(res)

            # 入库
            Comment(content= content, uid= user_id, ques_id= ques_id, reply= reply).save()
            res['code'] = 200
            res['message'] = '评论成功'
            return Response(res)

        res['code'] = 403
        res['message'] = '参数错误'


        return Response(res)


# 点赞
class FavoriteComment(APIView):
    def post(self, request):
        res = {}
        # 接收参数
        com_id = request.data.get("com_id")
        receive_id = request.data.get("receive_id")
        token = request.data.get('token')
        if com_id and receive_id and token:
            try:
                user_id = jwt_decode_handler(token)['user_id']
            except:
                res['data'] = 403
                res['message'] = '验证信息错误'
                return Response(res)
            # if com_id.isdigit() and receive_id.isdigit():
            # com_id = int(com_id)
            # receive_id = int(receive_id)
            # 查询是否关注
            fav = Favorite.objects.filter(com_id= com_id, uid= user_id)
            #  获取评论数据
            com_data = Comment.objects.filter(id= com_id)
            if fav:
                # 已关注，取消关注
                fav.delete()
                # 同步到评论表
                com_data.update(favorate= com_data.first().favorate - 1)
                res['code'] = 200
                res['message'] = '取消关注成功'
                return Response(res)
            else:
                # 未关注，入库
                Favorite(com_id= com_id, uid= user_id, receive_id= receive_id).save()
                #  同步到评论表
                com_data.update(favorate= com_data.first().favorate + 1)
                res['code'] = 200
                res['message'] = '关注成功'
                return Response(res)

        res['code'] = 403
        res['message'] = '参数错误'


        return Response(res)

class GetComments(APIView):
    def get(self, request):
        res = {}
        ques_id = request.GET.get('ques_id')
        token = request.GET.get('token')
        if token:
            user_id = jwt_decode_handler(token).get('user_id')
        if ques_id.isdigit():

            comments = Comment.objects.filter(ques_id= int(ques_id))

            ser = CommentSer(comments, many= True)
            # 查询user信息
            for i in ser.data:
                user = User.objects.filter(id=i.get('uid')).first()
                user_ser = UserSer(user)
                i['user_info'] = user_ser.data
                # 如果有token，加入收藏信息
                if token:
                    favorite = Favorite.objects.filter(uid= user_id, com_id= i['id'])
                    if favorite:
                        i['is_favorite'] = 1
                    else:
                        i['is_favorite'] = 0

            # 无限极化
            result = change_comments(ser.data)

            res['code'] = 200
            res['data'] = result
        else:
            res['code'] = 403
            res['message'] = '参数错误'
        return Response(res)



class GetQuestions(APIView):
    def get(self, request):
        res = {}
        # 接收参数
        type = request.GET.get('type', None)
        uid = request.GET.get('uid', None)
        cid = request.GET.get('cid', None)
        sid  = request.GET.get('sid', None)
        top = request.GET.get('top', None)
        excellent = request.GET.get('excellent', None)
        order_by = request.GET.get('order_by')

        # 首先，要有个参数
        if type in ['comment', 'report', 'course', 'sharing', 'discussion', 'announcement', 'all']:
            if type == 'all':
                # 讨论区全部，展示的是除课程评论外的内容
                question = Question.objects.exclude(type= 'comment')
            else:
                # 课程评论
                if type == 'comment':
                    question = Question.objects.filter(type= 'comment', cid= int(cid), is_delete= 0)
                # 实验报告
                elif type == 'report':
                    question = Question.objects.filter(type= 'report', sid= int(sid), is_delete= 0)
                # 实验问答
                elif type == 'course':
                    question = Question.objects.filter(type= 'course', cid = int(cid), is_delete= 0)
                # 其他
                else:
                    question = Question.objects.filter(type= type)

            ser = QuestionSer(question, many= True)
            res['code'] = 200
            res['data'] = ser.data
        return Response(res)


# 无限极评论计数器
def count_comments(data, dict):
    up = map(lambda x: x.get('reply'), data)
    up = list(up)
    while None in up:
        up.remove(None)
    if not up:
        return 0
    else:
        clear_list = []
        for i in data:
            if not i in clear_list:
                clear_list.append(i)
        new_list = []
        for i in clear_list:
            for j in data:
                if j['reply'] == i['id']:
                    dict[i['id']] += 1
                    new_list.append(i)
        count_comments(new_list, dict)


# 无限极评论转化器
def change_comments(data):
    list = []
    tree = {}
    dict = {}
    for i in data:
        dict[i['id']] = 0
    count_comments(data, dict)

    for i in data:
        i['count'] = dict[i['id']]
        # 将data循环，然后加入一个dict中，key为每条数据的ID，val对应为整条数据
        tree[i["id"]] = i
    for i in data:
        # reply==None，他就是祖先
        if i["reply"] == 0:
            root = tree[i["id"]]  # i.di为tree里的key，将key对应的val取出
            list.append(root)
        else:
            reply = i["reply"]
            # 判断父级是否有孩子字段（childlist），如果有将当前数据加入，如果没有添加（childlist）后再加入
            if "childlist" not in tree[reply]:
                tree[reply]['childlist'] = []
            tree[reply]["childlist"].append(tree[i["id"]])
    return list
