"""
Bcrypt Rounds Benchmark - Sikkerhed vs. Brugeroplevelse

FORMÅL:
  Denne test viser hvorfor bcrypt "rounds" (cost factor) er vigtig:
  - Flere rounds = LANGSOMMERE hashing = SVÆRERE for hackere at brute-force
  - Men også langsommere login for brugeren
  - Man vælger en middelvej: sikkert NOK, men stadig hurtigt for brugeren

HVORDAN ROUNDS VIRKER:
  bcrypt kører 2^rounds iterationer internt.
  Round 10 = 2^10 = 1.024 iterationer  (~46ms)
  Round 12 = 2^12 = 4.096 iterationer  (~185ms, 4x langsommere)
  Round 14 = 2^14 = 16.384 iterationer (~700ms, 16x langsommere)

  For en hacker der skal prøve millioner af passwords:
  Round 10: 1.000.000 forsøg × ~46ms  = ~13 timer
  Round 14: 1.000.000 forsøg × ~700ms = ~8 DAGE

KONKLUSION:
  Standard er round 12 - det er den bedste middelvej:
  - Brugeren mærker det knap nok (~185ms ved login)
  - En hacker skal bruge DAGE i stedet for timer
"""
import pytest
import time
import hashlib
import bcrypt


PASSWORD = "SuperHemmeligt123!"


class TestBcryptRounds:
    """Benchmark: Hvordan rounds påvirker hastighed og sikkerhed."""

    def test_sha256_speed(self):
        """
        RISIKO: SHA-256 er FOR hurtig til passwords → hackere kan prøve
        milliarder af kombinationer per sekund.
        """
        # Given: Et password
        password = PASSWORD.encode()
        iterations = 1000

        # When: Vi hasher 1000 gange med SHA-256
        start = time.perf_counter()
        for _ in range(iterations):
            hashlib.sha256(password).hexdigest()
        elapsed = time.perf_counter() - start

        per_hash = (elapsed / iterations) * 1000  # ms
        hashes_per_sec = iterations / elapsed

        # Then: SHA-256 er ekstremt hurtig (det er PROBLEMET)
        print(f"\n{'='*60}")
        print(f"SHA-256:  {per_hash:.4f} ms per hash")
        print(f"          {hashes_per_sec:,.0f} hashes/sekund")
        print(f"          ⚠️  For hurtig til passwords!")
        print(f"{'='*60}")

        assert per_hash < 1  # SHA-256 er under 1ms

    def test_bcrypt_round_10(self):
        """
        RISIKO: For få rounds → hackere kan brute-force hurtigere.
        """
        # Given: Et password og round 10 (2^10 = 1.024 iterationer)
        password = PASSWORD.encode()

        # When: Vi hasher med bcrypt round 10
        start = time.perf_counter()
        salt = bcrypt.gensalt(rounds=10)
        hashed = bcrypt.hashpw(password, salt)
        elapsed = (time.perf_counter() - start) * 1000

        # Then: Det tager ~50-100ms (allerede MEGET langsommere end SHA-256)
        print(f"\n{'='*60}")
        print(f"bcrypt round 10: {elapsed:.1f} ms")
        print(f"  → 2^10 = 1.024 iterationer")
        print(f"  → Hacker: ~{1000/elapsed:.0f} forsøg/sekund")
        print(f"{'='*60}")

        # Verificér at hash virker
        assert bcrypt.checkpw(password, hashed)

    def test_bcrypt_round_12(self):
        """
        RISIKO: Round 12 er standard - god middelvej.
        """
        # Given: Et password og round 12 (2^12 = 4.096 iterationer)
        password = PASSWORD.encode()

        # When: Vi hasher med bcrypt round 12 (ANBEFALET)
        start = time.perf_counter()
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password, salt)
        elapsed = (time.perf_counter() - start) * 1000

        # Then: Det tager ~200-300ms (brugeren mærker det knap nok)
        print(f"\n{'='*60}")
        print(f"bcrypt round 12: {elapsed:.1f} ms  ✅ ANBEFALET")
        print(f"  → 2^12 = 4.096 iterationer")
        print(f"  → Hacker: ~{1000/elapsed:.0f} forsøg/sekund")
        print(f"  → Bruger mærker det knap nok ved login")
        print(f"{'='*60}")

        assert bcrypt.checkpw(password, hashed)

    def test_bcrypt_round_14(self):
        """
        RISIKO: For mange rounds → brugeren venter for længe ved login.
        """
        # Given: Et password og round 14 (2^14 = 16.384 iterationer)
        password = PASSWORD.encode()

        # When: Vi hasher med bcrypt round 14
        start = time.perf_counter()
        salt = bcrypt.gensalt(rounds=14)
        hashed = bcrypt.hashpw(password, salt)
        elapsed = (time.perf_counter() - start) * 1000

        # Then: Det tager ~800ms+ (brugeren begynder at mærke det)
        print(f"\n{'='*60}")
        print(f"bcrypt round 14: {elapsed:.1f} ms")
        print(f"  → 2^14 = 16.384 iterationer")
        print(f"  → Hacker: ~{1000/elapsed:.0f} forsøg/sekund")
        print(f"  → ⚠️  Brugeren mærker forsinkelsen!")
        print(f"{'='*60}")

        assert bcrypt.checkpw(password, hashed)

    def test_rounds_comparison_summary(self):
        """
        RISIKO: Uden forståelse af rounds vælger man forkert sikkerhedsniveau.
        """
        password = PASSWORD.encode()
        results = {}

        # Given: Vi tester round 10, 12, 14
        for rounds in [10, 12, 14]:
            start = time.perf_counter()
            salt = bcrypt.gensalt(rounds=rounds)
            hashed = bcrypt.hashpw(password, salt)
            elapsed = (time.perf_counter() - start) * 1000
            results[rounds] = elapsed

            # Verificér at det virker
            assert bcrypt.checkpw(password, hashed)

        # When/Then: Vi sammenligner
        print(f"\n{'='*60}")
        print(f"SAMMENLIGNING: bcrypt rounds")
        print(f"{'='*60}")
        print(f"{'Round':<10} {'Tid':<15} {'Iterationer':<15} {'Forsøg/sek'}")
        print(f"{'-'*60}")

        for rounds, ms in results.items():
            iters = 2 ** rounds
            per_sec = 1000 / ms
            marker = " ✅ ANBEFALET" if rounds == 12 else ""
            print(f"{rounds:<10} {ms:>8.1f} ms     {iters:>10,}       {per_sec:>8.1f}{marker}")

        print(f"\n→ Flere rounds = langsommere for ALLE (bruger + hacker)")
        print(f"→ Men hackeren skal prøve MILLIONER af passwords")
        print(f"→ Brugeren logger kun ind ÉN gang")
        print(f"→ Round 12 = bedste middelvej!")
