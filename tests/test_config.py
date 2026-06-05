from pathlib import Path

from checkit.config import Settings


def make_settings(**overrides) -> Settings:
    # _env_file=None keeps tests hermetic from any local .env
    return Settings(_env_file=None, **overrides)


def test_data_root_defaults_to_secondary_drive():
    settings = make_settings()
    assert settings.data_root == Path("/data/files/OC12")


def test_data_subdirs_derive_from_data_root(tmp_path):
    settings = make_settings(data_root=tmp_path)
    assert settings.raw_dir == tmp_path / "raw"
    assert settings.processed_dir == tmp_path / "processed"
    assert settings.images_dir == tmp_path / "images"
    assert settings.corpora_dir == tmp_path / "corpora"


def test_data_root_overridable_via_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CHECKIT_DATA_ROOT", str(tmp_path))
    settings = make_settings()
    assert settings.data_root == tmp_path


def test_ensure_dirs_creates_the_tree(tmp_path):
    settings = make_settings(data_root=tmp_path / "oc12")
    settings.ensure_dirs()
    for d in (settings.raw_dir, settings.processed_dir, settings.images_dir, settings.corpora_dir):
        assert d.is_dir()


def test_api_keys_default_to_none_and_has_key_reflects_it():
    settings = make_settings()
    assert settings.newsdata_api_key is None
    assert settings.has_key("newsdata") is False


def test_has_key_true_when_key_set():
    settings = make_settings(guardian_api_key="g-secret")
    assert settings.has_key("guardian") is True


def test_secret_values_never_leak_in_repr():
    settings = make_settings(newsdata_api_key="super-secret-value")
    assert "super-secret-value" not in repr(settings)
    assert "super-secret-value" not in str(settings.newsdata_api_key)


def test_database_url_is_secret():
    settings = make_settings()
    assert "postgresql" in settings.database_url.get_secret_value()
    assert settings.database_url.get_secret_value() not in repr(settings)
