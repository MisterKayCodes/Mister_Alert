import unittest
from app.core.calculators.position_size import get_position_size
from app.core.calculators.risk_reward import calculate_risk_reward
from app.utils.symbol_validator import is_valid_symbol

class TestProductionHardening(unittest.TestCase):

    def test_eurusd_math(self):
        """
        Verify the USER's specific test case:
        EURUSD, Entry: 1.0500, SL: 1.03752 (124.8 pips), Risk: $20.00
        Expected: ~0.016 lots
        """
        # Note: 124.8 pips = 0.01248 price diff
        # 0.01248 / 0.0001 = 124.8 pips
        # formula: 20 / (124.8 * 10) = 20 / 1248 = 0.016025
        result = get_position_size("EURUSD", 1.0500, 1.03752, 20.00)
        self.assertEqual(result["pips"], 124.8)
        self.assertAlmostEqual(result["lots"], 0.016, places=3)
        self.assertIsNone(result["warning"])

    def test_calculator_warnings(self):
        """Verify that unusually wide stops trigger a warning."""
        # Standard Forex > 150 pips
        result = get_position_size("EURUSD", 1.1000, 1.0800, 100.00) # 200 pips
        self.assertEqual(result["pips"], 200.0)
        self.assertEqual(result["warning"], "Unusually wide Stop Loss")

        # Extremely wide > 1000 pips
        result = get_position_size("EURUSD", 1.2000, 1.0500, 100.00) # 1500 pips
        self.assertEqual(result["warning"], "Extremely wide Stop Loss")

    def test_gold_math(self):
        """Verify Gold (XAUUSD) math: $10 per 1.0 standard lot per 0.1 move."""
        # Gold 2000 -> 1990 is 100 pips (10.0 / 0.1)
        # Risk $100. 100 / (100 * 10) = 0.1 lots
        result = get_position_size("XAUUSD", 2000.0, 1990.0, 100.00)
        self.assertEqual(result["pips"], 100.0)
        self.assertEqual(result["lots"], 0.1)

    def test_symbol_validation(self):
        """Verify the new symbol validator respects production standards."""
        self.assertTrue(is_valid_symbol("BTCUSD"))
        self.assertTrue(is_valid_symbol("EUR/USD"))
        self.assertTrue(is_valid_symbol("NAS100"))
        
        self.assertFalse(is_valid_symbol("A")) # Too short
        self.assertFalse(is_valid_symbol("ThisIsWayTooLongForASymbolName")) # Too long
        self.assertFalse(is_valid_symbol("BTC!@#")) # Special chars

if __name__ == '__main__':
    unittest.main()
