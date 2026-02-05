"""
Decision Table Test - Login med MFA
IT-sikkerhed eksempel: Validering af login flow med Multi-Factor Authentication

Betingelser:
- Gyldigt brugernavn
- Gyldigt password
- MFA aktiveret
- MFA korrekt

Regler testes ud fra alle kombinationer.
"""
import pytest


def login_with_mfa(valid_username, valid_password, mfa_enabled, mfa_correct):
    """
    Simulerer login med MFA.
    Returnerer tuple: (adgang_givet, besked)
    """
    # R5: Ugyldigt brugernavn
    if not valid_username:
        return (False, "Adgang nægtes + log hændelse")
    
    # R4: Ugyldigt password
    if not valid_password:
        return (False, "Adgang nægtes")
    
    # Brugernavn og password OK
    if not mfa_enabled:
        # R1: Ingen MFA aktiveret
        return (True, "Adgang + Advarsel")
    
    # MFA aktiveret
    if mfa_correct:
        # R2: Alt korrekt
        return (True, "Adgang")
    else:
        # R3: MFA forkert
        return (False, "Adgang nægtes")


class TestDecisionTableMFA:
    """
    Decision Table Test for login med MFA.
    Tester alle kombinationer fra beslutnings-tabellen.
    """
    
    # Data-drevet test med alle regler fra tabellen
    @pytest.mark.parametrize(
        "valid_user, valid_pass, mfa_on, mfa_ok, expected_access, expected_msg",
        [
            # R1: Gyldigt login, ingen MFA
            (True, True, False, None, True, "Adgang + Advarsel"),
            
            # R2: Gyldigt login, MFA aktiveret og korrekt
            (True, True, True, True, True, "Adgang"),
            
            # R3: Gyldigt login, MFA aktiveret men forkert
            (True, True, True, False, False, "Adgang nægtes"),
            
            # R4: Gyldigt brugernavn, forkert password
            (True, False, None, None, False, "Adgang nægtes"),
            
            # R5: Ugyldigt brugernavn (log hændelse for sikkerhed)
            (False, None, None, None, False, "Adgang nægtes + log hændelse"),
        ],
        ids=["R1-NoMFA", "R2-MFA-OK", "R3-MFA-Wrong", "R4-BadPass", "R5-BadUser"]
    )
    def test_login_mfa_rules(self, valid_user, valid_pass, mfa_on, mfa_ok, expected_access, expected_msg):
        """Tester alle regler fra decision table."""
        access, msg = login_with_mfa(valid_user, valid_pass, mfa_on, mfa_ok)
        assert access == expected_access
        assert msg == expected_msg
