from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse

from .forms import PostForm
from .models import Group, Post


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

    context = {
        "author": user,
        "obj": posts,
    }
    return TemplateResponse(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    context = {"post": post}
    if post.author == request.user:
        context["is_author"] = True

    return render(request, "posts/post_detail.html", context=context)


@login_required
def post_create(request):
    user = request.user

    form = PostForm(request.POST or None)
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

    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)

    context = {"form": form, "is_edit": True}
    return render(request, "posts/create_post.html", context)
