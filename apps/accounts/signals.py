from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import User
from apps.chat.models import ChatRoom

@receiver(post_save, sender=User)
def create_system_room(sender, instance, created, **kwargs):
    if created:
        ChatRoom.objects.get_or_create(
            room_name=f"system_room_{instance.id}",
            is_system_room=True,
            buyer=instance
        )