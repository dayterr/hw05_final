from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def get_a_page(posts, request):
    page_number = request.GET.get('page')
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page = paginator.get_page(page_number)
    return page


def index(request):
    posts = Post.objects.select_related(
        'group', 'author').annotate(Count('comments'))
    page = get_a_page(posts, request)
    return render(request, 'posts/index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().select_related(
        'author').annotate(Count('comments'))
    page = get_a_page(posts, request)
    return render(request, 'posts/group.html', {'group': group, 'page': page})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        n_post = form.save(commit=False)
        n_post.author = request.user
        n_post.save()
        return redirect('index')
    context = {
        'form': form,
        'is_new': True,
    }
    return render(request, 'posts/post_new.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related(
        'author').prefetch_related('group').annotate(Count('comments'))
    page = get_a_page(posts, request)
    if request.user.is_authenticated:
        following = Follow.objects.filter(author=author,
                                          user=request.user).exists()
    else:
        following = False
    context = {
        'author': author,
        'page': page,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm()
    if request.method == 'POST':
        form = CommentForm(data=request.POST)
        if form.is_valid():
            n_com = form.save(commit=False)
            n_com.author = request.user
            n_com.post = post
            n_com.save()
            return redirect('post', username=username, post_id=post_id)
    context = {
        'author': post.author,
        'post': post,
        'form': form,
    }
    return render(request, 'posts/post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)

    context = {
        'form': form,
        'is_new': False,
        'post': post,
    }
    return render(request, 'posts/post_new.html', context)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        n_com = form.save(commit=False)
        n_com.author = request.user
        n_com.post = post
        n_com.save()
    context = {
        'form': form,
        'post': post,
        'author': post.author,
    }
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user).select_related(
        'author', 'group').annotate(Count('comments'))
    page = get_a_page(posts, request)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if not Follow.objects.filter(author__username=username,
                                 user=request.user).exists():
        if request.user.username != username:
            Follow.objects.create(author=author, user=request.user)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    fol = Follow.objects.filter(author=author, user=request.user)
    if fol.exists():
        fol.delete()
    return redirect('profile', username=username)
