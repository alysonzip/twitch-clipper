import pytest
from sqlmodel import Session

from src.models.settings import Settings
from src.services.settings_service import SettingsService
from src.database import engine, init_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test."""
    init_db()
    yield
    # Clean up after test
    with Session(engine) as session:
        session.exec(select(Settings)).delete()
        session.commit()


def test_dpapi_encrypt_decrypt_roundtrip():
    """Test DPAPI encryption/decryption round-trip works."""
    with Session(engine) as session:
        svc = SettingsService(session)
        plain = "my-secret-key-12345"
        enc = svc.encrypt_secret(plain)
        assert enc != plain
        assert len(enc) > 0
        dec = svc.decrypt_secret(enc)
        assert dec == plain


def test_dpapi_encrypt_decrypt_empty_string():
    """Test DPAPI handles empty string."""
    with Session(engine) as session:
        svc = SettingsService(session)
        plain = ""
        enc = svc.encrypt_secret(plain)
        dec = svc.decrypt_secret(enc)
        assert dec == ""


def test_dpapi_encrypt_decrypt_special_chars():
    """Test DPAPI handles special characters."""
    with Session(engine) as session:
        svc = SettingsService(session)
        plain = "key-with-!@#$%^&*()_+{}|:<>?~`-=[]\\;',./"
        enc = svc.encrypt_secret(plain)
        dec = svc.decrypt_secret(enc)
        assert dec == plain


def test_settings_service_get_creates_default():
    """Test SettingsService.get() creates default row if not exists."""
    with Session(engine) as session:
        svc = SettingsService(session)
        settings = svc.get()

        assert settings is not None
        assert settings.id == 1
        assert settings.obs_recordings_path == r"E:\OBS\Recordings"
        assert settings.gemini_api_key is None


def test_settings_service_get_returns_existing():
    """Test SettingsService.get() returns existing row."""
    with Session(engine) as session:
        svc = SettingsService(session)
        settings1 = svc.get()
        settings1.gemini_api_key = "test-key"
        session.add(settings1)
        session.commit()

        settings2 = svc.get()
        assert settings2.id == settings1.id
        assert settings2.gemini_api_key == "test-key"


def test_settings_service_update():
    """Test SettingsService.update() updates fields."""
    with Session(engine) as session:
        svc = SettingsService(session)
        settings = svc.get()

        updated = svc.update(
            obs_recordings_path=r"D:\New\Recordings",
            gemini_api_key="new-api-key",
            whisper_model="small",
            virality_threshold=0.90,
        )

        assert updated.obs_recordings_path == r"D:\New\Recordings"
        assert updated.gemini_api_key == "new-api-key"
        assert updated.whisper_model == "small"
        assert updated.virality_threshold == 0.90


def test_settings_service_update_ignores_unknown_fields():
    """Test SettingsService.update() ignores unknown fields."""
    with Session(engine) as session:
        svc = SettingsService(session)
        settings = svc.get()

        # Should not raise, just ignore unknown_field
        updated = svc.update(unknown_field="value", obs_recordings_path=r"D:\Test")
        assert updated.obs_recordings_path == r"D:\Test"


def test_settings_service_updated_at_changes():
    """Test SettingsService.update() updates updated_at timestamp."""
    with Session(engine) as session:
        svc = SettingsService(session)
        settings = svc.get()
        original_updated = settings.updated_at

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)

        updated = svc.update(obs_recordings_path=r"D:\Test")
        assert updated.updated_at > original_updated