from django.urls import path
from rest_framework.routers import SimpleRouter

from user_profile.views import ProfileUserViewSet, FriendshipRelationFromViewSet, FriendshipRelationToViewSet

router = SimpleRouter()

router.register('profile', ProfileUserViewSet)
router.register('friend-requests-from', FriendshipRelationFromViewSet, basename='friend-requests-from')
router.register('friend-requests-to', FriendshipRelationToViewSet, basename='friend-requests-to')

urlpatterns = router.urls
