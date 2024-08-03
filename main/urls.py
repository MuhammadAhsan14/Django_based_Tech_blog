from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from . views import react_to_post

urlpatterns = [
    path('', views.home, name='home'), 
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('profile_update/', views.profile_update, name='profile_update'),
    path('blogs/', views.blog_list, name='blog_list'),
    path('blogs/<int:pk>/', views.blog_detail, name='blog_detail'),
    path('blogs/create/', views.blog_create, name='blog_create'),
    path('blogs/edit/<int:pk>/', views.blog_edit, name='blog_edit'),
    path('blogs/<int:pk>/react/', react_to_post, name='react_to_post'),
    path('blogs/<int:pk>/comment/', views.add_comment, name='add_comment'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)