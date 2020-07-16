import time
import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
import redis
import base64
from django.http.request import QueryDict
import paramiko
import socket
from threading import Thread
import time
import os
from six import StringIO
from django.conf import settings


def get_key_obj(pkeyobj, pkey_file=None, pkey_obj=None, password=None):
    if pkey_file:
        with open(pkey_file) as fo:
            try:
                pkey = pkeyobj.from_private_key(fo, password=password)
                return pkey
            except:
                pass
    else:
        try:
            pkey = pkeyobj.from_private_key(pkey_obj, password=password)
            return pkey
        except:
            pkey_obj.seek(0)


class SSHBridge(object):
    """
    桥接WebSocket和ssh
    参考：https://blog.51cto.com/hongchen99/2336087
    """

    def __init__(self, websocket, simpleuser):
        self.websocket = websocket
        self.simpleuser = simpleuser

    def connect(self, host, user, pwd=None, key=None, port=22, timeout=6, term='xterm', pty_width=80, pty_height=24):
        """
        建立SSH连接，放在 self.ssh_channel 通道中，之后直接在通道中交互数据
        :param host:
        :param user:
        :param pwd:
        :param key:
        :param port:
        :param timeout:
        :param term:
        :param pty_width:
        :param pty_height:
        :return:
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if key:
                # 密钥方式认证
                pkey = get_key_obj(paramiko.RSAKey, pkey_obj=key, password=pwd) or \
                       get_key_obj(paramiko.DSSKey, pkey_obj=key, password=pwd) or \
                       get_key_obj(paramiko.ECDSAKey, pkey_obj=key, password=pwd) or \
                       get_key_obj(paramiko.Ed25519Key, pkey_obj=key, password=pwd)
                ssh_client.connect(username=user, hostname=host, port=port, pkey=pkey, timeout=timeout)
            else:
                ssh_client.connect(hostname=host, port=port, username=user, password=pwd, timeout=timeout)
        except Exception as e:
            # pri00nt(e)
            message = json.dumps({'flag': 'fail', 'message': str(e)})
            self.websocket.send_message_or_team(message)
            return

        transport = ssh_client.get_transport()

        """
        另一种方式建立通道
        transport = paramiko.Transport((host, port,))
        transport.start_client()
        transport.auth_password(username=user, password=pwd)
        """

        # 打开一个通道
        self.ssh_channel = transport.open_session()
        # 获取一个终端
        self.ssh_channel.get_pty(term=term, width=pty_width, height=pty_height)
        # 激活终端，这样就可以登录到终端了，就和我们用类似于xshell登录系统一样
        self.ssh_channel.invoke_shell()

        # 获取ssh连接主机后的返回内容，例如Linux，会显示上次登录等信息，把这些信息通过WebSocket显示到Web终端。
        # 连接建立一次，之后交互数据不会再进入该方法
        for i in range(2):
            recv = self.ssh_channel.recv(1024).decode('utf-8')
            message = json.dumps({'flag': 'msg', 'message': recv})
            # pri00nt('【WS  --websocket-->  Web】建立SSH通道后，返回欢迎信息：', message)
            self.websocket.send_message_or_team(message)

    def close(self):
        message = {'flag': 0, 'message': '关闭WebSocket和SSH连接'}
        # 向WebSocket发送一个关闭消息
        self.websocket.send_message_or_team(json.dumps(message))

        try:
            # 关闭ssh通道
            self.ssh_channel.close()
            # 关闭WebSocket连接
            self.websocket.close()
        except BaseException as e:
            # pri00nt('关闭WebSocket和SSH连接产生异常：', e)
            pass

    def _ws_to_ssh(self, data):
        """
        尝试发送数据到ssh通道，产生异常则关闭所有连接
        """
        try:
            # pri00nt('【Func  --paramiko-->  SSH】WebSocket中的数据发送数据到ssh通道：', data)
            self.ssh_channel.send(data)
        except OSError as e:
            # pri00nt(e)
            self.close()

    def _ssh_to_ws(self):
        try:
            # while True:
            while not self.ssh_channel.exit_status_ready():
                data = self.ssh_channel.recv(1024).decode('utf-8')
                # pri00nt('【SSH  --paramiko-->  Func】获取ssh通道返回的数据：', data)
                if len(data) != 0:
                    message = {'flag': 'msg', 'message': data}
                    # pri00nt('【WS --websocket-->  Web】通过WebSocket把信息发回前端，显示到Web终端：', message)
                    self.websocket.send_message_or_team(json.dumps(message))
                else:
                    break

        except:
            self.close()

    def shell(self, data):
        Thread(target=self._ws_to_ssh, args=(data,)).start()
        Thread(target=self._ssh_to_ws).start()
        """
        t1 = Thread(target=self._ws_to_ssh, args=(data,))
        t1.setDaemon(True)
        t1.start()
        t2 = Thread(target=self._ssh_to_ws)
        t2.setDaemon(True)
        t2.start()
        """

    def resize_pty(self, cols, rows):
        self.ssh_channel.resize_pty(width=cols, height=rows)


class WebsshConsumer(WebsocketConsumer):
    """
    1、xterm.js 在浏览器端模拟 shell 终端, 监听用户输入通过 websocket 将用户输入的内容上传到 django
    2、django 接受到用户上传的内容, 将用户在前端页面输入的内容通过 paramiko 建立的 ssh 通道上传到远程服务器执行
    3、paramiko 将远程服务器的处理结果返回给 django
    4、django 将 paramiko 返回的结果通过 websocket 返回给用户
    5、xterm.js 接收 django 返回的数据并将其写入前端页面
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_id = 1
        self.simple_user = 'root'
        self.is_team = False
        self.team_name = ''

    def connect(self):
        """
        建立WebSocket连接，并实例化SSHBridge类，在这个对象中建立SSH连接，放在 self.ssh_channel 通道中
        :return:
        """
        # pri00nt('【Web  --websocket-->  WS】建立WebSocket通道，当前连接用户：', self.simple_user)

        self.accept()

        # WebSocket连接成功后，连接ssh
        query_string = self.scope.get('query_string')
        ws_args = QueryDict(query_string=query_string, encoding='utf-8')
        # # pri00nt(ws_args)
        # <QueryDict: {'user': ['admin'], 'host': ['192.168.96.20'], 'port': ['22'], 'auth': ['pwd'], 'pwd': ['ZGphbmdvYWRtaW4='], 'key': [''], 'width': ['113'], 'height': ['43']}>
        # 根据参数判断是否是协作
        team = ws_args.get('team')
        if team:
            self.is_team = True
            self.team_name = "team_{}".format(self.host_id)  # 加到这个通道组
            async_to_sync(self.channel_layer.group_add)(
                self.team_name,
                self.channel_name
            )
            # 用户连接时，同一群组发送消息
            self.send_message_or_team(json.dumps({'flag': 'user', 'message': '用户 {} 已连接本终端'.format(self.simple_user)}))

        width = ws_args.get('width')
        height = ws_args.get('height')
        width = int(500)
        height = int(500)  # ssh连接要求int类型：required argument is an integer

        ssh_connect_dict = {}

        if self.host_id:
            # 指定连接
            # pri00nt('连接的服务器id：', self.host_id)
            if int(self.host_id) == 1:
                ssh_connect_dict = {
                    'host': '120.26.175.79',
                    'user': 'root',
                    'port': 22,
                    'timeout': 30,
                    'pty_width': width,
                    'pty_height': height,
                    'pwd': 'AAAAaaaa0'
                }
            else:
                self.close()
                return

        else:
            user = ws_args.get('user')
            host = ws_args.get('host')
            port = ws_args.get('port')
            port = int(port)
            auth = ws_args.get('auth')
            pwd = ws_args.get('pwd')
            if pwd:
                pwd = base64.b64decode(pwd).decode('utf-8')
            sshkey_filename = ws_args.get('sshkey_filename')

            ssh_connect_dict = {
                'host': host,
                'user': user,
                'port': port,
                'timeout': 30,
                'pty_width': width,
                'pty_height': height,
                'pwd': pwd
            }

            if auth == 'key':
                sshkey_file = os.path.join(settings.MEDIA_ROOT, 'sshkey', sshkey_filename)
                if not os.path.exists(sshkey_file):
                    self.send(json.dumps({'flag': 'error', 'message': '密钥文件不存在'}))

                else:
                    try:
                        f = open(sshkey_file, 'r', encoding='utf-8')
                        key = f.read()
                        string_io = StringIO()
                        string_io.write(key)
                        string_io.flush()
                        string_io.seek(0)
                        ssh_connect_dict['key'] = string_io

                        os.remove(sshkey_file)  # 用完之后删除key文件
                    except BaseException as e:
                        # pri00nt('打开密钥文件出错', e)
                        pass

        # 建立SSH连接
        self.ssh = SSHBridge(websocket=self, simpleuser=self.simple_user)
        # pri00nt('【WS  --SSHBridge-->  SSH】连接SSH参数：', ssh_connect_dict)
        self.ssh.connect(**ssh_connect_dict)

    def disconnect(self, close_code):
        # 断开连接
        # pri00nt('用户 {} 断开WebSocket连接，断开SSH连接'.format(self.simple_user))
        try:
            if self.is_team:
                # 用户连接时，同一群组发送消息
                self.send_message_or_team(json.dumps({'flag': 'user', 'message': '用户 {} 已断开本终端'.format(self.simple_user)}))
                # 退出群组
                async_to_sync(self.channel_layer.group_discard)(
                    self.team_name,
                    self.channel_name
                )
            self.ssh.close()
        except BaseException as e:
            pass

    def receive(self, text_data=None, bytes_data=None):
        # 从WebSocket中接收消息
        print(text_data)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname='120.26.175.79',port=22,username='root',password='AAAAaaaa0'
        )
        stdin, stdout, stderr = client.exec_command(text_data)
        ssh_message = stdout.read().decode('utf-8')
        print(type(ssh_message))
        my_message = ssh_message.replace('\n','\r\n')
        self.send_message_or_team(my_message)

    def send_message_or_team(self, message):
        if self.is_team:
            async_to_sync(self.channel_layer.group_send)(
                self.team_name,
                {
                    'type': 'team_message',
                    'message': message
                }
            )
        else:
            self.send(message)

    def team_message(self, event):
        message = event['message']

        # 发送消息到WebSocket
        self.send(message)












pool = redis.ConnectionPool(
  host="120.26.175.79",
  port=6379,
  max_connections=10,
  decode_response=True,
)
conn = redis.Redis(connection_pool=pool, decode_responses=True)
 
 
class ChatConsumer(AsyncWebsocketConsumer):
  async def connect(self, ):
    self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
    self.room_group_name = "chat_%s" % self.room_name
    print(self.room_name)
    await self.channel_layer.group_add(
      self.room_group_name,
      self.channel_name,
    )
    await self.accept()
 
  async def disconnect(self, close_code):
    print("close_code: ", close_code)
    await self.channel_layer.group_discard(
      self.room_group_name,
      self.channel_name
    )
 
  async def receive(self, text_data=None, bytes_data=None):
    print(text_data)
    text_data_json = json.loads(text_data)
    message = text_data_json["message"]
    to_user = text_data_json["to_user"]
    title = text_data_json["title"]
    print("receive_message：", message)
    print("receive_to_user：", to_user)
    print("receive_title：", title)
    # 这里添加一条判定,如果to_user获取成功,则将信息存储到对应用户的信息表中,如果to_user获取失败,则默认这条信息为群发,在信息表中给每一个用户添加这条信息
    # 这个判断是为了应对群发与单发的处理,因目前尚未决定信息表的相应字段设计,所以暂时不写

    '''
    if to_user == 'all_user':
        users = User.objects.all()
        users_id_list = [user.id for user in users]
        for uid in users_id_list:
            信息表(uid=uid, title=title, message=message).save()
    else:
        user = User.objects.filter(username=to_user).first()
        信息表(uid=user.id, title=title, message=message).save()
        pass
    '''
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        "type": "chat_message",
        "message": message
      }
    )
 
  async def chat_message(self, event):
    receive_message = event["message"]
    response_message = "你发送的数据为 :" + receive_message
    await self.send(text_data=json.dumps({
      "message": response_message
    }))
 
 
class PushMessage(WebsocketConsumer):
 
  def connect(self):
    self.room_group_name = self.scope["url_route"]["kwargs"]["room_name"]
    async_to_sync(self.channel_layer.group_add)(
      self.room_group_name,
      self.channel_name
    )
    self.accept()
 
  def disconnect(self, code):
    async_to_sync(self.channel_layer.group_discard)(
      self.room_group_name,
      self.channel_name
    )
 
  def push_message(self, event):
    """
    主动推送
    :param event:
    :return:
    """
    print(event, type(event))
    while True:
      time.sleep(2)
      msg = time.strftime("%Y-%m-%d %H:%M:%S") + "--- room_name: %s" % event["room_name"]
      self.send(text_data=json.dumps(
        {"message": msg}
      ))