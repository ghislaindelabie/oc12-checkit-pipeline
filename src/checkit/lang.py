"""Language-name → ISO 639-1 mapping shared by sources that send full names."""

LANGUAGE_CODES = {
    "french": "fr",
    "english": "en",
    "spanish": "es",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "arabic": "ar",
    "chinese": "zh",
    "greek": "el",
    "turkish": "tr",
    "dutch": "nl",
    "polish": "pl",
    "japanese": "ja",
}


def to_code(name: str | None) -> str | None:
    if not name:
        return None
    name = name.lower()
    return LANGUAGE_CODES.get(name, name[:2] if len(name) >= 2 else None)
