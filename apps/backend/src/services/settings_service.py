from sqlmodel import Session, select
from src.models.settings import Settings
from src.database import engine
import os

try:
    import win32crypt
    HAS_DPAPI = True
except ImportError:
    HAS_DPAPI = False


class SettingsService:
    def __init__(self, session: Session):
        self.session = session

    def get(self) -> Settings:
        """Get settings, creating default if not exists."""
        settings = self.session.get(Settings, 1)
        if not settings:
            settings = Settings()
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        return settings

    def update(self, **kwargs) -> Settings:
        """Update settings with provided values."""
        settings = self.get()
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        from datetime import datetime
        settings.updated_at = datetime.utcnow()
        self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return settings

    def encrypt_secret(self, plaintext: str) -> str:
        """Encrypt secret using Windows DPAPI."""
        if not HAS_DPAPI:
            # Fallback: simple base64 (not secure, but works for dev)
            import base64
            return base64.b64encode(plaintext.encode()).decode()

        # Use DPAPI for encryption
        data = plaintext.encode('utf-16-le')
        encrypted = win32crypt.CryptProtectData(data, None, None, None, None, 0)
        return encrypted.hex()

    def decrypt_secret(self, encrypted_hex: str) -> str:
        """Decrypt secret using Windows DPAPI."""
        if not HAS_DPAPI:
            # Fallback: base64 decode
            import base64
            return base64.b64decode(encrypted_hex).decode()

        encrypted = bytes.fromhex(encrypted_hex)
        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        return decrypted[1].decode('utf-16-le')