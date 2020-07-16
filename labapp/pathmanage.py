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


# 路径管理
class PathAdmin(APIView):
    # 增加路径
    def post(self, request):
        res = {}
        # 接收参数
        path_form = request.data.get('form')
        path_stage = request.data.get('stage')
        length = 0
        for stage in path_stage:
            # 计算总课程数
            length += len(stage.get('courses'))
        path_form['section_sum'] = length
        path_form['study_time'] = 0     # 计算预估学习时间
        print(path_form)
        path = PathSer(data = path_form)
        if path.is_valid():
            print('*'*100)
            path.save()
        # 获取id
        current = 1
        path_id = Path.objects.aggregate(Max('id')).get('id__max')
        print(path_id)
        for stage in path_stage:
            s = Stage(pid=path_id, stage= current,  stage_name= stage.get('name'))
            s.save()
            current += 1
            # 获取id
            stage_id = Stage.objects.aggregate(Max('id')).get('id__max')
            for course in stage.get('courses'):
                stage_course = Stage_Course(stage_id= stage_id, cid= course)
                stage_course.save()
        return Response(res)

    # 删除路径
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
                path = Path.objects.get(id=int(id))
                path.is_delete = is_delete
                path.save()
            else:
                res['code'] = 403
                res['message'] = '参数错误'

                return Response(res)

        res['code'] = 200
        res['message'] = message
        return Response(res)


#路径列表展示
class GetPath(APIView):
    def get(self, request):
        # 是否删除
        is_delete = request.GET.get('is_delete', 0)
        pathlist = Path.objects.filter(is_delete= int(is_delete))
        path_ser = PathSer(pathlist, many=True)
        data = path_ser.data
        
        res = {}
        res['code'] = 200
        res['data'] = data
        return Response(res)



#单个路径详情页面
class GetPathInfo(APIView):
    def get(self, request):

        #路径id
        pid = request.GET.get('pid', 0)

        # 路径信息
        path = Path.objects.get(id=int(pid))
        # 路径信息序列化
        path_ser = PathSer(path)

        # 路径阶段信息
        stagelist = Stage.objects.filter(pid=int(pid))
         # 路径阶段信息序列化
        stage_ser = StageSer(stagelist, many=True)

        #遍历路径阶段信息
        for i in stage_ser.data:

            #阶段课程信息
            stage_course_list = Stage_Course.objects.filter(stage_id=i['id'])
            stage_course_ser = Stage_CourseSer(stage_course_list, many=True)
            coursedata = []
            for j in stage_course_ser.data:
                courselist = Course.objects.filter(id=j['cid'])
                course_ser = CourseSer(courselist, many=True)
                coursedata.append(course_ser.data[0])
                
            i['coursedata'] = coursedata

        res = {}
        res['code'] = 200
        res['message'] = '查询成功'
        res['pathdata'] = path_ser.data
        res['stagedata'] = stage_ser.data

        return Response(res)


class HotPath(APIView):
     def get(self, request):
        hotpathlist = Path.objects.all().order_by('-section_sum')[0:5]
        path_ser = PathSer(hotpathlist, many=True)
        data = path_ser.data
        
        res = {}
        res['code'] = 200
        res['data'] = data
        return Response(res)

#用户对路径关注/取关
class PathFollow(APIView):
    def get(self,request):
        pid = request.GET.get("pid",None)
        uid = request.GET.get("uid",None)
        type = request.GET.get("type",'1')
        res={}
        if type == '1':
            #查询关注
            flow = PathUser.objects.filter(path_id=int(pid),uid=int(uid))
            if not flow:
                pathflow=PathUser(path_id=int(pid),uid=int(uid))
                pathflow.save()
                path = Path.objects.filter(id=int(pid)).first()
                path.add_sum = path.add_sum + 1
                path.save()
                res['code'] = 200
                res['message'] = '关注成功'
            else:
                res['code'] = 200
                res['message'] = '不能重复关注'
                pass
        else:
            #取关
            PathUser.objects.filter(path_id=int(pid),uid=int(uid)).delete()
            res['code'] = 200
            res['message'] = '取关成功'
            path = Path.objects.filter(id=int(pid)).first()
            path.add_sum = path.add_sum  - 1
            path.save()
    
        return Response(res)


#进入路径页面 判断用户是否已关注该路径
class IsPathFollow(APIView):
    def get(self,request):
        pid = request.GET.get("pid",None)
        uid = request.GET.get("uid", None)
        flow = PathUser.objects.filter(path_id=int(pid), uid=int(uid))
        res={}
        if flow:
            res['code'] = 200
            res['type'] = '1'
        else:
            res['code'] = 200
            res['type'] = '0'
        return Response(res)