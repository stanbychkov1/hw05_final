from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'page': page, 'paginator': paginator, 'group': group}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('index')
    return render(request, "new_post.html", {"form": form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.all()
    count_posts = author.posts.count()
    paginator = Paginator(user_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    count_following = author.follower.count()
    count_follower = author.following.count()
    return render(request, "profile.html", {'posts': page,
                                            'count_posts': count_posts,
                                            'paginator': paginator,
                                            'author': author,
                                            'count_follower': count_follower,
                                            'count_following': count_following
                                            })


def post_view(request, username, post_id):
    user_post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = get_object_or_404(User, username=username)
    count_posts = author.posts.count()
    items = user_post.comments.all()
    form = CommentForm()
    count_following = author.follower.count()
    count_follower = author.following.count()
    return render(request, "post.html", {'post': user_post,
                                         'count_posts': count_posts,
                                         'post_id': post_id,
                                         'author': author,
                                         'form': form,
                                         'items': items,
                                         'comment':False,
                                         'count_follower': count_follower,
                                         'count_following': count_following
                                         })


@login_required()
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    post = Post.objects.filter(pk=post_id).get()
    form = PostForm({'text': post})
    return render(request, "new_post.html", {"form": form, 'edit': True, 'post': post})


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = get_object_or_404(User, username=username)
    form = CommentForm(request.POST or None)
    count_posts = author.posts.count()
    items = post.comments.all()
    count_following = author.follower.count()
    count_follower = author.following.count()
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post = post
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, "post.html", {'post': post,
                                         'username': username,
                                         'count_posts': count_posts,
                                         'post_id': post_id,
                                         'author': author,
                                         'form': form,
                                         'items': items,
                                         'comment': True,
                                         'count_follower': count_follower,
                                         'count_following': count_following
                                         })


@login_required()
def follow_index(request):
    follower = get_object_or_404(User, username=request.user.username)
    subscribes = follower.follower.values_list('author')
    follower_post = Post.objects.filter(author__in=subscribes).all()
    paginator = Paginator(follower_post, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page, 'paginator': paginator})


@login_required()
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)
    follower = get_object_or_404(User, username=request.user.username)
    if following != follower:
        Follow.objects.get_or_create(user=follower, author=following)
        return redirect('profile', username=username)
    return redirect('profile', username=username)


@login_required()
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    follower = get_object_or_404(User, username=request.user.username)
    if following != follower:
        Follow.objects.filter(user=follower, author=following).delete()
        return redirect('profile', username=username)
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
