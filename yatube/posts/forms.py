from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        help_texts = {
            "text": "Вырази здесь свою душу",
            "group": "Выберите группу",
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        help_texts = {
            "text": "Не стесняйся, озвучь свое мнение 💩",
        }
