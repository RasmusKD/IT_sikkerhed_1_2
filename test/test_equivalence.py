"""
Ækvivalensklasser (Equivalence Partitioning)
IT-sikkerhed eksempel: Brugeralder validering

Klasser:
- Ugyldig: Under 0 (negativ alder)
- For ung: 0-12 (børn)
- Teenager: 13-17 (begrænset adgang)
- Voksen: 18-120 (fuld adgang)
- Ugyldig: Over 120 (urealistisk)
"""
import pytest


def get_access_level(age):
    """Returnerer adgangsniveau baseret på alder."""
    if age < 0 or age > 120:
        return "ugyldig"
    elif age <= 12:
        return "børn"
    elif age <= 17:
        return "teenager"
    else:
        return "voksen"


class TestEquivalencePartitioning:
    """
    Ækvivalensklasse test for aldersvalidering.
    Én test per klasse er nok - det er pointen med ækvivalensklasser!
    """
    
    # Én repræsentant fra hver klasse
    @pytest.mark.parametrize("age, expected", [
        (-5, "ugyldig"),      # Klasse: Negativ alder
        (8, "børn"),          # Klasse: 0-12 år
        (15, "teenager"),     # Klasse: 13-17 år
        (25, "voksen"),       # Klasse: 18-120 år
        (150, "ugyldig"),     # Klasse: Over 120 år
    ], ids=["negativ", "barn", "teenager", "voksen", "urealistisk"])
    def test_age_equivalence_classes(self, age, expected):
        """Tester én værdi fra hver ækvivalensklasse."""
        assert get_access_level(age) == expected
