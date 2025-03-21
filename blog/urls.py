from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('blogs/', views.BlogListView.as_view(), name='blogs'),
    path('blogger/<int:pk>/', views.BloggerDetailView.as_view(), name='blogger-detail'),
    path('bloggers/', views.BloggerListView.as_view(), name='bloggers'),
    path('<int:pk>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('<int:pk>/create/', views.create_comment, name='create-comment'),
    path('comment/<int:pk>/edit/', views.edit_comment, name='edit-comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete-comment'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('<int:pk>/generate-audio/', views.generate_audio, name='generate-audio'),
    path('<int:pk>/react/', views.react_to_post, name='react-to-post'),
] 