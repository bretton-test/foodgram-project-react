from django.urls import path, include
from rest_framework import routers

from users.views import CustomUserViewSet
from .views import IngredientViewSet, TagViewSet, RecipeViewSet

router_v1 = routers.DefaultRouter()
router_v1.register('ingredients', IngredientViewSet)
router_v1.register('tags', TagViewSet)
router_v1.register('recipes', RecipeViewSet)

router_v1.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
