import io
import tempfile

from PIL import Image
from unittest import mock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.core.files import File
from django.contrib.auth.models import User

from .models import Post, Group, Follow, Comment


class PostProjectTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client_auth = Client()
        self.client_unauth = Client()
        self.user = User.objects.create_user(username='sarah')
        self.client_auth.force_login(self.user)
        self.group = Group.objects.create(title='sarahconnor',
                                          slug='sarahconnor',
                                          description=None)

    def _post_group(self, response, post, text):
        if 'paginator' in response.context:
            new_post = response.context['paginator'].object_list[0]
            if new_post.image:
                self.assertContains(response, 'img')
            self.assertEqual(new_post.text, post.text)
            self.assertEqual(new_post.author, post.author)
            self.assertEqual(new_post.group, post.group)
        else:
            if post.image:
                self.assertContains(response, 'img')
            self.assertEqual(post.text, text)
            self.assertEqual(post.author, self.user)
            self.assertEqual(post.group, self.group)

    def _get_urls(self, post, text):
        urls = (reverse('index'),
                reverse('profile', kwargs={'username': self.user.username}),
                reverse('post', kwargs={'username': self.user.username,
                                        'post_id': post.pk}),
                reverse('group', kwargs={'slug': self.group.slug}))
        for url in urls:
            response = self.client_auth.get(url)
            self._post_group(response, post, text)

    def _create_test_image_file(self):
        file = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(255, 0, 0))
        image.save(file, 'png')
        file.name = 'test_image.png'
        file.seek(0)
        return file

    def test_to_see_profile(self):
        response = self.client.get(reverse('profile',
                                           kwargs={'username': 'sarah'}))
        self.assertEqual(response.status_code, 200)

    def test_auth_user_can_post(self):
        self.client_auth.post(reverse('new_post'), data={
            'text': 'new text',
            'group': self.group.pk,
            'author': self.user
        })
        response = self.client.get(reverse('profile',
                                           kwargs={'username': 'sarah'}))
        self.assertEqual(len(response.context['posts']), 1)
        new_post = Post.objects.first()
        self.assertEqual(new_post.text, 'new text')
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)

    def test_unauth_user_can_post(self):
        response = self.client_unauth.post(reverse('new_post'),
                                           {'text': 'new text unauth'})
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_new_post_view(self):
        text = 'new text'
        self.client_auth.post(reverse('new_post'), data={
            'text': text,
            'group': self.group.pk,
            'author': self.user
        })
        post = self.user.posts.first()
        self._get_urls(post, text)

    def test_post_can_be_edited(self):
        text = 'new text'
        new_text = 'new text new'
        self.client_auth.post(reverse('new_post'), data={
            'text': text,
            'group': self.group.pk,
            'author': self.user
        })
        post = Post.objects.first()
        response = self.client_auth.get(reverse('post_edit', kwargs={
            'username': self.user.username,
            'post_id': post.pk
        }))
        self.assertEqual(response.status_code, 200)
        self.client_auth.post(reverse('post_edit', kwargs={
            'username': self.user.username,
            'post_id': post.pk
        }), data={
            'text': new_text,
            'group': self.group.pk,
            'author': self.user
        })
        new_post = Post.objects.first()
        self._get_urls(new_post, new_text)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_user_can__post_post_with_image(self):
        img = self._create_test_image_file()
        self.client_auth.post(reverse('new_post'), data={
            'author': self.user,
            'group': self.group.pk,
            'text': 'post with image',
            'image': img
        })
        post = self.user.posts.first()
        response = self.client_auth.get(reverse('post', kwargs={
            'username': self.user, 'post_id': post.pk
        }))
        self.assertContains(response, '<img')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_image_posted_everywhere(self):
        text = 'post with image'
        img = self._create_test_image_file()
        self.client_auth.post(reverse('new_post'), data={
            'author': self.user,
            'group': self.group.pk,
            'text': text,
            'image': img
        })
        post = self.user.posts.first()
        self._get_urls(post, text)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_user_cant_post_post_with_file_not_img(self):
        text = 'post with file not image'
        file_mock = mock.MagicMock(spec=File, name='copy.txt')
        response = self.client_auth.post(reverse('new_post'), data={
            'author': self.user,
            'group': self.group.pk,
            'text': text,
            'image': file_mock
        })
        self.assertFormError(response,
                             form='form',
                             field='image',
                             errors='Загрузите правильное изображение.'
                                    ' Файл, который вы загрузили,'
                                    ' поврежден или не является изображением.'
                             )

    def test_cache_works(self):
        text = 'new text'
        self.client_auth.post(reverse('new_post'), data={
            'text': text,
            'group': self.group.pk,
            'author': self.user
        })
        response = self.client_auth.get(reverse('index'))
        post = self.user.posts.first()
        self.assertEqual(len(response.context['paginator'].object_list), 1)
        post.delete()
        response = self.client_auth.get(reverse('index'))
        self.assertContains(response, 'new text')

    def test_auth_user_can_follow(self):
        new_user = User.objects.create_user(username='wildorf')
        self.client_auth.get(reverse('profile_follow',
                                     kwargs={'username': new_user.username}))
        self.assertEqual(len(new_user.following.all()), 1)

    def test_auth_user_can_unfollow(self):
        new_user = User.objects.create_user(username='wildorf')
        self.client_auth.get(reverse('profile_follow',
                                     kwargs={'username': new_user.username}))
        self.assertEqual(len(new_user.following.all()), 1)
        self.client_auth.get(reverse('profile_unfollow',
                                     kwargs={'username': new_user.username}))
        self.assertEqual(len(new_user.following.all()), 0)

    def test_new_post_followers_can_see(self):
        text = 'new post'
        new_user1 = User.objects.create_user(username='wildorf')
        new_user2 = User.objects.create_user(username='ford')
        new_client1 = Client()
        new_client2 = Client()
        new_client1.force_login(new_user1)
        new_client2.force_login(new_user2)
        Follow.objects.create(user=new_user1, author=self.user)
        self.client_auth.post(reverse('new_post'), data={
            'text': text,
            'group': self.group.pk,
            'author': self.user
        })
        response1 = new_client1.get(reverse('follow_index'))
        response2 = new_client2.get(reverse('follow_index'))
        self.assertEqual(len(response1.context['paginator'].object_list), 1)
        self.assertEqual(len(response2.context['paginator'].object_list), 0)

    def test_only_auth_user_can_post_comment(self):
        text = 'new post'
        self.client_auth.post(reverse('new_post'), data={
            'text': text,
            'group': self.group.pk,
            'author': self.user
        })
        post = Post.objects.first()
        self.client_auth.post(reverse('add_comment',
                                      kwargs={
                                          'username': self.user.username,
                                          'post_id': post.pk}),
                                      data={
                                          'post': post.pk,
                                          'author': self.user,
                                          'text': 'new comment'
                                      })
        comment = Comment.objects.all()
        self.assertEqual(len(comment), 1)
        self.client_unauth.post(reverse('add_comment',
                                        kwargs={
                                            'username': self.user.username,
                                            'post_id': post.pk}),
                                        data={
                                            'post': post.pk,
                                            'author': self.user,
                                            'text': 'new comment'
                                        })
        comment = Comment.objects.all()
        self.assertEqual(len(comment), 1)
