from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q, F
from django.db.models.functions import TruncMonth, TruncWeek, TruncYear, TruncDay
from .models import Blog, View
import datetime
from collections import defaultdict
import re


def get_range_start(range_type):
    """
    Get the start date for the given range type based on calendar periods.
    """
    now = datetime.datetime.now()
    if range_type == 'month':
        # Start of current month
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_type == 'week':
        # Start of current week (Monday)
        days_since_monday = now.weekday()
        return (now - datetime.timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_type == 'year':
        # Start of current year
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        # Default to month
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def build_dynamic_filters(query_params, exclude_params, field_mapping=None):
    """
    Build Q objects from dynamic filter parameters.
    Supports operators: eq, ne, in, contains, icontains, gt, gte, lt, lte
    Example: country__eq=USA, user__in=alice,bob, title__icontains=django
    field_mapping: dict to map field names to actual model fields
    """
    if field_mapping is None:
        field_mapping = {}
    filters = Q()
    for key, value in query_params.items():
        if key in exclude_params:
            continue
        # Parse field__operator=value
        if '__' in key:
            field, operator = key.rsplit('__', 1)
            lookup = {
                'eq': 'exact',
                'ne': 'exact',  # will negate
                'in': 'in',
                'contains': 'contains',
                'icontains': 'icontains',
                'gt': 'gt',
                'gte': 'gte',
                'lt': 'lt',
                'lte': 'lte',
            }.get(operator, 'exact')

            # Map field name
            actual_field = field_mapping.get(field, field)

            # Handle 'in' operator with comma-separated values
            if operator == 'in':
                value = value.split(',')
            elif operator == 'ne':
                # For 'ne', we need to negate the Q object
                q = Q(**{f'{actual_field}__{lookup}': value})
                filters &= ~q
                continue

            filters &= Q(**{f'{actual_field}__{lookup}': value})
        else:
            # Default to exact match if no operator
            actual_field = field_mapping.get(key, key)
            filters &= Q(**{actual_field: value})
    return filters


class BlogViewsAPI(APIView):
    def get(self, request):
        object_type = request.query_params.get('object_type', 'country')
        if object_type not in ['country', 'user']:
            return Response({'error': 'object_type must be country or user'}, status=400)

        range_type = request.query_params.get('range', 'month')
        if range_type not in ['month', 'week', 'year']:
            return Response({'error': 'range must be month, week, or year'}, status=400)

        # dynamic filters
        field_mapping = {
            'country': 'author__country__name',
            'user': 'author__username',
            'title': 'title',
            'content': 'content',
        }
        filters = build_dynamic_filters(
            request.query_params,
            exclude_params=['object_type', 'range'],
            field_mapping=field_mapping
        )

        start = get_range_start(range_type)

        blogs_qs = Blog.objects.filter(filters)
        views_qs = View.objects.filter(timestamp__gte=start, blog__in=blogs_qs)

        if object_type == 'country':
            blogs_group = blogs_qs.values(
                country_id=F('author__country'),
                country_name=F('author__country__name')
            ).annotate(
                num_blogs=Count('id')
            )
            views_group = views_qs.values(
                country_id=F('blog__author__country'),
                country_name=F('blog__author__country__name')
            ).annotate(
                total_views=Count('id')
            )
            data = defaultdict(lambda: {'x': '', 'y': 0, 'z': 0})
            for b in blogs_group:
                data[b['country_id']]['x'] = b['country_name']
                data[b['country_id']]['y'] = b['num_blogs']
            for v in views_group:
                data[v['country_id']]['z'] = v['total_views']
            result = [v for v in data.values() if v['y'] > 0 or v['z'] > 0]
        elif object_type == 'user':
            blogs_group = blogs_qs.values(
                user_pk=F('author'),
                username=F('author__username')
            ).annotate(
                num_blogs=Count('id')
            )
            views_group = views_qs.values(
                user_pk=F('blog__author'),
                username=F('blog__author__username')
            ).annotate(
                total_views=Count('id')
            )
            data = defaultdict(lambda: {'x': '', 'y': 0, 'z': 0})
            for b in blogs_group:
                data[b['user_pk']]['x'] = b['username']
                data[b['user_pk']]['y'] = b['num_blogs']
            for v in views_group:
                data[v['user_pk']]['z'] = v['total_views']
            result = [v for v in data.values() if v['y'] > 0 or v['z'] > 0]
        else:
            result = []
        return Response(result)

class TopAPI(APIView):
    def get(self, request):
        top_type = request.query_params.get('top', 'user')
        if top_type not in ['user', 'country', 'blog']:
            return Response({'error': 'top must be user, country, or blog'}, status=400)

        range_type = request.query_params.get('range', 'month')
        if range_type not in ['month', 'week', 'year']:
            return Response({'error': 'range must be month, week, or year'}, status=400)

        # filters
        field_mapping = {
            'country': 'author__country__name',
            'user': 'author__username',
            'title': 'title',
            'content': 'content',
        }
        filters = build_dynamic_filters(
            request.query_params,
            exclude_params=['top', 'range'],
            field_mapping=field_mapping
        )

        start = get_range_start(range_type)

        blogs_qs = Blog.objects.filter(filters)
        views_qs = View.objects.filter(timestamp__gte=start, blog__in=blogs_qs)

        if top_type == 'user':
            # Pre-calculate blog counts to avoid N+1
            user_blog_counts = {
                item['author']: item['blog_count']
                for item in Blog.objects.filter(filters).values('author').annotate(
                    blog_count=Count('id')
                )
            }
            top = views_qs.values(
                user_pk=F('blog__author'),
                username=F('blog__author__username')
            ).annotate(
                total_views=Count('id')
            ).order_by('-total_views')[:10]
            result = []
            for t in top:
                num_blogs = user_blog_counts.get(t['user_pk'], 0)
                result.append({
                    'x': t['username'],
                    'y': t['total_views'],
                    'z': num_blogs
                })
        elif top_type == 'country':
            # Pre-calculate blog counts per country
            country_blog_counts = {
                item['author__country']: item['blog_count']
                for item in Blog.objects.filter(filters).values('author__country').annotate(
                    blog_count=Count('id')
                )
            }
            top = views_qs.values(
                country_id=F('blog__author__country'),
                country_name=F('blog__author__country__name')
            ).annotate(
                total_views=Count('id')
            ).order_by('-total_views')[:10]
            result = []
            for t in top:
                num_blogs = country_blog_counts.get(t['country_id'], 0)
                result.append({
                    'x': t['country_name'],
                    'y': t['total_views'],
                    'z': num_blogs
                })
        elif top_type == 'blog':
            top = views_qs.values(
                blog_pk=F('blog'),
                title=F('blog__title'),
                author_username=F('blog__author__username')
            ).annotate(
                total_views=Count('id')
            ).order_by('-total_views')[:10]
            result = []
            for t in top:
                result.append({
                    'x': t['title'],
                    'y': t['total_views'],
                    'z': t['author_username']
                })
        else:
            result = []
        return Response(result)

class PerformanceAPI(APIView):
    def get(self, request):
        compare = request.query_params.get('compare', 'month')
        if compare not in ['month', 'week', 'day', 'year']:
            return Response({'error': 'compare must be month, week, day, or year'}, status=400)

        user_param = request.query_params.get('user')

        # filters
        field_mapping = {
            'country': 'author__country__name',
            'user': 'author__username',
            'title': 'title',
            'content': 'content',
        }
        filters = build_dynamic_filters(
            request.query_params,
            exclude_params=['compare', 'user'],
            field_mapping=field_mapping
        )

        now = datetime.datetime.now()
        if compare == 'month':
            trunc_func = TruncMonth
            delta = datetime.timedelta(days=30*12)
        elif compare == 'week':
            trunc_func = TruncWeek
            delta = datetime.timedelta(days=7*12)
        elif compare == 'day':
            trunc_func = TruncDay
            delta = datetime.timedelta(days=30)
        elif compare == 'year':
            trunc_func = TruncYear
            delta = datetime.timedelta(days=365*5)
        else:
            trunc_func = TruncMonth
            delta = datetime.timedelta(days=30*12)

        start = now - delta

        blogs_qs = Blog.objects.filter(created_at__gte=start).filter(filters)
        if user_param:
            blogs_qs = blogs_qs.filter(author__username=user_param)

        views_qs = View.objects.filter(timestamp__gte=start, blog__in=blogs_qs)

        # blogs per period
        blogs_per_period = blogs_qs.annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            num_blogs=Count('id')
        ).order_by('period')

        # views per period
        views_per_period = views_qs.annotate(
            period=trunc_func('timestamp')
        ).values('period').annotate(
            total_views=Count('id')
        ).order_by('period')

        # combine
        data = defaultdict(lambda: {'period': None, 'blogs': 0, 'views': 0})
        for b in blogs_per_period:
            data[b['period']]['period'] = b['period']
            data[b['period']]['blogs'] = b['num_blogs']
        for v in views_per_period:
            data[v['period']]['views'] = v['total_views']

        # sort periods
        sorted_periods = sorted(data.keys())
        result = []
        prev_views = None
        for period in sorted_periods:
            d = data[period]
            x = f"{period.strftime('%Y-%m-%d')} ({d['blogs']} blogs)"
            y = d['views']
            if prev_views is not None and prev_views != 0:
                z = ((y - prev_views) / prev_views) * 100
            else:
                z = 0
            result.append({'x': x, 'y': y, 'z': round(z, 2)})
            prev_views = y
        return Response(result)
