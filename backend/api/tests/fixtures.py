import random
import shutil
import sys
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.test import override_settings

from recipes.models import Tag, Recipe, RecipeTag, RecipeIngredient, Ingredient, Unit

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


def image(image_name: str):
    """Return small in memory image"""
    return SimpleUploadedFile(
        name=image_name, content=small_gif, content_type='image/gif'
    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RecipeTest(TestCase):
    """Class to test post creation and editing"""

    authorized_client: Client
    another_auth_client: Client
    user = None
    another_user = None

    def get_client(self):
        """Returns a client instance"""
        if self.user:
            self.authorized_client = Client()
            self.authorized_client.force_login(self.user)

        if self.another_user:
            self.another_auth_client = Client()
            self.another_auth_client.force_login(self.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


def get_objects_instances_to_test(number_of_recipes=1):
    """create test data objects"""
    try:
        measurement_unit = Unit.objects.create(name='шт.')
        for rec_num in range(10):
            Ingredient.objects.create(name=f'ingredient{rec_num}', measurement_unit=measurement_unit)

        if not Tag.objects.exists():
            Tag.objects.create(
                name='Завтрак', color='#E26C2D', slug='breakfast'
            )
            Tag.objects.create(name='Обед', color='#E26C2D', slug='lunch')
            Tag.objects.create(name='Ужин', color='#E26C2D', slug='dinner')

        for rec_num in range(number_of_recipes):
            recipe = Recipe.objects.create(
                name=f'Recipe # {rec_num}',
                text=f'Тестовый рецепт {rec_num}',
                cooking_time=random.randint(1, 25),
                image=image(f'image#{rec_num}'),
                author=User.objects.first(),
            )

            RecipeTag.objects.create(
                recipe=recipe, tag=Tag.objects.first(),
            )

            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=Ingredient.objects.first(),

                amount=random.randint(1, 200),
            )



    except Exception as error:
        print(error)
