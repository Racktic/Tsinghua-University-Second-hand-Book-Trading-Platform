from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import send_system_notification
from apps.accounts.models import User
from apps.chat.models import ChatRoom
from apps.sales.models import Item
from apps.chat.serializers import CreateChatRoomSerializer, ListUserChatRoomsSerializer

def send_notification_when_need_match(item, need):
    """
    检查物品是否满足需求，并向买家和卖家发送系统通知
    """
    buyer = need.user
    seller = item.user
    item_id = item.id
    # 向买家推送通知
    buyer_message = f"以为您的需求 '{need.title}' 匹配到新发布的商品！请点击下访链接跳转到商品页面并与卖家联系。"
    send_system_notification(buyer, buyer_message, 'chat_message')
    buyer_link_message = f"{item_id}"
    send_system_notification(buyer, buyer_link_message, 'item_id')

    # 向卖家推送通知
    seller_message = f"您的物品 '{item.title}' 与已有需求匹配！请查看您的聊天中是否有买家联系您。"
    send_system_notification(seller, seller_message, 'chat_message')

    return True

class CreateChatRoomView(APIView):
    """
    API 用于创建或获取聊天房间
    """
    def post(self, request, *args, **kwargs):
        serializer = CreateChatRoomSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            item = serializer.validated_data['item']
            buyer = serializer.validated_data['buyer']
            seller = item.user
            room_name = f"room_{item.id}_{seller.id}_{buyer.id}"

            # 检查房间是否已存在
            room, created = ChatRoom.objects.get_or_create(
                seller=seller,
                buyer=buyer,
                item=item,
                defaults={'room_name': room_name}
            )
            return Response({
                'message': 'Chat room created successfully.' if created else 'Chat room already exists.',
                'room_name': room.room_name,
                'created': created
            }, status=status.HTTP_200_OK)
        # 根据serializer返回的错误信息返回不同status code
        if serializer.errors.get('item_id'):
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ListUserChatRoomsView(APIView):
    """
    API 用于列出用户的聊天房间
    """
    def get(self, request, *args, **kwargs):
        serializer = ListUserChatRoomsSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            chat_rooms = ChatRoom.objects.filter(seller=user) | ChatRoom.objects.filter(buyer=user)
            chat_rooms_data = []
            for room in chat_rooms:
                room_data = {
                    'room_name': room.room_name,
                    'is_system_room': room.is_system_room,
                }
                if room.is_system_room:
                    # 系统房间只有 buyer 信息
                    room_data.update({
                        'buyer_email': room.buyer.email if room.buyer else "",
                        'buyer_id': room.buyer.id if room.buyer else None,
                    })
                else:
                    room_data.update({
                        'seller_email': room.seller.email if room.seller else "",
                        'buyer_email': room.buyer.email if room.buyer else "",
                        'seller_id': room.seller.id if room.seller else None,
                        'buyer_id': room.buyer.id if room.buyer else None,
                    })
                chat_rooms_data.append(room_data)
            return Response(chat_rooms_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)