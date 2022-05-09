from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.views.decorators.cache import cache_page

from yatube.settings import CACHE_TIMEOUT

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


def add_pagination(objects_num=settings.PAGINATION_OBJECTS_NUM):
    """Декоратор для добавления пагинации"""

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            response = func(request, *args, **kwargs)
            obj = response.context_data.pop("obj")

            paginator = Paginator(obj, objects_num)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            response.context_data["page_obj"] = page_obj
            return response.render()

        return wrapper

    return decorator


@cache_page(CACHE_TIMEOUT, key_prefix="index_page")
@add_pagination()
def index(request):
    posts = Post.objects.all()
    return TemplateResponse(request, "posts/index.html", {"obj": posts})


@add_pagination()
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    context = {
        "group": group,
        "obj": posts,
    }
    return TemplateResponse(request, "posts/group_list.html", context)


@add_pagination()
def profile(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    posts = user.posts.all()

    context = {"author": user, "obj": posts}

    if request.user.is_authenticated:
        following_exist = request.user.follower.filter(author=user).exists()
        context["following"] = following_exist

    return TemplateResponse(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comment.all()
    comment_form = CommentForm(request.POST or None)

    context = {
        "post": post,
        "comment_form": comment_form,
        "comments": comments,
    }
    if post.author == request.user:
        context["is_author"] = True

    return render(request, "posts/post_detail.html", context=context)


@login_required
def post_create(request):
    user = request.user

    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(False)
        post.author = user
        post.save()
        return redirect("posts:profile", user.username)

    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    if post.author != user:
        return redirect("posts:post_detail", post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)

    context = {"form": form, "is_edit": True}
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
@add_pagination()
def follow_index(request):
    following_ids = request.user.follower.values_list("author", flat=True)
    posts = Post.objects.filter(author_id__in=following_ids)
    print()

    context = {"obj": posts}

    return TemplateResponse(request, "posts/index.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(get_user_model(), username=username)

    if request.user == author:
        return redirect("posts:profile", username=username)
    try:
        Follow.objects.create(user=request.user, author=author)
    except IntegrityError as e:
        if "unique constraint" in e.args[0]:
            return redirect("posts:profile", username=username)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = request.user.follower.filter(author__username=username).first()
    author.delete()
    return redirect("posts:profile", username=username)
