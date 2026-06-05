from checkit.transform.cleaning import nettoie_texte, text_fingerprint


def test_html_entities_unescaped():
    assert nettoie_texte("Macron &amp; l&#39;Europe") == "Macron & l'Europe"


def test_whitespace_collapsed_and_stripped():
    assert nettoie_texte("  Une\n\n  annonce \t choc  ") == "Une annonce choc"


def test_control_characters_removed():
    assert nettoie_texte("titre\x00caché\x07fin") == "titrecachéfin"


def test_none_and_empty_stay_none():
    assert nettoie_texte(None) is None
    assert nettoie_texte("   ") is None


def test_fingerprint_ignores_case_punctuation_spacing():
    a = text_fingerprint("BREAKING: Le scoop!!!", None)
    b = text_fingerprint("breaking   le scoop", None)
    assert a == b


def test_fingerprint_differs_on_content():
    assert text_fingerprint("titre A", None) != text_fingerprint("titre B", None)
