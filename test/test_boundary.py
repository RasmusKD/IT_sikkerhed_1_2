"""
Grænseværditest (Boundary Value Testing)
IT-sikkerhed eksempel: Password længde validering

Regler:
- Minimum: 8 tegn
- Maximum: 64 tegn
"""
import pytest


def validate_password_length(password):
    """Returnerer True hvis password er mellem 8-64 tegn."""
    length = len(password)
    return 8 <= length <= 64


# =============================================================================
# GRÆNSEVÆRDI TESTS - Tester ved grænserne
# =============================================================================

class TestPasswordBoundaryValues:
    """Tester grænseværdier for password længde (8-64 tegn)."""
    
    # --- Under minimum grænse ---
    def test_length_0_invalid(self):
        """Tomt password - langt under grænsen."""
        assert validate_password_length("") == False
    
    def test_length_7_invalid(self):
        """7 tegn - lige under minimum (grænseværdi)."""
        assert validate_password_length("a" * 7) == False
    
    # --- Ved minimum grænse ---
    def test_length_8_valid(self):
        """8 tegn - præcis på minimum (grænseværdi)."""
        assert validate_password_length("a" * 8) == True
    
    def test_length_9_valid(self):
        """9 tegn - lige over minimum."""
        assert validate_password_length("a" * 9) == True
    
    # --- Midt i gyldig range ---
    def test_length_32_valid(self):
        """32 tegn - midt i gyldig range."""
        assert validate_password_length("a" * 32) == True
    
    # --- Ved maximum grænse ---
    def test_length_63_valid(self):
        """63 tegn - lige under maximum."""
        assert validate_password_length("a" * 63) == True
    
    def test_length_64_valid(self):
        """64 tegn - præcis på maximum (grænseværdi)."""
        assert validate_password_length("a" * 64) == True
    
    def test_length_65_invalid(self):
        """65 tegn - lige over maximum (grænseværdi)."""
        assert validate_password_length("a" * 65) == False
    
    # --- Langt over maximum ---
    def test_length_100_invalid(self):
        """100 tegn - langt over maximum."""
        assert validate_password_length("a" * 100) == False
