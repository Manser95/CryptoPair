"""
Load testing configuration for ETH/USDT API
Simulates 300+ concurrent users to test high-load performance
"""
from locust import HttpUser, task, between
import random


class CryptoPriceUser(HttpUser):
    """Simulates a user fetching cryptocurrency prices"""
    
    # Wait between 1 and 5 seconds between requests
    wait_time = between(1, 5)
    
    # Define trading pairs to test
    trading_pairs = [
        "eth-usdt",
        "btc-usdt", 
        "bnb-usdt",
        "sol-usdt",
        "ada-usdt"
    ]
    
    @task(80)
    def get_eth_usdt_price(self):
        """Main task: Get ETH/USDT price (80% of requests)"""
        with self.client.get("/api/v1/prices/eth-usdt", 
                            catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "price" in data and data["price"] > 0:
                    response.success()
                else:
                    response.failure("Invalid price data")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(15)
    def get_random_price(self):
        """Secondary task: Get random trading pair price (15% of requests)"""
        pair = random.choice(self.trading_pairs)
        self.client.get(f"/api/v1/prices/{pair}")
    
    @task(5)
    def health_check(self):
        """Health check endpoint (5% of requests)"""
        self.client.get("/health/liveness")
    
    def on_start(self):
        """Called when a user starts"""
        # Warm up with a single request
        self.client.get("/health/readiness")


class HighLoadUser(HttpUser):
    """Simulates aggressive high-frequency trading bot behavior"""
    
    # Minimal wait time for stress testing
    wait_time = between(0.1, 0.5)
    
    @task
    def rapid_eth_usdt_check(self):
        """Rapid fire ETH/USDT price checks"""
        for _ in range(5):
            self.client.get("/api/v1/prices/eth-usdt", 
                          name="/api/v1/prices/eth-usdt [burst]")


class MixedLoadUser(HttpUser):
    """Simulates mixed load patterns"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Initialize user session"""
        self.pairs = ["eth-usdt", "btc-usdt", "bnb-usdt"]
        self.current_pair = 0
    
    @task(70)
    def sequential_price_check(self):
        """Check prices in sequence"""
        pair = self.pairs[self.current_pair]
        self.client.get(f"/api/v1/prices/{pair}")
        self.current_pair = (self.current_pair + 1) % len(self.pairs)
    
    @task(20)
    def parallel_price_check(self):
        """Check multiple prices quickly"""
        for pair in self.pairs[:2]:
            self.client.get(f"/api/v1/prices/{pair}",
                          name="/api/v1/prices/[parallel]")
    
    @task(10)
    def error_handling_check(self):
        """Test error handling with invalid pair"""
        self.client.get("/api/v1/prices/invalid-pair",
                      name="/api/v1/prices/[error-test]")


# Load test scenarios can be run with:
# 
# Basic test (300 users):
# locust -f locustfile.py --host=http://localhost:8000 --users=300 --spawn-rate=10
#
# Stress test (500 users):
# locust -f locustfile.py --host=http://localhost:8000 --users=500 --spawn-rate=20 --run-time=5m
#
# Endurance test (300 users for 30 minutes):
# locust -f locustfile.py --host=http://localhost:8000 --users=300 --spawn-rate=5 --run-time=30m
#
# Spike test (sudden load increase):
# locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=100 --run-time=2m
#
# High-load user specific test:
# locust -f locustfile.py --user-classes HighLoadUser --host=http://localhost:8000 --users=100 --spawn-rate=20
#
# Mixed load test:
# locust -f locustfile.py --user-classes MixedLoadUser --host=http://localhost:8000 --users=200 --spawn-rate=15