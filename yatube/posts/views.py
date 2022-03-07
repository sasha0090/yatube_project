from django.shortcuts import render


def index(request):
    return render(request, 'posts/index.html')


def group_posts(request, slug):
    return render(request, 'posts/group_list.html')