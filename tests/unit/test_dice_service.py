"""
Unit tests for Dice Service

Tests the core dice rolling functionality including:
- Basic dice rolling
- Advanced dice mechanics (advantage, disadvantage, critical hits)
- Dice expression parsing
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import random

from source_code.backend.services.dice_service import (
    DiceService, ParsedExpression, get_dice_service
)
from source_code.backend.api.schemas.dice import (
    DiceRoll, RollResult, RollRequest, RollResponse,
    AdvantageType, CriticalType, RollType, FormulaValidationResponse
)


class TestDiceService:
    """Test suite for DiceService class"""

    @pytest.fixture
    def dice_service(self):
        """Create a dice service instance with fixed seed for predictable tests"""
        return DiceService(seed=42)

    @pytest.fixture
    def dice_service_no_seed(self):
        """Create a dice service without seed for random tests"""
        return DiceService()

    def test_dice_service_initialization(self, dice_service):
        """Test that dice service initializes correctly"""
        assert dice_service is not None
        assert dice_service.STANDARD_DICE == [4, 6, 8, 10, 12, 20, 100]
        assert dice_service.CRITICAL_HIT_THRESHOLD == 20
        assert dice_service.CRITICAL_MISS_THRESHOLD == 1

    def test_parse_simple_expression(self, dice_service):
        """Test parsing simple dice expressions"""
        # Test basic NdS format
        parsed = dice_service.parse_dice_expression("2d6")
        assert parsed.count == 2
        assert parsed.sides == 6
        assert parsed.modifier == 0
        assert parsed.raw_expression == "2d6"

        # Test with modifier
        parsed = dice_service.parse_dice_expression("1d20+5")
        assert parsed.count == 1
        assert parsed.sides == 20
        assert parsed.modifier == 5

        # Test with negative modifier
        parsed = dice_service.parse_dice_expression("3d8-2")
        assert parsed.count == 3
        assert parsed.sides == 8
        assert parsed.modifier == -2

    def test_parse_advanced_expressions(self, dice_service):
        """Test parsing advanced dice expressions with options"""
        # Keep highest
        parsed = dice_service.parse_dice_expression("4d6kh3")
        assert parsed.count == 4
        assert parsed.sides == 6
        assert parsed.drop_highest == 1

        # Drop lowest
        parsed = dice_service.parse_dice_expression("4d6dl1")
        assert parsed.count == 4
        assert parsed.sides == 6
        assert parsed.drop_lowest == 1

        # Reroll
        parsed = dice_service.parse_dice_expression("2d10r8")
        assert parsed.count == 2
        assert parsed.sides == 10
        assert parsed.reroll_on == 8

        # Explode
        parsed = dice_service.parse_dice_expression("2d6!")
        assert parsed.count == 2
        assert parsed.sides == 6
        assert parsed.explode_on == 6

        # Explode on specific value
        parsed = dice_service.parse_dice_expression("2d6!5")
        assert parsed.count == 2
        assert parsed.sides == 6
        assert parsed.explode_on == 5

        # Minimum value
        parsed = dice_service.parse_dice_expression("1d20min10")
        assert parsed.count == 1
        assert parsed.sides == 20
        assert parsed.min_value == 10

    def test_parse_invalid_expressions(self, dice_service):
        """Test that invalid expressions raise appropriate errors"""
        invalid_expressions = [
            "d6",           # Missing count
            "2d",           # Missing sides
            "2d6.5",        # Non-integer sides
            "abc",          # Non-numeric
            "",             # Empty string
            "2d6x3",        # Invalid option
        ]

        for expr in invalid_expressions:
            with pytest.raises(ValueError, match="Invalid dice expression"):
                dice_service.parse_dice_expression(expr)

    def test_roll_single_die(self, dice_service_no_seed):
        """Test rolling a single die"""
        # Test basic roll
        results = dice_service_no_seed.roll_single_die(6)
        assert len(results) == 1
        assert 1 <= results[0] <= 6

        # Test with minimum value
        results = dice_service_no_seed.roll_single_die(20, min_value=10)
        assert results[0] >= 10

        # Test with maximum value
        results = dice_service_no_seed.roll_single_die(20, max_value=15)
        assert results[0] <= 15

    @patch('random.randint')
    def test_roll_single_die_with_reroll(self, mock_randint, dice_service):
        """Test reroll functionality"""
        # First roll triggers reroll, second roll is normal
        mock_randint.side_effect = [8, 15]  # First roll is 8 (reroll), second is 15

        results = dice_service.roll_single_die(20, reroll_on=8)

        assert len(results) == 1
        assert results[0] == 15
        assert mock_randint.call_count == 2

    @patch('random.randint')
    def test_roll_single_die_with_explode(self, mock_randint, dice_service):
        """Test explosion functionality"""
        # First roll triggers explosion, second roll is normal
        mock_randint.side_effect = [6, 4]  # First roll is 6 (explode), second is 4

        results = dice_service.roll_single_die(6, explode_on=6)

        assert len(results) == 2
        assert results == [6, 4]
        assert mock_randint.call_count == 2

    def test_roll_dice_expression_basic(self, dice_service):
        """Test basic dice expression rolling"""
        result = dice_service.roll_dice_expression("2d6")

        assert isinstance(result, RollResult)
        assert result.expression == "2d6"
        assert len(result.dice_rolls) == 2
        assert all(roll.sides == 6 for roll in result.dice_rolls)
        assert 2 <= result.total <= 14  # 2 dice * 6 max + 0 modifier

    def test_roll_dice_expression_with_modifier(self, dice_service):
        """Test rolling with modifiers"""
        result = dice_service.roll_dice_expression("1d20+5")

        assert result.modifier_total == 5
        assert result.total >= 6  # 1 + 5
        assert result.total <= 25  # 20 + 5

    def test_roll_dice_expression_with_drop_rules(self, dice_service):
        """Test rolling with drop lowest/highest rules"""
        # Use a known seed for predictable results
        dice_service_seeded = DiceService(seed=123)
        result = dice_service_seeded.roll_dice_expression("4d6dl1")

        # Should have 4 dice rolls but drop lowest
        assert len(result.dice_rolls) == 4

    def test_critical_detection(self, dice_service):
        """Test critical hit and miss detection"""
        # Mock specific rolls for testing
        with patch.object(dice_service, 'roll_single_die') as mock_roll:
            # Test natural 20 (critical hit)
            mock_roll.return_value = [20]
            result = dice_service.roll_dice_expression("1d20")
            assert result.critical_type == CriticalType.CRITICAL_HIT

            # Test natural 1 (critical miss)
            mock_roll.return_value = [1]
            result = dice_service.roll_dice_expression("1d20")
            assert result.critical_type == CriticalType.CRITICAL_MISS

            # Test normal roll
            mock_roll.return_value = [10]
            result = dice_service.roll_dice_expression("1d20")
            assert result.critical_type == CriticalType.NONE

    def test_roll_with_advantage(self, dice_service):
        """Test rolling with advantage and disadvantage"""
        # Test normal roll
        results = dice_service.roll_with_advantage("1d20", AdvantageType.NORMAL)
        assert len(results) == 1

        # Test advantage
        results = dice_service.roll_with_advantage("1d20", AdvantageType.ADVANTAGE)
        assert len(results) == 2

        # Test disadvantage
        results = dice_service.roll_with_advantage("1d20", AdvantageType.DISADVANTAGE)
        assert len(results) == 2

        # Test elven accuracy
        results = dice_service.roll_with_advantage("1d20", AdvantageType.ELVEN_ACCURACY)
        assert len(results) == 3

    def test_process_roll_request_basic(self, dice_service):
        """Test processing a complete roll request"""
        request = RollRequest(
            expressions=["1d20+5", "2d6"],
            roll_type=RollType.ATTACK,
            description="Test attack roll",
            character_id="test-char",
            session_id="test-session"
        )

        response = dice_service.process_roll_request(request)

        assert isinstance(response, RollResponse)
        assert response.id is not None
        assert response.character_id == "test-char"
        assert response.session_id == "test-session"
        assert len(response.results) == 2
        assert response.total > 0
        assert response.description == "Test attack roll"

    def test_process_roll_request_with_advantage(self, dice_service):
        """Test processing roll request with advantage"""
        request = RollRequest(
            expressions=["1d20"],
            advantage=AdvantageType.ADVANTAGE,
            roll_type=RollType.ATTACK,
            dc=15
        )

        response = dice_service.process_roll_request(request)

        # Should use best of two rolls for advantage
        assert len(response.results) == 1
        assert response.success is not None  # Should be determined since DC is provided

    def test_process_roll_request_with_dc(self, dice_service):
        """Test processing roll request with difficulty class"""
        request = RollRequest(
            expressions=["1d20"],
            dc=10,
            roll_type=RollType.SAVING_THROW
        )

        response = dice_service.process_roll_request(request)

        assert response.dc == 10
        assert response.success is not None
        assert isinstance(response.success, bool)

    def test_validate_formula_valid(self, dice_service):
        """Test formula validation for valid formulas"""
        valid_formulas = ["1d20", "2d6+3", "4d6kh3", "1d8!"]

        for formula in valid_formulas:
            validation = dice_service.validate_formula(formula)
            assert validation.is_valid is True
            assert validation.formula == formula
            assert validation.min_possible is not None
            assert validation.max_possible is not None
            assert validation.average is not None

    def test_validate_formula_invalid(self, dice_service):
        """Test formula validation for invalid formulas"""
        invalid_formulas = ["d6", "2d", "abc", ""]

        for formula in invalid_formulas:
            validation = dice_service.validate_formula(formula)
            assert validation.is_valid is False
            assert validation.error_message is not None

    def test_validate_formula_calculations(self, dice_service):
        """Test formula validation calculations"""
        validation = dice_service.validate_formula("2d6+3")

        # Min: 2 dice * 1 + 3 modifier = 5
        assert validation.min_possible == 5
        # Max: 2 dice * 6 + 3 modifier = 15
        assert validation.max_possible == 15
        # Average: 2 dice * 3.5 + 3 modifier = 10
        assert validation.average == 10.0

    def test_calculate_passive_score(self, dice_service):
        """Test passive score calculation"""
        # Passive score = 10 + bonus
        assert dice_service.calculate_passive_score(5) == 15
        assert dice_service.calculate_passive_score(0) == 10
        assert dice_service.calculate_passive_score(-2) == 8

    def test_calculate_critical_damage(self, dice_service):
        """Test critical damage calculation"""
        result = dice_service.calculate_critical_damage("2d6")

        # Should roll damage twice
        assert len(result.dice_rolls) == 4  # 2 dice * 2 rolls
        assert "2x2d6" in result.expression
        assert result.critical_type == CriticalType.CRITICAL_HIT

    def test_calculate_critical_damage_with_extra(self, dice_service):
        """Test critical damage with extra damage"""
        result = dice_service.calculate_critical_damage("2d6", "1d4")

        # Should have 2d6 (rolled twice) + 1d4 extra
        assert len(result.dice_rolls) == 5  # 4 from crit + 1 extra
        assert "2x2d6+1d4" in result.expression

    def test_roll_death_save_success(self, dice_service):
        """Test death saving throw success"""
        with patch.object(dice_service, 'roll_dice_expression') as mock_roll:
            mock_result = Mock()
            mock_result.total = 15
            mock_result.critical_type = CriticalType.NONE
            mock_result.metadata = {}
            mock_roll.return_value = mock_result

            result = dice_service.roll_death_save()
            assert result.metadata["outcome"] == "success"

    def test_roll_death_save_critical_success(self, dice_service):
        """Test death saving throw critical success (natural 20)"""
        with patch.object(dice_service, 'roll_dice_expression') as mock_roll:
            mock_result = Mock()
            mock_result.total = 20
            mock_result.critical_type = CriticalType.CRITICAL_HIT
            mock_result.metadata = {}
            mock_roll.return_value = mock_result

            result = dice_service.roll_death_save()
            assert result.metadata["outcome"] == "stable"
            assert result.metadata["heal_1_hp"] is True

    def test_roll_death_save_failure(self, dice_service):
        """Test death saving throw failure"""
        with patch.object(dice_service, 'roll_dice_expression') as mock_roll:
            mock_result = Mock()
            mock_result.total = 5
            mock_result.critical_type = CriticalType.NONE
            mock_result.metadata = {}
            mock_roll.return_value = mock_result

            result = dice_service.roll_death_save()
            assert result.metadata["outcome"] == "failure"

    def test_roll_death_save_critical_failure(self, dice_service):
        """Test death saving throw critical failure (natural 1)"""
        with patch.object(dice_service, 'roll_dice_expression') as mock_roll:
            mock_result = Mock()
            mock_result.total = 1
            mock_result.critical_type = CriticalType.CRITICAL_MISS
            mock_result.metadata = {}
            mock_roll.return_value = mock_result

            result = dice_service.roll_death_save()
            assert result.metadata["outcome"] == "critical_failure"
            assert result.metadata["two_failures"] is True

    def test_roll_initiative_normal(self, dice_service):
        """Test initiative roll with normal circumstances"""
        result = dice_service.roll_initiative(3)  # +3 Dexterity modifier

        assert result.total >= 4  # 1 (min d20) + 3
        assert result.total <= 23  # 20 (max d20) + 3
        assert "+3" in result.expression

    def test_roll_initiative_with_advantage(self, dice_service):
        """Test initiative roll with advantage"""
        with patch.object(dice_service, 'roll_with_advantage') as mock_advantage:
            mock_results = [Mock(total=15), Mock(total=8)]
            mock_advantage.return_value = mock_results

            result = dice_service.roll_initiative(2, AdvantageType.ADVANTAGE)

            # Should select the higher roll (15) and add modifier
            assert mock_advantage.called
            assert result.total == 17  # 15 + 2 modifier

    def test_get_ability_modifier_placeholder(self, dice_service):
        """Test ability modifier function (placeholder implementation)"""
        # This is currently a placeholder, should return 0
        result = dice_service.get_ability_modifier("strength")
        assert result == 0

    def test_set_ability_score_placeholder(self, dice_service):
        """Test setting ability score (placeholder implementation)"""
        # This is currently a placeholder, should not raise error
        dice_service.set_ability_score(16)
        assert True  # Should not raise any exceptions

    def test_global_dice_service_singleton(self):
        """Test that get_dice_service returns a singleton instance"""
        service1 = get_dice_service()
        service2 = get_dice_service()

        assert service1 is service2
        assert isinstance(service1, DiceService)

    def test_dice_service_with_custom_seed(self):
        """Test that dice service with seed produces consistent results"""
        service1 = DiceService(seed=42)
        service2 = DiceService(seed=42)

        # Both services should produce the same result for the same expression
        result1 = service1.roll_dice_expression("1d20")
        result2 = service2.roll_dice_expression("1d20")

        assert result1.total == result2.total


class TestDiceEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.fixture
    def dice_service(self):
        return DiceService()

    def test_zero_dice_count(self, dice_service):
        """Test handling of zero dice count"""
        # This should be invalid
        with pytest.raises(ValueError):
            dice_service.parse_dice_expression("0d6")

    def test_negative_dice_count(self, dice_service):
        """Test handling of negative dice count"""
        # This should be invalid
        with pytest.raises(ValueError):
            dice_service.parse_dice_expression("-1d6")

    def test_zero_sided_die(self, dice_service):
        """Test handling of zero-sided die"""
        with pytest.raises(ValueError):
            dice_service.parse_dice_expression("1d0")

    def test_negative_sided_die(self, dice_service):
        """Test handling of negative-sided die"""
        with pytest.raises(ValueError):
            dice_service.parse_dice_expression("1d-6")

    def test_very_large_dice_count(self, dice_service):
        """Test handling of very large dice counts"""
        parsed = dice_service.parse_dice_expression("1000d6")
        assert parsed.count == 1000

        # Actually rolling this might be slow, so we'll just test parsing
        # In a real implementation, you might want to limit this

    def test_very_large_sides(self, dice_service):
        """Test handling of dice with many sides"""
        parsed = dice_service.parse_dice_expression("1d1000000")
        assert parsed.sides == 1000000

    def test_complex_expression_parsing(self, dice_service):
        """Test parsing of complex expressions with multiple options"""
        # Expression with multiple options
        parsed = dice_service.parse_dice_expression("6d6dl1kh4r1!6min2max5")

        assert parsed.count == 6
        assert parsed.sides == 6
        assert parsed.drop_lowest == 1
        assert parsed.drop_highest == 1  # 6 - 4 = 2, but we specified dl1, so dh1
        assert parsed.reroll_on == 1
        assert parsed.explode_on == 6
        assert parsed.min_value == 2
        assert parsed.max_value == 5

    def test_whitespace_handling(self, dice_service):
        """Test that whitespace is properly handled"""
        expressions = [
            "2d6 + 3",
            " 1d20",
            "4d8 - 2 ",
            " 2d6 kh2 ",
            " 1d20 + 5 "
        ]

        for expr in expressions:
            # Should not raise an error
            parsed = dice_service.parse_dice_expression(expr)
            assert parsed.raw_expression == expr.strip().lower().replace(" ", "")

    def test_case_sensitivity(self, dice_service):
        """Test that expression parsing is case insensitive"""
        # Mixed case options
        parsed = dice_service.parse_dice_expression("2D6KH2")
        assert parsed.count == 2
        assert parsed.sides == 6
        assert parsed.drop_highest == 0  # 2 - 2 = 0 to keep

    def test_empty_roll_request(self, dice_service):
        """Test handling of empty roll request"""
        request = RollRequest(
            expressions=[],
            roll_type=RollType.ATTACK
        )

        response = dice_service.process_roll_request(request)
        assert len(response.results) == 0
        assert response.total == 0

    def test_multiple_expressions_roll_request(self, dice_service):
        """Test roll request with multiple expressions"""
        request = RollRequest(
            expressions=["1d20", "2d6+2", "1d4"],
            roll_type=RollType.DAMAGE
        )

        response = dice_service.process_roll_request(request)
        assert len(response.results) == 3
        assert response.total > 0

    def test_roll_request_metadata(self, dice_service):
        """Test roll request with custom metadata"""
        metadata = {
            "weapon": "longsword",
            "character": "fighter",
            "situational_modifiers": ["advantage", "bless"]
        }

        request = RollRequest(
            expressions=["1d20+5"],
            roll_type=RollType.ATTACK,
            metadata=metadata
        )

        response = dice_service.process_roll_request(request)
        assert response.metadata == metadata


class TestDicePerformance:
    """Performance-related tests for dice service"""

    @pytest.fixture
    def dice_service(self):
        return DiceService()

    def test_large_dice_roll_performance(self, dice_service):
        """Test that large dice rolls don't take too long"""
        import time

        start_time = time.time()
        result = dice_service.roll_dice_expression("100d6")
        end_time = time.time()

        # Should complete within reasonable time (less than 1 second)
        assert end_time - start_time < 1.0
        assert len(result.dice_rolls) == 100

    def test_multiple_roll_requests_performance(self, dice_service):
        """Test performance of multiple roll requests"""
        import time

        start_time = time.time()

        for _ in range(100):
            request = RollRequest(
                expressions=["1d20+5"],
                roll_type=RollType.ATTACK
            )
            dice_service.process_roll_request(request)

        end_time = time.time()

        # Should complete 100 rolls within reasonable time
        assert end_time - start_time < 2.0

    def test_concurrent_dice_rolls(self, dice_service):
        """Test thread safety of concurrent dice rolls"""
        import threading
        import time

        results = []
        errors = []

        def roll_dice():
            try:
                for _ in range(10):
                    result = dice_service.roll_dice_expression("1d20")
                    results.append(result.total)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=roll_dice)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have no errors and results from all threads
        assert len(errors) == 0
        assert len(results) == 50  # 5 threads * 10 rolls each