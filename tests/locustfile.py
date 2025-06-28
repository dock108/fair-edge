"""
Load Testing Configuration for Fair-Edge API
Simulates realistic user behavior patterns for performance testing
"""

from locust import HttpUser, task, between
import random
import json


class AnonymousUser(HttpUser):
    """Simulates anonymous/free users browsing opportunities"""
    
    wait_time = between(2, 8)  # Wait 2-8 seconds between requests
    weight = 3  # 60% of users are anonymous
    
    def on_start(self):
        """Called when a user starts"""
        # Check health endpoint once
        self.client.get("/health")
    
    @task(10)
    def view_opportunities(self):
        """Most common task - viewing opportunities"""
        self.client.get("/api/opportunities")
    
    @task(5)
    def view_opportunities_with_filters(self):
        """View opportunities with various filters"""
        params = {
            "limit": random.choice([10, 20, 50]),
            "min_ev": random.choice([None, 0, 1, 2])
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        self.client.get("/api/opportunities", params=params)
    
    @task(3)
    def check_user_info(self):
        """Check user information"""
        self.client.get("/api/user-info")
    
    @task(2)
    def view_root(self):
        """View API root information"""
        self.client.get("/")
    
    @task(1)
    def health_check(self):
        """Periodic health checks"""
        self.client.get("/health")


class SubscriberUser(HttpUser):
    """Simulates authenticated subscriber users with more features"""
    
    wait_time = between(1, 5)  # More active users
    weight = 1  # 20% of users are subscribers
    
    def on_start(self):
        """Called when a subscriber starts - simulate authentication"""
        # In a real scenario, this would authenticate and get a token
        # For load testing, we'll simulate subscriber behavior without real auth
        self.client.get("/health")
        self.client.get("/api/user-info")
    
    @task(8)
    def view_premium_opportunities(self):
        """Premium users access enhanced opportunities"""
        params = {
            "include_props": random.choice([True, False]),
            "include_totals": random.choice([True, False]),
            "include_spreads": random.choice([True, False]),
            "min_ev": random.choice([None, 0, 1, 2, 3]),
            "sort_by": random.choice(["ev_percentage", "odds", "commence_time"])
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Note: This endpoint requires authentication in real usage
        # For load testing, we expect it to return 401/403 which is fine
        with self.client.get("/premium/opportunities", params=params, catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected for unauthenticated load test
    
    @task(5)
    def view_regular_opportunities(self):
        """Subscribers also view regular opportunities"""
        self.client.get("/api/opportunities")
    
    @task(3)
    def export_raw_data(self):
        """Subscribers export raw betting data"""
        params = {
            "format": random.choice(["json", "csv"]),
            "include_metadata": random.choice([True, False])
        }
        
        # Note: This endpoint requires authentication in real usage
        with self.client.get("/api/bets/raw", params=params, catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected for unauthenticated load test
    
    @task(2)
    def view_analytics(self):
        """Subscribers access advanced analytics"""
        params = {
            "timeframe": random.choice(["1h", "6h", "24h", "7d"]),
            "include_trends": random.choice([True, False]),
            "include_sportsbook_analysis": random.choice([True, False])
        }
        
        # Note: This endpoint requires authentication in real usage
        with self.client.get("/api/analytics/advanced", params=params, catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected for unauthenticated load test


class AdminUser(HttpUser):
    """Simulates admin users performing management tasks"""
    
    wait_time = between(5, 15)  # Less frequent, more deliberate actions
    weight = 0.2  # 4% of requests are admin (very low volume)
    
    def on_start(self):
        """Admin user startup"""
        self.client.get("/health")
    
    @task(5)
    def check_system_status(self):
        """Admins check system health frequently"""
        self.client.get("/health")
    
    @task(3)
    def view_cache_status(self):
        """Check cache status"""
        with self.client.get("/api/cache-status", catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected for unauthenticated load test
    
    @task(2)
    def view_celery_health(self):
        """Check background task health"""
        with self.client.get("/api/celery-health", catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected for unauthenticated load test
    
    @task(1)
    def trigger_refresh(self):
        """Occasionally trigger manual refresh"""
        with self.client.post("/api/refresh", json={"priority": "normal"}, catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected for unauthenticated load test


class ErrorScenarioUser(HttpUser):
    """Simulates users that trigger error conditions"""
    
    wait_time = between(3, 10)
    weight = 0.5  # 10% of users trigger errors
    
    @task(3)
    def request_nonexistent_endpoints(self):
        """Request endpoints that don't exist"""
        fake_endpoints = [
            "/api/fake-endpoint",
            "/api/opportunities/nonexistent",
            "/api/users/12345",
            "/admin/secret"
        ]
        endpoint = random.choice(fake_endpoints)
        
        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # 404 is expected and handled correctly
    
    @task(2)
    def send_invalid_data(self):
        """Send invalid data to endpoints"""
        invalid_payloads = [
            {"invalid": "data"},
            {"malformed": True, "nested": {"deep": "value"}},
            []  # Empty array
        ]
        
        payload = random.choice(invalid_payloads)
        
        with self.client.post("/api/session", json=payload, catch_response=True) as response:
            if response.status_code in [400, 422]:
                response.success()  # Bad request is expected and handled correctly
    
    @task(1)
    def trigger_rate_limits(self):
        """Try to trigger rate limiting"""
        # Make rapid requests to trigger rate limiting
        for _ in range(5):
            with self.client.get("/api/opportunities", catch_response=True) as response:
                if response.status_code == 429:
                    response.success()  # Rate limiting working correctly
                    break


class RealisticUserBehavior(HttpUser):
    """Simulates realistic user behavior patterns"""
    
    wait_time = between(1, 3)
    weight = 1  # 20% realistic behavior
    
    def on_start(self):
        """User session start"""
        # Typical user journey starts with health/root check
        self.client.get("/")
    
    @task
    def realistic_browsing_session(self):
        """Simulate a realistic browsing session"""
        # 1. Check opportunities
        self.client.get("/api/opportunities")
        
        # 2. User thinks for a moment
        self.wait()
        
        # 3. Apply some filters
        self.client.get("/api/opportunities", params={"min_ev": 1, "limit": 20})
        
        # 4. Check user info
        self.client.get("/api/user-info")
        
        # 5. Maybe check different filters
        if random.random() < 0.3:  # 30% chance
            self.client.get("/api/opportunities", params={"min_ev": 2})
        
        # 6. Occasional health check
        if random.random() < 0.1:  # 10% chance
            self.client.get("/health")


# Test configuration
class WebsiteUser(HttpUser):
    """Main user class that randomly chooses behavior"""
    
    tasks = {
        AnonymousUser: 60,      # 60% anonymous users
        SubscriberUser: 20,     # 20% subscribers  
        AdminUser: 4,           # 4% admin actions
        ErrorScenarioUser: 10,  # 10% error scenarios
        RealisticUserBehavior: 20  # 20% realistic patterns
    }
    
    wait_time = between(1, 5)