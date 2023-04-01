from django.core.validators import MinValueValidator
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.utils import create_recipe_ingredients
from recipes.models import Ingredient, Tag, Recipe, RecipeIngredient
from users.serializers import CustomUserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.SlugRelatedField(
        read_only=True, slug_field='name'
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit.name

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        serializer = RecipeIngredientsSerializer(
            obj.recipe_ingredient.all(), many=True
        )
        return serializer.data

    def get_is_favorited(self, obj):
        user = self.context['request'].user

        return (
            obj.in_favorite.filter(user_id=user.id).exists()
            if not user.is_anonymous
            else False
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user

        return (
            obj.in_shopping_list.filter(user_id=user.id).exists()
            if not user.is_anonymous
            else False
        )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class CreateUpdateRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
        many=False,
        required=True,
    )
    amount = serializers.IntegerField(
        validators=(MinValueValidator(1, message='amount 1 min.'),)
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    ingredients = CreateUpdateRecipeIngredientSerializer(many=True)
    cooking_time = serializers.IntegerField(
        validators=(MinValueValidator(1, message='cooking_time >= 1 min'),)
    )
    image = Base64ImageField()

    def validate(self, data):
        recipe_id = self.initial_data.get('id')
        user = self.context.get('request').user
        name = self.initial_data.get('name')
        ingredients_value = data.get('ingredients', None)
        if not ingredients_value:
            raise serializers.ValidationError('ingredients is required')
        ingredients = [item['ingredient'] for item in ingredients_value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'A recipe cannot have two of the same ingredient.'
            )

        if not data.get('tags', None):
            raise serializers.ValidationError('tags is required')

        if user.recipes.exclude(pk=recipe_id).filter(name=name).exists():
            raise serializers.ValidationError('A recipe name already exists')

        return data

    @transaction.atomic
    def create(self, validated_data):

        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        create_recipe_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()
        create_recipe_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        )

        return serializer.data

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
