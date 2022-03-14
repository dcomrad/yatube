from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

PER_PAGE = 10
UPDATE_DELAY = 20


@cache_page(UPDATE_DELAY)
def index(request):
    template = 'posts/index.html'

    paginated_posts = Paginator(Post.objects.all(), PER_PAGE)
    page_obj = paginated_posts.get_page(request.GET.get('page') or 1)

    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


@login_required
def follow_index(request):
    template = 'posts/follow.html'

    followings = (follow.author for follow in request.user.follower.all())
    paginated_posts = Paginator(
        Post.objects.filter(author__in=followings), PER_PAGE
    )
    page_obj = paginated_posts.get_page(request.GET.get('page') or 1)

    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    user = get_object_or_404(get_user_model(), username=username)
    paginated_posts = Paginator(user.posts.all(), PER_PAGE)
    page_obj = paginated_posts.get_page(request.GET.get('page') or 1)
    if request.user.is_authenticated and request.user != user:
        followings = (follow.author for follow in request.user.follower.all())
    else:
        followings = ()

    context = {
        'user_obj': user,
        'page_obj': page_obj,
        'following': (user in followings)
    }

    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    paginated_posts = Paginator(group.posts.all(), PER_PAGE)
    page_obj = paginated_posts.get_page(request.GET.get('page') or 1)

    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)

    context = {
        'post': post,
        'comment_form': CommentForm(request.POST or None),
        'comments': post.comments.all(),
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(data=request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)

    template = 'posts/create_post.html'
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    template = 'posts/update_post.html'
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(data=request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id)

    return post_detail(request, post_id)


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=get_object_or_404(get_user_model(), username=username)
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.get(
        user=request.user,
        author=get_object_or_404(get_user_model(), username=username)
    ).delete()
    return redirect('posts:profile', username)
