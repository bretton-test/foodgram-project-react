from django.db.models import Case, F, FloatField, Q, Sum, Value, When
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from api.filters import RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import IsOwnerOrStaffOrReadOnly
from api.serializers import (
    IngredientSerializer, RecipeCreateUpdateSerializer,
    RecipeFavoriteSerializer, RecipeSerializer, TagSerializer,
)
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

from .utils import create_or_delete_record, create_pdf_from_queryset


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer

    def get_queryset(self):
        string = self.request.query_params.get('name', None)
        if string is not None:
            return (
                Ingredient.objects.select_related('measurement_unit')
                .filter(
                    Q(name__istartswith=string) | Q(name__icontains=string)
                )
                .annotate(
                    k1=Case(
                        When(name__istartswith=string, then=Value(1.0)),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                    k2=Case(
                        When(name__icontains=string, then=Value(1.0)),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                    rank=F("k1") + F("k2"),
                )
                .distinct()
                .order_by('-rank', 'name')
            )
        return Ingredient.objects.all()


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
