"""
Unit tests for Character Service

Tests character management functionality including:
- Character creation and validation
- Character updates and stats management
- Character abilities and skills
- Character inventory and equipment
- Character leveling and progression
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List
import json

from source_code.backend.services.character_sheet_service import CharacterSheetService
from source_code.backend.api.schemas.character import (
    CharacterCreate, CharacterUpdate, CharacterResponse,
    AbilityScores, Skills, CharacterStats, CharacterInventory,
    CharacterClass, CharacterLevel
)


class TestCharacterSheetService:
    """Test suite for CharacterSheetService"""

    @pytest.fixture
    def character_service(self):
        """Create a character service instance"""
        return CharacterSheetService()

    @pytest.fixture
    def sample_character_data(self):
        """Sample character data for testing"""
        return {
            "name": "Aldric Stormwind",
            "race": "Human",
            "class": "Fighter",
            "level": 1,
            "ability_scores": {
                "strength": 16,
                "dexterity": 14,
                "constitution": 15,
                "intelligence": 12,
                "wisdom": 13,
                "charisma": 10
            },
            "max_hp": 12,
            "current_hp": 12,
            "temp_hp": 0,
            "armor_class": 15,
            "speed": 30,
            "background": "Soldier",
            "alignment": "Lawful Good",
            "personality_traits": "Brave and loyal",
            "ideals": "Honor and justice",
            "bonds": "Protects the innocent",
            "flaws": "Impulsive",
            "proficiency_bonus": 2,
            "experience_points": 0
        }

    @pytest.fixture
    def ability_scores_data(self):
        """Sample ability scores data"""
        return AbilityScores(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=12,
            wisdom=13,
            charisma=10
        )

    def test_calculate_ability_modifier(self, character_service):
        """Test ability score modifier calculation"""
        test_cases = [
            (1, -5),   # 1 -> -5
            (2, -4),   # 2 -> -4
            (3, -4),   # 3 -> -4
            (10, 0),   # 10 -> 0
            (11, 0),   # 11 -> 0
            (12, +1),  # 12 -> +1
            (16, +3),  # 16 -> +3
            (20, +5),  # 20 -> +5
        ]

        for score, expected_modifier in test_cases:
            modifier = character_service.calculate_ability_modifier(score)
            assert modifier == expected_modifier, f"Score {score} should give modifier {expected_modifier}"

    def test_calculate_saving_throws(self, character_service, ability_scores_data):
        """Test saving throw calculations"""
        # For a fighter, strength and constitution are saving throw proficiencies
        saving_throws = character_service.calculate_saving_throws(
            ability_scores_data,
            proficient_saves=["strength", "constitution"],
            proficiency_bonus=2
        )

        assert saving_throws["strength"] == 3  # +3 (STR mod) + 2 (proficiency)
        assert saving_throws["dexterity"] == 2  # +2 (DEX mod) + 0 (no proficiency)
        assert saving_throws["constitution"] == 4  # +2 (CON mod) + 2 (proficiency)
        assert saving_throws["intelligence"] == 1  # +1 (INT mod) + 0 (no proficiency)
        assert saving_throws["wisdom"] == 1  # +1 (WIS mod) + 0 (no proficiency)
        assert saving_throws["charisma"] == 0  # +0 (CHA mod) + 0 (no proficiency)

    def test_calculate_skill_modifiers(self, character_service, ability_scores_data):
        """Test skill modifier calculations"""
        # Sample skill proficiencies for a rogue
        skill_proficiencies = {
            "acrobatics": "proficient",
            "athletics": "proficient",
            "deception": "expert",
            "stealth": "expert",
            "investigation": "proficient"
        }

        skills = character_service.calculate_skill_modifiers(
            ability_scores_data,
            skill_proficiencies,
            proficiency_bonus=2
        )

        # Acrobatics (DEX-based, proficient): +2 (DEX) + 2 (prof) = +4
        assert skills["acrobatics"] == 4
        # Athletics (STR-based, proficient): +3 (STR) + 2 (prof) = +5
        assert skills["athletics"] == 5
        # Deception (CHA-based, expert): +0 (CHA) + 2*2 (expert) = +4
        assert skills["deception"] == 4
        # Stealth (DEX-based, expert): +2 (DEX) + 2*2 (expert) = +6
        assert skills["stealth"] == 6
        # Investigation (INT-based, proficient): +1 (INT) + 2 (prof) = +3
        assert skills["investigation"] == 3
        # Unproficient skill (PERception, WIS-based): +1 (WIS) + 0 = +1
        assert skills["perception"] == 1

    def test_calculate_passive_perception(self, character_service):
        """Test passive perception calculation"""
        # Base perception +10
        passive_perception = character_service.calculate_passive_perception(wisdom_modifier=2)
        assert passive_perception == 12

        # With proficiency
        passive_perception = character_service.calculate_passive_perception(
            wisdom_modifier=2,
            perception_proficiency=True,
            proficiency_bonus=3
        )
        assert passive_perception == 15  # 10 + 2 + 3

        # With expertise
        passive_perception = character_service.calculate_passive_perception(
            wisdom_modifier=2,
            perception_proficiency=True,
            proficiency_bonus=3,
            perception_expertise=True
        )
        assert passive_perception == 18  # 10 + 2 + (3*2)

    def test_calculate_armor_class(self, character_service, ability_scores_data):
        """Test armor class calculations"""
        # No armor (base AC + DEX modifier)
        ac = character_service.calculate_armor_class(
            dexterity_modifier=character_service.calculate_ability_modifier(ability_scores_data.dexterity),
            armor_type=None,
            shield=False
        )
        assert ac == 12  # 10 + 2 (DEX mod)

        # With light armor (leather, AC 11 + DEX)
        ac = character_service.calculate_armor_class(
            dexterity_modifier=2,
            armor_type="light",
            armor_bonus=11,
            shield=False
        )
        assert ac == 13  # 11 (leather) + 2 (DEX)

        # With medium armor (chain shirt, AC 13 + DEX max 2)
        ac = character_service.calculate_armor_class(
            dexterity_modifier=4,  # High DEX but capped at 2 for medium
            armor_type="medium",
            armor_bonus=13,
            shield=False
        )
        assert ac == 15  # 13 (chain shirt) + 2 (DEX capped)

        # With heavy armor (plate, AC 18, no DEX bonus)
        ac = character_service.calculate_armor_class(
            dexterity_modifier=3,
            armor_type="heavy",
            armor_bonus=18,
            shield=False
        )
        assert ac == 18  # 18 (plate) + 0 (heavy armor)

        # With shield (+2)
        ac = character_service.calculate_armor_class(
            dexterity_modifier=2,
            armor_type="light",
            armor_bonus=11,
            shield=True
        )
        assert ac == 15  # 11 + 2 (DEX) + 2 (shield)

    def test_calculate_hit_points(self, character_service, ability_scores_data):
        """Test hit point calculations"""
        # Level 1 fighter: 10 + CON modifier
        hp = character_service.calculate_hit_points(
            hit_dice_type=10,  # d10 for fighter
            constitution_modifier=character_service.calculate_ability_modifier(ability_scores_data.constitution),
            level=1,
            rolled_hp=None
        )
        assert hp == 12  # 10 + 2 (CON mod)

        # Level 5 with average rolls: 10 + 4*5.5 + 2*5
        hp = character_service.calculate_hit_points(
            hit_dice_type=10,
            constitution_modifier=2,
            level=5,
            rolled_hp=None
        )
        assert hp == 10 + (4 * 5.5) + (2 * 5)  # 10 + 22 + 10 = 42

        # Level 3 with specific rolls
        rolled_hp = [6, 8, 4]  # Three level-up rolls
        hp = character_service.calculate_hit_points(
            hit_dice_type=10,
            constitution_modifier=2,
            level=4,  # Level 1 + 3 level-ups
            rolled_hp=rolled_hp
        )
        assert hp == 10 + sum(rolled_hp) + (2 * 4)  # 10 + 18 + 8 = 36

    def test_validate_character_creation(self, character_service, sample_character_data):
        """Test character creation validation"""
        # Valid character should pass validation
        validation = character_service.validate_character_creation(sample_character_data)
        assert validation.is_valid is True
        assert len(validation.errors) == 0

    def test_validate_character_invalid_name(self, character_service, sample_character_data):
        """Test validation with invalid character name"""
        invalid_data = sample_character_data.copy()
        invalid_data["name"] = ""  # Empty name

        validation = character_service.validate_character_creation(invalid_data)
        assert validation.is_valid is False
        assert any("name" in error.lower() for error in validation.errors)

    def test_validate_character_invalid_ability_scores(self, character_service, sample_character_data):
        """Test validation with invalid ability scores"""
        invalid_data = sample_character_data.copy()
        invalid_data["ability_scores"]["strength"] = 30  # Too high

        validation = character_service.validate_character_creation(invalid_data)
        assert validation.is_valid is False
        assert any("ability" in error.lower() or "score" in error.lower() for error in validation.errors)

    def test_validate_character_invalid_level(self, character_service, sample_character_data):
        """Test validation with invalid level"""
        invalid_data = sample_character_data.copy()
        invalid_data["level"] = 0  # Invalid level

        validation = character_service.validate_character_creation(invalid_data)
        assert validation.is_valid is False
        assert any("level" in error.lower() for error in validation.errors)

    def test_calculate_proficiency_bonus(self, character_service):
        """Test proficiency bonus calculation by level"""
        test_cases = [
            (1, 2),   # Level 1-4: +2
            (2, 2),
            (3, 2),
            (4, 2),
            (5, 3),   # Level 5-8: +3
            (6, 3),
            (7, 3),
            (8, 3),
            (9, 4),   # Level 9-12: +4
            (10, 4),
            (11, 4),
            (12, 4),
            (13, 5),  # Level 13-16: +5
            (14, 5),
            (15, 5),
            (16, 5),
            (17, 6),  # Level 17-20: +6
            (18, 6),
            (19, 6),
            (20, 6),
        ]

        for level, expected_bonus in test_cases:
            bonus = character_service.calculate_proficiency_bonus(level)
            assert bonus == expected_bonus, f"Level {level} should have proficiency bonus {expected_bonus}"

    def test_calculate_carry_capacity(self, character_service, ability_scores_data):
        """Test carry capacity calculation"""
        strength_score = ability_scores_data.strength
        carry_capacity = character_service.calculate_carry_capacity(strength_score)

        # Carry capacity = Strength score * 15
        expected_capacity = strength_score * 15
        assert carry_capacity == expected_capacity

        # Test other encumbrance thresholds
        push_lift_drag = character_service.calculate_push_lift_drag(strength_score)
        assert push_lift_drag == expected_capacity * 2  # Double normal capacity

    @pytest.mark.asyncio
    async def test_create_character(self, character_service, sample_character_data):
        """Test character creation"""
        with patch.object(character_service, 'save_character') as mock_save:
            mock_save.return_value = {"id": "test-char-id", **sample_character_data}

            character = await character_service.create_character(
                user_id="test-user-id",
                character_data=sample_character_data
            )

            assert character["name"] == sample_character_data["name"]
            assert character["race"] == sample_character_data["race"]
            assert character["class"] == sample_character_data["class"]
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_character(self, character_service, sample_character_data):
        """Test character update"""
        character_id = "test-char-id"
        update_data = {
            "name": "Aldric Stormwind II",
            "level": 2,
            "experience_points": 300
        }

        with patch.object(character_service, 'get_character') as mock_get, \
             patch.object(character_service, 'save_character') as mock_save:

            # Mock existing character
            mock_get.return_value = {"id": character_id, **sample_character_data}
            mock_save.return_value = {"id": character_id, **sample_character_data, **update_data}

            updated_character = await character_service.update_character(
                character_id=character_id,
                update_data=update_data
            )

            assert updated_character["name"] == update_data["name"]
            assert updated_character["level"] == update_data["level"]
            mock_get.assert_called_once_with(character_id)
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_level_up_character(self, character_service, sample_character_data):
        """Test character level up"""
        character_id = "test-char-id"
        current_level = sample_character_data["level"]

        with patch.object(character_service, 'get_character') as mock_get, \
             patch.object(character_service, 'save_character') as mock_save:

            mock_get.return_value = {"id": character_id, **sample_character_data}

            # Mock level up data
            level_up_data = {
                "new_level": current_level + 1,
                "hit_dice_roll": 8,
                "new_hp": 20,
                "new_features": ["Action Surge", "Extra Attack"]
            }

            mock_save.return_value = {
                "id": character_id,
                **sample_character_data,
                "level": current_level + 1,
                "max_hp": level_up_data["new_hp"],
                "features": level_up_data["new_features"]
            }

            leveled_character = await character_service.level_up_character(
                character_id=character_id,
                level_up_data=level_up_data
            )

            assert leveled_character["level"] == current_level + 1
            assert leveled_character["max_hp"] == level_up_data["new_hp"]

    def test_calculate_spell_save_dc(self, character_service):
        """Test spell save DC calculation"""
        # Formula: 8 + proficiency bonus + spellcasting ability modifier
        spell_save_dc = character_service.calculate_spell_save_dc(
            spellcasting_ability_modifier=4,  # +4 from high intelligence
            proficiency_bonus=2
        )
        assert spell_save_dc == 14  # 8 + 2 + 4

        # Test with different ability scores
        spell_save_dc = character_service.calculate_spell_save_dc(
            spellcasting_ability_modifier=2,  # +2 from wisdom
            proficiency_bonus=3
        )
        assert spell_save_dc == 13  # 8 + 3 + 2

    def test_calculate_spell_attack_bonus(self, character_service):
        """Test spell attack bonus calculation"""
        # Formula: proficiency bonus + spellcasting ability modifier
        spell_attack = character_service.calculate_spell_attack_bonus(
            spellcasting_ability_modifier=5,  # +5 from charisma
            proficiency_bonus=3
        )
        assert spell_attack == 8  # 3 + 5

    def test_add_character_feature(self, character_service, sample_character_data):
        """Test adding features to character"""
        character = sample_character_data.copy()
        character["features"] = []

        # Add a feature
        updated_character = character_service.add_character_feature(
            character=character,
            feature_name="Second Wind",
            feature_description="Regain hit points as a bonus action",
            feature_type="class"
        )

        assert len(updated_character["features"]) == 1
        feature = updated_character["features"][0]
        assert feature["name"] == "Second Wind"
        assert feature["type"] == "class"

    def test_remove_character_feature(self, character_service, sample_character_data):
        """Test removing features from character"""
        character = sample_character_data.copy()
        character["features"] = [
            {"name": "Second Wind", "type": "class"},
            {"name": "Action Surge", "type": "class"}
        ]

        # Remove a feature
        updated_character = character_service.remove_character_feature(
            character=character,
            feature_name="Second Wind"
        )

        assert len(updated_character["features"]) == 1
        assert updated_character["features"][0]["name"] == "Action Surge"

    def test_calculate_initiative(self, character_service, ability_scores_data):
        """Test initiative calculation"""
        dexterity_modifier = character_service.calculate_ability_modifier(ability_scores_data.dexterity)
        initiative = character_service.calculate_initiative(
            dexterity_modifier=dexterity_modifier,
            initiative_bonus=2  # From a feat or feature
        )
        assert initiative == dexterity_modifier + 2

    def test_calculate_speed(self, character_service):
        """Test speed calculation with various modifiers"""
        base_speed = 30

        # Normal speed
        speed = character_service.calculate_speed(base_speed=base_speed)
        assert speed == 30

        # With armor penalty
        speed = character_service.calculate_speed(
            base_speed=base_speed,
            armor_speed_penalty=10
        )
        assert speed == 20

        # With racial bonus
        speed = character_service.calculate_speed(
            base_speed=base_speed,
            racial_speed_bonus=5
        )
        assert speed == 35

        # Combined effects
        speed = character_service.calculate_speed(
            base_speed=base_speed,
            armor_speed_penalty=10,
            racial_speed_bonus=5
        )
        assert speed == 25

    def test_validate_death_saving_throws(self, character_service, sample_character_data):
        """Test death saving throw validation and tracking"""
        character = sample_character_data.copy()
        character["death_saves"] = {
            "successes": 0,
            "failures": 0
        }

        # Add a success
        updated_character = character_service.add_death_save_result(
            character=character,
            result="success"
        )
        assert updated_character["death_saves"]["successes"] == 1
        assert updated_character["death_saves"]["failures"] == 0

        # Add failures
        for _ in range(2):
            updated_character = character_service.add_death_save_result(
                character=updated_character,
                result="failure"
            )
        assert updated_character["death_saves"]["successes"] == 1
        assert updated_character["death_saves"]["failures"] == 2

        # Check if character is dead
        is_dead = character_service.is_character_dead(updated_character)
        assert is_dead is False  # Only 2 failures, need 3

        # Add final failure
        updated_character = character_service.add_death_save_result(
            character=updated_character,
            result="failure"
        )
        is_dead = character_service.is_character_dead(updated_character)
        assert is_dead is True

    def test_reset_death_saves(self, character_service, sample_character_data):
        """Test resetting death saves when character stabilizes"""
        character = sample_character_data.copy()
        character["death_saves"] = {
            "successes": 2,
            "failures": 1
        }

        reset_character = character_service.reset_death_saves(character)
        assert reset_character["death_saves"]["successes"] == 0
        assert reset_character["death_saves"]["failures"] == 0


class TestCharacterInventory:
    """Test character inventory management"""

    @pytest.fixture
    def character_service(self):
        return CharacterSheetService()

    @pytest.fixture
    def sample_item(self):
        """Sample item data"""
        return {
            "name": "Longsword",
            "type": "weapon",
            "rarity": "common",
            "weight": 3,
            "cost": {"gp": 15},
            "properties": ["versatile"],
            "damage": "1d8 slashing",
            "quantity": 1,
            "equipped": False
        }

    def test_add_item_to_inventory(self, character_service, sample_item):
        """Test adding items to character inventory"""
        character = {"inventory": []}

        updated_character = character_service.add_item_to_inventory(
            character=character,
            item=sample_item
        )

        assert len(updated_character["inventory"]) == 1
        added_item = updated_character["inventory"][0]
        assert added_item["name"] == sample_item["name"]
        assert added_item["id"] is not None  # Should generate an ID

    def test_remove_item_from_inventory(self, character_service, sample_item):
        """Test removing items from character inventory"""
        item_with_id = {**sample_item, "id": "item-123"}
        character = {"inventory": [item_with_id]}

        updated_character = character_service.remove_item_from_inventory(
            character=character,
            item_id="item-123"
        )

        assert len(updated_character["inventory"]) == 0

    def test_equip_item(self, character_service, sample_item):
        """Test equipping items"""
        item_with_id = {**sample_item, "id": "item-123", "equipped": False}
        character = {"inventory": [item_with_id]}

        updated_character = character_service.equip_item(
            character=character,
            item_id="item-123"
        )

        equipped_item = next(item for item in updated_character["inventory"] if item["id"] == "item-123")
        assert equipped_item["equipped"] is True

    def test_unequip_item(self, character_service, sample_item):
        """Test unequipping items"""
        item_with_id = {**sample_item, "id": "item-123", "equipped": True}
        character = {"inventory": [item_with_id]}

        updated_character = character_service.unequip_item(
            character=character,
            item_id="item-123"
        )

        unequipped_item = next(item for item in updated_character["inventory"] if item["id"] == "item-123")
        assert unequipped_item["equipped"] is False

    def test_calculate_encumbrance(self, character_service):
        """Test calculating character encumbrance"""
        items = [
            {"name": "Longsword", "weight": 3, "quantity": 1},
            {"name": "Shield", "weight": 6, "quantity": 1},
            {"name": "Rations", "weight": 1, "quantity": 5},  # 5 pounds total
            {"name": "Gold Coins", "weight": 0.02, "quantity": 100}  # 2 pounds total
        ]

        total_weight = character_service.calculate_encumbrance(items)
        expected_weight = 3 + 6 + 5 + 2  # 16 pounds total
        assert abs(total_weight - expected_weight) < 0.1

    def test_check_encumbrance_status(self, character_service):
        """Test encumbrance status checking"""
        strength_score = 14  # Carry capacity = 14 * 15 = 210 pounds

        # Light load (under 70 pounds)
        status = character_service.check_encumbrance_status(
            current_weight=50,
            strength_score=strength_score
        )
        assert status == "light"

        # Medium load (70-140 pounds)
        status = character_service.check_encumbrance_status(
            current_weight=100,
            strength_score=strength_score
        )
        assert status == "medium"

        # Heavy load (140-210 pounds)
        status = character_service.check_encumbrance_status(
            current_weight=180,
            strength_score=strength_score
        )
        assert status == "heavy"

        # Over capacity (over 210 pounds)
        status = character_service.check_encumbrance_status(
            current_weight=250,
            strength_score=strength_score
        )
        assert status == "overloaded"


class TestCharacterEdgeCases:
    """Test edge cases and error conditions for character management"""

    @pytest.fixture
    def character_service(self):
        return CharacterSheetService()

    def test_character_with_minimal_stats(self, character_service):
        """Test character creation with minimal ability scores"""
        minimal_scores = {
            "strength": 1,
            "dexterity": 1,
            "constitution": 1,
            "intelligence": 1,
            "wisdom": 1,
            "charisma": 1
        }

        # Should handle minimal scores without crashing
        for ability, score in minimal_scores.items():
            modifier = character_service.calculate_ability_modifier(score)
            assert modifier == -5  # Minimum modifier

    def test_character_with_maximal_stats(self, character_service):
        """Test character creation with maximum ability scores"""
        maximal_scores = {
            "strength": 20,
            "dexterity": 20,
            "constitution": 20,
            "intelligence": 20,
            "wisdom": 20,
            "charisma": 20
        }

        # Should handle maximum scores without crashing
        for ability, score in maximal_scores.items():
            modifier = character_service.calculate_ability_modifier(score)
            assert modifier == 5  # Maximum modifier

    def test_character_level_20(self, character_service):
        """Test character at maximum level"""
        proficiency_bonus = character_service.calculate_proficiency_bonus(20)
        assert proficiency_bonus == 6

    def test_character_with_negative_hp(self, character_service):
        """Test character with negative hit points"""
        character = {
            "current_hp": -5,
            "temp_hp": 0,
            "max_hp": 20,
            "death_saves": {"successes": 0, "failures": 0}
        }

        # Character should be unconscious/death saving
        is_unconscious = character_service.is_character_unconscious(character)
        assert is_unconscious is True

    def test_character_with_temporary_hp(self, character_service):
        """Test character with temporary hit points"""
        character = {
            "current_hp": 15,
            "temp_hp": 10,
            "max_hp": 20,
            "death_saves": {"successes": 0, "failures": 0}
        }

        effective_hp = character_service.get_effective_hp(character)
        assert effective_hp == 25  # 15 + 10 temporary

    def test_character_inventory_weight_limits(self, character_service):
        """Test inventory weight calculation with edge cases"""
        # Very heavy items
        heavy_items = [
            {"weight": 100, "quantity": 1},
            {"weight": 0, "quantity": 1000},  # Weightless items
            {"weight": 0.5, "quantity": 200},  # Many light items
        ]

        total_weight = character_service.calculate_encumbrance(heavy_items)
        assert total_weight == 200  # 100 + 0 + 100

    def test_character_data_corruption_handling(self, character_service):
        """Test handling of corrupted or incomplete character data"""
        # Missing required fields
        incomplete_character = {
            "name": "Test Character",
            # Missing other required fields
        }

        # Should handle gracefully without crashing
        validation = character_service.validate_character_data(incomplete_character)
        assert validation.is_valid is False
        assert len(validation.errors) > 0

    def test_duplicate_feature_handling(self, character_service):
        """Test handling of duplicate features"""
        character = {
            "features": [
                {"name": "Second Wind", "type": "class"},
                {"name": "Second Wind", "type": "class"}
            ]
        }

        # Should identify and handle duplicates
        validation = character_service.validate_character_features(character)
        assert validation.has_duplicates is True