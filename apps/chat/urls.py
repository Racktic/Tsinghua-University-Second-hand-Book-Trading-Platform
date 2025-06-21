from django.urls import path
from .views import CreateChatRoomView, ListUserChatRoomsView

urlpatterns = [
    path('create-room', CreateChatRoomView.as_view(), name='create-room'),
    path('check-rooms', ListUserChatRoomsView.as_view(), name='check-rooms'),
]