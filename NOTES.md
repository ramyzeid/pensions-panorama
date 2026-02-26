# Session Notes (Feb 25, 2026)

## Summary
- Added a new **Country Deep Profile** tab to the Streamlit dashboard.
- Implemented deep profile schema, builder, and CLI command `pp build-deep-profiles`.
- Added offline mode (`--offline`) to skip network calls and rely on mapping overrides.
- Added mappings for Costa Rica (CRI), Jordan (JOR), Morocco (MAR).
- Added tests for ordering/structure/not-available behavior.

## Important Environment Issue
- No active network interface in this environment.
- DNS resolution fails for all hosts (including `api.worldbank.org`).
- As a result, WDI API calls fail unless you run `--offline` with overrides.

## Files Added/Modified
- `pensions_panorama/schema/deep_profile_schema.py`
- `pensions_panorama/deep_profile/builder.py`
- `pensions_panorama/cli.py`
- `pensions_panorama/web/app.py`
- `pensions_panorama/web/i18n.py`
- `data/deep_profiles/CRI.yaml`
- `data/deep_profiles/JOR.yaml`
- `data/deep_profiles/MAR.yaml`
- `data/deep_profiles/_template.yaml`
- `tests/test_deep_profile.py`
- `README.md`

## Commands Used
- Build (online attempt):
  ```bash
  pp build-deep-profiles --countries "CRI JOR MAR"
  ```
- Build (offline success):
  ```bash
  pp build-deep-profiles --countries "CRI JOR MAR" --offline
  ```

## Next Steps
1. Restore network connectivity.
2. Re-run without `--offline`:
   ```bash
   pp build-deep-profiles --countries "CRI JOR MAR"
   ```
3. Confirm WDI fields populate in `reports/deep_profiles/*.json`.
4. Add more country mappings as needed.
