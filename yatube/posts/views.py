from django.shortcuts import render


def index(request):
    title = "Это главная страница проекта Yatube"
    context = {
        "title": title,
    }
    return render(request, "posts/index.html", context)


def group_posts(request):
    title = "Здесь будет информация о группах проекта Yatube"
    context = {
        "title": title,
    }
    return render(request, "posts/group_list.html", context)
