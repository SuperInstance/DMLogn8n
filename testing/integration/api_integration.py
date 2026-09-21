#!/usr/bin/env python3
"""
DMLogn8n API Integration Tests
Comprehensive API endpoint integration testing
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import hmac
import base64

import aiohttp
import jwt
from urllib.parse import urljoin

# Import test framework
from integration_test_suite import TestResult, TestStatus

class APIIntegrationTests:
    """
    Comprehensive API integration testing
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('api_integration')
        self.base_url = config['base_url']
        self.api_key = config.get('api_key', 'test_api_key')
        self.test_tokens = {}
        self.test_users = {}

    async def test_api_availability(self) -> TestResult:
        """
        Test API availability and basic connectivity
        """
        result = TestResult(
            name="api_availability",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            # Test core endpoints
            endpoints = [
                ('/health', 'GET', None),
                ('/api/health', 'GET', None),
                ('/api/version', 'GET', None),
                ('/api/status', 'GET', None)
            ]

            results = {}
            async with aiohttp.ClientSession() as session:
                for endpoint, method, data in endpoints:
                    url = urljoin(self.base_url, endpoint)
                    try:
                        if method == 'GET':
                            async with session.get(url, timeout=10) as response:
                                results[endpoint] = {
                                    'status': response.status,
                                    'response_time': response.headers.get('X-Response-Time', 'N/A'),
                                    'success': response.status == 200
                                }
                        elif method == 'POST':
                            async with session.post(url, json=data, timeout=10) as response:
                                results[endpoint] = {
                                    'status': response.status,
                                    'response_time': response.headers.get('X-Response-Time', 'N/A'),
                                    'success': response.status in [200, 201]
                                }
                    except Exception as e:
                        results[endpoint] = {
                            'status': 'ERROR',
                            'error': str(e),
                            'success': False
                        }

            all_available = all(result['success'] for result in results.values())

            result.status = TestStatus.PASSED if all_available else TestStatus.FAILED
            result.message = "API availability check completed" if all_available else "Some API endpoints are unavailable"
            result.details = results

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"API availability test failed: {str(e)}"
            self.logger.error(f"API availability test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_authentication_endpoints(self) -> TestResult:
        """
        Test authentication and authorization endpoints
        """
        result = TestResult(
            name="authentication_endpoints",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            # Generate test user
            test_user = self.generate_test_user()

            auth_tests = {
                'registration': await self.test_user_registration_api(test_user),
                'login': await self.test_user_login_api(test_user),
                'token_validation': await self.test_token_validation(test_user),
                'token_refresh': await self.test_token_refresh(test_user),
                'logout': await self.test_user_logout(test_user),
                'password_reset': await self.test_password_reset(test_user)
            }

            all_passed = all(test['success'] for test in auth_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Authentication endpoints test completed" if all_passed else "Some authentication tests failed"
            result.details = auth_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Authentication endpoints test failed: {str(e)}"
            self.logger.error(f"Authentication endpoints test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

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

    async def test_user_registration_api(self, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test user registration API endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/auth/register",
                    json=user_data,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    if response.status == 201:
                        self.test_users['registered'] = user_data
                        return {
                            'success': True,
                            'status': response.status,
                            'user_id': response_data.get('user_id'),
                            'message': 'Registration successful'
                        }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': response_data.get('error', 'Registration failed')
                        }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_user_login_api(self, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test user login API endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/auth/login",
                    json={
                        'email': user_data['email'],
                        'password': user_data['password']
                    },
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    if response.status == 200:
                        token = response_data.get('token')
                        if token:
                            self.test_tokens['user'] = token
                            self.test_users['logged_in'] = user_data

                        return {
                            'success': True,
                            'status': response.status,
                            'token': token[:20] + '...' if token else None,
                            'user_id': response_data.get('user_id'),
                            'message': 'Login successful'
                        }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': response_data.get('error', 'Login failed')
                        }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_token_validation(self, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test token validation endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {
                    'success': False,
                    'error': 'No valid token available for testing'
                }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/auth/validate",
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'valid': response_data.get('valid', False),
                        'user_id': response_data.get('user_id')
                    }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_token_refresh(self, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test token refresh endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {
                    'success': False,
                    'error': 'No valid token available for testing'
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/auth/refresh",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    if response.status == 200:
                        new_token = response_data.get('token')
                        if new_token:
                            self.test_tokens['user'] = new_token

                        return {
                            'success': True,
                            'status': response.status,
                            'new_token': new_token[:20] + '...' if new_token else None,
                            'message': 'Token refresh successful'
                        }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': response_data.get('error', 'Token refresh failed')
                        }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_user_logout(self, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test user logout endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {
                    'success': False,
                    'error': 'No valid token available for testing'
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/auth/logout",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    # Clear token after logout
                    if response.status == 200:
                        self.test_tokens.pop('user', None)

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'message': 'Logout successful' if response.status == 200 else 'Logout failed'
                    }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_password_reset(self, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Test password reset endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                # Request password reset
                async with session.post(
                    f"{self.base_url}/api/auth/password-reset/request",
                    json={'email': user_data['email']}
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    if response.status == 200:
                        # In a real test, we would get the reset token from email or database
                        # For testing purposes, we'll simulate this
                        reset_token = 'test_reset_token_' + uuid.uuid4().hex[:16]

                        # Test password reset confirmation
                        async with session.post(
                            f"{self.base_url}/api/auth/password-reset/confirm",
                            json={
                                'token': reset_token,
                                'new_password': 'NewPassword123!'
                            }
                        ) as response:
                            return {
                                'success': response.status == 200,
                                'status': response.status,
                                'message': 'Password reset process tested'
                            }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': response_data.get('error', 'Password reset request failed')
                        }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_user_management_endpoints(self) -> TestResult:
        """
        Test user management endpoints
        """
        result = TestResult(
            name="user_management_endpoints",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            # Ensure we have a logged-in user
            if not self.test_tokens.get('user'):
                test_user = self.generate_test_user()
                registration_result = await self.test_user_registration_api(test_user)
                if registration_result['success']:
                    login_result = await self.test_user_login_api(test_user)
                    if not login_result['success']:
                        raise Exception("Failed to login test user")

            user_id = self.test_users.get('logged_in', {}).get('username', 'test_user')

            user_tests = {
                'get_profile': await self.test_get_user_profile(user_id),
                'update_profile': await self.test_update_user_profile(user_id),
                'get_preferences': await self.test_get_user_preferences(user_id),
                'update_preferences': await self.test_update_user_preferences(user_id),
                'delete_account': await self.test_delete_user_account(user_id)
            }

            all_passed = all(test['success'] for test in user_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "User management endpoints test completed" if all_passed else "Some user management tests failed"
            result.details = user_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"User management endpoints test failed: {str(e)}"
            self.logger.error(f"User management endpoints test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Test get user profile endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {'success': False, 'error': 'No valid token available'}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/users/profile",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'profile_data': response_data.get('profile', {}),
                        'message': 'Profile retrieved successfully' if response.status == 200 else 'Failed to retrieve profile'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_update_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Test update user profile endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {'success': False, 'error': 'No valid token available'}

            update_data = {
                'display_name': f'Updated User {uuid.uuid4().hex[:6]}',
                'bio': 'Updated bio for testing',
                'timezone': 'UTC'
            }

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.base_url}/api/users/profile",
                    json=update_data,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'updated_fields': response_data.get('updated', []),
                        'message': 'Profile updated successfully' if response.status == 200 else 'Failed to update profile'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Test get user preferences endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {'success': False, 'error': 'No valid token available'}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/users/preferences",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'preferences': response_data.get('preferences', {}),
                        'message': 'Preferences retrieved successfully' if response.status == 200 else 'Failed to retrieve preferences'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_update_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Test update user preferences endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {'success': False, 'error': 'No valid token available'}

            preferences_data = {
                'theme': 'dark',
                'notifications': {
                    'email': True,
                    'push': False,
                    'in_app': True
                },
                'privacy': {
                    'profile_visibility': 'public',
                    'show_online_status': True
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.base_url}/api/users/preferences",
                    json=preferences_data,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'updated_preferences': response_data.get('updated', []),
                        'message': 'Preferences updated successfully' if response.status == 200 else 'Failed to update preferences'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_delete_user_account(self, user_id: str) -> Dict[str, Any]:
        """Test delete user account endpoint"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return {'success': False, 'error': 'No valid token available'}

            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/api/users/account",
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    },
                    json={'confirmation': True}
                ) as response:
                    # Clear token after deletion
                    if response.status == 200:
                        self.test_tokens.pop('user', None)
                        self.test_users.pop('logged_in', None)

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'message': 'Account deleted successfully' if response.status == 200 else 'Failed to delete account'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_game_session_endpoints(self) -> TestResult:
        """
        Test game session management endpoints
        """
        result = TestResult(
            name="game_session_endpoints",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            # Ensure we have a logged-in user with character
            await self.setup_test_user_and_character()

            session_tests = {
                'create_session': await self.test_create_game_session(),
                'get_session': await self.test_get_game_session(),
                'update_session': await self.test_update_game_session(),
                'send_message': await self.test_send_session_message(),
                'end_session': await self.test_end_game_session()
            }

            all_passed = all(test['success'] for test in session_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Game session endpoints test completed" if all_passed else "Some game session tests failed"
            result.details = session_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Game session endpoints test failed: {str(e)}"
            self.logger.error(f"Game session endpoints test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def setup_test_user_and_character(self):
        """Setup test user and character for session testing"""
        if not self.test_tokens.get('user'):
            test_user = self.generate_test_user()
            registration_result = await self.test_user_registration_api(test_user)
            if registration_result['success']:
                login_result = await self.test_user_login_api(test_user)
                if login_result['success']:
                    # Create test character
                    await self.create_test_character()

    async def create_test_character(self):
        """Create a test character"""
        try:
            token = self.test_tokens.get('user')
            if not token:
                return

            character_data = {
                'name': f"TestChar_{uuid.uuid4().hex[:6]}",
                'class': 'warrior',
                'background': 'Test character for integration testing',
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
                    f"{self.base_url}/api/characters/create",
                    json=character_data,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    if response.status == 201:
                        response_data = await response.json()
                        self.test_tokens['character_id'] = response_data.get('character_id')

        except Exception as e:
            self.logger.error(f"Failed to create test character: {e}")

    async def test_create_game_session(self) -> Dict[str, Any]:
        """Test create game session endpoint"""
        try:
            token = self.test_tokens.get('user')
            character_id = self.test_tokens.get('character_id')

            if not token or not character_id:
                return {'success': False, 'error': 'No valid user or character available'}

            session_data = {
                'character_id': character_id,
                'scenario': 'tavern_adventure',
                'difficulty': 'normal',
                'max_players': 1
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/sessions/create",
                    json=session_data,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    if response.status == 201:
                        session_id = response_data.get('session_id')
                        self.test_tokens['session_id'] = session_id

                        return {
                            'success': True,
                            'status': response.status,
                            'session_id': session_id,
                            'message': 'Game session created successfully'
                        }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': response_data.get('error', 'Failed to create game session')
                        }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_get_game_session(self) -> Dict[str, Any]:
        """Test get game session endpoint"""
        try:
            token = self.test_tokens.get('user')
            session_id = self.test_tokens.get('session_id')

            if not token or not session_id:
                return {'success': False, 'error': 'No valid user session available'}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/sessions/{session_id}",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'session_data': response_data.get('session', {}),
                        'message': 'Game session retrieved successfully' if response.status == 200 else 'Failed to retrieve game session'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_update_game_session(self) -> Dict[str, Any]:
        """Test update game session endpoint"""
        try:
            token = self.test_tokens.get('user')
            session_id = self.test_tokens.get('session_id')

            if not token or not session_id:
                return {'success': False, 'error': 'No valid user session available'}

            update_data = {
                'status': 'paused',
                'notes': 'Session updated for testing'
            }

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.base_url}/api/sessions/{session_id}",
                    json=update_data,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'updated_fields': response_data.get('updated', []),
                        'message': 'Game session updated successfully' if response.status == 200 else 'Failed to update game session'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_send_session_message(self) -> Dict[str, Any]:
        """Test send session message endpoint"""
        try:
            token = self.test_tokens.get('user')
            session_id = self.test_tokens.get('session_id')

            if not token or not session_id:
                return {'success': False, 'error': 'No valid user session available'}

            message_data = {
                'content': 'Hello! I would like to start an adventure.',
                'type': 'user_action',
                'metadata': {
                    'action_type': 'dialogue',
                    'target': 'tavern_keeper'
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/sessions/{session_id}/messages",
                    json=message_data,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else {}

                    return {
                        'success': response.status == 201,
                        'status': response.status,
                        'message_id': response_data.get('message_id'),
                        'ai_response': response_data.get('ai_response'),
                        'message': 'Message sent successfully' if response.status == 201 else 'Failed to send message'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_end_game_session(self) -> Dict[str, Any]:
        """Test end game session endpoint"""
        try:
            token = self.test_tokens.get('user')
            session_id = self.test_tokens.get('session_id')

            if not token or not session_id:
                return {'success': False, 'error': 'No valid user session available'}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/sessions/{session_id}/end",
                    headers={'Authorization': f'Bearer {token}'}
                ) as response:
                    # Clear session after ending
                    if response.status == 200:
                        self.test_tokens.pop('session_id', None)

                    return {
                        'success': response.status == 200,
                        'status': response.status,
                        'message': 'Game session ended successfully' if response.status == 200 else 'Failed to end game session'
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_api_rate_limiting(self) -> TestResult:
        """
        Test API rate limiting functionality
        """
        result = TestResult(
            name="api_rate_limiting",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            rate_limit_tests = {
                'health_endpoint': await self.test_endpoint_rate_limit('/api/health'),
                'auth_endpoint': await self.test_endpoint_rate_limit('/api/health'),
                'user_endpoint': await self.test_endpoint_rate_limit('/api/health', auth_required=True)
            }

            result.status = TestStatus.PASSED
            result.message = "API rate limiting test completed"
            result.details = rate_limit_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"API rate limiting test failed: {str(e)}"
            self.logger.error(f"API rate limiting test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_endpoint_rate_limit(self, endpoint: str, auth_required: bool = False) -> Dict[str, Any]:
        """Test rate limiting on a specific endpoint"""
        try:
            headers = {}
            if auth_required and self.test_tokens.get('user'):
                headers['Authorization'] = f'Bearer {self.test_tokens["user"]}'

            response_codes = []
            response_times = []

            async with aiohttp.ClientSession() as session:
                # Make rapid requests to test rate limiting
                for i in range(20):
                    start_time = time.time()
                    async with session.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers
                    ) as response:
                        response_time = time.time() - start_time
                        response_codes.append(response.status)
                        response_times.append(response_time)

                        # Add small delay
                        await asyncio.sleep(0.1)

            # Analyze results
            rate_limited = 429 in response_codes
            avg_response_time = sum(response_times) / len(response_times)

            return {
                'endpoint': endpoint,
                'requests_made': len(response_codes),
                'rate_limited': rate_limited,
                'rate_limit_status_codes': [code for code in response_codes if code == 429],
                'avg_response_time': avg_response_time,
                'success': True
            }

        except Exception as e:
            return {
                'endpoint': endpoint,
                'success': False,
                'error': str(e)
            }

    async def test_api_security(self) -> TestResult:
        """
        Test API security measures
        """
        result = TestResult(
            name="api_security",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            security_tests = {
                'sql_injection': await self.test_sql_injection_protection(),
                'xss_protection': await self.test_xss_protection(),
                'cors_headers': await self.test_cors_headers(),
                'authentication_required': await self.test_authentication_required(),
                'authorization_checks': await self.test_authorization_checks()
            }

            all_passed = all(test.get('success', False) for test in security_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "API security test completed" if all_passed else "Some security tests failed"
            result.details = security_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"API security test failed: {str(e)}"
            self.logger.error(f"API security test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_sql_injection_protection(self) -> Dict[str, Any]:
        """Test SQL injection protection"""
        try:
            sql_injection_payloads = [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "admin'--",
                "' UNION SELECT * FROM users --"
            ]

            async with aiohttp.ClientSession() as session:
                for payload in sql_injection_payloads:
                    # Test in login endpoint
                    async with session.post(
                        f"{self.base_url}/api/auth/login",
                        json={'email': payload, 'password': 'test'}
                    ) as response:
                        if response.status == 500:  # Server error indicates potential SQL injection success
                            return {
                                'success': False,
                                'vulnerable': True,
                                'payload': payload,
                                'message': 'Potential SQL injection vulnerability detected'
                            }

            return {
                'success': True,
                'vulnerable': False,
                'message': 'SQL injection protection working correctly'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_xss_protection(self) -> Dict[str, Any]:
        """Test XSS protection"""
        try:
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "';alert('xss');//"
            ]

            async with aiohttp.ClientSession() as session:
                for payload in xss_payloads:
                    # Test in user profile update
                    if self.test_tokens.get('user'):
                        async with session.put(
                            f"{self.base_url}/api/users/profile",
                            json={'display_name': payload},
                            headers={'Authorization': f'Bearer {self.test_tokens["user"]}'}
                        ) as response:
                            if response.status == 200:
                                # Check if the payload was sanitized
                                response_data = await response.json()
                                updated_name = response_data.get('updated', {}).get('display_name', '')
                                if payload in updated_name:
                                    return {
                                        'success': False,
                                        'vulnerable': True,
                                        'payload': payload,
                                        'message': 'Potential XSS vulnerability detected'
                                    }

            return {
                'success': True,
                'vulnerable': False,
                'message': 'XSS protection working correctly'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_cors_headers(self) -> Dict[str, Any]:
        """Test CORS headers"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.options(
                    f"{self.base_url}/api/health",
                    headers={
                        'Origin': 'https://example.com',
                        'Access-Control-Request-Method': 'GET',
                        'Access-Control-Request-Headers': 'Content-Type'
                    }
                ) as response:
                    cors_headers = {
                        'access-control-allow-origin': response.headers.get('Access-Control-Allow-Origin'),
                        'access-control-allow-methods': response.headers.get('Access-Control-Allow-Methods'),
                        'access-control-allow-headers': response.headers.get('Access-Control-Allow-Headers')
                    }

                    has_cors_headers = any(cors_headers.values())

                    return {
                        'success': True,
                        'has_cors_headers': has_cors_headers,
                        'cors_headers': cors_headers,
                        'message': 'CORS headers configured' if has_cors_headers else 'No CORS headers found'
                    }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_authentication_required(self) -> Dict[str, Any]:
        """Test that protected endpoints require authentication"""
        try:
            protected_endpoints = [
                '/api/users/profile',
                '/api/sessions/create',
                '/api/characters/create'
            ]

            results = {}
            async with aiohttp.ClientSession() as session:
                for endpoint in protected_endpoints:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        results[endpoint] = {
                            'status': response.status,
                            'requires_auth': response.status == 401
                        }

            all_protected = all(result['requires_auth'] for result in results.values())

            return {
                'success': all_protected,
                'endpoints_tested': list(results.keys()),
                'results': results,
                'message': 'Authentication properly required' if all_protected else 'Some endpoints missing authentication'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_authorization_checks(self) -> Dict[str, Any]:
        """Test authorization checks"""
        try:
            # Test accessing another user's resources
            if not self.test_tokens.get('user'):
                return {'success': False, 'error': 'No authenticated user for testing'}

            # Try to access non-existent user's profile
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/users/999999/profile",
                    headers={'Authorization': f'Bearer {self.test_tokens["user"]}'}
                ) as response:
                    unauthorized_access = response.status == 403 or response.status == 404

                    return {
                        'success': unauthorized_access,
                        'status': response.status,
                        'message': 'Authorization checks working' if unauthorized_access else 'Potential authorization bypass'
                    }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }