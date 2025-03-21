from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.generic.edit import CreateView
from .models import BlogPost, BlogAuthor, Comment, Reaction
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserRegistrationForm
from django.http import Http404, JsonResponse
from django.contrib.auth import logout
from django.db.models import Count
from django.http import HttpResponseForbidden

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('blog:index')

def index(request):
    """View function for home page of site."""
    num_posts = BlogPost.objects.all().count()
    num_authors = BlogAuthor.objects.all().count()
    
    context = {
        'num_posts': num_posts,
        'num_authors': num_authors,
    }
    return render(request, 'index.html', context=context)

class BlogListView(generic.ListView):
    model = BlogPost
    paginate_by = 5
    template_name = 'blog/blogpost_list.html'

class BloggerListView(generic.ListView):
    model = BlogAuthor
    template_name = 'blog/blogger_list.html'

    def get_queryset(self):
        # Only show authors whose associated users still exist
        return BlogAuthor.objects.filter(user__isnull=False)

class BlogDetailView(generic.DetailView):
    model = BlogPost
    template_name = 'blog/blogpost_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.needs_audio_update():
            context['needs_audio_generation'] = True
        # Ensure user is in context
        context['user'] = self.request.user
        # Get comments
        context['comments'] = self.object.comments.all()
        return context

class BloggerDetailView(generic.DetailView):
    model = BlogAuthor
    template_name = 'blog/blogger_detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user is None:
            raise Http404("Author not found")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts'] = BlogPost.objects.filter(author=self.object).order_by('-post_date')
        return context

@login_required
def create_comment(request, pk):
    """View function for creating a comment on a blog post."""
    blog_post = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            Comment.objects.create(
                blog=blog_post,
                author=request.user,
                text=comment_text
            )
            messages.success(request, 'Comment added successfully.')
        return redirect(blog_post.get_absolute_url())

    return render(request, 'blog/comment_form.html', {'blog': blog_post})

def generate_audio(request, pk):
    """View to generate audio for a blog post."""
    blog_post = get_object_or_404(BlogPost, pk=pk)
    
    success = blog_post.generate_audio()
    
    if success:
        return JsonResponse({
            'success': True,
            'audio_url': blog_post.audio_file.url,
            'message': 'Audio generated successfully'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate audio'
        }, status=500)

@login_required
def react_to_post(request, pk):
    """View function for handling likes and dislikes on a blog post."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    blog_post = get_object_or_404(BlogPost, pk=pk)
    reaction_type = request.POST.get('reaction_type')
    
    if reaction_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Invalid reaction type'}, status=400)
    
    # Get or create the reaction
    reaction, created = Reaction.objects.get_or_create(
        post=blog_post,
        user=request.user,
        defaults={'reaction_type': reaction_type}
    )
    
    if not created:
        if reaction.reaction_type == reaction_type:
            # If clicking the same reaction, remove it
            reaction.delete()
            action = 'removed'
        else:
            # If changing reaction type, update it
            reaction.reaction_type = reaction_type
            reaction.save()
            action = 'updated'
    else:
        action = 'added'
    
    # Get updated reaction counts
    reaction_counts = Reaction.objects.filter(post=blog_post).values('reaction_type').annotate(count=Count('id'))
    likes = next((r['count'] for r in reaction_counts if r['reaction_type'] == 'like'), 0)
    dislikes = next((r['count'] for r in reaction_counts if r['reaction_type'] == 'dislike'), 0)
    
    return JsonResponse({
        'success': True,
        'action': action,
        'reaction_type': reaction_type,
        'likes': likes,
        'dislikes': dislikes
    })

@login_required
def edit_comment(request, pk):
    """View function for editing a comment."""
    comment = get_object_or_404(Comment, pk=pk)
    
    if not comment.can_edit(request.user):
        return HttpResponseForbidden("You don't have permission to edit this comment.")
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            comment.text = comment_text
            comment.is_edited = True
            comment.save()
            messages.success(request, 'Comment updated successfully.')
        return redirect(comment.blog.get_absolute_url())
    
    return render(request, 'blog/comment_form.html', {
        'blog': comment.blog,
        'comment': comment,
        'is_edit': True
    })

@login_required
def delete_comment(request, pk):
    """View function for deleting a comment."""
    comment = get_object_or_404(Comment, pk=pk)
    
    if not comment.can_delete(request.user):
        return HttpResponseForbidden("You don't have permission to delete this comment.")
    
    if request.method == 'POST':
        blog_url = comment.blog.get_absolute_url()
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
        return redirect(blog_url)
    
    return render(request, 'blog/comment_confirm_delete.html', {'comment': comment})
