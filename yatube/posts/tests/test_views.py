from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from django import forms

from posts.models import Follow, Group, Post
from posts.forms import CommentForm, PostForm
from posts.views import PER_PAGE

User = get_user_model()

TEST_POSTS_COUNT = 13


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_post',
            group=cls.group,
        )
        cls.group_2 = Group.objects.create(
            title='test_group_2',
            slug='test_slug_2',
            description='test_description_2'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Главная страница показывает список постов.
        При создании поста он появляется на главной странице."""
        response = self.client.get(reverse(
            'posts:index'
        )).context['page_obj'][0]
        page_fields_context = {
            response: self.post,
            response.author.get_full_name(): self.user.get_full_name(),
            response.pub_date: self.post.pub_date,
            response.image: self.post.image,
            response.text: 'test_post',
        }
        for page_field, context in page_fields_context.items():
            with self.subTest(page_field=page_field):
                self.assertEqual(page_field, context)

    def test_group_list_page_show_correct_context(self):
        """Cтраница показывает список постов, отфильтрованных по группе.
        При создании поста он появляется на странице с постами группы."""
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        )).context['page_obj'][0]
        page_fields_context = {
            response: self.post,
            response.group.title: 'test_group',
            response.group.description: 'test_description',
            response.author.get_full_name(): self.user.get_full_name(),
            response.pub_date: self.post.pub_date,
            response.image: self.post.image,
            response.text: 'test_post',
        }
        for page_field, context in page_fields_context.items():
            with self.subTest(page_field=page_field):
                self.assertEqual(page_field, context)
        """ Проверяем, что пост не попал в другую группу """
        self.assertNotEqual(response.group, self.group_2)

    def test_profile_page_show_correct_context(self):
        """Cтраница показывает список постов, отфильтрованных по пользователю.
        При создании поста он появляется на странице профиля пользователя."""
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )).context['page_obj'][0]
        page_fields_context = {
            response: self.post,
            response.author.get_full_name(): self.user.get_full_name(),
            response.pub_date: self.post.pub_date,
            response.image: self.post.image,
            response.text: 'test_post',
            response.author.posts.all().count(): len(self.user.posts.all()),
        }
        for page_field, context in page_fields_context.items():
            with self.subTest(page_field=page_field):
                self.assertEqual(page_field, context)

    def test_post_detail_page_show_correct_context(self):
        """Страница показывает один пост, отфильтрованный по id."""
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        )).context.get('post')
        page_fields_context = {
            response.group.title: 'test_group',
            response.author.get_full_name(): self.user.get_full_name(),
            response.pub_date: self.post.pub_date,
            response.image: self.post.image,
            response.text: 'test_post',
            response.author.posts.all().count(): len(self.user.posts.all()),
        }
        for page_field, context in page_fields_context.items():
            with self.subTest(page_field=page_field):
                self.assertEqual(page_field, context)

        """Страница показывает комментарии к посту."""
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(
            set(response.context['comments']),
            set(self.post.comments.all())
        )
        self.assertIsInstance(response.context.get('form'), CommentForm)
        self.assertIsInstance(response.context.get(
            'form').fields.get('text'), forms.fields.CharField)

    def test_create_post_page_show_correct_context(self):
        """Страница показывает форму для создания поста."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        self.assertIsInstance(response.context.get('form'), PostForm)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Страница показывает форму для редактирования поста,
        отфильтрованного по id."""
        response = (self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id})))
        self.assertIsInstance(response.context.get('form'), PostForm)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)
        self.assertIsInstance(is_edit, bool)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        for i in range(TEST_POSTS_COUNT):
            cls.posts = Post.objects.create(
                author=cls.user,
                text=f'test_post {i + 1}',
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_correct(self):
        templates = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for i in range(len(templates)):
            with self.subTest(templates=templates[i]):
                response = self.authorized_client.get(templates[i])
                self.assertEqual(len(response.context['page_obj']), PER_PAGE)

    def test_pages_contains_records(self):
        test_index = reverse('posts:index')
        test_group_list = reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'})
        test_profile = reverse(
            'posts:profile', kwargs={'username': 'test_user'})
        posts_on_page = {
            (test_index, 1): PER_PAGE,
            (test_index, 2): TEST_POSTS_COUNT - PER_PAGE,
            (test_group_list, 1): PER_PAGE,
            (test_group_list, 2): TEST_POSTS_COUNT - PER_PAGE,
            (test_profile, 1): PER_PAGE,
            (test_profile, 2): TEST_POSTS_COUNT - PER_PAGE,
        }
        for (url, page), pages in posts_on_page.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, {'page': page})
                self.assertEqual(len(response.context['page_obj']), pages)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_post',
        )
        cls.follower = User.objects.create_user(username='follower')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.following_client = Client()
        self.following_client.force_login(self.follower)

    def test_follow_and_unfollow_correct(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        self.following_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user}
        ))
        follow = Follow.objects.filter(
            user=self.follower, author=self.user).exists()
        self.assertTrue(follow)
        self.following_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user}
        ))
        follow = Follow.objects.filter(
            user=self.follower, author=self.user).exists()
        self.assertEqual(follow, False)

    def test_follow_post(self):
        """Новая запись пользователя
        появляется в ленте тех, кто на него подписан."""
        Follow.objects.create(user=self.follower, author=self.user)
        response = self.following_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0].text, 'test_post')
        """ Новая запись пользователя
        не появляется в ленте тех, кто не подписан. """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(response, 'test_post')
