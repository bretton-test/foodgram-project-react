from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from api.filters import RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import IsOwnerOrStaffOrReadOnly
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    RecipeCreateUpdateSerializer,
    RecipeFavoriteSerializer,
)
from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
)
from .utils import (
    create_pdf_from_queryset,
    create_or_delete_record,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerOrStaffOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer

        return RecipeSerializer

    @action(detail=True, methods=('post', 'delete'))
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        in_favorite = recipe.in_favorite.filter(user=self.request.user)
        return create_or_delete_record(
            request=request,
            record=in_favorite,
            serializer_data=RecipeFavoriteSerializer(recipe).data,
            params={'recipe': recipe},
        )

    @action(detail=True, methods=('post', 'delete'))
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        in_shopping_list = recipe.in_shopping_list.filter(
            user=self.request.user
        )
        return create_or_delete_record(
            request=request,
            record=in_shopping_list,
            serializer_data=RecipeFavoriteSerializer(recipe).data,
            params={'recipe': recipe},
        )

    @action(
        detail=False, methods=('get',), permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        # log = logging.getLogger('django.db.backends')
        # log.setLevel(logging.DEBUG)
        # log.addHandler(logging.StreamHandler())
        user = self.request.user
        recipes = user.shopping_list.values('recipe__id')

        buy_list = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit__name')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        pdf_file = create_pdf_from_queryset(buy_list, user.username)
        return FileResponse(
            pdf_file, as_attachment=True, filename='buy_list.pdf'
        )
