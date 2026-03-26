# Implementation Plan: OwL's Eyes (Pilot Project)

## Goal Description
The objective is to properly develop the scaffolding and a Minimum Viable Product (MVP) of the **OwL's Eyes** module, a Personal Attack Surface Management (PASM) tool, so it can be demonstrated at an event as a pilot project. The tool will be integrated into the **0wL PyOpS** framework as a Purple Team plugin. It will act as a centralized hub for executing 7 distinct reconnaissance, attack, and defensive modules.

## Proposed Changes

### Core Plugin Integration
- **`plugins/purple/owls_eyes.py` [NEW]**: 
  - Will be created extending `BasePlugin`.
  - Metadata: 
    - `PLUGIN_ID = "001"` (or an available ID in Purple)
    - `NAME = "Personal Attack Surface Management (OwL's Eyes)"`
    - `GROUP = "Purple"`
    - `TACTIC = "TA0043"`
  - The `run()` method will clear the screen and show an internal CLI menu for OwL's Eyes allowing the user to select which of the 7 modules to execute.

### Module Architecture
To keep the plugin file clean, the logic for the 7 modules will be separated:
- **`plugins/purple/owls_eyes_modules/` [NEW]**: A self-contained package for this plugin.
  - **`__init__.py` [NEW]**: To make it a standard python package.
  - **`mod1_opsec.py` [NEW]**: Placeholder for OPSEC & Infrastructure.
  - **`mod2_socmint.py` [NEW]**: Implementation of basic SOCMINT queries (e.g., username search stub).
  - **`mod3_footprint.py` [NEW]**: Implementation of basic Digital Footprint tracking.
  - **`mod4_breach.py` [NEW]**: Placeholder for Breach Hunting.
  - **`mod5_monitor.py` [NEW]**: Placeholder for Information Monitoring.
  - **`mod6_socialeng.py` [NEW]**: Placeholder for Social Engineering.
  - **`mod7_defensive.py` [NEW]**: Placeholder for Defensive Measures.

### UI / UX Conformance
- Use `core.logger.log` (info, success, warning, error) exclusively inside these files to guarantee ANSI aesthetic continuity as required by the PyOpS `plugin_tutorial.md`.
- Implement `KeyboardInterrupt` handling to gracefully exit to the main PyOpS menu without traceback errors.

## Verification Plan

### Automated / Integration Tests
- **Plugin Loading Check**: Run `pytest tests/test_plugin_loader.py` (if existing) or simply run the PyOpS entrypoint to verify that the auto-discovery correctly finds and indexes "OwL's Eyes" in the "Purple" group without crashing the application.

### Manual Verification
1. Execute `python3 pyops.py` (or the equivalent entrypoint).
2. Ensure the "Purple" category appears in the main menu and lists `Personal Attack Surface Management (OwL's Eyes)`.
3. Select its associated `PLUGIN_ID`.
4. Verify the internal dispatcher opens the OwL's Eyes hub menu.
5. Select **Module 2: SOCMINT** to test the MVP capability.
6. Verify aesthetic outputs (via `core.logger`).
7. Press `Ctrl+C` inside the module to verify it gracefully exits back to the main PyOpS menu.
