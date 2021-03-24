from rest_framework.routers import SimpleRouter

from user_profile.views import ProfileUserViewSet, FriendshipRelationFromMeViewSet, FriendshipRelationToMeViewSet

router = SimpleRouter()

router.register('profile', ProfileUserViewSet, basename='profile')
router.register('friend-requests-from-me', FriendshipRelationFromMeViewSet, basename='friend-requests-from-me')
router.register('friend-requests-to-me', FriendshipRelationToMeViewSet, basename='friend-requests-to-me')

urlpatterns = router.urls
