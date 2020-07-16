"""lab_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve

import labapp

from labapp.coursemanage import *
from labapp.coursemanage import CourseRecord
from labapp.admin import *
from labapp.user import *
from labapp.question_comment import *
from lab_django.websocket import *
from labapp.pathmanage import *
from django.conf.urls import url


urlpatterns = [
    # 全文检索
    url(r'abc/$', basic_search),
    # 秒杀
    path('seckill_admin/', SeckillAdmin.as_view()),
    path('seckill_data/', SeckillData.as_view()),
    # 路径
    path('path_admin/', PathAdmin.as_view()),
    # 帖子和评论区
    path('get_questions/', GetQuestions.as_view()),
    path('get_comments/', GetComments.as_view()),
    path('favorite_comment/', FavoriteComment.as_view()),
    path('publish_comment/', PublishComment.as_view()),
    # 定义超链接路由
    re_path('^static/upload/(?P<path>.*)$', serve, {'document_root': '/static/upload/'}),
    path('admin/', admin.site.urls),
    path('insertcourse/', InsertCourse.as_view()),
    path('updatecourse/', UpdateCourse.as_view()),
    path('deletecourse/', DeleteCourse.as_view()),
    path('searchcourse/', SearchCourse.as_view()),
    path('getcourses/', GetCourses.as_view()),
    path('getcourses1/', GetCourses1.as_view()),    
    path('courseinfo/', CourseInfo.as_view()),     #获取课程详情信息
    path("uploadfile/", UploadFile.as_view()),  #文件上传

    path('getpath/', GetPath.as_view()),
    path('getpathinfo/', GetPathInfo.as_view()),
    path('gethotpath/', HotPath.as_view()),
    path('pathfollow/', PathFollow.as_view()),
    path('ispathfollow/', IsPathFollow.as_view()),
    path('insertlearn/', InsertLearn.as_view()),    # 加入课程


    path('set_stocks/', SetStock.as_view()),       # 训练营详情
    path('drillcourse/', DrillCourse.as_view()),       # 训练营详情
    path('getuser/', GetUser.as_view()),       # 成员详情
    # 获取所有标签
    path('get_tags/', GetTags.as_view()),
    # 检查用户是否存在，存在返回用户id
    path('check_username/', CheckUsername.as_view()),
    path('courserecord/', CourseRecord.as_view()),       # 学习进度入库
    path('', include('labapp.urls')),
    path('login/', Login.as_view()),                # 登录
    path('register/', Register.as_view()),          # 注册
    path('verifyemail/', EmailVerify.as_view()),    # 发送邮件
    path('sendalysms/', SendAlysms.as_view()),    # 发送手机验证码
    # path('verifytoken/', TokenVerify.as_view()),    # 校验
    path('vip_list/', Vip_List.as_view()),          # 会员展示页面请求
    path('alipay/', Alipay.as_view()),          # 沙箱支付请求
    path('get_alipy/', Get_Alipy.as_view()),          # 沙箱支付请求 及 post订单入库
    path('create_order/', Create_Order.as_view()),          # 生成订单接口



    path('user_info/', UserInfo.as_view()),
    path('updateuserimg/', UpdateUserImg.as_view()),

    # 管理员路由
    path('admin_register/', AdminRegister.as_view()),  # 注册
    path('admin_login/', AdminLogin.as_view()),  # 登录
    path('email_login/', EmailLogin.as_view()),  # 邮箱登录
    path('userlist/', UserList.as_view()),  # 用户列表(get请求包含vip表所有数据)
    
    # 课程
    # path('get_courses/', GetCourses.as_view()),
    # 课程章节
    path('section_info/', SectionInfo.as_view()),
    # 七牛云
    path('uptoken/', QiNiu.as_view()),

    # # 实验课程(学过的 & 关注的 & 发布的) & 实验报告 & 实验讨论
    path('learnview/', LearnView.as_view()),


    # 三方登陆(微博)
    path('weibo/', wb_back),
    path('verif/', Verif.as_view()),   

    # 获取作者信息
    path('authinfo/', Auth_Info.as_view()),
    # 获取作者的课程数量信息
    path('coursecount/', Course_Count.as_view()),


    # 获取用户学习信息
    path('learninfo/', LearnInfo.as_view()),

    # 添加免费课程
    path('coursecount/', Course_Count.as_view()),
    # 三方登陆(钉钉)
    path('dingding_back/', ding_back),

    # 修改课程信息
    path('course_admin/', CourseAdmin.as_view()),

    # 添加章节视频
    path('sectionvideo/', SectionVideo.as_view()),
    # 访客
    path('visitor/', Visitor.as_view()),

    # 优惠券
    path('create_coupon/', CreateCoupon.as_view()),
    # 获取用户优惠券
    path('coupon_list/', CouponList.as_view()),
    # 获取实验豆剩余数量
    path('getblan/', GetBlan.as_view()),



    
    # 获取用户vip等级
    path('getvid/', GetVid.as_view()),
    

    
    path('purchase/', Purchase.as_view()),
    # 生成订单
    path('getcoursepay/', GetCoursePay.as_view()),

    # 课程推荐
    path('reco_course/', RecoCourse.as_view()),
    # 发表报告
    path('add_report/', AddReport.as_view()),
    path('repor_tlist/', ReportList.as_view()),

    path('', index, name='index'),

    path('<str:room_name>/', room, name='room'),
    
    path("push", pushRedis, name="push"),   

]
