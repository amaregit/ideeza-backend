from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Country, User, Blog, View
import datetime


class AnalyticsAPITestCase(APITestCase):
    def setUp(self):
        # Create test data
        self.country1 = Country.objects.create(name='USA')
        self.country2 = Country.objects.create(name='Canada')

        self.user1 = User.objects.create(username='alice', country=self.country1)
        self.user2 = User.objects.create(username='bob', country=self.country2)

        self.blog1 = Blog.objects.create(
            title='Blog 1',
            content='Content 1',
            author=self.user1,
            created_at=datetime.datetime.now() - datetime.timedelta(days=5)
        )
        self.blog2 = Blog.objects.create(
            title='Blog 2',
            content='Content 2',
            author=self.user2,
            created_at=datetime.datetime.now() - datetime.timedelta(days=3)
        )

        # Create views
        View.objects.create(blog=self.blog1, user=self.user1)
        View.objects.create(blog=self.blog1, user=self.user2)
        View.objects.create(blog=self.blog2, user=self.user1)

    def test_blog_views_api_country_grouping(self):
        url = reverse('blog-views')
        response = self.client.get(url, {'object_type': 'country', 'range': 'month'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('x', response.data[0])
        self.assertIn('y', response.data[0])
        self.assertIn('z', response.data[0])

    def test_blog_views_api_user_grouping(self):
        url = reverse('blog-views')
        response = self.client.get(url, {'object_type': 'user', 'range': 'month'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blog_views_api_invalid_object_type(self):
        url = reverse('blog-views')
        response = self.client.get(url, {'object_type': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blog_views_api_dynamic_filtering(self):
        url = reverse('blog-views')
        response = self.client.get(url, {'country__eq': 'USA'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_top_api_user_top(self):
        url = reverse('top')
        response = self.client.get(url, {'top': 'user', 'range': 'month'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_top_api_country_top(self):
        url = reverse('top')
        response = self.client.get(url, {'top': 'country', 'range': 'month'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_top_api_blog_top(self):
        url = reverse('top')
        response = self.client.get(url, {'top': 'blog', 'range': 'month'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_top_api_invalid_top_type(self):
        url = reverse('top')
        response = self.client.get(url, {'top': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_performance_api_month_compare(self):
        url = reverse('performance')
        response = self.client.get(url, {'compare': 'month'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_performance_api_invalid_compare(self):
        url = reverse('performance')
        response = self.client.get(url, {'compare': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_performance_api_with_user_filter(self):
        url = reverse('performance')
        response = self.client.get(url, {'compare': 'month', 'user': 'amare_zeru'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_advanced_analytics_api(self):
        url = reverse('advanced-analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('trend_analysis', response.data)
        self.assertIn('anomaly_detection', response.data)
        self.assertIn('performance_insights', response.data)
        self.assertIn('smart_recommendations', response.data)
        self.assertIn('predictive_analytics', response.data)
