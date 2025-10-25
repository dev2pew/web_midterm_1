from rest_framework_nested import routers

from .views import PostViewSet, ThreadViewSet

router = routers.DefaultRouter()
router.register(r"threads", ThreadViewSet, basename="thread")

threads_router = routers.NestedDefaultRouter(router, r"threads", lookup="thread")
threads_router.register(r"posts", PostViewSet, basename="thread-posts")

urlpatterns = router.urls + threads_router.urls
