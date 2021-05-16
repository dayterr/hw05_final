import re
import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post, User


class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тест',
            slug='test-group',
        )
        cls.user = User.objects.create_user(username='TestUser')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='pic.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Это текст тестового поста. Кстати, привет, мир!',
            'group': PostCreateFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(post.author, PostCreateFormTests.user)
        self.assertEqual(post.image.name, 'posts/' + uploaded.name)

    def test_edit_post(self):
        other_group = Group.objects.create(
            title='Другое',
            slug='other-group',
        )
        post = Post.objects.create(
            text='Это текст тестового поста. Кстати, привет, мир!',
            group=PostCreateFormTests.group,
            author=PostCreateFormTests.user,
        )
        post_amount = Post.objects.count()
        kwargs = {
            'username': PostCreateFormTests.user.username,
            'post_id': post.id,
        }
        text_to_insert = 'А это текст, на который нужно исправить'
        form_data = {
            'text': text_to_insert,
            'group': other_group.id,
        }
        response = self.authorized_client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=post.id)
        self.assertRedirects(response, reverse('post', kwargs=kwargs))
        self.assertEqual(Post.objects.count(), post_amount)
        self.assertEqual(post.text, text_to_insert)
        self.assertEqual(post.group, other_group)
        self.assertEqual(post.author, PostCreateFormTests.user)

    def test_new_unauth(self):
        post_amount = Post.objects.count()
        form_data = {
            'text': 'Пост, который не добавится',
            'group': PostCreateFormTests.group,
        }
        response = self.client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        rev_login = reverse('login')
        rev_new = reverse('new_post')
        self.assertEqual(Post.objects.count(), post_amount)
        self.assertRedirects(response, f'{rev_login}?next={rev_new}')

    def test_edit_post_non_author(self):
        reader = User.objects.create(username='mimokrokodil')
        reader_client = Client()
        reader_client.force_login(reader)
        post = Post.objects.create(
            text='Это текст тестового поста. Кстати, привет, мир!',
            group=PostCreateFormTests.group,
            author=PostCreateFormTests.user,
        )
        text = 'Этот текст не появится в посте'
        form_data = {
            'text': text,
        }
        kwargs = {
            'username': PostCreateFormTests.user.username,
            'post_id': post.id,
        }
        response = reader_client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data,
            follow=True
        )
        post_to_check = Post.objects.get(id=post.id)
        self.assertRedirects(response, reverse('post', kwargs=kwargs))
        self.assertNotEqual(post_to_check.text, text)

    def test_auth_comment(self):
        post = Post.objects.create(
            text='Это текст тестового поста. Кстати, привет, мир!',
            group=PostCreateFormTests.group,
            author=PostCreateFormTests.user,
        )
        amount = post.comments.filter(post=post).count()
        text = 'Интересный комментарий'
        form_data = {
            'text': text,
            'post': post
        }
        kwargs = {
            'username': PostCreateFormTests.user.username,
            'post_id': post.id,
        }
        response = self.authorized_client.post(
            reverse('add_comment', kwargs=kwargs),
            data=form_data,
            follow=True
        )
        com = Comment.objects.first()
        self.assertEqual(post.comments.filter(post=post).count(), amount + 1)
        #self.assertRedirects(response, reverse('post', kwargs=kwargs))
        self.assertEqual(com.text, text)
        self.assertEqual(com.post, post)

    def test_guest_comment(self):
        post = Post.objects.create(
            text='Это текст тестового поста. Кстати, привет, мир!',
            group=PostCreateFormTests.group,
            author=PostCreateFormTests.user,
        )
        amount = Comment.objects.filter(post=post).count()
        text = 'Коммент, который не запостится'
        form_data = {
            'text': text,
            'post': post
        }
        kwargs = {
            'username': PostCreateFormTests.user.username,
            'post_id': post.id,
        }
        response = self.client.post(
            reverse('add_comment', kwargs=kwargs),
            data=form_data,
            follow=True
        )
        rev_login = reverse('login')
        rev_com = reverse('add_comment', kwargs=kwargs)
        self.assertEqual(Comment.objects.filter(post=post).count(), amount)
        self.assertRedirects(response, f'{rev_login}?next={rev_com}')
