import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import Session

from src.services.twitch_service import TwitchService
from src.models.settings import Settings
from src.database import engine, init_db


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    with Session(engine) as session:
        session.exec(select(Settings)).delete()
        session.commit()


@pytest.fixture
def mock_settings_with_creds(session: Session):
    """Create settings with mocked Twitch credentials."""
    settings = Settings()
    settings.twitch_client_id = "test_client_id"
    settings.twitch_client_secret_encrypted = "encrypted_secret"
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def test_auth_url_contains_required_params(mock_settings_with_creds, session):
    """Test auth URL generation includes required OAuth parameters."""
    with patch.object(SettingsService, 'decrypt_secret', return_value="test_secret"):
        twitch = TwitchService(session)
        url = twitch.get_auth_url()

        assert "client_id=test_client_id" in url
        assert "redirect_uri=http://localhost:8765/api/v1/twitch/callback" in url
        assert "response_type=code" in url
        assert "scope=user:read:email+clips:read" in url


def test_auth_url_raises_without_credentials(session):
    """Test auth URL raises when credentials not configured."""
    twitch = TwitchService(session)
    with pytest.raises(ValueError, match="Twitch credentials not configured"):
        twitch.get_auth_url()


@pytest.mark.asyncio
async def test_exchange_code_stores_tokens(mock_settings_with_creds, session):
    """Test code exchange stores access and refresh tokens."""
    with patch.object(SettingsService, 'decrypt_secret', return_value="test_secret"):
        twitch = TwitchService(session)

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await twitch.exchange_code("test_code")

        assert result["access_token"] == "new_access_token"
        assert result["refresh_token"] == "new_refresh_token"

        # Verify tokens stored in settings
        settings = session.get(Settings, 1)
        assert settings.twitch_access_token == "new_access_token"
        assert settings.twitch_refresh_token == "new_refresh_token"


@pytest.mark.asyncio
async def test_refresh_access_token_updates_tokens(mock_settings_with_creds, session):
    """Test token refresh updates stored tokens."""
    with patch.object(SettingsService, 'decrypt_secret', return_value="test_secret"):
        # Pre-populate with old tokens
        settings = mock_settings_with_creds
        settings.twitch_refresh_token = "old_refresh_token"
        session.add(settings)
        session.commit()

        twitch = TwitchService(session)

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "access_token": "refreshed_access_token",
            "refresh_token": "refreshed_refresh_token",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            new_token = await twitch.refresh_access_token()

        assert new_token == "refreshed_access_token"

        # Verify tokens updated
        settings = session.get(Settings, 1)
        assert settings.twitch_access_token == "refreshed_access_token"
        assert settings.twitch_refresh_token == "refreshed_refresh_token"


@pytest.mark.asyncio
async def test_get_vods_returns_vod_list(mock_settings_with_creds, session):
    """Test get_vods returns list of VODs."""
    with patch.object(SettingsService, 'decrypt_secret', return_value="test_secret"):
        twitch = TwitchService(session)
        settings = mock_settings_with_creds
        settings.twitch_access_token = "valid_token"
        session.add(settings)
        session.commit()

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "123", "title": "VOD 1", "url": "https://twitch.tv/videos/123"},
                {"id": "456", "title": "VOD 2", "url": "https://twitch.tv/videos/456"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            vods = await twitch.get_vods()

        assert len(vods) == 2
        assert vods[0]["id"] == "123"
        assert vods[1]["title"] == "VOD 2"


def test_download_vod_calls_ytdlp(mock_settings_with_creds, session, tmp_path):
    """Test download_vod calls yt-dlp with correct args."""
    with patch.object(SettingsService, 'decrypt_secret', return_value="test_secret"):
        twitch = TwitchService(session)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            output = twitch.download_vod("12345", tmp_path / "vod.mp4")

        assert output == tmp_path / "vod.mp4"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "yt-dlp" in args
        assert "-f" in args
        assert "best[ext=mp4]" in args
        assert "-o" in args
        assert "twitch.tv/videos/12345" in args