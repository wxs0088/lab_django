from django.shortcuts import render
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
 
 
def index(request):
  return render(request, "chat/index.html")
 
 
def room(request, room_name):
  return render(request, "chat/room.html", {"room_name": room_name})

 
def pushRedis(request):
  room = request.GET.get("room")
  print(room)
 
  def push(msg):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
      room,
      {"type": "push.message", "message": msg, "room_name": room}
    )
 
  push("推送测试", )
  return JsonResponse({"1": 1})