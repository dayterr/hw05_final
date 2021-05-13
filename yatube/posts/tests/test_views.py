import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Follow, Group, Post, User


class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тест',
            slug='test-group',
            description='Это тестовая группа'
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            text='Это текст тестового поста. Кстати, привет, мир!',
            group=cls.group,
            author=cls.user,
            image=uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.user)

    def check_post_correct_data(self, context, is_page):
        """Вспомогательный метод для проверки атрибутов поста."""
        if is_page:
            self.assertIn('page', context)
            post = context['page'].object_list[0]
        else:
            self.assertIn('post', context)
            post = context['post']
        self.assertEqual(PostsPagesTests.post.text, post.text)
        self.assertEqual(PostsPagesTests.post.group, post.group)
        self.assertEqual(PostsPagesTests.post.pub_date, post.pub_date)
        self.assertEqual(PostsPagesTests.post.author, post.author)
        self.assertEqual(PostsPagesTests.post.image, post.image)

    def test_pages_correct_templates(self):
        templates_pages_names = (
            ('index.html', 'index', None),
            ('post.html', 'post', (PostsPagesTests.user.username,
                                   PostsPagesTests.post.id,)),
            ('group.html', 'group_view', (PostsPagesTests.group.slug,)),
            ('profile.html', 'profile', (PostsPagesTests.user.username,)),
            ('post_new.html', 'new_post', None),
            ('post_new.html', 'post_edit', (PostsPagesTests.user.username,
                                            PostsPagesTests.post.id,)),
        )
        for template, reverse_name, args in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse(reverse_name,
                                                              args=args))
                self.assertTemplateUsed(response, 'posts/' + template)

    def test_index_correct_context(self):
        response = self.client.get(reverse('index'))
        self.check_post_correct_data(response.context, True)

    def test_group_correct_context(self):
        response = self.client.get(reverse(
            'group_view', kwargs={'slug': PostsPagesTests.group.slug}
        ))
        self.assertIn('group', response.context)
        group_from_context = response.context['group']
        self.assertEqual(PostsPagesTests.group.title, group_from_context.title)
        self.assertEqual(PostsPagesTests.group.description,
                         group_from_context.description)
        self.check_post_correct_data(response.context, True)

    def test_group_unused_correct_context(self):
        group_unused = Group.objects.create(
            title='Контрольная',
            slug='test-unused'
        )
        response = self.client.get(reverse(
            'group_view', kwargs={'slug': group_unused.slug}
        ))
        self.assertIn('page', response.context)
        posts = response.context['page'].object_list
        self.assertNotIn(PostsPagesTests.post, posts)

    def test_profile_correct_context(self):
        response = self.client.get(reverse(
            'profile', kwargs={
                'username': PostsPagesTests.user.username,
            })
        )
        self.assertIn('author', response.context)
        self.assertEqual(PostsPagesTests.user, response.context['author'])
        self.check_post_correct_data(response.context, True)

    def test_post_correct_context(self):
        response = self.client.get(reverse(
            'post', kwargs={
                'username': PostsPagesTests.post.author,
                'post_id': PostsPagesTests.post.id,
            })
        )
        self.assertIn('author', response.context)
        self.assertEqual(PostsPagesTests.user, response.context['author'])
        self.check_post_correct_data(response.context, False)

    def test_paginator(self):
        objs = (Post(text=f'Какой-то пост {i}',
                     group=PostsPagesTests.group) for i in range(14))
        Post.objects.bulk_create(objs)
        all_posts = PostsPagesTests.group.posts.count()
        for page in range(1, 3):
            with self.subTest(page=page):
                response = self.client.get(reverse(
                    'group_view', args=[PostsPagesTests.group.slug]
                ), data={'page': page})
                self.assertIn('page', response.context)
                page_from_view = response.context['page']
                page_posts = page_from_view.object_list
                if page_from_view.has_next():
                    self.assertEqual(len(page_posts), settings.POSTS_PER_PAGE)
                else:
                    last_page = all_posts % settings.POSTS_PER_PAGE
                    self.assertEqual(len(page_posts), last_page)

    def test_new_post_correct_context(self):
        response = self.authorized_client.get(reverse('new_post'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIn('is_new', response.context)
        self.assertIs(response.context['is_new'], True)

    def test_edit_post_correct_context(self):
        args = (PostsPagesTests.user.username, PostsPagesTests.post.id)
        response = self.authorized_client.get(reverse('post_edit', args=args))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIn('is_new', response.context)
        self.assertIsInstance(response.context['is_new'], bool)
        self.assertFalse(response.context['is_new'])

    def test_cache(self):
        response = self.client.get(reverse('index'))
        Post.objects.create(
            text='Ещё один пост',
            group=PostsPagesTests.group,
        )
        response2 = self.client.get(reverse('index'))
        cont = response.content.decode()
        cont2 = response2.content.decode()
        self.assertEqual(cont, cont2)
        cache.clear()

    def test_auth_follow_unfollow(self):
        amount = Follow.objects.count()
        followed = User.objects.create(username='interesnyuser')
        self.authorized_client.get(reverse('profile_follow',
                                           kwargs={'username': followed.username}))
        self.assertEqual(Follow.objects.count(), amount + 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, followed)
        self.assertEqual(follow.user, PostsPagesTests.user)
        self.authorized_client.get(reverse('profile_unfollow',
                                           kwargs={'username': followed.username}))
        self.assertEqual(Follow.objects.count(), amount)

    def test_follow_index(self):
        interesting = User.objects.create(username='interesnyuser')
        boring = User.objects.create(username='otheruser')
        self.authorized_client.get(reverse('profile_follow',
                                           kwargs={'username': interesting.username}))
        post_in = Post.objects.create(
            text='Пост появится в ленте',
            author=interesting,
        )
        post_not_in = Post.objects.create(
            text='Этого поста в лнте не будет',
            author=boring,
        )
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertIn('page', response.context)
        self.assertIn(post_in, response.context['page'].object_list)
        self.assertNotIn(post_not_in, response.context['page'].object_list)
