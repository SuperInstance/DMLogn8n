"""
End-to-end tests for complete user journeys

Tests full user workflows using Playwright including:
- User registration and authentication
- Character creation and management
- Campaign creation and participation
- Dice rolling and game mechanics
- Real-time collaboration
- Cross-browser compatibility
- Mobile responsive testing
"""

import pytest
import asyncio
from playwright.async_api import Page, Browser, BrowserContext
from typing import Dict, Any
import time


class TestUserRegistrationJourney:
    """Test complete user registration and onboarding journey"""

    @pytest.fixture(autouse=True)
    async def setup(self, page: Page):
        """Setup for each test"""
        await page.goto("http://localhost:3000")
        await page.wait_for_load_state("networkidle")

    async def test_complete_user_registration_flow(self, page: Page):
        """Test complete user registration from start to finish"""
        # Navigate to registration page
        await page.click("text=Sign Up")
        await page.wait_for_selector("form#registration-form")

        # Fill registration form
        await page.fill("#username", "testuser_e2e")
        await page.fill("#email", "e2e_test@example.com")
        await page.fill("#password", "SecurePass123!")
        await page.fill("#confirm-password", "SecurePass123!")
        await page.fill("#display-name", "E2E Test User")

        # Accept terms and conditions
        await page.check("#terms-accepted")

        # Submit registration
        await page.click("button[type='submit']")

        # Wait for successful registration
        await page.wait_for_selector("text=Registration successful!")
        await page.wait_for_selector("text=Verify your email")

        # Check email verification screen
        await page.wait_for_selector("text=Verification email sent")
        assert "e2e_test@example.com" in await page.text_content(".email-confirmation")

        # Simulate email verification (skip for E2E test)
        await page.goto("http://localhost:3000/verify-email?token=test-verification-token")
        await page.wait_for_selector("text=Email verified successfully!")

        # Complete onboarding
        await page.click("button:has-text('Get Started')")

        # Should be redirected to dashboard
        await page.wait_for_selector("h1:has-text('Welcome to DMLog')")
        assert "E2E Test User" in await page.text_content(".user-info")

    async def test_social_registration_flow(self, page: Page):
        """Test social media registration flow"""
        await page.click("text=Sign Up")
        await page.wait_for_selector(".social-login-buttons")

        # Test Google OAuth (mocked in test environment)
        with page.expect_navigation():
            await page.click("button:has-text('Continue with Google')")

        # Mock OAuth callback
        await page.goto("http://localhost:3000/auth/callback?code=test-oauth-code")

        # Should complete registration with social account
        await page.wait_for_selector("text=Account created successfully!")

    async def test_registration_validation_errors(self, page: Page):
        """Test registration form validation"""
        await page.click("text=Sign Up")

        # Submit empty form
        await page.click("button[type='submit']")

        # Check for validation errors
        await page.wait_for_selector(".error-message")
        error_messages = await page.all_text_contents(".error-message")
        assert any("username is required" in msg.lower() for msg in error_messages)
        assert any("email is required" in msg.lower() for msg in error_messages)
        assert any("password is required" in msg.lower() for msg in error_messages)

        # Test password mismatch
        await page.fill("#password", "Password123!")
        await page.fill("#confirm-password", "DifferentPassword123!")
        await page.click("button[type='submit']")

        await page.wait_for_selector("text=Passwords do not match")

        # Test weak password
        await page.fill("#password", "weak")
        await page.fill("#confirm-password", "weak")
        await page.click("button[type='submit']")

        await page.wait_for_selector("text=Password is too weak")

    async def test_duplicate_registration_handling(self, page: Page):
        """Test handling of duplicate registration attempts"""
        # First registration
        await page.click("text=Sign Up")
        await page.fill("#username", "existing_user")
        await page.fill("#email", "existing@example.com")
        await page.fill("#password", "SecurePass123!")
        await page.fill("#confirm-password", "SecurePass123!")
        await page.check("#terms-accepted")
        await page.click("button[type='submit']")

        await page.wait_for_selector("text=Registration successful!")

        # Try to register again with same email
        await page.goto("http://localhost:3000/register")
        await page.fill("#username", "different_user")
        await page.fill("#email", "existing@example.com")  # Same email
        await page.fill("#password", "SecurePass123!")
        await page.fill("#confirm-password", "SecurePass123!")
        await page.check("#terms-accepted")
        await page.click("button[type='submit']")

        await page.wait_for_selector("text=Email already registered")


class TestCharacterManagementJourney:
    """Test complete character creation and management journey"""

    @pytest.fixture(autouse=True)
    async def setup(self, page: Page):
        """Login user before each test"""
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

    async def test_complete_character_creation_flow(self, page: Page):
        """Test complete character creation process"""
        # Navigate to character creation
        await page.click("text=Characters")
        await page.click("button:has-text('Create New Character')")

        # Basic Information
        await page.wait_for_selector("#character-name")
        await page.fill("#character-name", "Aldric Stormwind")
        await page.select_option("#race", "Human")
        await page.select_option("#class", "Fighter")
        await page.fill("#level", "1")
        await page.select_option("#alignment", "Lawful Good")
        await page.fill("#background", "Soldier")

        # Ability Scores (use point buy or standard array)
        await page.click("text=Use Standard Array")
        await page.wait_for_selector(".ability-scores")

        # Assign ability scores
        scores = {"strength": "15", "dexterity": "14", "constitution": "13",
                 "intelligence": "12", "wisdom": "10", "charisma": "8"}

        for ability, score in scores.items():
            await page.select_option(f"#{ability}", score)

        # Combat Stats
        await page.fill("#max-hp", "12")
        await page.fill("#armor-class", "15")
        await page.fill("#speed", "30")

        # Skills and Proficiencies
        await page.check("#proficiency-athletics")
        await page.check("#proficiency-intimidation")
        await page.check("#proficiency-survival")

        # Equipment
        await page.click("button:has-text('Add Equipment')")
        await page.fill("#equipment-name", "Longsword")
        await page.select_option("#equipment-type", "weapon")
        await page.fill("#equipment-quantity", "1")
        await page.click("button:has-text('Add')")

        # Spells (if spellcaster)
        # Skip for fighter

        # Personality and Background
        await page.fill("#personality-traits", "Brave and loyal, always ready to defend the innocent")
        await page.fill("#ideals", "Honor and justice above all else")
        await page.fill("#bonds", "Protects his companions at all costs")
        await page.fill("#flaws", "Sometimes acts impulsively without thinking")

        # Save Character
        await page.click("button:has-text('Create Character')")

        # Verify character creation success
        await page.wait_for_selector("text=Character created successfully!")
        await page.wait_for_selector(".character-sheet")

        # Verify character details
        assert "Aldric Stormwind" in await page.text_content(".character-name")
        assert "Human Fighter" in await page.text_content(".character-class")
        assert "Level 1" in await page.text_content(".character-level")

    async def test_character_editing_flow(self, page: Page):
        """Test character editing and updating"""
        # Navigate to existing character
        await page.click("text=Characters")
        await page.click(".character-card:has-text('Aldric Stormwind')")

        # Edit character
        await page.click("button:has-text('Edit Character')")

        # Update level
        await page.fill("#level", "2")
        await page.fill("#experience-points", "300")

        # Update ability scores (level up)
        await page.select_option("#constitution", "14")  # Constitution increase

        # Update equipment
        await page.click("button:has-text('Add Equipment')")
        await page.fill("#equipment-name", "Shield")
        await page.select_option("#equipment-type", "armor")
        await page.fill("#equipment-quantity", "1")
        await page.click("button:has-text('Add')")

        # Save changes
        await page.click("button:has-text('Save Changes')")

        # Verify updates
        await page.wait_for_selector("text=Character updated successfully!")
        assert "Level 2" in await page.text_content(".character-level")
        assert "Shield" in await page.text_content(".equipment-list")

    async def test_character_sheet_visualization(self, page: Page):
        """Test character sheet display and visualization"""
        await page.click("text=Characters")
        await page.click(".character-card:has-text('Aldric Stormwind')")

        # Test character sheet tabs
        tabs = ["Overview", "Combat", "Skills", "Equipment", "Spells", "Notes"]

        for tab in tabs:
            await page.click(f"button:has-text('{tab}')")
            await page.wait_for_selector(f".{tab.lower()}-tab")
            # Verify content is loaded
            assert await page.is_visible(f".{tab.lower()}-tab")

        # Test PDF export
        with page.expect_download() as download_info:
            await page.click("button:has-text('Export PDF')")
        download = await download_info.value

        assert download.suggested_filename.endswith('.pdf')

    async def test_character_deletion_flow(self, page: Page):
        """Test character deletion process"""
        await page.click("text=Characters")
        await page.click(".character-card:has-text('Aldric Stormwind')")

        # Delete character
        await page.click("button:has-text('Delete Character')")

        # Confirm deletion modal
        await page.wait_for_selector(".modal:has-text('Delete Character')")
        await page.fill("#confirm-name", "Aldric Stormwind")
        await page.click("button:has-text('Delete Forever')")

        # Verify deletion
        await page.wait_for_selector("text=Character deleted successfully!")

        # Verify character is no longer in list
        await page.click("text=Characters")
        assert await page.is_hidden(".character-card:has-text('Aldric Stormwind')")


class TestCampaignManagementJourney:
    """Test complete campaign creation and management journey"""

    @pytest.fixture(autouse=True)
    async def setup(self, page: Page):
        """Login user before each test"""
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

    async def test_complete_campaign_creation_flow(self, page: Page):
        """Test complete campaign creation process"""
        # Navigate to campaign creation
        await page.click("text=Campaigns")
        await page.click("button:has-text('Create New Campaign')")

        # Basic Campaign Information
        await page.wait_for_selector("#campaign-name")
        await page.fill("#campaign-name", "The Lost Mine of Phandelver")
        await page.fill("#campaign-description", "A beginner D&D 5e adventure set in the Forgotten Realms")
        await page.select_option("#setting", "Forgotten Realms")
        await page.fill("#starting-level", "1")
        await page.fill("#max-players", "4")

        # Campaign Settings
        await page.uncheck("#public-campaign")  # Private campaign
        await page.select_option("#difficulty", "Normal")
        await page.check("#allow-character-creation")
        await page.fill("#house-rules", "Standard D&D 5e rules with minor modifications for new players")

        # Schedule and Availability
        await page.select_option("#session-frequency", "Weekly")
        await page.select_option("#preferred-day", "Saturday")
        await page.select_option("#preferred-time", "19:00")
        await page.fill("#session-duration", "4 hours")
        await page.select_option("#timezone", "UTC-5 (EST)")

        # Content Warnings and Tags
        await page.check("#content-violence")
        await page.check("#content-language")
        await page.fill("#campaign-tags", "beginner-friendly, exploration, combat")

        # Create Campaign
        await page.click("button:has-text('Create Campaign')")

        # Verify campaign creation success
        await page.wait_for_selector("text=Campaign created successfully!")
        await page.wait_for_selector(".campaign-dashboard")

        # Verify campaign details
        assert "The Lost Mine of Phandelver" in await page.text_content(".campaign-title")
        assert "Dungeon Master" in await page.text_content(".user-role")

    async def test_campaign_player_invitation_flow(self, page: Page):
        """Test inviting players to campaign"""
        # Navigate to campaign
        await page.click("text=Campaigns")
        await page.click(".campaign-card:has-text('The Lost Mine of Phandelver')")

        # Invite players
        await page.click("button:has-text('Invite Players')")

        # Test different invitation methods
        # Email invitation
        await page.click("text=Invite by Email")
        await page.fill("#player-email", "player1@example.com")
        await page.fill("#invitation-message", "Join our D&D campaign!")
        await page.click("button:has-text('Send Invitation')")

        await page.wait_for_selector("text=Invitation sent!")

        # Username invitation
        await page.click("text=Invite by Username")
        await page.fill("#player-username", "player2")
        await page.click("button:has-text('Send Invitation')")

        await page.wait_for_selector("text=Invitation sent!")

        # Generate invite link
        await page.click("text=Share Invite Link")
        await page.wait_for_selector("#invite-link")
        invite_link = await page.input_value("#invite-link")
        assert "localhost:3000/invite/" in invite_link

        # Copy link
        await page.click("button:has-text('Copy Link')")
        await page.wait_for_selector("text=Link copied!")

    async def test_campaign_management_features(self, page: Page):
        """Test campaign management features"""
        await page.click("text=Campaigns")
        await page.click(".campaign-card:has-text('The Lost Mine of Phandelver')")

        # Test session management
        await page.click("text=Sessions")
        await page.click("button:has-text('Schedule New Session')")

        await page.fill("#session-name", "Session 1: Goblin Ambush")
        await page.fill("#session-description", "The party encounters goblins on the road to Phandalin")
        await page.fill("#scheduled-date", "2024-01-20")
        await page.fill("#scheduled-time", "19:00")
        await page.fill("#estimated-duration", "4 hours")

        await page.click("button:has-text('Schedule Session')")

        await page.wait_for_selector("text=Session scheduled successfully!")

        # Test campaign notes
        await page.click("text=Notes")
        await page.click("button:has-text('Add Note')")
        await page.fill("#note-title", "Session 1 Preparation")
        await page.fill("#note-content", "Prepare goblin miniatures and battle map")
        await page.select_option("#note-type", "Prep")
        await page.click("button:has-text('Save Note')")

        # Test campaign gallery
        await page.click("text=Gallery")
        await page.click("button:has-text('Upload Image')")

        # Upload battle map (mock file upload)
        file_input = await page.query_selector("input[type='file']")
        await file_input.set_input_files("tests/fixtures/battlemap.jpg")

        await page.fill("#image-description", "First battle map for goblin encounter")
        await page.click("button:has-text('Upload')")

        await page.wait_for_selector("text=Image uploaded successfully!")

    async def test_campaign_settings_management(self, page: Page):
        """Test campaign settings and configuration"""
        await page.click("text=Campaigns")
        await page.click(".campaign-card:has-text('The Lost Mine of Phandelver')")

        # Navigate to settings
        await page.click("button:has-text('Campaign Settings')")

        # Update campaign details
        await page.fill("#campaign-description", "Updated description with more details about the adventure")
        await page.select_option("#max-players", "5")

        # Change privacy settings
        await page.check("#public-campaign")  # Make public

        # Update house rules
        await page.fill("#house-rules", "Updated house rules with clarifications on critical hits")

        # Save settings
        await page.click("button:has-text('Save Settings')")

        await page.wait_for_selector("text=Settings updated successfully!")

        # Test DM transfer
        await page.click("text=Transfer DM Role")
        await page.fill("#new-dm-username", "assistant_dm")
        await page.fill("#confirmation-message", "I want to transfer DM role")
        await page.click("button:has-text('Transfer Role')")

        await page.wait_for_selector("text=DM role transferred successfully!")


class TestGameplayJourney:
    """Test complete gameplay and interactive features"""

    @pytest.fixture(autouse=True)
    async def setup(self, page: Page):
        """Setup and join campaign"""
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

        # Navigate to campaign
        await page.click("text=Campaigns")
        await page.click(".campaign-card:has-text('The Lost Mine of Phandelver')")

    async def test_dice_rolling_journey(self, page: Page):
        """Test complete dice rolling functionality"""
        # Navigate to dice roller
        await page.click("text=Dice Roller")

        # Test basic dice roll
        await page.select_option("#dice-type", "d20")
        await page.fill("#dice-count", "1")
        await page.fill("#modifier", "+5")
        await page.fill("#roll-description", "Attack roll with longsword")
        await page.click("button:has-text('Roll Dice')")

        # Verify roll result
        await page.wait_for_selector(".dice-result")
        assert await page.is_visible(".dice-animation")
        await page.wait_for_selector(".dice-total")

        roll_result = await page.text_content(".dice-total")
        assert roll_result.isdigit() or ("+" in roll_result and roll_result.replace("+", "").isdigit())

        # Test advantage roll
        await page.check("#advantage")
        await page.click("button:has-text('Roll Dice')")

        await page.wait_for_selector(".advantage-result")
        advantage_results = await page.all_text_contents(".advantage-die")
        assert len(advantage_results) == 2  # Should show 2 dice for advantage

        # Test multiple dice types
        await page.uncheck("#advantage")
        await page.click("button:has-text('Add Dice Type')")
        await page.select_option("#dice-type-2", "d6")
        await page.fill("#dice-count-2", "2")
        await page.click("button:has-text('Roll All')")

        await page.wait_for_selector(".multiple-results")
        results = await page.all_text_contents(".result-group")
        assert len(results) >= 2

        # Test quick roll buttons
        await page.click("button:has-text('Attack Roll')")
        await page.wait_for_selector(".dice-result")

        await page.click("button:has-text('Saving Throw')")
        await page.wait_for_selector(".dice-result")

        await page.click("button:has-text('Skill Check')")
        await page.wait_for_selector(".dice-result")

        # Test roll history
        await page.click("text=Roll History")
        await page.wait_for_selector(".roll-history-item")
        history_items = await page.all_text_contents(".roll-history-item")
        assert len(history_items) > 0

    async def test_real_time_gameplay_journey(self, page: Page):
        """Test real-time gameplay features"""
        # Start/join game session
        await page.click("text=Active Session")
        await page.click("button:has-text('Join Session')")

        # Wait for WebSocket connection
        await page.wait_for_selector(".connection-status:has-text('Connected')")

        # Test chat functionality
        await page.fill("#chat-input", "Hello everyone! Ready to start the session?")
        await page.click("button:has-text('Send')")

        await page.wait_for_selector(".chat-message:has-text('Hello everyone!')")

        # Test character sheet integration
        await page.click("text=Character Sheet")
        await page.wait_for_selector(".character-stats")

        # Make an attack roll from character sheet
        await page.click("button:has-text('Attack Roll')")
        await page.wait_for_selector(".dice-result")

        # Update hit points
        await page.click("#current-hp")
        await page.fill("#current-hp", "10")  # Take damage
        await page.press("#current-hp", "Enter")

        await page.wait_for_selector(".hp-update:has-text('HP updated')")

        # Test initiative tracking
        await page.click("text=Initiative")
        await page.click("button:has-text('Roll Initiative')")
        await page.wait_for_selector(".initiative-result")

        # Test combat tracker
        await page.click("text=Combat Tracker")
        await page.click("button:has-text('Add Combatant')")
        await page.fill("#combatant-name", "Goblin")
        await page.fill("#combatant-initiative", "12")
        await page.fill("#combatant-ac", "15")
        await page.fill("#combatant-hp", "7")
        await page.click("button:has-text('Add Combatant')")

        await page.wait_for_selector(".combatant:has-text('Goblin')")

        # Test turn management
        await page.click("button:has-text('Next Turn')")
        await page.wait_for_selector(".current-turn-indicator")

    async def test_map_and_tokens_journey(self, page: Page):
        """Test interactive map and token functionality"""
        # Navigate to battle map
        await page.click("text=Battle Map")

        # Upload/load map
        await page.click("button:has-text('Load Map')")
        await page.click(".map-option:has-text('Forest Clearing')")

        await page.wait_for_selector(".battle-map-canvas")

        # Add player token
        await page.click("button:has-text('Add Token')")
        await page.select_option("#token-type", "Player")
        await page.select_option("#token-character", "Aldric Stormwind")
        await page.click("button:has-text('Place Token')")

        # Click on map to place token
        await page.click(".battle-map-canvas", position={"x": 100, "y": 100})

        await page.wait_for_selector(".player-token")

        # Add enemy tokens
        await page.click("button:has-text('Add Token')")
        await page.select_option("#token-type", "Enemy")
        await page.fill("#token-name", "Goblin 1")
        await page.click("button:has-text('Place Token')")
        await page.click(".battle-map-canvas", position={"x": 200, "y": 100})

        # Test token movement
        await page.click(".player-token")
        await page.click(".battle-map-canvas", position={"x": 150, "y": 150})

        await page.wait_for_selector(".token-movement-animation")

        # Test measurement tool
        await page.click("button:has-text('Measure Distance')")
        await page.click(".battle-map-canvas", position={"x": 150, "y": 150})
        await page.click(".battle-map-canvas", position={"x": 200, "y": 100})

        await page.wait_for_selector(".measurement-line")
        distance = await page.text_content(".measurement-text")
        assert "ft" in distance  # Should show distance in feet

        # Test map effects
        await page.click("button:has-text('Draw Effect')")
        await page.select_option("#effect-type", "Fireball")
        await page.click(".battle-map-canvas", position={"x": 175, "y": 125})

        await page.wait_for_selector(".area-effect-overlay")

    async def test_session_recording_journey(self, page: Page):
        """Test session recording and playback features"""
        # Start recording
        await page.click("button:has-text('Start Recording')")
        await page.wait_for_selector(".recording-indicator:has-text('Recording')")

        # Perform some actions during recording
        await page.click("text=Chat")
        await page.fill("#chat-input", "This action will be recorded")
        await page.click("button:has-text('Send')")

        await page.click("text=Dice Roller")
        await page.click("button:has-text('Roll Dice')")

        # Stop recording
        await page.click("button:has-text('Stop Recording')")
        await page.wait_for_selector(".recording-complete-modal")

        # Save recording
        await page.fill("#session-title", "Session 1 Recording")
        await page.fill("#session-summary", "First session with goblin combat")
        await page.click("button:has-text('Save Recording')")

        await page.wait_for_selector("text=Recording saved successfully!")

        # Test playback
        await page.click("text=Session Library")
        await page.click(".session-recording:has-text('Session 1 Recording')")
        await page.click("button:has-text('Play Recording')")

        await page.wait_for_selector(".playback-controls")
        await page.wait_for_selector(".recording-timeline")

        # Test playback controls
        await page.click("button:has-text('Play/Pause')")
        await page.wait_for_timeout(1000)
        await page.click("button:has-text('Play/Pause')")  # Pause

        await page.click("button:has-text('Jump to Start')")
        await page.click("button:has-text('Jump to End')")


class TestCrossBrowserCompatibility:
    """Test cross-browser compatibility"""

    @pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
    async def test_basic_functionality_all_browsers(self, browser_name: str, browser: Browser):
        """Test basic functionality across all browsers"""
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Test login
            await page.goto("http://localhost:3000/login")
            await page.fill("#username", "testuser_e2e")
            await page.fill("#password", "SecurePass123!")
            await page.click("button[type='submit']")
            await page.wait_for_selector(".dashboard")

            # Test navigation
            await page.click("text=Characters")
            await page.wait_for_selector(".character-list")

            # Test dice roller
            await page.click("text=Dice Roller")
            await page.click("button:has-text('Roll Dice')")
            await page.wait_for_selector(".dice-result")

            # Verify no console errors
            # Note: Playwright doesn't expose console directly, but we can check for error indicators
            assert not await page.is_visible(".error-boundary")

        finally:
            await context.close()

    async def test_mobile_responsive_design(self, browser: Browser):
        """Test mobile responsive design"""
        # iPhone viewport
        context = await browser.new_context(viewport={"width": 375, "height": 667})
        page = await context.new_page()

        try:
            await page.goto("http://localhost:3000/login")
            await page.fill("#username", "testuser_e2e")
            await page.fill("#password", "SecurePass123!")
            await page.click("button[type='submit']")
            await page.wait_for_selector(".dashboard")

            # Test mobile navigation
            assert await page.is_visible(".mobile-menu-button")
            await page.click(".mobile-menu-button")
            await page.wait_for_selector(".mobile-menu")

            # Test mobile character sheet
            await page.click("text=Characters")
            await page.wait_for_selector(".mobile-character-cards")

            # Test mobile dice roller
            await page.click("text=Dice Roller")
            await page.wait_for_selector(".mobile-dice-roller")

            # Verify mobile layout
            mobile_layout = await page.evaluate("window.innerWidth")
            assert mobile_layout <= 375

        finally:
            await context.close()

    async def test_tablet_responsive_design(self, browser: Browser):
        """Test tablet responsive design"""
        # iPad viewport
        context = await browser.new_context(viewport={"width": 768, "height": 1024})
        page = await context.new_page()

        try:
            await page.goto("http://localhost:3000/login")
            await page.fill("#username", "testuser_e2e")
            await page.fill("#password", "SecurePass123!")
            await page.click("button[type='submit']")
            await page.wait_for_selector(".dashboard")

            # Test tablet layout
            assert await page.is_visible(".tablet-layout")

            # Test split view functionality
            await page.click("text=Characters")
            await page.wait_for_selector(".tablet-character-split-view")

        finally:
            await context.close()


class TestPerformanceJourney:
    """Test performance across user journeys"""

    async def test_page_load_performance(self, page: Page):
        """Test page load performance"""
        # Login first
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

        # Test navigation performance
        pages_to_test = ["Characters", "Campaigns", "Dice Roller", "Battle Map"]

        for page_name in pages_to_test:
            start_time = time.time()
            await page.click(f"text={page_name}")
            await page.wait_for_load_state("networkidle")
            load_time = time.time() - start_time

            # Should load within reasonable time
            assert load_time < 3.0, f"{page_name} took too long to load: {load_time}s"

    async def test_dice_rolling_performance(self, page: Page):
        """Test dice rolling performance under stress"""
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

        await page.click("text=Dice Roller")

        # Test rapid dice rolling
        start_time = time.time()
        for _ in range(50):
            await page.click("button:has-text('Roll Dice')")
            await page.wait_for_selector(".dice-result")
        total_time = time.time() - start_time

        avg_time_per_roll = total_time / 50
        assert avg_time_per_roll < 0.5, f"Average roll time too slow: {avg_time_per_roll}s"

    async def test_memory_usage_during_session(self, page: Page):
        """Test memory usage during extended session"""
        # This would require browser memory monitoring
        # For now, test that page doesn't become sluggish
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

        # Simulate extended usage
        actions = [
            lambda: page.click("text=Characters"),
            lambda: page.click("text=Campaigns"),
            lambda: page.click("text=Dice Roller"),
            lambda: page.click("button:has-text('Roll Dice')"),
        ]

        for cycle in range(10):
            for action in actions:
                await action()
                await page.wait_for_timeout(100)  # Brief pause

        # Verify page is still responsive
        start_time = time.time()
        await page.click("text=Dashboard")
        await page.wait_for_selector(".dashboard")
        response_time = time.time() - start_time

        assert response_time < 2.0, f"Page became sluggish: {response_time}s response time"


class TestErrorHandlingJourney:
    """Test error handling in user journeys"""

    async def test_network_error_handling(self, page: Page):
        """Test handling of network errors"""
        # Simulate network offline
        await page.context.set_offline(True)

        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")

        # Should show network error message
        await page.wait_for_selector(".error-message:has-text('Network error')")

        # Restore network
        await page.context.set_offline(False)
        await page.click("button:has-text('Retry')")
        await page.wait_for_selector(".dashboard")

    async def test_session_expiry_handling(self, page: Page):
        """Test handling of session expiry"""
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

        # Clear session/cookies to simulate expiry
        await page.context.clear_cookies()

        # Try to access protected page
        await page.click("text=Characters")

        # Should redirect to login with session expired message
        await page.wait_for_selector(".login-page")
        assert await page.is_visible(".session-expired-message")

    async def test_concurrent_modification_handling(self, page: Page):
        """Test handling of concurrent modifications"""
        # This would require multiple browser contexts
        # For now, test optimistic locking UI
        await page.goto("http://localhost:3000/login")
        await page.fill("#username", "testuser_e2e")
        await page.fill("#password", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".dashboard")

        await page.click("text=Characters")
        await page.click(".character-card:first-child")
        await page.click("button:has-text('Edit Character')")

        # Simulate concurrent modification
        await page.evaluate("""
        // Simulate receiving a WebSocket message about character update
        window.dispatchEvent(new CustomEvent('character-updated', {
            detail: { characterId: 'test-id', updatedBy: 'another-user' }
        }));
        """)

        # Should show concurrent modification warning
        await page.wait_for_selector(".concurrent-modification-warning")