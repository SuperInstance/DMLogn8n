"""
Load testing file for DMLog using Locust

Tests system performance under various load scenarios including:
- User authentication and registration
- API endpoint performance
- Database query performance
- WebSocket connection handling
- Concurrent user scenarios
- Stress testing limits
"""

from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
import gevent
import random
import json
import time
from datetime import datetime


class DMLogLoadTest(HttpUser):
    """
    Load testing user for DMLog application
    Simulates realistic user behavior patterns
    """

    wait_time = between(1, 3)  # Realistic wait time between actions

    def on_start(self):
        """Called when a simulated user starts"""
        self.username = f"loadtest_user_{random.randint(1000, 9999)}"
        self.email = f"{self.username}@loadtest.com"
        self.password = "LoadTest123!"
        self.token = None
        self.character_id = None
        self.campaign_id = None

        # Register and login user
        self.register_user()
        self.login_user()

    def register_user(self):
        """Register a new user"""
        user_data = {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "display_name": f"Load Test {random.randint(1, 100)}"
        }

        response = self.client.post("/api/auth/register", json=user_data)
        if response.status_code == 201:
            self.logger.info(f"User {self.username} registered successfully")
        elif response.status_code == 400 and "already exists" in response.text:
            self.logger.info(f"User {self.username} already exists, proceeding to login")
        else:
            self.logger.error(f"Registration failed: {response.status_code} - {response.text}")

    def login_user(self):
        """Login user and store token"""
        login_data = {
            "username": self.username,
            "password": self.password
        }

        response = self.client.post("/api/auth/login", data=login_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            self.logger.info(f"User {self.username} logged in successfully")
        else:
            self.logger.error(f"Login failed: {response.status_code} - {response.text}")

    @task(10)
    def get_dashboard(self):
        """Get user dashboard - most common operation"""
        self.client.get("/api/dashboard")

    @task(8)
    def get_characters(self):
        """Get user's character list"""
        response = self.client.get("/api/characters")
        if response.status_code == 200:
            characters = response.json()
            if characters and not self.character_id:
                self.character_id = characters[0]["id"]

    @task(5)
    def create_character(self):
        """Create a new character"""
        if random.random() < 0.3:  # 30% chance to create character
            character_data = {
                "name": f"Character {random.randint(1, 1000)}",
                "race": random.choice(["Human", "Elf", "Dwarf", "Halfling", "Dragonborn"]),
                "class": random.choice(["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian"]),
                "level": random.randint(1, 5),
                "ability_scores": {
                    "strength": random.randint(8, 18),
                    "dexterity": random.randint(8, 18),
                    "constitution": random.randint(8, 18),
                    "intelligence": random.randint(8, 18),
                    "wisdom": random.randint(8, 18),
                    "charisma": random.randint(8, 18)
                },
                "max_hp": random.randint(8, 15),
                "current_hp": random.randint(1, 15),
                "armor_class": random.randint(10, 18),
                "speed": 30
            }

            response = self.client.post("/api/characters", json=character_data)
            if response.status_code == 201:
                self.character_id = response.json()["id"]

    @task(6)
    def get_character_details(self):
        """Get details of a specific character"""
        if self.character_id:
            self.client.get(f"/api/characters/{self.character_id}")

    @task(4)
    def update_character(self):
        """Update character details"""
        if self.character_id and random.random() < 0.4:  # 40% chance to update
            update_data = {
                "current_hp": random.randint(1, 20),
                "temp_hp": random.randint(0, 10),
                "experience_points": random.randint(0, 500)
            }

            self.client.patch(f"/api/characters/{self.character_id}", json=update_data)

    @task(7)
    def get_campaigns(self):
        """Get user's campaigns"""
        response = self.client.get("/api/campaigns")
        if response.status_code == 200:
            campaigns = response.json()
            if campaigns and not self.campaign_id:
                self.campaign_id = campaigns[0]["id"]

    @task(3)
    def create_campaign(self):
        """Create a new campaign"""
        if random.random() < 0.2:  # 20% chance to create campaign
            campaign_data = {
                "name": f"Campaign {random.randint(1, 1000)}",
                "description": "Load testing campaign",
                "setting": random.choice(["Forgotten Realms", "Eberron", "Dragonlance", "Greyhawk"]),
                "max_players": random.randint(3, 6),
                "is_public": random.choice([True, False]),
                "status": "planning"
            }

            response = self.client.post("/api/campaigns", json=campaign_data)
            if response.status_code == 201:
                self.campaign_id = response.json()["id"]

    @task(9)
    def roll_dice(self):
        """Roll dice - very common operation"""
        dice_types = ["1d20", "2d6", "1d8+3", "3d4", "1d12-1"]
        expressions = random.choices(dice_types, k=random.randint(1, 3))

        roll_data = {
            "expressions": expressions,
            "description": f"Load test roll {random.randint(1, 1000)}",
            "roll_type": random.choice(["attack", "damage", "saving_throw", "skill_check"])
        }

        if random.random() < 0.3:  # 30% chance for advantage/disadvantage
            roll_data["advantage"] = random.choice(["advantage", "disadvantage"])

        if random.random() < 0.2:  # 20% chance for DC
            roll_data["dc"] = random.randint(10, 20)

        self.client.post("/api/dice/roll", json=roll_data)

    @task(8)
    def validate_dice_formula(self):
        """Validate dice formulas"""
        formulas = [
            "1d20+5",
            "2d6kh1",
            "4d8dh1",
            "1d12+2d6",
            "3d4!6",
            "2d10r8min2",
            "invalid_formula"  # Test error handling
        ]

        formula_data = {"formula": random.choice(formulas)}
        self.client.post("/api/dice/validate", json=formula_data)

    @task(5)
    def get_campaign_details(self):
        """Get campaign details"""
        if self.campaign_id:
            self.client.get(f"/api/campaigns/{self.campaign_id}")

    @task(3)
    def get_campaign_sessions(self):
        """Get campaign game sessions"""
        if self.campaign_id:
            self.client.get(f"/api/campaigns/{self.campaign_id}/sessions")

    @task(4)
    def search_characters(self):
        """Search characters"""
        search_terms = ["test", "character", "hero", "adventurer", ""]
        search_term = random.choice(search_terms)

        params = {}
        if search_term:
            params["search"] = search_term

        if random.random() < 0.5:
            params["class"] = random.choice(["Fighter", "Wizard", "Rogue"])

        if random.random() < 0.3:
            params["level"] = str(random.randint(1, 20))

        self.client.get("/api/characters", params=params)

    @task(2)
    def get_user_profile(self):
        """Get user profile"""
        self.client.get("/api/auth/me")

    @task(1)
    def upload_character_avatar(self):
        """Upload character avatar (file upload test)"""
        if self.character_id and random.random() < 0.1:  # 10% chance
            # Create a small fake image
            fake_image_content = b"fake_image_content_for_testing"
            files = {
                "file": ("avatar.jpg", fake_image_content, "image/jpeg")
            }

            self.client.post(
                f"/api/characters/{self.character_id}/avatar",
                files=files
            )


class DatabaseLoadTest(HttpUser):
    """
    Database-specific load testing
    Focuses on database-intensive operations
    """

    wait_time = between(0.5, 2)
    weight = 1  # Lower weight than regular users

    def on_start(self):
        self.token = self.get_test_token()
        if self.token:
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    def get_test_token(self):
        """Get authentication token for testing"""
        response = self.client.post("/api/auth/login", data={
            "username": "loadtest_db_user",
            "password": "LoadTest123!"
        })
        return response.json().get("access_token") if response.status_code == 200 else None

    @task
    def create_test_data(self):
        """Create大量测试数据"""
        # Create multiple characters
        for i in range(5):
            character_data = {
                "name": f"DB Test Character {i}_{int(time.time())}",
                "race": "Human",
                "class": "Fighter",
                "level": 1,
                "ability_scores": {"strength": 16, "dexterity": 14, "constitution": 15,
                                 "intelligence": 12, "wisdom": 13, "charisma": 10},
                "max_hp": 12,
                "current_hp": 12
            }
            self.client.post("/api/characters", json=character_data)

    @task
    def complex_queries(self):
        """Test complex database queries"""
        # Search with multiple filters
        self.client.get("/api/characters", params={
            "search": "test",
            "class": "Fighter",
            "level_min": "1",
            "level_max": "10",
            "limit": "50",
            "offset": "0"
        })

        # Get campaigns with relationships
        self.client.get("/api/campaigns", params={
            "include": "characters,sessions",
            "status": "active"
        })

    @task
    def batch_operations(self):
        """Test batch operations"""
        # Create campaign with multiple characters
        campaign_data = {
            "name": f"Batch Test Campaign {int(time.time())}",
            "description": "Campaign for batch testing",
            "max_players": 6
        }

        response = self.client.post("/api/campaigns", json=campaign_data)
        if response.status_code == 201:
            campaign_id = response.json()["id"]

            # Add multiple characters to campaign
            characters_response = self.client.get("/api/characters", params={"limit": "5"})
            if characters_response.status_code == 200:
                characters = characters_response.json()
                for character in characters:
                    self.client.post(
                        f"/api/campaigns/{campaign_id}/characters",
                        json={"character_id": character["id"]}
                    )


class WebSocketLoadTest:
    """
    WebSocket load testing
    Tests real-time features under load
    """

    def __init__(self):
        self.connections = []

    def run_websocket_test(self, num_connections=100):
        """Run WebSocket load test"""
        import websockets
        import asyncio

        async def websocket_client(user_id):
            uri = f"ws://localhost:8000/ws?user_id={user_id}"
            try:
                async with websockets.connect(uri) as websocket:
                    # Send authentication
                    await websocket.send(json.dumps({
                        "type": "authenticate",
                        "token": "test_token"
                    }))

                    # Simulate dice rolls
                    for i in range(10):
                        await websocket.send(json.dumps({
                            "type": "dice_roll",
                            "data": {
                                "expressions": ["1d20"],
                                "description": f"WebSocket test roll {i}"
                            }
                        }))
                        response = await websocket.recv()

                        # Small delay between rolls
                        await asyncio.sleep(0.1)

            except Exception as e:
                print(f"WebSocket client {user_id} error: {e}")

        # Run multiple WebSocket clients
        async def run_test():
            tasks = []
            for i in range(num_connections):
                task = asyncio.create_task(websocket_client(f"ws_user_{i}"))
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Run the test
        asyncio.run(run_test())


class StressTestUser(HttpUser):
    """
    Stress testing user
    Pushes system to its limits
    """

    wait_time = between(0.1, 0.5)  # Very fast requests
    weight = 0.5  # Fewer stress test users

    def on_start(self):
        self.token = self.get_test_token()
        if self.token:
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    def get_test_token(self):
        response = self.client.post("/api/auth/login", data={
            "username": "stress_test_user",
            "password": "StressTest123!"
        })
        return response.json().get("access_token") if response.status_code == 200 else None

    @task
    def rapid_dice_rolls(self):
        """Very rapid dice rolling"""
        for _ in range(10):
            roll_data = {
                "expressions": ["1d20+5"],
                "description": "Stress test roll"
            }
            self.client.post("/api/dice/roll", json=roll_data)

    @task
    def rapid_character_creation(self):
        """Rapid character creation"""
        character_data = {
            "name": f"Stress Character {int(time.time() * 1000)}",
            "race": "Human",
            "class": "Fighter",
            "level": 1
        }
        self.client.post("/api/characters", json=character_data)

    @task
    def concurrent_requests(self):
        """Simulate concurrent requests"""
        import threading

        def make_request():
            self.client.get("/api/characters")

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


# Custom event handlers for reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, exception, **kwargs):
    """
    Custom request event handler
    Logs slow requests and errors
    """
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 2000:  # Log slow requests (>2 seconds)
        print(f"Slow request: {name} - {response_time:.2f}s")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called when a test starts
    """
    print("Starting DMLog load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when a test stops
    """
    print("DMLog load test completed.")

    # Print statistics summary
    stats = environment.stats
    print("\n=== Load Test Results ===")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"Requests per second: {stats.total.current_rps:.2f}")


# Test scenarios
class TestScenarios:
    """Define different test scenarios"""

    @staticmethod
    def light_load():
        """Light load test - 10 users for 5 minutes"""
        environment = Environment(user_classes=[DMLogLoadTest])
        environment.create_local_runner()
        environment.runner.start(10, spawn_rate=2)
        gevent.spawn_later(300, lambda: environment.runner.stop())
        environment.runner.greenlet.join()

    @staticmethod
    def moderate_load():
        """Moderate load test - 50 users for 10 minutes"""
        environment = Environment(user_classes=[DMLogLoadTest])
        environment.create_local_runner()
        environment.runner.start(50, spawn_rate=5)
        gevent.spawn_later(600, lambda: environment.runner.stop())
        environment.runner.greenlet.join()

    @staticmethod
    def heavy_load():
        """Heavy load test - 200 users for 15 minutes"""
        environment = Environment(user_classes=[DMLogLoadTest, DatabaseLoadTest])
        environment.create_local_runner()
        environment.runner.start(200, spawn_rate=10)
        gevent.spawn_later(900, lambda: environment.runner.stop())
        environment.runner.greenlet.join()

    @staticmethod
    def stress_test():
        """Stress test - 500 users for 5 minutes"""
        environment = Environment(user_classes=[DMLogLoadTest, StressTestUser])
        environment.create_local_runner()
        environment.runner.start(500, spawn_rate=50)
        gevent.spawn_later(300, lambda: environment.runner.stop())
        environment.runner.greenlet.join()

    @staticmethod
    def websocket_test():
        """WebSocket load test"""
        ws_test = WebSocketLoadTest()
        ws_test.run_websocket_test(num_connections=100)


if __name__ == "__main__":
    """Run load tests directly"""
    import sys

    if len(sys.argv) > 1:
        scenario = sys.argv[1]
        scenarios = {
            "light": TestScenarios.light_load,
            "moderate": TestScenarios.moderate_load,
            "heavy": TestScenarios.heavy_load,
            "stress": TestScenarios.stress_test,
            "websocket": TestScenarios.websocket_test
        }

        if scenario in scenarios:
            print(f"Running {scenario} load test...")
            scenarios[scenario]()
        else:
            print(f"Unknown scenario: {scenario}")
            print("Available scenarios: light, moderate, heavy, stress, websocket")
    else:
        print("Usage: python locustfile.py <scenario>")
        print("Available scenarios: light, moderate, heavy, stress, websocket")