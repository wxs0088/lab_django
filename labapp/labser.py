# 导入数据库表
from labapp.models import *
# 导入序列化包
from rest_framework import serializers

# 课程标签序列化器
class CourseTagSer(serializers.ModelSerializer):

    class Meta:
        model = CourseTag
        fields = "__all__"

# 用户表序列化器
class UserSer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"

# 优惠券表序列化器
class CouponSer(serializers.ModelSerializer):

    class Meta:
        model = Coupon
        fields = "__all__"

# 订单表序列化器
class OrderSer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = "__all__"


# 会员表序列化器
class VIPSer(serializers.ModelSerializer):

    class Meta:
        model = VIP
        fields = "__all__"


# 收藏表序列化器
class CollectSer(serializers.ModelSerializer):

    class Meta:
        model = Collection
        fields = "__all__"


# 关注表序列化器
class FollowSer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = "__all__"


# 已学表序列化器
class LearnSer(serializers.ModelSerializer):

    class Meta:
        model = Learn
        fields = "__all__"


# 已购买表序列化器
class BuySer(serializers.ModelSerializer):

    class Meta:
        model = Buy
        fields = "__all__"


# 课程标签表序列化
class TagSer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = "__all__"


# 课程表序列化器
class CourseSer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


# 课程章节表序列化器
class SectionSer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = "__all__"


# 帖子分类表序列化器
class QuestionTypeSer(serializers.ModelSerializer):
    class Meta:
        model = QuestionType
        fields = "__all__"


# 帖子表序列化器
class QuestionSer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


# 评论&回复表序列化器
class CommentSer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"


# 点赞表序列化器
class FavoriteSer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = "__all__"


# 报告表序列化器
class ReportSer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"


# 路径表序列化器
class PathSer(serializers.ModelSerializer):
    class Meta:
        model = Path
        fields = "__all__"


# 路径阶段表序列化器
class StageSer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = "__all__"


# 阶段课程表序列化器
class Stage_CourseSer(serializers.ModelSerializer):
    class Meta:
        model = Stage_Course
        fields = "__all__"

# 课程标签联表序列化器
class CourseTagSer(serializers.ModelSerializer):
    class Meta:
        model = CourseTag
        fields = "__all__"