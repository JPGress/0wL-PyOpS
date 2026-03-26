# Implementation Plan: OwL's Eyes (Pilot Project)

## Goal Description
The objective is to properly develop the scaffolding and a Minimum Viable Product (MVP) of the **OwL's Eyes** module, a Personal Attack Surface Management (PASM) tool, so it can be demonstrated at an event as a pilot project. The tool will be integrated into the **0wL PyOpS** framework as a Purple Team plugin. It will act as a centralized hub for executing 7 distinct reconnaissance, attack, and defensive modules.

## Proposed Changes (Phase 2: SOCMINT Full Implementation)

### `plugins/purple/owls_eyes_modules/mod2_socmint.py` [MODIFY]
- Will be updated to perform actual data extraction and output a `.json` file.
- **Dependencies**: `instaloader` (for Instagram), `requests`, and `beautifulsoup4` (for LinkedIn/Web scraping).

#### Instagram Logic (via `instaloader`)
- Prompt the user for the Instagram username.
- Initialize `instaloader.Instaloader()`.
- Fetch profile using `instaloader.Profile.from_username()`.
- **Private Profile Check**: 
  - If `profile.is_private` is True, abort collection and use `core.logger` to suggest using OPSEC avatars (sock puppets) for further intelligence gathering.
- **Public Profile Collection Modes**:
  - Prompt user to select: `[1] Rápida` or `[2] Completa`.
  - **Rápida**: Extract bio, external URL, number of followers/following, and iterate through the latest posts (e.g., top 10) to extract photo URLs and captions.
  - **Completa**: Extract everything from 'Rápida', plus iterate through `profile.get_followers()` and `profile.get_followees()` to build a list of all connections. *(Note: Instaloader requires the script to be logged in to fetch followers. We will prompt the user if they want to load an OPSEC session, otherwise this step might fail due to Instagram's API restrictions).*

#### LinkedIn Logic
- Prompt the user for the LinkedIn username/URL.
- **Scraping Strategy**: Direct scraping of LinkedIn without authentication is heavily rate-limited and often blocked by auth-walls. 
- The script will attempt to fetch the public profile via `requests` using a specialized Googlebot/modern User-Agent.
- It will parse the HTML with `BeautifulSoup` to extract the `<title>`, `<meta name="description">` (which usually contains the current job title, company, and location), and any available structured JSON-LD data.
- If direct scraping fails (HTTP 999/Auth Wall), it will fallback to performing a Google Dork (`site:linkedin.com/in/ "username"`) to extract the professional summary from the search engine's snippet.

#### JSON Output
- Aggregate all collected data into a Python dictionary.
- Output the dictionary to a file named `target_<username>_socmint.json` in the current working directory, confirming the path via `core.logger.success`.

## Verification Plan

### Automated Tests
- N/A for this specific external scraping script, as real network requests are prone to change and rate limits.

### Manual Verification
1. Install dependencies (`pip install instaloader requests beautifulsoup4`).
2. Run `pyops.py`, select Purple Team -> OwL's Eyes -> Mod 2.
3. Input a known public Instagram profile and select "Rápida". Verify the JSON output contains bio and post summaries.
4. Input a private Instagram profile. Verify the OPSEC warning is triggered.
5. Input a LinkedIn username. Verify the professional information is extracted and appended to the JSON.
