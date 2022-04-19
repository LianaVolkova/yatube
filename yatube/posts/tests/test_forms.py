import shutil
import tempfile

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
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
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test.gif',
            content=test_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.author)

    def test_post_create(self):
        """При отправке формы создаётся новая запись в базе данных."""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': self.post.text,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.author.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image='posts/test.gif'
            ).exists()
        )

    def test_post_edit(self):
        form_data = {
            'group': self.group.id,
            'text': self.post.text,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
            ).exists()
        )


class CommentAddFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='test_post',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='test_comment',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentAddFormTests.author)

    def test_comment_add(self):
        """При отправке формы создаётся новый комментарий в базе данных."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': self.comment.text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )
