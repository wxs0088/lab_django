# Create your views here.
from rest_framework_jwt.settings import api_settings
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    phone = serializers.CharField()
    token = serializers.CharField(read_only=True)

    def create(self, data):
        user = User.objects.create(**data)
        user.set_password(data.get('password'))
        user.save()

        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)


        user.token = token
        return user