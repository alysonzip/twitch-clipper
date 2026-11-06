import httpx
import subprocess
from pathlib import Path
from urllib.parse import urlencode
from sqlmodel import Session

from src.models.settings import Settings
from src.services.settings_service import SettingsService


class TwitchService:
    HELIX_BASE = "https://api.twitch.tv/helix"
    OAUTH_BASE = "https://id.twitch.tv/oauth2"

    def __init__(self, session: Session):
        self.session = session
        self.settings_svc = SettingsService(session)

    def _get_credentials(self) -> tuple[str, str]:
        settings = self.settings_svc.get()
        if not settings.twitch_client_id or not settings.twitch_client_secret_encrypted:
            raise ValueError("Twitch credentials not configured")
        client_secret = self.settings_svc.decrypt_secret(settings.twitch_client_secret_encrypted)
        return settings.twitch_client_id, client_secret

    def get_auth_url(self) -> str:
        client_id, _ = self._get_credentials()
        redirect_uri = "http://localhost:8765/api/v1/twitch/callback"
        scopes = "user:read:email clips:read"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scopes,
        }
        return f"{self.OAUTH_BASE}/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        client_id, client_secret = self._get_credentials()
        redirect_uri = "http://localhost:8765/api/v1/twitch/callback"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.OAUTH_BASE}/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        # Store tokens encrypted
        settings = self.settings_svc.get()
        settings.twitch_access_token = token_data["access_token"]
        settings.twitch_refresh_token = token_data.get("refresh_token")
        self.session.add(settings)
        self.session.commit()

        return token_data

    async def refresh_access_token(self) -> str:
        settings = self.settings_svc.get()
        if not settings.twitch_refresh_token:
            raise ValueError("No refresh token available")

        client_id, client_secret = self._get_credentials()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.OAUTH_BASE}/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": settings.twitch_refresh_token,
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        settings.twitch_access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            settings.twitch_refresh_token = token_data["refresh_token"]
        self.session.add(settings)
        self.session.commit()

        return token_data["access_token"]

    async def _get_valid_access_token(self) -> str:
        settings = self.settings_svc.get()
        if not settings.twitch_access_token:
            raise ValueError("Not authenticated with Twitch")

        # Try current token, if 401 then refresh
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.HELIX_BASE}/users",
                headers={
                    "Client-ID": settings.twitch_client_id,
                    "Authorization": f"Bearer {settings.twitch_access_token}",
                },
            )

            if resp.status_code == 401:
                return await self.refresh_access_token()
            resp.raise_for_status()
            return settings.twitch_access_token

    async def get_vods(self, user_id: str | None = None) -> list[dict]:
        token = await self._get_valid_access_token()
        settings = self.settings_svc.get()

        async with httpx.AsyncClient() as client:
            params = {"first": 20}
            if user_id:
                params["user_id"] = user_id

            resp = await client.get(
                f"{self.HELIX_BASE}/videos",
                headers={
                    "Client-ID": settings.twitch_client_id,
                    "Authorization": f"Bearer {token}",
                },
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])

    async def get_vod_info(self, vod_id: str) -> dict | None:
        token = await self._get_valid_access_token()
        settings = self.settings_svc.get()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.HELIX_BASE}/videos",
                headers={
                    "Client-ID": settings.twitch_client_id,
                    "Authorization": f"Bearer {token}",
                },
                params={"id": vod_id},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0] if data["data"] else None

    def download_vod(self, vod_id: str, output_path: Path) -> Path:
        """Download VOD using yt-dlp. Returns path to downloaded file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        url = f"https://twitch.tv/videos/{vod_id}"

        cmd = [
            "yt-dlp",
            "-f", "best[ext=mp4]",
            "-o", str(output_path),
            "--no-playlist",
            url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {result.stderr}")

        return output_path