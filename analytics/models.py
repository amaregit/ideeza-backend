from django.db import models
from django.core.exceptions import ValidationError


class Country(models.Model):
    """
    Model representing a country.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Country Name",
        help_text="The full name of the country.",
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name or "Unnamed Country"

    def clean(self):
        if not self.name or not self.name.strip():
            raise ValidationError("Country name cannot be empty.")
        self.name = self.name.strip()
    
    
class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return self.username


class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class View(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
        ]
