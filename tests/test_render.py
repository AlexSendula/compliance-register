from compliance_register.render import printable


def test_printable_returns_printable_non_ascii_text_unchanged_and_the_same_object_identity():
    for text in ("café", "日本語", "العربية"):
        assert printable(text) is text


def test_printable_maps_t_n_r_to_their_mnemonics_and_codepoints_above_u_ffff_to_u_followed_by_eight_hex_digits():
    assert printable("a\tb\nc\rd") == "a\\tb\\nc\\rd"
    assert printable("x\U000E0001y") == "x\\U000e0001y"  # U+E0001 LANGUAGE TAG, category Cf
