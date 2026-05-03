"""OpenDota API client helpers."""

import subprocess
import time
from pathlib import Path
import requests
from logging_config import get_logger


logger = get_logger(__name__)


def fetch_json(url, delay=1, retries=3):
    """Fetch JSON with retry and delay handling for transient failures."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.json()

            logger.warning(
                "Request returned non-200 status. " \
                "url=%s status=%s attempt=%d/%d",
                url,
                resp.status_code,
                attempt,
                retries,
            )
        except requests.RequestException:
            logger.warning(
                "HTTP request failed. url=%s attempt=%d/%d",
                url,
                attempt,
                retries,
                exc_info=True,
            )

        if attempt < retries:
            time.sleep(delay)

    logger.error(
        "Request failed after retries. " \
        "url=%s retries=%d", url, retries)
    raise RuntimeError(f"Failed to fetch {url} after {retries} retries.")


def fetch_matches(account_id):
    """Fetch recent matches for a player account from OpenDota."""
    url = f"https://api.opendota.com/api/players/{account_id}/matches"
    all_matches = fetch_json(url)
    logger.info(
        "Fetched recent matches from OpenDota. account_id=%s total=%d",
        account_id,
        len(all_matches),
    )
    return all_matches


def parse_request(match_id):
    """Request parsed match details for a specific match ID.

    Returns:
        tuple[bool, str]: (submitted, message)
    """
    try:
        resp = requests.post(
            f"https://api.opendota.com/api/request/{match_id}",
            timeout=30,
        )
    except requests.RequestException:
        logger.exception(
            "Parse request failed due to network error. " \
            "match_id=%s", match_id)
        return False, "Network error while submitting parse request."

    if resp.status_code in (200, 202):
        logger.info("Submitted parse request. match_id=%s", match_id)
        return True, "Parse request submitted."

    detail = resp.text.strip() or f"HTTP {resp.status_code}"
    logger.warning(
        "Parse request rejected. match_id=%s status=%s detail=%s",
        match_id,
        resp.status_code,
        detail,
    )
    return False, f"Parse request rejected: {detail}"


def increment_match_retries(cur, conn, match_id: int) -> None:
    """Increase the parse-request retry counter for one stored match."""
    cur.execute(
        """
        UPDATE player_matches
        SET retries = COALESCE(retries, 0) + 1
        WHERE match_id = ?
        """,
        (match_id,),
    )
    conn.commit()


def sync_repo():
    """Sync local constants repository used for static Dota metadata."""
    path = Path("dotaconstants")

    try:
        if not (path / ".git").exists():
            if path.exists():
                raise RuntimeError(
                    "dotaconstants/ exists but is not a Git checkout. "
                    "Rename or remove that folder, then try again."
                )

            logger.info("Cloning dotaconstants repository.")
            subprocess.run(
                ["git", "clone", 
                 "https://github.com/odota/dotaconstants.git"],
                check=True,
            )

        else:
            logger.info("Pulling latest dotaconstants changes.")
            subprocess.run(["git", "pull"], cwd=path, check=True)

    except subprocess.CalledProcessError as e:
        logger.error("Failed to sync dotaconstants repository: %s", e)
        raise RuntimeError(
            "Git command failed. " \
            "Ensure Git is installed and accessible.")   
    
    except FileNotFoundError:
        logger.error(
            "Git is not installed or not found in PATH.")
        raise RuntimeError("Git is not installed or not found in PATH.")
