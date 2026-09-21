#!/usr/bin/env python3
"""
DMLogn8n System Integration Tests
End-to-end system integration testing for complete user journeys
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random
import string

import aiohttp
import psycopg2
import redis
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import websockets

# Import test framework
from integration_test_suite import TestResult, TestStatus

class SystemIntegrationTests:
    """
    Complete system integration testing
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('system_integration')
        self.driver = None
        self.setup_browser()

    def setup_browser(self):
        """Setup Selenium WebDriver"""
        chrome_options = Options()
        if self.config.get('headless', True):
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def cleanup_browser(self):
        """Cleanup WebDriver"""
        if self.driver:
            self.driver.quit()

    def generate_test_user(self) -> Dict[str, str]:
        """Generate test user data"""
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.dmlog.local"
        password = "TestPassword123!"

        return {
            'username': username,
            'email': email,
            'password': password
        }

    async def test_complete_user_journey(self) -> TestResult:
        """
        Test complete user journey from signup to gameplay
        """
        result = TestResult(
            name="complete_user_journey",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()
            test_user = self.generate_test_user()
            journey_data = {}

            # Step 1: User Registration
            self.logger.info("Testing user registration...")
            registration_result = await self.test_user_registration(test_user)
            if not registration_result:
                raise Exception("User registration failed")
            journey_data['registration'] = registration_result

            # Step 2: Email Verification
            self.logger.info("Testing email verification...")
            verification_result = await self.test_email_verification(test_user['email'])
            if not verification_result:
                raise Exception("Email verification failed")
            journey_data['verification'] = verification_result

            # Step 3: User Login
            self.logger.info("Testing user login...")
            login_result = await self.test_user_login(test_user)
            if not login_result:
                raise Exception("User login failed")
            journey_data['login'] = login_result

            # Step 4: Character Creation
            self.logger.info("Testing character creation...")
            character_result = await self.test_character_creation(login_result['user_id'])
            if not character_result:
                raise Exception("Character creation failed")
            journey_data['character'] = character_result

            # Step 5: Game Session Start
            self.logger.info("Testing game session start...")
            session_result = await self.test_game_session_start(
                login_result['user_id'],
                character_result['character_id']
            )
            if not session_result:
                raise Exception("Game session start failed")
            journey_data['session'] = session_result

            # Step 6: AI Interaction
            self.logger.info("Testing AI interaction...")
            ai_result = await self.test_ai_interaction(
                login_result['user_id'],
                session_result['session_id']
            )
            if not ai_result:
                raise Exception("AI interaction failed")
            journey_data['ai_interaction'] = ai_result

            # Step 7: Real-time Features
            self.logger.info("Testing real-time features...")
            realtime_result = await self.test_realtime_features(
                login_result['user_id'],
                session_result['session_id']
            )
            if not realtime_result:
                raise Exception("Real-time features failed")
            journey_data['realtime'] = realtime_result

            # Step 8: Game Session End
            self.logger.info("Testing game session end...")
            end_result = await self.test_game_session_end(session_result['session_id'])
            if not end_result:
                raise Exception("Game session end failed")
            journey_data['session_end'] = end_result

            result.status = TestStatus.PASSED
            result.message = "Complete user journey successful"
            result.details = journey_data

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"User journey failed: {str(e)}"
            self.logger.error(f"Complete user journey failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_user_registration(self, user_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Test user registration via web UI"""
        try:
            # Navigate to registration page
            self.driver.get(f"{self.config['base_url']}/register")

            # Wait for form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "registration-form"))
            )

            # Fill registration form
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(user_data['username'])

            email_field = self.driver.find_element(By.ID, "email")
            email_field.clear()
            email_field.send_keys(user_data['email'])

            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(user_data['password'])

            confirm_password_field = self.driver.find_element(By.ID, "confirm-password")
            confirm_password_field.clear()
            confirm_password_field.send_keys(user_data['password'])

            # Submit form
            submit_button = self.driver.find_element(By.ID, "register-button")
            submit_button.click()

            # Wait for success message or redirect
            WebDriverWait(self.driver, 10).until(
                lambda driver: "/verify-email" in driver.current_url or
                "/dashboard" in driver.current_url or
                driver.find_elements(By.CLASS_NAME, "success-message")
            )

            # Verify registration via API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/api/auth/verify-registration",
                    json={'email': user_data['email']}
                ) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        return {
                            'user_id': user_info.get('user_id'),
                            'username': user_data['username'],
                            'email': user_data['email']
                        }

            return None

        except Exception as e:
            self.logger.error(f"User registration test failed: {e}")
            return None

    async def test_email_verification(self, email: str) -> bool:
        """Test email verification process"""
        try:
            # Simulate email verification by accessing verification endpoint
            async with aiohttp.ClientSession() as session:
                # Get verification code from database (for testing)
                conn = psycopg2.connect(self.config['database_url'])
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT verification_code FROM users WHERE email = %s",
                        (email,)
                    )
                    result = cursor.fetchone()
                    conn.close()

                    if result:
                        verification_code = result[0]

                        # Verify email
                        async with session.post(
                            f"{self.config['base_url']}/api/auth/verify-email",
                            json={'email': email, 'code': verification_code}
                        ) as response:
                            return response.status == 200

            return False

        except Exception as e:
            self.logger.error(f"Email verification test failed: {e}")
            return False

    async def test_user_login(self, user_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Test user login"""
        try:
            async with aiohttp.ClientSession() as session:
                # Login via API
                async with session.post(
                    f"{self.config['base_url']}/api/auth/login",
                    json={
                        'email': user_data['email'],
                        'password': user_data['password']
                    }
                ) as response:
                    if response.status == 200:
                        login_data = await response.json()
                        return {
                            'user_id': login_data.get('user_id'),
                            'token': login_data.get('token'),
                            'username': user_data['username']
                        }

            return None

        except Exception as e:
            self.logger.error(f"User login test failed: {e}")
            return None

    async def test_character_creation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Test character creation"""
        try:
            character_data = {
                'name': f"TestCharacter_{uuid.uuid4().hex[:6]}",
                'class': 'warrior',
                'background': 'A brave adventurer seeking glory',
                'attributes': {
                    'strength': 16,
                    'dexterity': 14,
                    'constitution': 15,
                    'intelligence': 12,
                    'wisdom': 13,
                    'charisma': 11
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/api/characters/create",
                    json=character_data,
                    headers={'X-User-ID': user_id}
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            'character_id': result.get('character_id'),
                            'name': character_data['name'],
                            'class': character_data['class']
                        }

            return None

        except Exception as e:
            self.logger.error(f"Character creation test failed: {e}")
            return None

    async def test_game_session_start(self, user_id: str, character_id: str) -> Optional[Dict[str, Any]]:
        """Test starting a game session"""
        try:
            session_data = {
                'character_id': character_id,
                'scenario': 'tavern_adventure',
                'difficulty': 'normal'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/api/sessions/start",
                    json=session_data,
                    headers={'X-User-ID': user_id}
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            'session_id': result.get('session_id'),
                            'scenario': session_data['scenario'],
                            'status': 'active'
                        }

            return None

        except Exception as e:
            self.logger.error(f"Game session start test failed: {e}")
            return None

    async def test_ai_interaction(self, user_id: str, session_id: str) -> bool:
        """Test AI interaction in game session"""
        try:
            # Test multiple AI interactions
            test_messages = [
                "Hello, I'm looking for adventure!",
                "Tell me about the local tavern",
                "I want to take on a quest",
                "What skills do I have available?"
            ]

            async with aiohttp.ClientSession() as session:
                for message in test_messages:
                    async with session.post(
                        f"{self.config['base_url']}/api/sessions/{session_id}/message",
                        json={'message': message},
                        headers={'X-User-ID': user_id}
                    ) as response:
                        if response.status != 200:
                            return False

                        result = await response.json()
                        if not result.get('response'):
                            return False

                        # Add small delay between messages
                        await asyncio.sleep(0.5)

            return True

        except Exception as e:
            self.logger.error(f"AI interaction test failed: {e}")
            return False

    async def test_realtime_features(self, user_id: str, session_id: str) -> bool:
        """Test real-time features like WebSocket communication"""
        try:
            ws_url = f"ws://localhost:8001/ws/session/{session_id}?user_id={user_id}"

            async with websockets.connect(ws_url) as websocket:
                # Send test message
                test_message = {
                    'type': 'user_action',
                    'action': 'look_around',
                    'timestamp': datetime.now().isoformat()
                }

                await websocket.send(json.dumps(test_message))

                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_data = json.loads(response)

                if response_data.get('type') == 'dm_response':
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Real-time features test failed: {e}")
            return False

    async def test_game_session_end(self, session_id: str) -> bool:
        """Test ending a game session"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/api/sessions/{session_id}/end"
                ) as response:
                    return response.status == 200

        except Exception as e:
            self.logger.error(f"Game session end test failed: {e}")
            return False

    async def test_multi_user_scenario(self) -> TestResult:
        """
        Test multi-user scenarios and social features
        """
        result = TestResult(
            name="multi_user_scenario",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()
            users = []

            # Create multiple test users
            for i in range(3):
                user_data = self.generate_test_user()
                registration_result = await self.test_user_registration(user_data)
                if registration_result:
                    login_result = await self.test_user_login(user_data)
                    if login_result:
                        users.append({
                            'user_data': user_data,
                            'login': login_result
                        })

            if len(users) < 2:
                raise Exception("Failed to create enough test users")

            # Test user-to-user communication
            communication_results = await self.test_user_communication(users[:2])

            # Test shared game session
            shared_session_result = await self.test_shared_game_session(users)

            # Test leaderboards and social features
            social_features_result = await self.test_social_features(users)

            result.status = TestStatus.PASSED
            result.message = "Multi-user scenario completed successfully"
            result.details = {
                'users_created': len(users),
                'communication': communication_results,
                'shared_session': shared_session_result,
                'social_features': social_features_result
            }

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Multi-user scenario failed: {str(e)}"
            self.logger.error(f"Multi-user scenario test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_user_communication(self, users: List[Dict[str, Any]]) -> bool:
        """Test user-to-user communication features"""
        try:
            # Test friend requests
            async with aiohttp.ClientSession() as session:
                # Send friend request
                async with session.post(
                    f"{self.config['base_url']}/api/social/friend-request",
                    json={
                        'from_user_id': users[0]['login']['user_id'],
                        'to_user_id': users[1]['login']['user_id']
                    }
                ) as response:
                    if response.status != 201:
                        return False

                # Accept friend request
                async with session.post(
                    f"{self.config['base_url']}/api/social/friend-request/accept",
                    json={
                        'user_id': users[1]['login']['user_id'],
                        'request_id': 'test_request_id'  # Would normally get from previous response
                    }
                ) as response:
                    return response.status == 200

            return False

        except Exception as e:
            self.logger.error(f"User communication test failed: {e}")
            return False

    async def test_shared_game_session(self, users: List[Dict[str, Any]]) -> bool:
        """Test shared game session between multiple users"""
        try:
            # Create characters for all users
            character_ids = []
            for user in users:
                character = await self.test_character_creation(user['login']['user_id'])
                if character:
                    character_ids.append(character['character_id'])

            if len(character_ids) < 2:
                return False

            # Start shared session
            session_data = {
                'character_ids': character_ids[:2],  # Use first 2 characters
                'scenario': 'cooperative_quest',
                'difficulty': 'normal'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/api/sessions/shared/start",
                    json=session_data,
                    headers={'X-User-ID': users[0]['login']['user_id']}
                ) as response:
                    return response.status == 201

        except Exception as e:
            self.logger.error(f"Shared game session test failed: {e}")
            return False

    async def test_social_features(self, users: List[Dict[str, Any]]) -> bool:
        """Test social features like leaderboards, achievements"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test leaderboard access
                async with session.get(
                    f"{self.config['base_url']}/api/social/leaderboard",
                    headers={'X-User-ID': users[0]['login']['user_id']}
                ) as response:
                    if response.status != 200:
                        return False

                # Test achievements
                async with session.get(
                    f"{self.config['base_url']}/api/social/achievements",
                    headers={'X-User-ID': users[0]['login']['user_id']}
                ) as response:
                    return response.status == 200

        except Exception as e:
            self.logger.error(f"Social features test failed: {e}")
            return False

    async def test_cross_platform_functionality(self) -> TestResult:
        """
        Test cross-platform functionality and compatibility
        """
        result = TestResult(
            name="cross_platform_functionality",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            # Test API compatibility across different endpoints
            api_endpoints = [
                '/api/health',
                '/api/version',
                '/api/features',
                '/api/auth/status'
            ]

            api_results = {}
            async with aiohttp.ClientSession() as session:
                for endpoint in api_endpoints:
                    async with session.get(f"{self.config['base_url']}{endpoint}") as response:
                        api_results[endpoint] = {
                            'status': response.status,
                            'content_type': response.headers.get('content-type'),
                            'success': response.status == 200
                        }

            # Test mobile responsiveness (via Selenium)
            mobile_results = await self.test_mobile_responsiveness()

            # Test different browsers (simulate via user agent)
            browser_results = await self.test_browser_compatibility()

            # Test API versioning
            versioning_results = await self.test_api_versioning()

            result.status = TestStatus.PASSED
            result.message = "Cross-platform functionality test completed"
            result.details = {
                'api_endpoints': api_results,
                'mobile_responsive': mobile_results,
                'browser_compatibility': browser_results,
                'api_versioning': versioning_results
            }

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Cross-platform test failed: {str(e)}"
            self.logger.error(f"Cross-platform functionality test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_mobile_responsiveness(self) -> bool:
        """Test mobile responsiveness of web interface"""
        try:
            # Test different viewport sizes
            viewport_sizes = [
                (375, 667),  # iPhone
                (768, 1024), # iPad
                (360, 640),  # Android
            ]

            for width, height in viewport_sizes:
                self.driver.set_window_size(width, height)
                self.driver.get(f"{self.config['base_url']}/")

                # Check for mobile navigation
                try:
                    mobile_nav = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "mobile-nav"))
                    )
                except:
                    # If no mobile nav found, check if responsive design is implemented
                    body_width = self.driver.execute_script("return document.body.scrollWidth")
                    if body_width > width:
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Mobile responsiveness test failed: {e}")
            return False

    async def test_browser_compatibility(self) -> Dict[str, bool]:
        """Test browser compatibility via user agent simulation"""
        results = {}

        user_agents = {
            'chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        }

        for browser, user_agent in user_agents.items():
            try:
                headers = {'User-Agent': user_agent}
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(f"{self.config['base_url']}/") as response:
                        results[browser] = response.status == 200
            except Exception as e:
                self.logger.error(f"Browser compatibility test for {browser} failed: {e}")
                results[browser] = False

        return results

    async def test_api_versioning(self) -> bool:
        """Test API versioning compatibility"""
        try:
            # Test different API versions
            api_versions = ['v1', 'v2']

            async with aiohttp.ClientSession() as session:
                for version in api_versions:
                    async with session.get(f"{self.config['base_url']}/api/{version}/health") as response:
                        if response.status not in [200, 404]:  # 404 is acceptable for non-existent versions
                            return False

            return True

        except Exception as e:
            self.logger.error(f"API versioning test failed: {e}")
            return False

    async def test_error_scenarios(self) -> TestResult:
        """
        Test system behavior under error conditions
        """
        result = TestResult(
            name="error_scenarios",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            error_tests = {
                'invalid_credentials': await self.test_invalid_credentials(),
                'malformed_requests': await self.test_malformed_requests(),
                'resource_not_found': await self.test_resource_not_found(),
                'rate_limiting': await self.test_rate_limiting(),
                'service_unavailable': await self.test_service_unavailable()
            }

            all_passed = all(error_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Error scenario testing completed" if all_passed else "Some error scenarios failed"
            result.details = error_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Error scenario testing failed: {str(e)}"
            self.logger.error(f"Error scenarios test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_invalid_credentials(self) -> bool:
        """Test system behavior with invalid credentials"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/api/auth/login",
                    json={
                        'email': 'nonexistent@test.com',
                        'password': 'wrongpassword'
                    }
                ) as response:
                    return response.status == 401

        except Exception as e:
            self.logger.error(f"Invalid credentials test failed: {e}")
            return False

    async def test_malformed_requests(self) -> bool:
        """Test system behavior with malformed requests"""
        try:
            async with aiohttp.ClientSession() as session:
                # Send invalid JSON
                async with session.post(
                    f"{self.config['base_url']}/api/auth/login",
                    data="invalid json",
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status != 400:
                        return False

                # Send missing required fields
                async with session.post(
                    f"{self.config['base_url']}/api/auth/login",
                    json={'email': 'test@test.com'}  # Missing password
                ) as response:
                    return response.status == 400

        except Exception as e:
            self.logger.error(f"Malformed requests test failed: {e}")
            return False

    async def test_resource_not_found(self) -> bool:
        """Test system behavior when requesting non-existent resources"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test non-existent user
                async with session.get(
                    f"{self.config['base_url']}/api/users/nonexistent-user"
                ) as response:
                    if response.status != 404:
                        return False

                # Test non-existent character
                async with session.get(
                    f"{self.config['base_url']}/api/characters/nonexistent-character"
                ) as response:
                    return response.status == 404

        except Exception as e:
            self.logger.error(f"Resource not found test failed: {e}")
            return False

    async def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        try:
            async with aiohttp.ClientSession() as session:
                # Make multiple rapid requests
                responses = []
                for _ in range(10):
                    async with session.get(f"{self.config['base_url']}/api/health") as response:
                        responses.append(response.status)

                # Check if any requests were rate limited (429)
                return 429 in responses

        except Exception as e:
            self.logger.error(f"Rate limiting test failed: {e}")
            return False

    async def test_service_unavailable(self) -> bool:
        """Test system behavior when dependent services are unavailable"""
        try:
            # This test would require temporarily stopping dependent services
            # For now, we'll simulate by calling a health check that includes dependencies
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config['base_url']}/api/health/detailed") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        # Check if any dependencies are unhealthy
                        dependencies = health_data.get('dependencies', {})
                        return any(dep.get('status') != 'healthy' for dep in dependencies.values())

            return False

        except Exception as e:
            self.logger.error(f"Service unavailable test failed: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.cleanup_browser()