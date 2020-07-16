# 数据库模块
from django.db import models
# 时间模块快
from django.utils import timezone
# 用户表
from django.contrib.auth.models import AbstractUser


# Create your models here.

# 基类表
class Base(models.Model):
    create_time = models.DateTimeField(default=timezone.now, null=True)  # 添加数据时，自动写入当前添加时间
    is_delete = models.IntegerField(default=0)  # 逻辑关联删除字段({0:未删除,1:已删除})

    class Meta:
        abstract = True


# 用户表
class User(AbstractUser):
    username = models.CharField(max_length=200, unique=True)  # 用户名
    password = models.CharField(max_length=200)  # 密码
    email = models.CharField(max_length=200, null=True)  # 邮箱
    phone = models.CharField(max_length=11)  # 手机号
    photo = models.CharField(max_length=200, default="1.jpg")  # 头像
    sign = models.CharField(max_length=200, null=True)  # 用户简介
    occupation = models.CharField(max_length=200, null=True)  # 职业
    school = models.CharField(max_length=200, null=True)  # 学校/公司
    vid = models.IntegerField(default=1)  # 会员等级(1为普通用户，2为普通会员，3为高级会员)
    vip_start_time = models.DateTimeField(null=True)  # 开通会员时间
    vip_end_time = models.DateTimeField(null=True)  # 会员到期时间
    balance = models.IntegerField(default=0)  # 余额（单位：分）
    bean = models.IntegerField(default=0)  # 实验豆（单位：个）
    experience = models.IntegerField(default=0)  # 经验值
    weibo = models.IntegerField(null=True)  # 微博ID
    dingding = models.IntegerField(null=True)  # 钉钉ID
    code = models.CharField(max_length=8, null=True)  # 邀请码
    is_delete = models.IntegerField(default=0)  # 逻辑删除

    class Meta:
        db_table = "user"

# 优惠券表
class Coupon(Base):
    coupon = models.CharField(max_length=200)
    uid = models.IntegerField()
    price = models.IntegerField()
    end_time = models.DateTimeField(null=True)
    title = models.CharField(max_length=30, null=True)
    img = models.CharField(max_length=200, default="coupon.jpg")

    class Meta:
        db_table = 'coupon'


# 订单表
class Order(Base):
    uid = models.IntegerField()  # 购买用户
    order = models.CharField(max_length=16)  # 订单号
    price = models.IntegerField()  # 消费价格
    behoof = models.CharField(max_length=200, null=True)  # 消费记录
    is_succeed = models.IntegerField(default=0)  # 是否支付成功

    class Meta:
        db_table = "order"


# 会员表
class VIP(Base):
    grade = models.CharField(max_length=20, null=True)  # 会员等级（普通会员、高级会员）
    price = models.IntegerField(null=True)  # 会员价格（单位：分）
    exempt_cour = models.IntegerField(null=True)  # 免费课程   {0或空:不享受,1:享受}
    vip_cour = models.IntegerField(null=True)  # 会员课程   {0或空:不享受,1:享受}
    environment = models.IntegerField(null=True)  # 实验环境联网   {0或空:不享受,1:享受}
    save = models.IntegerField(null=True)  # 保存2个环境(30天)   {0或空:不享受,1:享受}
    client = models.IntegerField(null=True)  # 客户端     {0或空:不享受,1:享受}
    ssh = models.IntegerField(null=True)  # SSH直连   {0或空:不享受,1:享受}
    webide = models.IntegerField(null=True)  # WebIDE    {0或空:不享受,1:享受}
    discounts = models.IntegerField(null=True)  # 训练营优惠   {0或空:不享受,1:享受}
    exempt_study = models.IntegerField(null=True)  # 训练营课程免费学习   {0或空:不享受,1:享受}

    class Meta:
        db_table = "vip"


# 收藏表
class Collection(Base):
    uid = models.IntegerField()  # 用户id
    iid = models.IntegerField()  # 帖子id

    class Meta:
        db_table = "collection"


# 关注表
class Follow(Base):
    uid = models.IntegerField()  # 用户id
    cid = models.IntegerField()  # 课程id

    class Meta:
        db_table = "follow"


# 已学表
class Learn(Base):
    uid = models.IntegerField()  # 用户id
    cid = models.IntegerField()  # 课程id
    sid = models.IntegerField()  # 章节id

    class Meta:
        db_table = "learn"


# 已购买表
class Buy(Base):
    uid = models.IntegerField()  # 用户id
    cid = models.IntegerField()  # 课程id

    class Meta:
        db_table = "buy"


# 标签名表
class Tag(Base):
    name = models.CharField(max_length=200)  # 标签名

    class Meta:
        db_table = "tag"


# 课程标签表
class CourseTag(Base):
    tid = models.IntegerField()  # 标签id
    cid = models.IntegerField()  # 课程id

    class Meta:
        db_table = "coursetag"


# 课程表
class Course(Base):
    name = models.CharField(max_length=200)  # 课程名
    uid = models.IntegerField()  # 发布人id
    img = models.CharField(max_length=200, default="1.jpg")  # 封面
    desc = models.TextField()  # 简介
    video = models.CharField(max_length=200, null=True)  # 课程视频
    category = models.CharField(max_length=200, null=True)  # 所属分类(训练营、会员、高级会员、限免)
    price = models.IntegerField(default=0)  # 价格（单位：分）
    collect_num = models.IntegerField(default=0)  # 总收藏数
    is_online = models.IntegerField(default=0)  # 是否上线({0:未上线,1:即将上线})

    class Meta:
        db_table = "course"


# 课程章节表
class Section(Base):
    cid = models.IntegerField()  # 课程id
    section_name = models.CharField(max_length=200)  # 章节名
    video = models.CharField(max_length=200, null=True)  # 章节视频

    class Meta:
        db_table = "section"


# 帖子分类表
class QuestionType(Base):
    type = models.CharField(max_length=200)  # 模块分类名(课程评论、实验报告、实验问答、课程问答、

    # 交流讨论、技术分享、站内公告,路径)
    class Meta:
        db_table = "question_type"


# 帖子表
class Question(Base):
    title = models.CharField(max_length=200)  # 帖子标题
    content = models.TextField()  # 帖子内容
    type = models.CharField(max_length=40, default='course')  # 所属分类
    uid = models.IntegerField()  # 发布人
    cid = models.IntegerField(null=True)  # 课程id
    sid = models.IntegerField(null=True)  # 章节id
    top = models.IntegerField(default=0)  # 置顶值(值大的置顶)
    excellent = models.IntegerField(default=0)  # 精品(值大的是精品)
    examine = models.IntegerField(default=0)  # 查看总数
    favorite = models.IntegerField(default=0)  # 收藏总数

    class Meta:
        db_table = "question"


# 评论&回复表
class Comment(Base):
    content = models.CharField(max_length=500)  # 评论或回复内容
    uid = models.IntegerField()  # 评论人或回复人
    ques_id = models.IntegerField()  # 所属帖子
    reply = models.IntegerField(null=True)  # 自关联回复人
    favorate = models.IntegerField(default=0)  # 点赞总数

    class Meta:
        db_table = "comment"


# 点赞表
class Favorite(Base):
    uid = models.IntegerField()  # 点赞用户
    com_id = models.IntegerField()  # 评论或回复id
    # ques_id = models.IntegerField()                 # 点赞所属帖子
    receive_id = models.IntegerField()  # 收赞用户

    class Meta:
        db_table = "favorite"


# 报告表
class Report(Base):
    cid = models.IntegerField()  # 所属课程id
    sid = models.IntegerField()  # 所属章节id
    uid = models.IntegerField()  # 发布报告用户id
    content = models.TextField()  # 报告内容

    class Meta:
        db_table = "report"


# 路径表
class Path(Base):
    name = models.CharField(max_length=200)  # 路径名
    img = models.CharField(max_length=200, default="1.jpg")  # 路径头图
    desc = models.CharField(max_length=500)  # 路径简介
    section_sum = models.IntegerField()  # 总章节数
    add_sum = models.IntegerField(default=0)  # 添加人数
    study_time = models.IntegerField()  # 预计学习时长（单位：分钟）

    class Meta:
        db_table = "path"


# 路径阶段表
class Stage(Base):
    pid = models.IntegerField()  # 路径id
    stage = models.CharField(max_length=200)  # 阶段（如：第一阶段、第二阶段）
    stage_name = models.CharField(max_length=200)  # 阶段名（如：基础知识、编程语言）

    class Meta:
        db_table = "stage"


# 阶段课程表
class Stage_Course(Base):
    stage_id = models.IntegerField()  # 阶段id
    cid = models.IntegerField()  # 课程id

    class Meta:
        db_table = "stage_course"


# 路径收藏表
class PathUser(Base):
    path_id = models.IntegerField()
    uid = models.IntegerField()

    class Meta:
        db_table = 'path_user'


# 秒杀活动表
class Seckill(Base):
    title = models.CharField(max_length= 100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    img = models.CharField(max_length= 100)

    class Meta:
        db_table = 'seckill'

# 秒杀-课程关系表
class SecCourse(Base):
    sid = models.IntegerField()
    cid = models.IntegerField()

    class Meta:
        db_table = "sec_course"


