"""
Cycle Process Test
IT-sikkerhed eksempel: Login/Logout cyklus

Tester at systemet kan gentage den samme proces mange gange
uden at miste ydeevne eller stabilitet.
"""
import pytest


class SessionManager:
    """Simpel session manager til at simulere login/logout cyklus."""
    
    def __init__(self):
        self.logged_in = False
        self.session_count = 0
        self.login_history = []
    
    def login(self, username):
        """Login: Start session."""
        if self.logged_in:
            raise ValueError("Allerede logget ind")
        self.logged_in = True
        self.session_count += 1
        self.login_history.append(username)
        return True
    
    def do_action(self, action):
        """Udfør handling mens logget ind."""
        if not self.logged_in:
            raise ValueError("Ikke logget ind")
        return f"Udførte: {action}"
    
    def logout(self):
        """Logout: Afslut session."""
        if not self.logged_in:
            raise ValueError("Ikke logget ind")
        self.logged_in = False
        return True


@pytest.fixture
def session():
    """Fixture: Ny session manager."""
    return SessionManager()


class TestCycleProcess:
    """
    Cycle Process Test - gentager login/action/logout cyklus.
    Sikrer at systemet er stabilt over mange gentagelser.
    """
    
    def test_single_cycle(self, session):
        """Én komplet cyklus: login → action → logout."""
        session.login("rasmus")
        result = session.do_action("læs data")
        session.logout()
        
        assert result == "Udførte: læs data"
        assert session.session_count == 1
    
    def test_multiple_cycles_stability(self, session):
        """
        Gentager cyklus 10 gange - tester stabilitet.
        Systemet skal håndtere gentagne operationer uden fejl.
        """
        cycles = 10
        
        for i in range(cycles):
            # Login
            session.login(f"user_{i}")
            
            # Do multiple actions
            session.do_action("læs data")
            session.do_action("skriv log")
            session.do_action("tjek status")
            
            # Logout
            session.logout()
        
        # Verificer at alle cyklusser gennemførtes
        assert session.session_count == cycles
        assert len(session.login_history) == cycles
        assert not session.logged_in  # Skal være logget ud
    
    def test_cycle_maintains_history(self, session):
        """Tester at data akkumuleres korrekt over cyklusser."""
        users = ["alice", "bob", "charlie"]
        
        for user in users:
            session.login(user)
            session.do_action("tjek")
            session.logout()
        
        assert session.login_history == users
    
    def test_cycle_recovery_after_error(self, session):
        """Tester at systemet genopretter efter fejl."""
        # Normal cyklus
        session.login("user1")
        session.logout()
        
        # Forsøg at logge ud uden at være logget ind (fejl)
        with pytest.raises(ValueError):
            session.logout()
        
        # System skal stadig kunne køre normal cyklus
        session.login("user2")
        session.do_action("recovery test")
        session.logout()
        
        assert session.session_count == 2
