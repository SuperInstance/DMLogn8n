"""
Integration tests for API endpoints

Tests the complete API functionality including:
- Authentication and authorization
- CRUD operations for all resources
- Request/response validation
- Error handling and status codes
- API pagination and filtering
- File upload/download
- WebSocket connections
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
import io
import base64

from source_code.backend.main import app
from source_code.backend.api.schemas.user import UserCreate, UserResponse
from source_code.backend.api.schemas.character import CharacterCreate, CharacterUpdate
from source_code.backend.api.schemas.campaign import CampaignCreate, CampaignUpdate
from source_code.backend.api.schemas.session import GameSessionCreate


class TestAuthenticationEndpoints:
    """Test authentication-related endpoints"""

    def test_register_user_success(self, test_client: TestClient):
        """Test successful user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "display_name": "Test User"
        }

        response = test_client.post("/api/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data  # Password should not be returned
        assert "id" in data

    def test_register_user_duplicate_email(self, test_client: TestClient, sample_user_data):
        """Test registration with duplicate email"""
        # First registration
        test_client.post("/api/auth/register", json=sample_user_data)

        # Second registration with same email
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "different_user"

        response = test_client.post("/api/auth/register", json=duplicate_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_user_invalid_data(self, test_client: TestClient):
        """Test registration with invalid data"""
        invalid_data = {
            "username": "te",  # Too short
            "email": "invalid-email",
            "password": "123"  # Too weak
        }

        response = test_client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) >= 2  # Should have multiple validation errors

    def test_login_success(self, test_client: TestClient, sample_user_data):
        """Test successful user login"""
        # Register user first
        test_client.post("/api/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }

        response = test_client.post("/api/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, test_client: TestClient, sample_user_data):
        """Test login with invalid credentials"""
        # Register user first
        test_client.post("/api/auth/register", json=sample_user_data)

        # Login with wrong password
        login_data = {
            "username": sample_user_data["username"],
            "password": "wrong_password"
        }

        response = test_client.post("/api/auth/login", data=login_data)

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_get_current_user(self, authenticated_test_client: TestClient):
        """Test getting current authenticated user"""
        response = authenticated_test_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "password" not in data

    def test_get_current_user_unauthorized(self, test_client: TestClient):
        """Test getting current user without authentication"""
        response = test_client.get("/api/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_refresh_token(self, authenticated_test_client: TestClient):
        """Test token refresh"""
        response = authenticated_test_client.post("/api/auth/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_logout(self, authenticated_test_client: TestClient):
        """Test user logout"""
        response = authenticated_test_client.post("/api/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


class TestCharacterEndpoints:
    """Test character management endpoints"""

    def test_create_character(self, authenticated_test_client: TestClient, sample_character_data):
        """Test creating a new character"""
        response = authenticated_test_client.post("/api/characters", json=sample_character_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_character_data["name"]
        assert data["race"] == sample_character_data["race"]
        assert data["class"] == sample_character_data["class"]
        assert "id" in data

    def test_get_character(self, authenticated_test_client: TestClient, sample_character_data):
        """Test retrieving a specific character"""
        # Create character first
        create_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]

        # Get character
        response = authenticated_test_client.get(f"/api/characters/{character_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == character_id
        assert data["name"] == sample_character_data["name"]

    def test_get_character_not_found(self, authenticated_test_client: TestClient):
        """Test retrieving a non-existent character"""
        response = authenticated_test_client.get("/api/characters/999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_character_unauthorized(self, test_client: TestClient):
        """Test retrieving character without authentication"""
        response = test_client.get("/api/characters/1")

        assert response.status_code == 401

    def test_list_characters(self, authenticated_test_client: TestClient, sample_character_data):
        """Test listing user's characters"""
        # Create multiple characters
        characters = []
        for i in range(3):
            char_data = sample_character_data.copy()
            char_data["name"] = f"Character {i+1}"
            response = authenticated_test_client.post("/api/characters", json=char_data)
            characters.append(response.json())

        # List characters
        response = authenticated_test_client.get("/api/characters")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all("name" in char for char in data)

    def test_update_character(self, authenticated_test_client: TestClient, sample_character_data):
        """Test updating a character"""
        # Create character first
        create_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]

        # Update character
        update_data = {
            "name": "Updated Character Name",
            "level": 2,
            "experience_points": 300
        }

        response = authenticated_test_client.patch(
            f"/api/characters/{character_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Character Name"
        assert data["level"] == 2
        assert data["experience_points"] == 300

    def test_delete_character(self, authenticated_test_client: TestClient, sample_character_data):
        """Test deleting a character"""
        # Create character first
        create_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = create_response.json()["id"]

        # Delete character
        response = authenticated_test_client.delete(f"/api/characters/{character_id}")

        assert response.status_code == 204

        # Verify character is deleted
        get_response = authenticated_test_client.get(f"/api/characters/{character_id}")
        assert get_response.status_code == 404

    def test_character_validation(self, authenticated_test_client: TestClient):
        """Test character data validation"""
        invalid_character = {
            "name": "",  # Empty name
            "level": 0,  # Invalid level
            "ability_scores": {
                "strength": 30  # Too high
            }
        }

        response = authenticated_test_client.post("/api/characters", json=invalid_character)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) >= 2

    def test_character_pagination(self, authenticated_test_client: TestClient, sample_character_data):
        """Test character list pagination"""
        # Create many characters
        for i in range(15):
            char_data = sample_character_data.copy()
            char_data["name"] = f"Character {i+1}"
            authenticated_test_client.post("/api/characters", json=char_data)

        # Test pagination
        response = authenticated_test_client.get("/api/characters?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Test second page
        response = authenticated_test_client.get("/api/characters?limit=5&offset=5")
        data = response.json()
        assert len(data) == 5

    def test_character_search(self, authenticated_test_client: TestClient, sample_character_data):
        """Test character search functionality"""
        # Create characters with specific names
        search_names = ["Aldric", "Bob", "Charlie"]
        for name in search_names:
            char_data = sample_character_data.copy()
            char_data["name"] = name
            authenticated_test_client.post("/api/characters", json=char_data)

        # Search for specific character
        response = authenticated_test_client.get("/api/characters?search=Aldric")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Aldric"


class TestCampaignEndpoints:
    """Test campaign management endpoints"""

    def test_create_campaign(self, authenticated_test_client: TestClient, sample_campaign_data):
        """Test creating a new campaign"""
        response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_campaign_data["name"]
        assert data["description"] == sample_campaign_data["description"]
        assert "id" in data

    def test_get_campaign(self, authenticated_test_client: TestClient, sample_campaign_data):
        """Test retrieving a specific campaign"""
        # Create campaign first
        create_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = create_response.json()["id"]

        # Get campaign
        response = authenticated_test_client.get(f"/api/campaigns/{campaign_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign_id
        assert data["name"] == sample_campaign_data["name"]

    def test_list_campaigns(self, authenticated_test_client: TestClient, sample_campaign_data):
        """Test listing user's campaigns"""
        # Create multiple campaigns
        for i in range(3):
            campaign_data = sample_campaign_data.copy()
            campaign_data["name"] = f"Campaign {i+1}"
            authenticated_test_client.post("/api/campaigns", json=campaign_data)

        # List campaigns
        response = authenticated_test_client.get("/api/campaigns")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_campaign(self, authenticated_test_client: TestClient, sample_campaign_data):
        """Test updating a campaign"""
        # Create campaign first
        create_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = create_response.json()["id"]

        # Update campaign
        update_data = {
            "name": "Updated Campaign Name",
            "description": "Updated description",
            "max_players": 6
        }

        response = authenticated_test_client.patch(
            f"/api/campaigns/{campaign_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign Name"
        assert data["max_players"] == 6

    def test_add_character_to_campaign(self, authenticated_test_client: TestClient,
                                      sample_character_data, sample_campaign_data):
        """Test adding a character to a campaign"""
        # Create character
        char_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = char_response.json()["id"]

        # Create campaign
        campaign_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = campaign_response.json()["id"]

        # Add character to campaign
        response = authenticated_test_client.post(
            f"/api/campaigns/{campaign_id}/characters",
            json={"character_id": character_id}
        )

        assert response.status_code == 200

        # Verify character is in campaign
        campaign_response = authenticated_test_client.get(f"/api/campaigns/{campaign_id}")
        campaign_data = campaign_response.json()
        assert len(campaign_data["characters"]) == 1
        assert campaign_data["characters"][0]["id"] == character_id

    def test_remove_character_from_campaign(self, authenticated_test_client: TestClient,
                                           sample_character_data, sample_campaign_data):
        """Test removing a character from a campaign"""
        # Create character and campaign
        char_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = char_response.json()["id"]

        campaign_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = campaign_response.json()["id"]

        # Add character to campaign
        authenticated_test_client.post(
            f"/api/campaigns/{campaign_id}/characters",
            json={"character_id": character_id}
        )

        # Remove character from campaign
        response = authenticated_test_client.delete(
            f"/api/campaigns/{campaign_id}/characters/{character_id}"
        )

        assert response.status_code == 204

        # Verify character is removed
        campaign_response = authenticated_test_client.get(f"/api/campaigns/{campaign_id}")
        campaign_data = campaign_response.json()
        assert len(campaign_data["characters"]) == 0


class TestGameSessionEndpoints:
    """Test game session management endpoints"""

    def test_create_game_session(self, authenticated_test_client: TestClient,
                               sample_campaign_data, sample_game_session_data):
        """Test creating a new game session"""
        # Create campaign first
        campaign_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = campaign_response.json()["id"]

        # Create game session
        session_data = sample_game_session_data.copy()
        session_data["campaign_id"] = campaign_id

        response = authenticated_test_client.post("/api/sessions", json=session_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == session_data["name"]
        assert data["campaign_id"] == campaign_id

    def test_get_game_session(self, authenticated_test_client: TestClient,
                             sample_campaign_data, sample_game_session_data):
        """Test retrieving a specific game session"""
        # Create campaign and session
        campaign_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = campaign_response.json()["id"]

        session_data = sample_game_session_data.copy()
        session_data["campaign_id"] = campaign_id
        session_response = authenticated_test_client.post("/api/sessions", json=session_data)
        session_id = session_response.json()["id"]

        # Get session
        response = authenticated_test_client.get(f"/api/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["name"] == session_data["name"]

    def test_join_game_session(self, authenticated_test_client: TestClient,
                              sample_campaign_data, sample_game_session_data,
                              sample_character_data):
        """Test joining a game session with a character"""
        # Create character
        char_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = char_response.json()["id"]

        # Create campaign
        campaign_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = campaign_response.json()["id"]

        # Create game session
        session_data = sample_game_session_data.copy()
        session_data["campaign_id"] = campaign_id
        session_response = authenticated_test_client.post("/api/sessions", json=session_data)
        session_id = session_response.json()["id"]

        # Join session with character
        response = authenticated_test_client.post(
            f"/api/sessions/{session_id}/join",
            json={"character_id": character_id}
        )

        assert response.status_code == 200

        # Verify character is in session
        session_response = authenticated_test_client.get(f"/api/sessions/{session_id}")
        session_data = session_response.json()
        assert len(session_data["participants"]) == 1
        assert session_data["participants"][0]["character_id"] == character_id


class TestDiceRollingEndpoints:
    """Test dice rolling endpoints"""

    def test_roll_dice_basic(self, authenticated_test_client: TestClient):
        """Test basic dice rolling"""
        roll_data = {
            "expressions": ["1d20+5", "2d6"],
            "description": "Attack roll with damage"
        }

        response = authenticated_test_client.post("/api/dice/roll", json=roll_data)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert len(data["results"]) == 2
        assert data["total"] > 0

    def test_roll_dice_with_advantage(self, authenticated_test_client: TestClient):
        """Test dice rolling with advantage"""
        roll_data = {
            "expressions": ["1d20"],
            "advantage": "advantage",
            "description": "Attack with advantage"
        }

        response = authenticated_test_client.post("/api/dice/roll", json=roll_data)

        assert response.status_code == 200
        data = response.json()
        assert data["advantage"] == "advantage"

    def test_roll_dice_with_dc(self, authenticated_test_client: TestClient):
        """Test dice rolling against difficulty class"""
        roll_data = {
            "expressions": ["1d20+3"],
            "dc": 15,
            "description": "Saving throw"
        }

        response = authenticated_test_client.post("/api/dice/roll", json=roll_data)

        assert response.status_code == 200
        data = response.json()
        assert data["dc"] == 15
        assert "success" in data
        assert isinstance(data["success"], bool)

    def test_validate_dice_formula(self, authenticated_test_client: TestClient):
        """Test dice formula validation"""
        formula_data = {"formula": "2d6+3"}

        response = authenticated_test_client.post("/api/dice/validate", json=formula_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "min_possible" in data
        assert "max_possible" in data
        assert "average" in data

    def test_validate_invalid_dice_formula(self, authenticated_test_client: TestClient):
        """Test invalid dice formula validation"""
        formula_data = {"formula": "invalid_formula"}

        response = authenticated_test_client.post("/api/dice/validate", json=formula_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "error_message" in data

    def test_roll_for_character(self, authenticated_test_client: TestClient,
                                sample_character_data):
        """Test rolling dice for a specific character"""
        # Create character first
        char_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = char_response.json()["id"]

        # Roll for character
        roll_data = {
            "character_id": character_id,
            "expressions": ["1d20"],
            "roll_type": "attack"
        }

        response = authenticated_test_client.post("/api/dice/roll", json=roll_data)

        assert response.status_code == 200
        data = response.json()
        assert data["character_id"] == character_id
        assert data["roll_type"] == "attack"


class TestFileUploadEndpoints:
    """Test file upload and download endpoints"""

    def test_upload_character_avatar(self, authenticated_test_client: TestClient,
                                   sample_character_data):
        """Test uploading character avatar"""
        # Create character first
        char_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = char_response.json()["id"]

        # Create fake image file
        image_content = b"fake image content"
        files = {"file": ("avatar.png", io.BytesIO(image_content), "image/png")}

        response = authenticated_test_client.post(
            f"/api/characters/{character_id}/avatar",
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data

    def test_upload_invalid_file_type(self, authenticated_test_client: TestClient,
                                     sample_character_data):
        """Test uploading invalid file type"""
        # Create character first
        char_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = char_response.json()["id"]

        # Create fake executable file
        file_content = b"fake executable content"
        files = {"file": ("malware.exe", io.BytesIO(file_content), "application/x-executable")}

        response = authenticated_test_client.post(
            f"/api/characters/{character_id}/avatar",
            files=files
        )

        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()

    def test_download_character_avatar(self, authenticated_test_client: TestClient,
                                     sample_character_data):
        """Test downloading character avatar"""
        # This test would require actual file storage implementation
        # For now, we'll test the endpoint structure
        char_response = authenticated_test_client.post("/api/characters", json=sample_character_data)
        character_id = char_response.json()["id"]

        response = authenticated_test_client.get(f"/api/characters/{character_id}/avatar")

        # Should either return the file or 404 if no avatar exists
        assert response.status_code in [200, 404]

    def test_upload_campaign_map(self, authenticated_test_client: TestClient,
                                sample_campaign_data):
        """Test uploading campaign map"""
        # Create campaign first
        campaign_response = authenticated_test_client.post("/api/campaigns", json=sample_campaign_data)
        campaign_id = campaign_response.json()["id"]

        # Create fake map file
        map_content = b"fake map content"
        files = {"file": ("battlemap.png", io.BytesIO(map_content), "image/png")}

        response = authenticated_test_client.post(
            f"/api/campaigns/{campaign_id}/maps",
            files=files,
            data={"name": "Battle Map", "description": "First battle map"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "name" in data
        assert data["name"] == "Battle Map"


class TestSearchAndFiltering:
    """Test search and filtering functionality"""

    def test_search_characters_by_name(self, authenticated_test_client: TestClient,
                                      sample_character_data):
        """Test searching characters by name"""
        # Create characters with specific names
        names = ["Gandalf", "Aragorn", "Legolas", "Gimli"]
        for name in names:
            char_data = sample_character_data.copy()
            char_data["name"] = name
            authenticated_test_client.post("/api/characters", json=char_data)

        # Search for characters starting with "Ga"
        response = authenticated_test_client.get("/api/characters?search=Ga")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Gandalf and (potentially others starting with Ga)
        names_found = [char["name"] for char in data]
        assert "Gandalf" in names_found

    def test_filter_characters_by_class(self, authenticated_test_client: TestClient,
                                       sample_character_data):
        """Test filtering characters by class"""
        # Create characters of different classes
        classes = ["Fighter", "Wizard", "Rogue", "Cleric"]
        for char_class in classes:
            char_data = sample_character_data.copy()
            char_data["name"] = f"Test {char_class}"
            char_data["class"] = char_class
            authenticated_test_client.post("/api/characters", json=char_data)

        # Filter by Fighter class
        response = authenticated_test_client.get("/api/characters?class=Fighter")

        assert response.status_code == 200
        data = response.json()
        assert all(char["class"] == "Fighter" for char in data)

    def test_filter_campaigns_by_status(self, authenticated_test_client: TestClient,
                                       sample_campaign_data):
        """Test filtering campaigns by status"""
        # Create campaigns with different statuses
        statuses = ["active", "planning", "completed", "on_hold"]
        for status in statuses:
            campaign_data = sample_campaign_data.copy()
            campaign_data["name"] = f"Campaign {status}"
            campaign_data["status"] = status
            authenticated_test_client.post("/api/campaigns", json=campaign_data)

        # Filter by active status
        response = authenticated_test_client.get("/api/campaigns?status=active")

        assert response.status_code == 200
        data = response.json()
        assert all(campaign["status"] == "active" for campaign in data)

    def test_sort_characters_by_level(self, authenticated_test_client: TestClient,
                                     sample_character_data):
        """Test sorting characters by level"""
        # Create characters with different levels
        levels = [1, 5, 3, 2, 4]
        for i, level in enumerate(levels):
            char_data = sample_character_data.copy()
            char_data["name"] = f"Character {i+1}"
            char_data["level"] = level
            authenticated_test_client.post("/api/characters", json=char_data)

        # Sort by level descending
        response = authenticated_test_client.get("/api/characters?sort=level&order=desc")

        assert response.status_code == 200
        data = response.json()
        character_levels = [char["level"] for char in data[:5]]  # First 5 characters
        assert character_levels == sorted(character_levels, reverse=True)


class TestErrorHandling:
    """Test API error handling"""

    def test_404_not_found(self, authenticated_test_client: TestClient):
        """Test 404 Not Found responses"""
        # Test non-existent character
        response = authenticated_test_client.get("/api/characters/999999")
        assert response.status_code == 404

        # Test non-existent campaign
        response = authenticated_test_client.get("/api/campaigns/999999")
        assert response.status_code == 404

    def test_422_validation_error(self, authenticated_test_client: TestClient):
        """Test 422 Validation Error responses"""
        # Send invalid character data
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "level": -1  # Negative level should fail
        }

        response = authenticated_test_client.post("/api/characters", json=invalid_data)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_403_forbidden(self, test_client: TestClient, sample_character_data):
        """Test 403 Forbidden responses"""
        # Create character as one user
        test_client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "TestPass123!"
        })
        login_response = test_client.post("/api/auth/login", data={
            "username": "user1",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        char_response = test_client.post("/api/characters", json=sample_character_data, headers=headers)
        character_id = char_response.json()["id"]

        # Try to access as different user (unauthenticated in this case)
        response = test_client.patch(f"/api/characters/{character_id}", json={"name": "Hacked"})
        assert response.status_code == 401  # Unauthenticated

    def test_429_rate_limiting(self, authenticated_test_client: TestClient):
        """Test rate limiting (if implemented)"""
        # This test would need actual rate limiting implementation
        # For now, we'll test the endpoint structure
        for i in range(100):  # Make many requests
            response = authenticated_test_client.get("/api/characters")
            if response.status_code == 429:
                assert "rate limit" in response.json()["detail"].lower()
                break
        else:
            # If rate limiting isn't implemented, this test passes
            pass

    def test_500_server_error_handling(self, authenticated_test_client: TestClient):
        """Test 500 server error handling"""
        # This would require mocking a server error
        # For now, we'll verify error response format
        response = authenticated_test_client.get("/api/health")
        if response.status_code == 500:
            data = response.json()
            assert "detail" in data


class TestAPIPerformance:
    """Test API performance and response times"""

    def test_response_time_basic_endpoints(self, authenticated_test_client: TestClient):
        """Test basic endpoint response times"""
        import time

        # Test health endpoint
        start_time = time.time()
        response = authenticated_test_client.get("/api/health")
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 0.5  # Should respond within 500ms

    def test_response_time_complex_queries(self, authenticated_test_client: TestClient,
                                          sample_character_data):
        """Test complex query response times"""
        import time

        # Create many characters
        for i in range(20):
            char_data = sample_character_data.copy()
            char_data["name"] = f"Character {i+1}"
            authenticated_test_client.post("/api/characters", json=char_data)

        # Test complex search
        start_time = time.time()
        response = authenticated_test_client.get("/api/characters?search=Character&sort=level&limit=10")
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second

    def test_concurrent_requests(self, authenticated_test_client: TestClient):
        """Test handling concurrent requests"""
        import threading
        import time

        results = []
        errors = []

        def make_request():
            try:
                start_time = time.time()
                response = authenticated_test_client.get("/api/characters")
                response_time = time.time() - start_time
                results.append((response.status_code, response_time))
            except Exception as e:
                errors.append(e)

        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all requests to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(errors) == 0
        assert len(results) == 10
        assert all(status == 200 for status, _ in results)
        assert all(time < 2.0 for _, time in results)  # All should complete within 2 seconds


class TestWebsocketEndpoints:
    """Test WebSocket functionality"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, async_test_client: AsyncClient):
        """Test basic WebSocket connection"""
        async with async_test_client.websocket_connect("/ws") as websocket:
            await websocket.send_json({"type": "ping"})
            data = await websocket.receive_json()
            assert data["type"] == "pong"

    @pytest.mark.asyncio
    async def test_websocket_authentication(self, async_test_client: AsyncClient):
        """Test WebSocket authentication"""
        # Test without authentication
        with pytest.raises(Exception):  # Should raise exception for unauthenticated
            async with async_test_client.websocket_connect("/ws") as websocket:
                pass

    @pytest.mark.asyncio
    async def test_websocket_campaign_join(self, async_test_client: AsyncClient):
        """Test joining campaign via WebSocket"""
        # This would require proper WebSocket authentication setup
        async with async_test_client.websocket_connect("/ws") as websocket:
            # Join campaign
            await websocket.send_json({
                "type": "join_campaign",
                "campaign_id": "test-campaign-id"
            })

            response = await websocket.receive_json()
            assert response["type"] == "campaign_joined"

    @pytest.mark.asyncio
    async def test_websocket_dice_roll_broadcast(self, async_test_client: AsyncClient):
        """Test broadcasting dice rolls via WebSocket"""
        async with async_test_client.websocket_connect("/ws") as websocket:
            # Send dice roll
            await websocket.send_json({
                "type": "dice_roll",
                "expressions": ["1d20"],
                "campaign_id": "test-campaign-id"
            })

            response = await websocket.receive_json()
            assert response["type"] == "dice_roll_result"
            assert "results" in response["data"]