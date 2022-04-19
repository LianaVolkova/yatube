from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .models import Group, Post, Follow
from .forms import CommentForm, PostForm

User = get_user_model()


PER_PAGE = 10


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {
        'page_obj': page_obj,
    }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_obj,
    }
    )


def profile(request, username):
    author = User.objects.get(username=username)
    post_list = Post.objects.filter(author=author)
    posts_number = post_list.count()
    paginator = Paginator(post_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )
    return render(request, 'posts/profile.html', {
        'author': author,
        'posts_number': posts_number,
        'page_obj': page_obj,
        'following': following,
    }
    )


def post_detail(request, post_id):
    post = Post.objects.select_related('author', 'group').get(id=post_id)
    post_list = Post.objects.filter(author=post.author)
    posts_number = post_list.count()
    form = CommentForm()
    comments = post.comments.all()
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'posts_number': posts_number,
        'post_id': post_id,
        'form': form,
        'comments': comments,
    }
    )


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if not form.is_valid():
        return render(
            request, 'posts/create_post.html',
            {'form': form, 'is_edit': is_edit, 'post': post}
        )
    post = form.save(commit=False)
    post.save()
    return redirect('posts:post_detail', post_id=post_id)


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
    post_list = Post.objects.filter(author__following__user=request.user).all()
    paginator = Paginator(post_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {
        'page_obj': page_obj,
    }
    )


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect('posts:follow_index')
    following = get_object_or_404(User, username=username)
    follows = Follow.objects.filter(
        user=request.user,
        author=following
    ).exists()
    if not follows:
        Follow.objects.create(user=request.user, author=following)
    return redirect('posts:index')


@login_required
def profile_unfollow(request, username):
    follower = get_object_or_404(User, username=username)
    Follow.objects.filter(author=follower, user=request.user).delete()
    return redirect('posts:follow_index')
