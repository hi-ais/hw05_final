from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.conf import settings


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, settings.PAGINATOR_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, settings.PAGINATOR_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = f'Записи сообщества {group.title}'
    context = {
        'title': title,
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    paginator = Paginator(post_list, settings.PAGINATOR_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = Follow.objects.filter(user__username=request.user,
                                      author=user).exists()
    context = {
        'page_obj': page_obj,
        'author': user,
        'post_list': post_list,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_posts_count = Post.objects.filter(author_id=post.author_id).count()
    title = str(post)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'author_posts_count': author_posts_count,
        'title': title,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    context = {
        'title': 'Удаление записи',
        'text': 'Запись удалена',
    }
    if post.author == request.user:
        post.delete()
    return render(request, 'posts/post_delete.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST, files=request.FILES or None)
    if request.method != 'POST':
        return render(request, 'posts/create_post.html',
                      {'form': form, 'username': request.user})
    if not form.is_valid():
        return render(request, 'posts/create_post.html',
                      {'form': form, 'username': request.user})
    form = form.save(commit=False)
    form.author = request.user
    form.save()
    return redirect('posts:profile', username=form.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    form = PostForm(
        request.POST,
        files=request.FILES or None,
        instance=post)
    if not form.has_changed():
        return redirect('posts:post_detail', post_id=post.pk)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.pk)
    return render(request, 'posts/create_post.html',
                  {'form': form, 'username': request.user,
                   'is_edit': is_edit, 'post_id': post_id})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow_post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(follow_post, settings.PAGINATOR_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Посты мои подписок'
    context = {
        'title': title,
        'follow_post': follow_post,
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    if follower.exists():
        follower.delete()
    return redirect('posts:profile', username=author.username)
