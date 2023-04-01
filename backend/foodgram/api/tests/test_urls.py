from rest_framework import status
from rest_framework.authtoken.models import Token

from api.serializers import (
    RecipeSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeIngredientsSerializer,
)
from api.tests.fixtures import RecipeTest, get_objects_instances_to_test
from recipes.models import Recipe, Tag, Ingredient
from users.models import User, Follow
from users.serializers import SubscriptionSerializer

RECIPE_TO_TEST = 2


class PostURLTests(RecipeTest):
    """Url Pages Tests_Class"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='HasNoName',
            email='HasNoEmail@mail.com',
            first_name='HasNoFirstName',
            last_name='HasNoLastName',
        )
        cls.another_user = User.objects.create_user(
            username='HasNoName1',
            email='HasNoEmail1@mail.com',
            first_name='HasNoFirstName1',
            last_name='HasNoLastName1',
        )
        cls.token = Token.objects.create(user=cls.user)
        cls.another_token = Token.objects.create(user=cls.another_user)

        get_objects_instances_to_test(RECIPE_TO_TEST)
        Follow.objects.create(user=cls.another_user, author=cls.user)

    def setUp(self):
        self.get_client()

    def recipe_ingredient_data_test(self, data, msg):
        obj = Recipe.objects.first()
        serializer = RecipeIngredientsSerializer(
            obj.recipe_ingredient.all(), many=True
        )
        self.assertEqual(data, serializer.data, msg)

    def ingredient_test(self, client, url, many=False):
        response = client.get(url)
        data = response.json()[0] if many else response.json()
        self.ingredient_data_test(data, 'tag test failed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def ingredient_data_test(self, data, msg):
        ingredient = Ingredient.objects.first()
        serializer = IngredientSerializer(ingredient)
        self.assertEqual(data, serializer.data, msg)

    def tag_data_test(self, data, msg):
        tag = Tag.objects.first()
        serializer = TagSerializer(tag)
        self.assertEqual(data, serializer.data, msg)

    def tag_test(self, client, url, many=False):
        response = client.get(url)
        data = response.json()[0] if many else response.json()
        self.tag_data_test(data, 'tag test failed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def recipe_test(self, client, user, url, many=False):
        response = client.get(url)
        recipe = Recipe.objects.first()
        request = response.wsgi_request
        if user:
            request.user = self.user

        serializer = RecipeSerializer(recipe, context={'request': request})
        data = response.json().get('results')[0] if many else response.json()

        self.tag_data_test(data.get('tags')[0], 'recipe_tag_test failed')
        self.recipe_ingredient_data_test(
            data.get('ingredients'), 'recipe_ingredients_test failed'
        )
        self.assertEqual(data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_recipe_list_url(self):
        self.recipe_test(
            self.authorized_client, self.user, '/api/recipes/', True
        )

    def test_anonymous_get_recipe_list_url(self):
        self.recipe_test(self.client, None, '/api/recipes/', True)

    def test_get_recipe__url(self):
        self.recipe_test(
            self.authorized_client,
            self.user,
            f'/api/recipes/{RECIPE_TO_TEST}/',
            False,
        )

    def test_anonymous_get_recipe_url(self):
        self.recipe_test(self.client, None, f'/api/recipes/{RECIPE_TO_TEST}/')

    def test_get_tag_list_url(self):
        self.tag_test(self.authorized_client, '/api/tags/', many=True)

    def test_anonymous_get_tag_list_url(self):
        self.tag_test(self.authorized_client, '/api/tags/', many=True)

    def test_get_tag_url(self):
        self.tag_test(self.authorized_client, '/api/tags/1/')

    def test_anonymous_get_tag_url(self):
        self.tag_test(self.client, '/api/tags/1/')

    def test_get_ingredient_list_url(self):
        self.ingredient_test(
            self.authorized_client, '/api/ingredients/', many=True
        )

    def test_anonymous_get_ingredient_list_url(self):
        self.ingredient_test(self.client, '/api/ingredients/', many=True)

    def test_get_ingredient_url(self):
        self.ingredient_test(self.authorized_client, '/api/ingredients/1/')

    def test_anonymous_get_ingredient_url(self):
        self.ingredient_test(self.client, '/api/ingredients/1/')

    def test_get_subscription_url(self):
        response = self.another_auth_client.get(
            '/api/users/subscriptions/',
            HTTP_AUTHORIZATION='Token {}'.format(self.another_token),
        )
        data = response.json().get('results')[0]
        request = response.wsgi_request
        request.user = self.another_user
        serializer = SubscriptionSerializer(
            self.user, context={'request': request}
        )
        self.assertEqual(len(data.get('recipes')), RECIPE_TO_TEST)
        self.assertEqual(data.get('recipes_count'), RECIPE_TO_TEST)
        self.assertEqual(data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
