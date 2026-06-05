from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHECKIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Bulk data lives on the secondary drive, never in the repo.
    data_root: Path = Path("/data/files/OC12")

    database_url: SecretStr = SecretStr("postgresql://checkit:checkit@localhost:5432/checkit")

    # Salts author pseudonymization (Bluesky); override in .env.
    pseudo_salt: SecretStr = SecretStr("checkit-local-salt")

    newsdata_api_key: SecretStr | None = None
    guardian_api_key: SecretStr | None = None
    gnews_api_key: SecretStr | None = None
    currents_api_key: SecretStr | None = None
    mediastack_api_key: SecretStr | None = None
    thenewsapi_api_key: SecretStr | None = None
    worldnews_api_key: SecretStr | None = None

    @property
    def raw_dir(self) -> Path:
        return self.data_root / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_root / "processed"

    @property
    def images_dir(self) -> Path:
        return self.data_root / "images"

    @property
    def corpora_dir(self) -> Path:
        return self.data_root / "corpora"

    def ensure_dirs(self) -> None:
        for d in (self.raw_dir, self.processed_dir, self.images_dir, self.corpora_dir):
            d.mkdir(parents=True, exist_ok=True)

    def has_key(self, source: str) -> bool:
        """Sources without a configured key are skipped, not failed."""
        key: SecretStr | None = getattr(self, f"{source}_api_key", None)
        return key is not None and bool(key.get_secret_value())
