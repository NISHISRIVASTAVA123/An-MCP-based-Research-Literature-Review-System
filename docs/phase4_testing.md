# Phase 4 Testing & Validation Suite

## 1. Overview

Phase 4 includes a comprehensive automated test suite in `backend/tests/` and an end-to-end live execution script in `backend/scripts/phase4_live_test.py`.

---

## 2. Automated Test Modules

| Test File | Tests Covered | Pass Rate | Execution Time |
|---|---|---|---|
| `test_synthesis_data_and_retrieval.py` | Relational persistence of all 6 Phase 4 models, screening exclusion enforcement | 2 / 2 PASSED | ~0.4s |
| `test_comparison_matrix_and_themes.py` | Multi-paper comparison matrix, "Not reported" handling, CSV/Markdown export, theme clustering | 2 / 2 PASSED | ~0.4s |
| `test_pattern_analysis_and_gap_generation.py` | Frequency analysis, qualified denominators, gap generation across categories, end-to-end provenance, human review lifecycle | 3 / 3 PASSED | ~0.6s |
| `test_synthesis_api_and_mcp.py` | REST API routes lifecycle, 12 MCP Phase 4 tool invocations | 2 / 2 PASSED | ~1.2s |
| **Complete System Test Suite** | All Phases (1, 2, 3, 4) across 17 test modules | **62 / 62 PASSED** | **2.87s** |

---

## 3. Running Tests

Execute the complete test suite:
```powershell
backend/env/Scripts/pytest.exe -v
```

Execute only Phase 4 tests:
```powershell
backend/env/Scripts/pytest.exe backend/tests/test_synthesis_data_and_retrieval.py backend/tests/test_comparison_matrix_and_themes.py backend/tests/test_pattern_analysis_and_gap_generation.py backend/tests/test_synthesis_api_and_mcp.py -v
```

Execute the live end-to-end verification script:
```powershell
backend/env/Scripts/python.exe backend/scripts/phase4_live_test.py
```
