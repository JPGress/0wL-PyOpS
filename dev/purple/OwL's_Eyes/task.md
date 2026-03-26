# OwL's Eyes - Pilot Project Development Task List

[x] 1. **Scaffolding the Core Plugin**
  - [x] Create `plugins/purple/owls_eyes.py` inheriting from `BasePlugin`.
  - [x] Set plugin metadata (`PLUGIN_ID`, `NAME`, `GROUP`, `TACTIC`, `DESCRIPTION`) according to the specification.
  - [x] Implement the `run()` method to display the OwL's Eyes main menu.

[x] 2. **Structuring Sub-Modules (The Hub)**
  - [x] Create a directory `plugins/purple/owls_eyes_modules/` to store the logic for the 7 specified modules.
  - [x] Create an `__init__.py` or a main router inside the sub-directory.
  - [x] Create placeholder files/classes for each module (e.g., `mod1_opsec.py`, `mod2_socmint.py`, etc.).

[x] 3. **Pilot Project Minimum Viable Product (MVP)**
  - [x] Implement a basic functional skeleton for **Module 2: SOCMINT & Identity** (as a demonstration of capability).
  - [x] Implement a basic functional skeleton for **Module 3: Digital Footprint & Devices**.
  - [x] Ensure all other modules display an "Under Construction / Pilot Phase" message when accessed.

[x] 4. **Integration & UI/UX**
  - [x] Use `core.logger.log` to style the output of the plugin to strictly match PyOpS' aesthetic requirements.
  - [x] Implement safe exit mechanisms (`try-except KeyboardInterrupt`).

[x] 5. **Documentation & Verification**
  - [x] Run automated discovery verification by executing `python3 pyops.py` to ensure the plugin is loaded correctly.
  - [x] Test the execution flow of the MVP modules.

---

# Phase 2: Full SOCMINT Implementation (Module 2)

[x] 1. **Planning & Setup**
  - [x] Define the scraping approach for Instagram and LinkedIn.
  - [x] Add `instaloader`, `requests`, and `beautifulsoup4` to project requirements (if applicable) or ensure they are documented.

[x] 2. **Instagram Implementation (`mod2_socmint.py`)**
  - [x] Integrate `instaloader` to fetch profile data.
  - [x] Implement Private Profile detection and OPSEC warning.
  - [x] Implement Fast Mode (Bio, Stats, Captions/Photos).
  - [x] Implement Complete Mode (Followers/Following extraction). Alert user about auth necessity.

[x] 3. **LinkedIn Implementation (`mod2_socmint.py`)**
  - [x] Implement robust `requests` + `bs4` fallback scraper for LinkedIn professional info.
  - [x] Parse relevant career information (Title, Location, Company).

[x] 4. **JSON Export & Integration**
  - [x] Combine data into a structured Python dictionary.
  - [x] Export to `<target>_socmint.json`.
  - [x] Ensure formatting strictly uses `core.logger.log` and gracefully handles `KeyboardInterrupt`.
