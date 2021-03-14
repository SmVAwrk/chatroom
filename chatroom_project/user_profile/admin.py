from django.contrib import admin

from user_profile.models import UserProfile, FriendshipRelation


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(FriendshipRelation)
class FriendshipRelationAdmin(admin.ModelAdmin):
    pass
