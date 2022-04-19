from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='test_post',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location_for_client(self):
        """ Проверяем доступность страниц для любого пользователя. """
        url_names_status_code = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/test_author/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            '/posts/1/edit/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, status_code in url_names_status_code.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_exists_at_desired_location_for_authorized_client(self):
        """ Проверяем доступность страниц для авторизованного пользователя. """
        url_names_status_code = {
            '/create/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.FOUND,
        }
        for url, status_code in url_names_status_code.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_edit_post_url_exists_at_desired_location_for_author_client(self):
        """Страница /posts/1/edit/ доступна автору."""
        response = self.author_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_url_redirect_anonymous_on_profile(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_post_url_redirect_non_author_on_post_detail(self):
        """Страница /posts/1/edit/ перенаправит пользователя,
        не являющегося автором поста, на страницу поста.
        """
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for url, template in url_names_templates.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)


class CachePageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post_cache = Post.objects.create(
            author=cls.user,
            text='test_cache',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_page(self):
        """Проверка кеширования главной страницы."""
        response = self.authorized_client.get(
            reverse('posts:index')).content
        self.post_cache.delete()
        response_cache = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response, response_cache)
        cache.clear()
        response_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(response, response_clear)
