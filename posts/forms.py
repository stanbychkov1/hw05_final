from django.forms import ModelForm
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {
            'text': ('Текст'),
            'group': ('Группа'),
            'image': ('Изображение')
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': ('Комментарий')}
