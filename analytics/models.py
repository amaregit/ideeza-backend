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

    class Meta:
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return self.username


class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['author']),
            models.Index(fields=['created_at']),
            models.Index(fields=['author', 'created_at']),
        ]

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
            models.Index(fields=['blog']),
            models.Index(fields=['user']),
            models.Index(fields=['blog', 'timestamp']),
            models.Index(fields=['timestamp', 'blog']),
        ]


class AnalyticsSnapshot(models.Model):
    """
    Pre-aggregated analytics data for performance.
    """
    SNAPSHOT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    snapshot_type = models.CharField(max_length=10, choices=SNAPSHOT_TYPES)
    date = models.DateField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Aggregated metrics
    total_views = models.PositiveIntegerField(default=0)
    total_blogs = models.PositiveIntegerField(default=0)
    unique_users = models.PositiveIntegerField(default=0)

    # Performance metrics
    avg_response_time = models.FloatField(default=0.0)
    cache_hit_rate = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['snapshot_type', 'date']),
            models.Index(fields=['country', 'snapshot_type']),
            models.Index(fields=['user', 'snapshot_type']),
            models.Index(fields=['date']),
        ]
        unique_together = ['snapshot_type', 'date', 'country', 'user']

    def __str__(self):
        scope = f"Country: {self.country}" if self.country else f"User: {self.user}" if self.user else "Global"
        return f"{self.snapshot_type.title()} {scope} - {self.date}"


class QueryOptimization(models.Model):
    """
    Tracks query performance and optimization opportunities.
    """
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    query_params = models.JSONField(default=dict)
    execution_time = models.FloatField()
    result_count = models.PositiveIntegerField()
    cache_hit = models.BooleanField(default=False)
    optimized = models.BooleanField(default=False)

    # System metrics
    cpu_usage = models.FloatField(default=0.0)
    memory_usage = models.FloatField(default=0.0)
    db_queries_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['endpoint', 'created_at']),
            models.Index(fields=['execution_time']),
            models.Index(fields=['cache_hit']),
        ]

    def __str__(self):
        return f"{self.endpoint} - {self.execution_time:.2f}s"
