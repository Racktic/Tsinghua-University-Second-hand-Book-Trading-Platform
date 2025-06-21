from rest_framework import serializers
from apps.sales.models import Item
from apps.accounts.models import User
from apps.sales.serializers import verify_user_is_online

class CreateChatRoomSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    buyer_email = serializers.EmailField()

    def validate(self, data):
        item_id = data.get('item_id')
        buyer_email = data.get('buyer_email')

        # 验证物品是否存在
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            raise serializers.ValidationError({'item_id': ['Item does not exist.']})
        data['item'] = item
        seller = item.user
        data['seller'] = seller
        request = self.context.get('request')
        online_user = verify_user_is_online(None, request)
        if online_user.email != buyer_email and online_user.email != seller.email:
            raise serializers.ValidationError({'buyer_email': ['You are not authorized to create a chat room for this item.']})
        buyer = User.objects.filter(email=buyer_email).first()
        if not buyer:
            raise serializers.ValidationError({'buyer_email': ['Buyer does not exist.']})
        data['buyer'] = buyer
        return data

class ListUserChatRoomsSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate(self, data):
        # 验证用户是否在线
        request = self.context['request']
        email = data.get('email')
        data['user'] = verify_user_is_online(email, request)

        return data
