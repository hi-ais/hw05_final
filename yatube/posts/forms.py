from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        text = forms.CharField(
            widget=forms.Textarea
            (attrs={"rows": 10, "cols": 40}),
            required=True)
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
