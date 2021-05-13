from django.test import TestCase

from posts.models import Group, Post


class ModelTest(TestCase):

    def test_names(self):
        group = Group.objects.create(
            title='Тестовый пост',
        )
        post = Post.objects.create(
            text='Это текст тестового поста. Кстати, привет, мир!',
        )
        objects_names = {
            group: group.title,
            post: post.text[:15],
        }
        for obj, name in objects_names.items():
            with self.subTest(obj=str(obj), name=name):
                self.assertEqual(str(obj), name)
