from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Follow, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = (
            'text',
            'group',
            'image',
        )


class CommentForm(forms.ModelForm):
    
    class Meta:
        model = Comment
        fields = (
            'text',
        )
