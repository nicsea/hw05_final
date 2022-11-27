from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect


from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow
from .utils import posts_paginator

POSTS_COUNT: int = 10
CHAR_COUNT_TITLE: int = 30


def index(request):
    post_list = Post.objects.select_related('group')
    page_obj = posts_paginator(request, post_list, POSTS_COUNT)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = posts_paginator(request, post_list, POSTS_COUNT)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.select_related('group').filter(
        author_id=author.id)
    page_obj = posts_paginator(request, post_list, POSTS_COUNT)

    following = False
    if request.user.is_authenticated:
        follow = Follow.objects.filter(author=author, user=request.user)
        if follow.count() > 0:
            following = True

    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_posts_count = Post.objects.filter(author_id=post.author_id).count()
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post_id=post_id)
    context = {
        'post': post,
        'char_count': CHAR_COUNT_TITLE,
        'author_posts_count': author_posts_count,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    followed_authors = Follow.objects.filter(user=request.user)
    author_ids = [followed.author.id for followed in followed_authors]
    post_list = Post.objects.filter(
        author__in=author_ids).select_related('group')
    page_obj = posts_paginator(request, post_list, POSTS_COUNT)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        if Follow.objects.filter(author=author, user=user).count() == 0:
            Follow.objects.create(author=author, user=user)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('posts:index')
