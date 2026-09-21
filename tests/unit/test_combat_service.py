"""
Unit tests for Combat Service

Tests combat mechanics and functionality including:
- Attack and damage calculations
- Initiative and turn order
- Status effects and conditions
- Combat encounter management
- Automated combat resolution
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List
import json

from source_code.backend.services.combat_service import CombatService
from source_code.backend.api.schemas.combat import (
    CombatEncounter, CombatParticipant, CombatAction,
    AttackAction, DamageType, Condition, InitiativeRoll,
    CombatLog, TurnOrder
)


class TestCombatService:
    """Test suite for CombatService"""

    @pytest.fixture
    def combat_service(self):
        """Create a combat service instance"""
        return CombatService()

    @pytest.fixture
    def sample_attacker(self):
        """Sample attacker character data"""
        return {
            "id": "attacker-1",
            "name": "Fighter",
            "strength": 16,  # +3 modifier
            "dexterity": 14,  # +2 modifier
            "constitution": 15,  # +2 modifier
            "proficiency_bonus": 2,
            "armor_class": 15,
            "max_hp": 45,
            "current_hp": 45,
            "weapons": [
                {
                    "name": "Longsword",
                    "attack_bonus": 5,  # STR +3 + Prof +2
                    "damage_dice": "1d8",
                    "damage_bonus": 3,  # STR modifier
                    "damage_type": "slashing",
                    "properties": ["versatile"]
                }
            ],
            "abilities": ["Extra Attack", "Action Surge"]
        }

    @pytest.fixture
    def sample_defender(self):
        """Sample defender character data"""
        return {
            "id": "defender-1",
            "name": "Goblin",
            "armor_class": 13,
            "max_hp": 15,
            "current_hp": 15,
            "resistances": [],
            "immunities": [],
            "vulnerabilities": []
        }

    @pytest.fixture
    def sample_combat_encounter(self):
        """Sample combat encounter data"""
        return {
            "id": "encounter-1",
            "name": "Goblin Ambush",
            "description": "A group of goblins attacks the party",
            "participants": [],
            "turn_order": [],
            "current_round": 1,
            "current_turn_index": 0,
            "status": "active",
            "started_at": datetime.utcnow(),
            "environment": "forest",
            "terrain": "difficult"
        }

    def test_roll_initiative(self, combat_service):
        """Test initiative rolling"""
        # Normal initiative roll
        initiative = combat_service.roll_initiative(dexterity_modifier=2)
        assert 3 <= initiative <= 22  # 1d20 + 2

        # With advantage
        initiatives = combat_service.roll_initiative_with_advantage(
            dexterity_modifier=1,
            advantage="advantage"
        )
        assert len(initiatives) == 2

        # With disadvantage
        initiatives = combat_service.roll_initiative_with_advantage(
            dexterity_modifier=0,
            advantage="disadvantage"
        )
        assert len(initiatives) == 2

    def test_calculate_attack_roll(self, combat_service, sample_attacker, sample_defender):
        """Test attack roll calculations"""
        attack_action = AttackAction(
            attacker_id=sample_attacker["id"],
            target_id=sample_defender["id"],
            weapon=sample_attacker["weapons"][0],
            advantage="normal"
        )

        with patch.object(combat_service, 'roll_d20') as mock_roll:
            mock_roll.return_value = 15  # Roll a 15

            attack_result = combat_service.calculate_attack_roll(
                attack_action=attack_action,
                attacker=sample_attacker,
                target=sample_defender
            )

            # Total = roll (15) + attack bonus (5) = 20
            assert attack_result["total_attack_roll"] == 20
            assert attack_result["attack_bonus"] == 5
            assert attack_result["natural_roll"] == 15
            assert attack_result["hits"] is True  # 20 > AC 13
            assert attack_result["critical_hit"] is False  # 15 < 20

    def test_calculate_critical_hit(self, combat_service, sample_attacker, sample_defender):
        """Test critical hit calculation"""
        attack_action = AttackAction(
            attacker_id=sample_attacker["id"],
            target_id=sample_defender["id"],
            weapon=sample_attacker["weapons"][0],
            advantage="normal"
        )

        with patch.object(combat_service, 'roll_d20') as mock_roll:
            mock_roll.return_value = 20  # Natural 20

            attack_result = combat_service.calculate_attack_roll(
                attack_action=attack_action,
                attacker=sample_attacker,
                target=sample_defender
            )

            assert attack_result["natural_roll"] == 20
            assert attack_result["critical_hit"] is True
            assert attack_result["hits"] is True  # Natural 20 always hits

    def test_calculate_critical_miss(self, combat_service, sample_attacker, sample_defender):
        """Test critical miss calculation"""
        attack_action = AttackAction(
            attacker_id=sample_attacker["id"],
            target_id=sample_defender["id"],
            weapon=sample_attacker["weapons"][0],
            advantage="normal"
        )

        with patch.object(combat_service, 'roll_d20') as mock_roll:
            mock_roll.return_value = 1  # Natural 1

            attack_result = combat_service.calculate_attack_roll(
                attack_action=attack_action,
                attacker=sample_attacker,
                target=sample_defender
            )

            assert attack_result["natural_roll"] == 1
            assert attack_result["critical_miss"] is True
            assert attack_result["hits"] is False  # Natural 1 always misses

    def test_calculate_damage(self, combat_service, sample_attacker, sample_defender):
        """Test damage calculation"""
        weapon = sample_attacker["weapons"][0]

        with patch.object(combat_service, 'roll_dice') as mock_roll:
            mock_roll.return_value = 6  # Roll 6 on d8

            damage_result = combat_service.calculate_damage(
                weapon=weapon,
                attacker=sample_attacker,
                target=sample_defender,
                critical_hit=False
            )

            # Normal damage: 6 (roll) + 3 (STR bonus) = 9
            assert damage_result["total_damage"] == 9
            assert damage_result["base_damage"] == 9
            assert damage_result["critical_damage"] == 0

    def test_calculate_critical_damage(self, combat_service, sample_attacker, sample_defender):
        """Test critical damage calculation"""
        weapon = sample_attacker["weapons"][0]

        with patch.object(combat_service, 'roll_dice') as mock_roll:
            mock_roll.return_value = 5  # Roll 5 on d8

            damage_result = combat_service.calculate_damage(
                weapon=weapon,
                attacker=sample_attacker,
                target=sample_defender,
                critical_hit=True
            )

            # Critical damage: (5 + 3) * 2 = 16 (roll dice twice, add STR bonus once)
            assert damage_result["total_damage"] == 16
            assert damage_result["base_damage"] == 8  # 5 + 3
            assert damage_result["critical_damage"] == 8  # Additional 5

    def test_apply_resistances_and_immunities(self, combat_service):
        """Test damage application with resistances and immunities"""
        test_cases = [
            # (damage, damage_type, resistances, immunities, expected_damage)
            (10, "fire", ["fire"], [], 5),      # Half damage from resistance
            (10, "cold", [], ["cold"], 0),      # No damage from immunity
            (10, "lightning", ["fire"], ["cold"], 10),  # Full damage, no applicable resistance/immunity
            (15, "fire", ["fire"], [], 8),      # Round down: 15 / 2 = 7.5 -> 7
            (1, "fire", ["fire"], [], 1),       # Minimum 1 damage from resistance
        ]

        for damage, damage_type, resistances, immunities, expected in test_cases:
            target = {
                "resistances": resistances,
                "immunities": immunities
            }

            actual_damage = combat_service.apply_damage_resistances(
                damage=damage,
                damage_type=damage_type,
                target=target
            )

            assert actual_damage == expected, \
                f"Failed for damage={damage}, type={damage_type}, expected={expected}, got={actual_damage}"

    def test_apply_vulnerabilities(self, combat_service):
        """Test damage application with vulnerabilities"""
        target = {
            "vulnerabilities": ["radiant"],
            "resistances": [],
            "immunities": []
        }

        # Vulnerable damage is doubled
        damage = combat_service.apply_damage_resistances(
            damage=8,
            damage_type="radiant",
            target=target
        )
        assert damage == 16  # 8 * 2

    def test_apply_hit_points(self, combat_service, sample_defender):
        """Test applying damage to hit points"""
        defender = sample_defender.copy()

        # Apply damage
        updated_defender = combat_service.apply_damage(
            character=defender,
            damage=10
        )

        assert updated_defender["current_hp"] == 5  # 15 - 10

        # Apply more damage (reducing below 0)
        updated_defender = combat_service.apply_damage(
            character=updated_defender,
            damage=8
        )

        assert updated_defender["current_hp"] == -3  # 5 - 8

    def test_apply_temporary_hit_points(self, combat_service, sample_defender):
        """Test temporary hit points"""
        defender = sample_defender.copy()
        defender["temp_hp"] = 5

        # Apply damage less than temp HP
        updated_defender = combat_service.apply_damage(
            character=defender,
            damage=3
        )

        assert updated_defender["temp_hp"] == 2  # 5 - 3
        assert updated_defender["current_hp"] == 15  # Unchanged

        # Apply damage more than temp HP
        updated_defender = combat_service.apply_damage(
            character=updated_defender,
            damage=5
        )

        assert updated_defender["temp_hp"] == 0  # Depleted
        assert updated_defender["current_hp"] == 12  # 15 - (5 - 2) = 12

    def test_apply_healing(self, combat_service, sample_defender):
        """Test healing application"""
        defender = sample_defender.copy()
        defender["current_hp"] = 8  # Start wounded

        # Apply healing
        updated_defender = combat_service.apply_healing(
            character=defender,
            healing=5
        )

        assert updated_defender["current_hp"] == 13  # 8 + 5

        # Apply overhealing (should not exceed max)
        updated_defender = combat_service.apply_healing(
            character=updated_defender,
            healing=10
        )

        assert updated_defender["current_hp"] == 15  # Capped at max HP

    def test_check_condition_application(self, combat_service):
        """Test condition application and effects"""
        character = {
            "strength": 16,
            "dexterity": 14,
            "speed": 30,
            "conditions": []
        }

        # Apply frightened condition
        updated_character = combat_service.apply_condition(
            character=character,
            condition="frightened"
        )

        assert "frightened" in updated_character["conditions"]

        # Check condition effects
        effects = combat_service.get_condition_effects("frightened")
        assert "disadvantage_on_ability_checks" in effects
        assert effects["disadvantage_on_ability_checks"] == ["strength", "dexterity", "wisdom", "charisma"]

    def test_remove_condition(self, combat_service):
        """Test condition removal"""
        character = {
            "conditions": ["frightened", "poisoned"]
        }

        updated_character = combat_service.remove_condition(
            character=character,
            condition="frightened"
        )

        assert "frightened" not in updated_character["conditions"]
        assert "poisoned" in updated_character["conditions"]

    def test_check_consciousness(self, combat_service):
        """Test consciousness checking"""
        # Conscious character
        conscious_character = {"current_hp": 10, "temp_hp": 0}
        assert combat_service.is_conscious(conscious_character) is True

        # Unconscious but stable (0 HP, no death saves)
        unconscious_character = {"current_hp": 0, "temp_hp": 0}
        assert combat_service.is_conscious(unconscious_character) is False

        # Unconscious and dying (negative HP)
        dying_character = {"current_hp": -5, "temp_hp": 0}
        assert combat_service.is_conscious(dying_character) is False

        # Dead (3 failed death saves)
        dead_character = {
            "current_hp": -3,
            "temp_hp": 0,
            "death_saves": {"failures": 3, "successes": 0}
        }
        assert combat_service.is_conscious(dead_character) is False
        assert combat_service.is_dead(dead_character) is True

    def test_calculate_armor_class_with_conditions(self, combat_service):
        """Test AC calculation with conditions"""
        base_character = {"armor_class": 15}

        # No conditions
        ac = combat_service.get_effective_armor_class(base_character)
        assert ac == 15

        # Prone condition (attacks against prone creature have advantage if within 5ft, disadvantage otherwise)
        prone_character = {**base_character, "conditions": ["prone"]}
        ac = combat_service.get_effective_armor_class(prone_character)
        assert ac == 15  # Base AC unchanged, but attack rolls would be modified

        # Unconscious condition (auto-critical hits)
        unconscious_character = {**base_character, "conditions": ["unconscious"]}
        ac = combat_service.get_effective_armor_class(unconscious_character)
        assert ac == 15  # Base AC unchanged, but attacks are auto-crits

    @pytest.mark.asyncio
    async def test_create_combat_encounter(self, combat_service, sample_combat_encounter):
        """Test creating a new combat encounter"""
        with patch.object(combat_service, 'save_encounter') as mock_save:
            mock_save.return_value = {"id": "encounter-123", **sample_combat_encounter}

            encounter = await combat_service.create_encounter(
                name=sample_combat_encounter["name"],
                description=sample_combat_encounter["description"],
                environment=sample_combat_encounter["environment"]
            )

            assert encounter["name"] == sample_combat_encounter["name"]
            assert encounter["status"] == "active"
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_participant_to_encounter(self, combat_service, sample_combat_encounter, sample_attacker):
        """Test adding participants to combat encounter"""
        encounter_id = "encounter-123"

        with patch.object(combat_service, 'get_encounter') as mock_get, \
             patch.object(combat_service, 'save_encounter') as mock_save:

            mock_get.return_value = {**sample_combat_encounter, "participants": []}

            participant = await combat_service.add_participant(
                encounter_id=encounter_id,
                participant_data=sample_attacker
            )

            mock_get.assert_called_once_with(encounter_id)
            mock_save.assert_called_once()

    def test_roll_initiative_for_participants(self, combat_service):
        """Test rolling initiative for all participants"""
        participants = [
            {"id": "pc-1", "name": "Fighter", "dexterity_modifier": 2},
            {"id": "pc-2", "name": "Rogue", "dexterity_modifier": 4},
            {"id": "enemy-1", "name": "Goblin", "dexterity_modifier": 1}
        ]

        with patch.object(combat_service, 'roll_initiative') as mock_roll:
            mock_roll.side_effect = [15, 18, 12]  # Fixed initiatives for testing

            initiatives = combat_service.roll_initiative_for_participants(participants)

            assert len(initiatives) == 3
            assert initiatives[0]["participant_id"] == "pc-1"
            assert initiatives[0]["initiative"] == 15
            assert initiatives[1]["participant_id"] == "pc-2"
            assert initiatives[1]["initiative"] == 18
            assert initiatives[2]["participant_id"] == "enemy-1"
            assert initiatives[2]["initiative"] == 12

    def test_determine_turn_order(self, combat_service):
        """Test determining turn order from initiatives"""
        initiatives = [
            {"participant_id": "pc-1", "initiative": 15, "dexterity_score": 14},
            {"participant_id": "enemy-1", "initiative": 15, "dexterity_score": 12},
            {"participant_id": "pc-2", "initiative": 18, "dexterity_score": 20}
        ]

        turn_order = combat_service.determine_turn_order(initiatives)

        # Should be sorted by initiative (highest first), then by DEX for ties
        assert turn_order[0]["participant_id"] == "pc-2"  # 18 initiative
        assert turn_order[1]["participant_id"] == "pc-1"  # 15 initiative, higher DEX
        assert turn_order[2]["participant_id"] == "enemy-1"  # 15 initiative, lower DEX

    def test_get_current_turn(self, combat_service):
        """Test getting current turn in combat"""
        encounter = {
            "turn_order": [
                {"participant_id": "pc-1", "initiative": 18},
                {"participant_id": "enemy-1", "initiative": 15},
                {"participant_id": "pc-2", "initiative": 12}
            ],
            "current_turn_index": 1,
            "current_round": 2
        }

        current_turn = combat_service.get_current_turn(encounter)
        assert current_turn["participant_id"] == "enemy-1"
        assert current_turn["turn_number"] == 4  # (Round 2 - 1) * 3 + Index 1 + 1 = 4

    def test_advance_to_next_turn(self, combat_service):
        """Test advancing to next turn"""
        encounter = {
            "turn_order": [
                {"participant_id": "pc-1"},
                {"participant_id": "enemy-1"},
                {"participant_id": "pc-2"}
            ],
            "current_turn_index": 1,
            "current_round": 1
        }

        # Advance to next turn (same round)
        updated_encounter = combat_service.advance_turn(encounter)
        assert updated_encounter["current_turn_index"] == 2
        assert updated_encounter["current_round"] == 1

        # Advance to next turn (new round)
        updated_encounter = combat_service.advance_turn(updated_encounter)
        assert updated_encounter["current_turn_index"] == 0  # Back to start
        assert updated_encounter["current_round"] == 2  # New round

    def test_resolve_attack_action(self, combat_service, sample_attacker, sample_defender):
        """Test resolving a complete attack action"""
        attack_action = AttackAction(
            attacker_id=sample_attacker["id"],
            target_id=sample_defender["id"],
            weapon=sample_attacker["weapons"][0],
            advantage="normal"
        )

        with patch.object(combat_service, 'roll_d20') as mock_attack_roll, \
             patch.object(combat_service, 'roll_dice') as mock_damage_roll:

            # Setup mocks
            mock_attack_roll.return_value = 16  # Hit
            mock_damage_roll.return_value = 5

            combat_log = combat_service.resolve_attack_action(
                attack_action=attack_action,
                attacker=sample_attacker,
                target=sample_defender
            )

            assert combat_log["action_type"] == "attack"
            assert combat_log["attacker_id"] == sample_attacker["id"]
            assert combat_log["target_id"] == sample_defender["id"]
            assert combat_log["hit"] is True
            assert combat_log["damage"] > 0
            assert combat_log["target_remaining_hp"] < sample_defender["current_hp"]

    def test_resolve_saving_throw(self, combat_service):
        """Test resolving saving throws"""
        character = {
            "id": "pc-1",
            "name": "Wizard",
            "dexterity": 14,  # +2 modifier
            "wisdom": 12,     # +1 modifier
            "proficiency_bonus": 2
        }

        # Dexterity saving throw (proficient for wizard)
        with patch.object(combat_service, 'roll_d20') as mock_roll:
            mock_roll.return_value = 14  # Roll 14

            save_result = combat_service.resolve_saving_throw(
                character=character,
                save_type="dexterity",
                save_dc=15,
                is_proficient=True
            )

            # Total = 14 (roll) + 2 (DEX) + 2 (proficiency) = 18
            assert save_result["total"] == 18
            assert save_result["success"] is True  # 18 >= DC 15

        # Wisdom saving throw (not proficient)
        with patch.object(combat_service, 'roll_d20') as mock_roll:
            mock_roll.return_value = 10  # Roll 10

            save_result = combat_service.resolve_saving_throw(
                character=character,
                save_type="wisdom",
                save_dc=14,
                is_proficient=False
            )

            # Total = 10 (roll) + 1 (WIS) + 0 (no proficiency) = 11
            assert save_result["total"] == 11
            assert save_result["success"] is False  # 11 < DC 14

    def test_spell_attack_resolution(self, combat_service):
        """Test resolving spell attacks"""
        caster = {
            "id": "caster-1",
            "spellcasting_ability": "intelligence",
            "intelligence": 18,  # +4 modifier
            "proficiency_bonus": 2
        }

        target = {
            "id": "target-1",
            "armor_class": 14
        }

        spell = {
            "name": "Fire Bolt",
            "attack_bonus": 6,  # INT +4 + Prof +2
            "damage_dice": "1d10",
            "damage_type": "fire"
        }

        with patch.object(combat_service, 'roll_d20') as mock_roll, \
             patch.object(combat_service, 'roll_dice') as mock_damage:

            mock_roll.return_value = 12  # Roll 12
            mock_damage.return_value = 7  # Roll 7

            result = combat_service.resolve_spell_attack(
                caster=caster,
                target=target,
                spell=spell
            )

            # Attack: 12 + 6 = 18 vs AC 14 = Hit
            assert result["hit"] is True
            assert result["attack_roll_total"] == 18
            # Damage: 7 (no stat bonus to spell damage typically)
            assert result["damage"] == 7

    def test_area_of_effect_spell(self, combat_service):
        """Test resolving area of effect spells"""
        spell = {
            "name": "Fireball",
            "damage_dice": "8d6",
            "damage_type": "fire",
            "save_dc": 15,
            "save_ability": "dexterity"
        }

        targets = [
            {"id": "target-1", "dexterity": 14, "dexterity_save_proficient": False},  # +2, not proficient
            {"id": "target-2", "dexterity": 16, "dexterity_save_proficient": True},   # +3, proficient
            {"id": "target-3", "dexterity": 12, "dexterity_save_proficient": False}    # +1, not proficient
        ]

        with patch.object(combat_service, 'roll_d20') as mock_save_roll, \
             patch.object(combat_service, 'roll_dice') as mock_damage:

            # Setup saving throws
            mock_save_roll.side_effect = [15, 12, 8]  # Different rolls for each target
            mock_damage.return_value = 28  # Fireball damage

            results = combat_service.resolve_area_spell(
                spell=spell,
                targets=targets
            )

            # Target 1: Roll 15 + 2 = 17 >= DC 15 = Save for half
            assert results[0]["target_id"] == "target-1"
            assert results[0]["save_success"] is True
            assert results[0]["damage_taken"] == 14  # Half of 28

            # Target 2: Roll 12 + 3 + 2 = 17 >= DC 15 = Save for half
            assert results[1]["target_id"] == "target-2"
            assert results[1]["save_success"] is True
            assert results[1]["damage_taken"] == 14

            # Target 3: Roll 8 + 1 = 9 < DC 15 = Fail, full damage
            assert results[2]["target_id"] == "target-3"
            assert results[2]["save_success"] is False
            assert results[2]["damage_taken"] == 28

    def test_grapple_and_shove_attempts(self, combat_service):
        """Test grapple and shove special attacks"""
        attacker = {
            "id": "attacker-1",
            "strength": 16,  # +3 modifier
            "athletics_proficient": True,
            "proficiency_bonus": 2
        }

        target = {
            "id": "target-1",
            "strength": 12,  # +1 modifier
            "athletics_proficient": False
        }

        # Grapple attempt (attack vs. escape)
        with patch.object(combat_service, 'roll_d20') as mock_roll:
            # Attacker roll: 15, Target roll: 8
            mock_roll.side_effect = [15, 8]

            grapple_result = combat_service.resolve_grapple(
                attacker=attacker,
                target=target
            )

            # Attacker: 15 + 3 + 2 = 20
            # Target: 8 + 1 = 9
            # Attacker wins
            assert grapple_result["success"] is True
            assert "grappled" in grapple_result["applied_conditions"]

        # Shove attempt (push vs. prone)
        with patch.object(combat_service, 'roll_d20') as mock_roll:
            # Attacker roll: 12, Target roll: 16
            mock_roll.side_effect = [12, 16]

            shove_result = combat_service.resolve_shove(
                attacker=attacker,
                target=target,
                shove_type="prone"  # Knock prone
            )

            # Attacker: 12 + 3 + 2 = 17
            # Target: 16 + 1 = 17
            # Tie goes to defender
            assert shove_result["success"] is False
            assert len(shove_result["applied_conditions"]) == 0


class TestCombatEdgeCases:
    """Test edge cases and unusual combat scenarios"""

    @pytest.fixture
    def combat_service(self):
        return CombatService()

    def test_invisible_attacker(self, combat_service):
        """Test attacks from invisible attackers"""
        invisible_attacker = {
            "conditions": ["invisible"],
            "strength": 16,
            "proficiency_bonus": 2
        }

        target = {
            "armor_class": 15
        }

        # Invisible attackers have advantage on attacks
        with patch.object(combat_service, 'roll_d20_with_advantage') as mock_roll:
            mock_roll.return_value = [18, 12]  # Roll with advantage

            attack_result = combat_service.calculate_attack_roll(
                attack_action=None,
                attacker=invisible_attacker,
                target=target
            )

            assert attack_result["advantage_used"] is True
            assert attack_result["total_attack_roll"] == 23  # 18 + 5 attack bonus

    def_test_attack_against_blinded_target(self, combat_service):
        """Test attacks against blinded targets"""
        blinded_target = {
            "armor_class": 15,
            "conditions": ["blinded"]
        }

        attacker = {
            "strength": 16,
            "proficiency_bonus": 2
        }

        # Attacks against blinded targets have advantage
        with patch.object(combat_service, 'roll_d20_with_advantage') as mock_roll:
            mock_roll.return_value = [14, 19]

            attack_result = combat_service.calculate_attack_roll(
                attack_action=None,
                attacker=attacker,
                target=blinded_target
            )

            assert attack_result["advantage_used"] is True
            assert attack_result["total_attack_roll"] == 24  # 19 + 5 attack bonus

    def test_attacker_with_exhaustion(self, combat_service):
        """Test attacks from characters with exhaustion levels"""
        exhausted_attacker = {
            "strength": 16,
            "proficiency_bonus": 2,
            "conditions": ["exhaustion_3"]  # Level 3 exhaustion
        }

        target = {
            "armor_class": 15
        }

        # Level 3+ exhaustion: disadvantage on attack rolls
        with patch.object(combat_service, 'roll_d20_with_disadvantage') as mock_roll:
            mock_roll.return_value = [8, 15]

            attack_result = combat_service.calculate_attack_roll(
                attack_action=None,
                attacker=exhausted_attacker,
                target=target
            )

            assert attack_result["disadvantage_used"] is True
            assert attack_result["total_attack_roll"] == 13  # 8 + 5 attack bonus (worse roll)

    def test_zero_damage_situations(self, combat_service):
        """Test situations that result in zero damage"""
        target = {
            "resistances": ["fire"],
            "immunities": ["poison"],
            "temp_hp": 10,
            "current_hp": 20
        }

        # Fire damage against resistant target (should be minimum 1)
        fire_damage = combat_service.apply_damage_resistances(
            damage=1,
            damage_type="fire",
            target=target
        )
        assert fire_damage == 1  # Minimum 1 damage

        # Poison damage against immune target
        poison_damage = combat_service.apply_damage_resistances(
            damage=10,
            damage_type="poison",
            target=target
        )
        assert poison_damage == 0

        # Apply damage to temp HP only
        updated_target = combat_service.apply_damage(target, damage=5)
        assert updated_target["temp_hp"] == 5
        assert updated_target["current_hp"] == 20

    def test_multiple_conditions_interaction(self, combat_service):
        """Test interaction of multiple conditions"""
        character = {
            "strength": 16,
            "dexterity": 14,
            "speed": 30,
            "armor_class": 15,
            "conditions": ["grappled", "prone"]
        }

        # Prone and grappled: speed is 0, disadvantage on attacks
        effective_speed = combat_service.get_effective_speed(character)
        assert effective_speed == 0

        # Attack with disadvantage from prone, but also check if grappled affects
        # (grappled doesn't directly give disadvantage on attacks)
        attack_disadvantage = combat_service.has_attack_disadvantage(character)
        assert attack_disadvantage is True  # From prone condition

    def test_concentration_saving_throw(self, combat_service):
        """Test concentration saving throws"""
        caster = {
            "constitution": 14,  # +2 modifier
            "proficiency_bonus": 2,
            "concentration": True
        }

        # Taking damage that requires concentration save
        with patch.object(combat_service, 'roll_d20') as mock_roll:
            mock_roll.return_value = 13  # Roll 13

            save_result = combat_service.resolve_concentration_save(
                caster=caster,
                damage_taken=25  # Damage taken
            )

            # DC = 10 or half damage, whichever is higher
            # Half damage = 12.5, so DC = 13
            # Save total = 13 + 2 = 15 >= DC 13 = Success
            assert save_result["save_dc"] == 13
            assert save_result["save_total"] == 15
            assert save_result["concentration_maintained"] is True

    def test_cover_effects(self, combat_service):
        """Test effects of cover on attacks"""
        target = {
            "armor_class": 15,
            "cover": "half"  # Half cover (+2 to AC)
        }

        attacker = {
            "strength": 16,
            "proficiency_bonus": 2
        }

        with patch.object(combat_service, 'roll_d20') as mock_roll:
            mock_roll.return_value = 13

            attack_result = combat_service.calculate_attack_roll(
                attack_action=None,
                attacker=attacker,
                target=target
            )

            # Attack roll: 13 + 5 = 18
            # Target AC with cover: 15 + 2 = 17
            # 18 >= 17 = Hit
            assert attack_result["hits"] is True
            assert attack_result["target_ac"] == 17
            assert attack_result["cover_bonus"] == 2

    def test_unconscious_target_auto_criticals(self, combat_service):
        """Test that attacks against unconscious targets are automatic criticals"""
        unconscious_target = {
            "armor_class": 15,
            "conditions": ["unconscious"]
        }

        attacker = {
            "strength": 16,
            "proficiency_bonus": 2
        }

        attack_result = combat_service.calculate_attack_roll(
            attack_action=None,
            attacker=attacker,
            target=unconscious_target
        )

        # Auto-hit and auto-crit against unconscious targets
        assert attack_result["hits"] is True
        assert attack_result["critical_hit"] is True
        assert attack_result["auto_critical"] is True

    def test_long_combat_round_tracking(self, combat_service):
        """Test combat over multiple rounds"""
        encounter = {
            "turn_order": [
                {"participant_id": "pc-1"},
                {"participant_id": "enemy-1"},
                {"participant_id": "pc-2"}
            ],
            "current_turn_index": 0,
            "current_round": 1,
            "status": "active"
        }

        # Simulate 5 rounds of combat
        for round_num in range(1, 6):
            for turn_num in range(3):
                assert encounter["current_round"] == round_num
                assert encounter["current_turn_index"] == turn_num
                encounter = combat_service.advance_turn(encounter)

        # After 5 rounds (15 turns), should be round 6, turn 0
        assert encounter["current_round"] == 6
        assert encounter["current_turn_index"] == 0