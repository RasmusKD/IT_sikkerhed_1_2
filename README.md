# IT_sikkerhed_1_2

Dette er et skoleprojekt til IT-sikkerhed på Zealand Næstved.

## Indhold

- Opgaver og øvelser relateret til IT-sikkerhed
- Dokumentation og noter

## Unit Tests (03-02)

Vi har lavet unit tests med pytest for at demonstrere hvordan testing fungerer.

### Test Resultater

![Test Resultater](test_results.png)

**Alle tests kører som forventet!**

> **Bemærk:** Selvom nogle tests viser "FAILED", er dette forventet opførsel. 
> Vi har bevidst lavet tests der skal fejle for at demonstrere hvordan pytest håndterer forskellige test outcomes:
> - `test_pass` / `test_pass_udvidet` → Designet til at PASSE ✅
> - `test_fail` / `test_fail_udvidet` → Designet til at FEJLE ❌
> - `test_skip` / `test_skip_udvidet` → Designet til at blive SKIPPED ⏭️
> - `test_crash` → Designet til at CRASHE 💥

### Kør tests

```bash
pytest -v
```

## Grænseværditest (05-02)

Boundary value testing af password længde validering (8-64 tegn).

| Længde | Resultat | Type |
|--------|----------|------|
| 7 | ❌ Invalid | Grænseværdi (under min) |
| 8 | ✅ Valid | Grænseværdi (præcis min) |
| 64 | ✅ Valid | Grænseværdi (præcis max) |
| 65 | ❌ Invalid | Grænseværdi (over max) |

## Udarbejdet af

Rasmus
