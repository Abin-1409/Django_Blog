from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import math
from gtts import gTTS
import os
from django.conf import settings
from django.core.files import File
from pathlib import Path
from django.db.models.signals import post_save
from django.dispatch import receiver
import threading

class BlogAuthor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=1000, help_text="Enter your bio details here.")

    class Meta:
        ordering = ['user__username']

    def get_absolute_url(self):
        return reverse('blog:blogger-detail', args=[str(self.id)])

    def __str__(self):
        return self.user.username

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(BlogAuthor, on_delete=models.CASCADE)
    content = models.TextField(help_text="Write your blog post here.")
    post_date = models.DateTimeField(default=timezone.now)
    audio_file = models.FileField(upload_to='blog_audio/', null=True, blank=True)
    audio_generation_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-post_date']

    def get_absolute_url(self):
        return reverse('blog:blog-detail', args=[str(self.id)])

    def __str__(self):
        return self.title

    def get_word_count(self):
        return len(self.content.split())

    def get_reading_time(self):
        """Calculate estimated reading time in minutes."""
        words_per_minute = 200  # Average reading speed
        word_count = self.get_word_count()
        reading_time = math.ceil(word_count / words_per_minute)
        return max(1, reading_time)  # Minimum 1 minute

    def get_audio_duration(self):
        """Calculate estimated audio duration in minutes."""
        words_per_minute = 150  # Average speaking rate
        word_count = self.get_word_count()
        audio_duration = math.ceil(word_count / words_per_minute)
        return max(1, audio_duration)  # Minimum 1 minute

    def generate_audio(self):
        """Generate audio file for the blog post content."""
        if not self.content:
            return False

        # Create audio directory if it doesn't exist
        audio_dir = Path(settings.MEDIA_ROOT) / 'blog_audio'
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Generate audio file path
        audio_filename = f'post_{self.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.mp3'
        audio_path = audio_dir / audio_filename

        try:
            # Generate audio using gTTS
            tts = gTTS(text=self.content, lang='en', slow=False)
            tts.save(str(audio_path))

            # Save the audio file to the model
            with open(audio_path, 'rb') as audio_file:
                self.audio_file.save(audio_filename, File(audio_file), save=False)
            
            self.audio_generation_date = timezone.now()
            self.save()

            # Clean up the temporary file
            os.remove(audio_path)
            return True
        except Exception as e:
            print(f"Error generating audio: {e}")
            if audio_path.exists():
                os.remove(audio_path)
            return False

    def needs_audio_update(self):
        """Check if audio needs to be regenerated."""
        if not self.audio_file:
            return True
        if not self.audio_generation_date:
            return True
        return self.audio_generation_date < self.post_date

def generate_audio_async(blog_post):
    """Generate audio in a separate thread."""
    blog_post.generate_audio()

@receiver(post_save, sender=BlogPost)
def handle_audio_generation(sender, instance, created, **kwargs):
    """Signal handler to generate audio after a new blog post is created."""
    if created:
        # Start audio generation in a separate thread
        thread = threading.Thread(target=generate_audio_async, args=(instance,))
        thread.start()

class Comment(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=1000, help_text="Enter your comment here.")
    post_date = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['post_date']

    def __str__(self):
        return f"{self.text[:75]}..."

    def can_edit(self, user=None):
        """Check if the user can edit this comment."""
        if not user or not user.is_authenticated:
            return False
        return user == self.author or user.is_staff

    def can_delete(self, user=None):
        """Check if the user can delete this comment."""
        if not user or not user.is_authenticated:
            return False
        return user == self.author or user.is_staff

class Reaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    ]
    
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=7, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['post', 'user']

    def __str__(self):
        return f"{self.user.username} {self.reaction_type}d {self.post.title}"
