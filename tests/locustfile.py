"""
Load Testing Configuration for bet-intel API
Uses Locust to simulate realistic user traffic patterns
"""
from locust import HttpUser, task, between, events
import json


class BetIntelUser(HttpUser):
    """Simulates a typical bet-intel user"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        self.client.verify = False  # Disable SSL verification for testing
        
        # Test health endpoint first
        response = self.client.get("/health")
        if response.status_code != 200:
            print(f"Health check failed: {response.status_code}")
    
    @task(10)
    def view_homepage(self):
        """Most common task - viewing the homepage"""
        self.client.get("/", name="homepage")
    
    @task(8)
    def get_opportunities(self):
        """Second most common - getting betting opportunities"""
        with self.client.get("/api/opportunities", catch_response=True, name="opportunities") as response:
            if response.status_code == 401:
                # Expected for unauthenticated users
                response.success()
            elif response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, (list, dict)):
                        response.success()
                    else:
                        response.failure(f"Invalid response format: {type(data)}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
    
    @task(5)
    def view_api_docs(self):
        """Users checking API documentation"""
        self.client.get("/docs", name="api_docs")
    
    @task(3)
    def check_metrics(self):
        """Monitoring systems checking metrics"""
        self.client.get("/metrics", name="metrics")
    
    @task(2)
    def get_openapi_schema(self):
        """API clients fetching schema"""
        self.client.get("/openapi.json", name="openapi_schema")
    
    @task(1)
    def test_nonexistent_endpoint(self):
        """Occasional 404 requests"""
        with self.client.get("/nonexistent", catch_response=True, name="404_test") as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404, got {response.status_code}")


class AuthenticatedUser(HttpUser):
    """Simulates authenticated users with more API access"""
    
    wait_time = between(0.5, 3)  # Authenticated users are more active
    weight = 3  # 3x more likely to be selected than BetIntelUser
    
    def on_start(self):
        """Setup for authenticated user"""
        self.client.verify = False
        
        # Simulate login (would need actual auth endpoint)
        self.auth_token = None
        
        # Test health
        response = self.client.get("/health")
        if response.status_code != 200:
            print(f"Health check failed: {response.status_code}")
    
    @task(15)
    def get_opportunities_frequent(self):
        """Authenticated users check opportunities more frequently"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        with self.client.get("/api/opportunities", headers=headers, 
                             catch_response=True, name="auth_opportunities") as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(8)
    def view_dashboard(self):
        """Authenticated users view dashboard"""
        self.client.get("/", name="dashboard")
    
    @task(5)
    def api_health_checks(self):
        """Frequent health checks from authenticated clients"""
        self.client.get("/health", name="health_check")
    
    @task(3)
    def concurrent_requests(self):
        """Simulate concurrent API calls"""
        # Make multiple requests quickly
        endpoints = ["/health", "/metrics", "/openapi.json"]
        for endpoint in endpoints:
            self.client.get(endpoint, name=f"concurrent_{endpoint.replace('/', '_')}")


class AdminUser(HttpUser):
    """Simulates admin users with heavy monitoring usage"""
    
    wait_time = between(2, 8)  # Admins check less frequently but more thoroughly
    weight = 1  # Fewer admin users
    
    @task(10)
    def monitor_metrics(self):
        """Admins frequently check metrics"""
        self.client.get("/metrics", name="admin_metrics")
    
    @task(8)
    def check_system_health(self):
        """Comprehensive health monitoring"""
        self.client.get("/health", name="admin_health")
    
    @task(5)
    def view_api_documentation(self):
        """Admins review API docs"""
        self.client.get("/docs", name="admin_docs")
    
    @task(3)
    def stress_test_opportunities(self):
        """Admin stress testing the opportunities endpoint"""
        for _ in range(3):  # Make 3 rapid requests
            with self.client.get("/api/opportunities", catch_response=True, 
                                 name="admin_stress_opportunities") as response:
                if response.status_code in [200, 401, 429]:  # 429 = rate limited
                    response.success()
                else:
                    response.failure(f"Unexpected status: {response.status_code}")


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Custom request logging"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 5000:  # Log slow requests (>5s)
        print(f"Slow request: {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("🚀 Starting bet-intel load test...")
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("🏁 Load test completed!")
    
    # Print summary statistics
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    
    # Fail the test if error rate is too high
    if stats.total.num_requests > 0:
        error_rate = stats.total.num_failures / stats.total.num_requests
        if error_rate > 0.05:  # Fail if >5% error rate
            print(f"❌ High error rate: {error_rate:.2%}")
            environment.process_exit_code = 1
        else:
            print(f"✅ Error rate acceptable: {error_rate:.2%}")


# Custom load test scenarios
class QuickLoadTest(HttpUser):
    """Quick load test for CI pipeline"""
    
    wait_time = between(0.1, 0.5)  # Very fast requests for CI
    
    @task
    def quick_health_check(self):
        """Fast health check"""
        self.client.get("/health", name="ci_health")
    
    @task
    def quick_homepage(self):
        """Fast homepage check"""
        self.client.get("/", name="ci_homepage")


if __name__ == "__main__":
    # Can be run directly for testing
    import subprocess
    import sys
    
    print("Running quick load test...")
    cmd = [
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--host", "http://localhost:8000",
        "--users", "10",
        "--spawn-rate", "2",
        "--run-time", "30s",
        "--headless"
    ]
    
    subprocess.run(cmd) 