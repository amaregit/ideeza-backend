import time
import logging
import psutil
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('analytics')

class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor API performance, cache analytics data, and log metrics.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only monitor analytics endpoints
        if not request.path.startswith('/analytics/'):
            return self.get_response(request)

        start_time = time.time()
        start_cpu = psutil.cpu_percent(interval=None)
        start_memory = psutil.virtual_memory().percent

        # Check cache for analytics requests
        cache_key = self._generate_cache_key(request)
        cached_response = self._get_cached_response(cache_key, request)

        if cached_response is not None:
            logger.info(f"Cache hit for {request.path}", extra={
                'cache_hit': True,
                'response_time': 0,
                'cpu_usage': 0,
                'memory_usage': 0
            })
            return cached_response

        # Process the request
        response = self.get_response(request)

        # Calculate performance metrics
        end_time = time.time()
        end_cpu = psutil.cpu_percent(interval=None)
        end_memory = psutil.virtual_memory().percent

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        cpu_usage = end_cpu - start_cpu
        memory_usage = end_memory - start_memory

        # Log performance metrics
        self._log_performance_metrics(request, response, response_time, cpu_usage, memory_usage)

        # Cache successful analytics responses
        if response.status_code == 200 and self._should_cache_response(request):
            self._cache_response(cache_key, response, request)

        return response

    def _generate_cache_key(self, request):
        """Generate a unique cache key based on request parameters"""
        params = dict(request.GET)
        # Sort parameters for consistent caching
        sorted_params = sorted(params.items())
        param_string = '&'.join(f"{k}={v}" for k, v in sorted_params)
        return f"analytics:{request.path}:{param_string}"

    def _get_cached_response(self, cache_key, request):
        """Check if response is cached"""
        if not getattr(settings, 'ANALYTICS_CACHE_TIMEOUT', 0):
            return None

        cached_data = cache.get(cache_key, version=2)  # Use analytics cache
        if cached_data:
            # Reconstruct response from cached data
            from django.http import JsonResponse
            return JsonResponse(cached_data, status=200, safe=False)
        return None

    def _cache_response(self, cache_key, response, request):
        """Cache the response data"""
        try:
            import json
            data = json.loads(response.content.decode('utf-8'))
            timeout = getattr(settings, 'ANALYTICS_CACHE_TIMEOUT', 1800)  # 30 minutes default
            cache.set(cache_key, data, timeout=timeout, version=2)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Don't cache non-JSON responses
            pass

    def _should_cache_response(self, request):
        """Determine if response should be cached"""
        # Don't cache filtered or user-specific requests
        exclude_params = ['user']
        for param in exclude_params:
            if param in request.GET:
                return False
        return True

    def _log_performance_metrics(self, request, response, response_time, cpu_usage, memory_usage):
        """Log detailed performance metrics"""
        logger.info(f"Analytics API call: {request.path}", extra={
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'response_status': response.status_code,
            'response_time_ms': round(response_time, 2),
            'cpu_usage_percent': round(cpu_usage, 2),
            'memory_usage_percent': round(memory_usage, 2),
            'cache_hit': False,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'remote_addr': self._get_client_ip(request),
        })

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AnalyticsThrottlingMiddleware:
    """
    Custom throttling for analytics endpoints to prevent abuse.
    Implements sliding window rate limiting using Redis.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/analytics/'):
            return self.get_response(request)

        client_ip = self._get_client_ip(request)

        # Check rate limit
        if self._is_rate_limited(client_ip):
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': 60
            }, status=429)

        # Add current request to rate limit window
        self._record_request(client_ip)

        return self.get_response(request)

    def _is_rate_limited(self, client_ip):
        """Check if client has exceeded rate limit"""
        cache_key = f"rate_limit:{client_ip}"
        request_count = cache.get(cache_key, 0, version=1)

        # Allow 50 requests per minute for analytics
        return request_count >= 50

    def _record_request(self, client_ip):
        """Record the request in sliding window"""
        cache_key = f"rate_limit:{client_ip}"
        current_count = cache.get(cache_key, 0, version=1)
        cache.set(cache_key, current_count + 1, timeout=60, version=1)  # 1 minute window

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip