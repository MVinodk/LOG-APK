
# Update checker for APKs.
# Configure UPDATE_JSON_URL to point to a JSON file with keys:
#   latest_version (string), apk_url (string), notes (string), force_update (bool)
import os, json, urllib.request, ssl

UPDATE_JSON_URL = os.environ.get("SBPI_UPDATE_JSON_URL", "https://example.com/sbpi_update.json")
CURRENT_VERSION = "1.0.0"

class UpdateChecker:
    def __init__(self, url=None):
        self.url = url or UPDATE_JSON_URL

    def fetch_json(self):
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(self.url, context=ctx, timeout=8) as resp:
                data = resp.read().decode('utf-8')
                return json.loads(data)
        except Exception as e:
            return None

    def check_for_update(self):
        info = self.fetch_json()
        if not info:
            return False, {}
        latest = info.get("latest_version")
        if not latest:
            return False, {}
        if latest.strip() != CURRENT_VERSION.strip():
            return True, info
        return False, info

    def download_apk(self, apk_url, dest_path):
        try:
            urllib.request.urlretrieve(apk_url, dest_path)
            return True
        except Exception:
            return False
