from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тест',
            slug='test-group',
        )
        cls.author = User.objects.create(
            username='testuser',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.author)

    def test_hardcode_url_equals_name(self):
        author = StaticURLTests.author.username
        post_id = StaticURLTests.post.id
        group_slug = StaticURLTests.group.slug
        urls_names = (
            ('/', 'index', None),
            ('/new/', 'new_post', None),
            (f'/{author}/', 'profile', (author,)),
            (f'/{author}/{post_id}/', 'post', (author, post_id,)),
            (f'/group/{group_slug}/', 'group_view', (group_slug,)),
            (f'/{author}/{post_id}/edit/', 'post_edit', (author, post_id,))
        )
        for url, name, args in urls_names:
            with self.subTest(url=url, name=name):
                self.assertEqual(url, reverse(name, args=args))

    def test_pages_available(self):
        author = StaticURLTests.author.username
        post_id = StaticURLTests.post.id
        group_slug = StaticURLTests.group.slug
        post_edit_url = f'/{author}/{post_id}/edit/'
        test_data = (
            ('/', self.client, HTTPStatus.OK),
            ('/new/', self.authorized_client, HTTPStatus.OK),
            (f'/{author}/', self.client, HTTPStatus.OK),
            (f'/{author}/{post_id}/', self.client, HTTPStatus.OK),
            (f'/group/{group_slug}/', self.client, HTTPStatus.OK),
            (post_edit_url, self.authorized_client, HTTPStatus.OK),
        )
        for url, client, code in test_data:
            with self.subTest(url=url, code=str(code)):
                response = client.get(url)
                self.assertEqual(response.status_code, code)

    def test_redirect(self):
        author = StaticURLTests.author.username
        post_id = StaticURLTests.post.id
        reader = User.objects.create(
            username='onemoreuser'
        )
        reader_client = Client()
        reader_client.force_login(reader)
        profile = f'/{author}/{post_id}/'
        post_edit_url = f'/{author}/{post_id}/edit/'
        rev_login = reverse('login')
        rev_ed = reverse('post_edit', args=(author, post_id,))
        rev_new = reverse('new_post')
        login = f'{rev_login}?next={rev_ed}'
        red_new = f'{rev_login}?next={rev_new}'
        test_data = (
            ('/new/', self.client, HTTPStatus.FOUND, red_new),
            (post_edit_url, self.client, HTTPStatus.FOUND, login),
            (post_edit_url, reader_client, HTTPStatus.FOUND, profile),
        )
        for url, client, code, redir in test_data:
            with self.subTest(url=url, code=str(code)):
                response = client.get(url)
                self.assertEqual(response.status_code, code)
                self.assertRedirects(response, redir)

    def test_not_found(self):
        response = self.client.get('/rruth/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
