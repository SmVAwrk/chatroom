from django.contrib import admin

from chat_app.models import Room, Message, RoomInvite


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    pass


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass


@admin.register(RoomInvite)
class RoomInviteAdmin(admin.ModelAdmin):
    pass
