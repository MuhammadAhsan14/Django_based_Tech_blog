# views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.contrib import messages

from . models import BlogPost, Reaction, Comment
from .forms import BlogPostForm, CustomUserCreationForm, CustomAuthenticationForm, CustomUserChangeForm, CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
def react_to_post(request, pk):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        reaction_type = data.get('reaction')
        post = get_object_or_404(BlogPost, pk=pk)
        reaction, created = Reaction.objects.get_or_create(
            post=post,
            user=request.user,
            defaults={'reaction_type': reaction_type}
        )
        if not created:
            reaction.reaction_type = reaction_type
            reaction.save()
        return JsonResponse({'status': 'success', 'reaction': reaction_type})
    
def blog_list(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'blog_list.html', {'posts': posts})

@login_required
def blog_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    comments = Comment.objects.filter(post=post).order_by('-created_at')
    user_reaction = None
    if request.user.is_authenticated:
        user_reaction = Reaction.objects.filter(post=post, user=request.user).first()
    
    if request.method == 'POST':
        if request.is_ajax():
            data = json.loads(request.body)
            content = data.get('content')
            comment = Comment.objects.create(post=post, user=request.user, content=content)
            response_data = {
                'status': 'success',
                'username': request.user.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            return JsonResponse(response_data)
    
    context = {
        'post': post,
        'comments': comments,
        'user_reaction': user_reaction
    }
    return render(request, 'blog_detail.html', context)

@login_required
def add_comment(request, pk):
    if request.method == 'POST':
        content = request.POST.get('content')
        post = get_object_or_404(BlogPost, pk=pk)
        Comment.objects.create(post=post, user=request.user, content=content)
        return redirect('blog_detail', pk=pk)

@csrf_exempt  # Only use this if absolutely necessary
def post_comment(request, post_id):
    if request.method == 'POST':
        # Ensure request contains JSON data
        if request.content_type != 'application/json':
            return JsonResponse({'status': 'error', 'message': 'Invalid content type'}, status=400)

        data = json.loads(request.body)
        content = data.get('content')

        if not content:
            return JsonResponse({'status': 'error', 'message': 'No content provided'}, status=400)

        # Save the comment
        comment = Comment.objects.create(
            post_id=post_id,
            user=request.user,
            content=content,
            created_at=timezone.now()
        )

        response_data = {
            'status': 'success',
            'username': request.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        return JsonResponse(response_data)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            blog_post.author = request.user
            blog_post.save()
            return redirect('blog_list')
    else:
        form = BlogPostForm()
    return render(request, 'blog_form.html', {'form': form})

@login_required
def blog_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog_detail', pk=post.pk)
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'blog_form.html', {'form': form})

@login_required
def profile_update(request):
    if request.method == 'POST':
        profile_form = CustomUserChangeForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')

        if password_form.is_valid():
            password_form.save()
            messages.success(request, 'Your password has been updated! Please log in with your new password.')
            logout(request)
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        profile_form = CustomUserChangeForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'profile_update.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })

def home(request):
    return render(request, 'home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Username is already taken.')
            elif User.objects.filter(email=email).exists():
                form.add_error('email', 'Email is already registered.')
            else:
                # Save user if no errors
                user = form.save(commit=False)
                user.is_active = False  # Deactivate account until it is confirmed
                user.save()
                current_site = get_current_site(request)
                mail_subject = 'Activate your account.'
                message = render_to_string('acc_active_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                to_email = form.cleaned_data.get('email')

                # Send HTML email
                email_message = EmailMessage(
                    subject=mail_subject,
                    body=message,
                    from_email='agchaveli@gmail.com',
                    to=[to_email],
                    headers={'Content-Type': 'text/html'}  # Ensures the email is treated as HTML
                )
                email_message.send()

                messages.success(request, 'Please confirm your email address to complete the registration.')
                return redirect('login')  # Redirect to login page after registration
        else:
            # Display form errors using messages
            messages.error(request, 'There was an error with your registration. Please check the form below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Your account has been activated successfully!')
        return redirect('home')
    else:
        messages.error(request, 'Activation link is invalid!')
        return render(request, 'activation_invalid.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect to home if user is already logged in

    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid Data. Please check the fields and try again.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})



def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')
