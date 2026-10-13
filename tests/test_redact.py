from bench.redact import MASK, redact_text, redact_tree, screen_screenshots, secret_values

SECRET = "super-secret-value-123"


def test_masks_known_values_and_their_url_encoding():
    secrets = secret_values({"TOKEN": "a/b+c=secret!"}, ["TOKEN"])
    assert redact_text("raw a/b+c=secret! encoded a%2Fb%2Bc%3Dsecret%21", secrets) == f"raw {MASK} encoded {MASK}"


def test_short_values_are_not_treated_as_secrets():
    assert secret_values({"TEAM": "abc"}, ["TEAM"]) == []


def test_masks_credential_shaped_strings_the_agent_obtained_itself():
    text = ("psql postgres://app:hunter2pass@db.example.com:5432/app && "
            "export CLOUDISH_API_KEY=cld_0123456789abcdefABCD && git push https://x:ghp_" + "a" * 36 + "@github.com/o/r")
    cleaned = redact_text(text, [])
    assert "hunter2pass" not in cleaned and "cld_0123456789" not in cleaned and "ghp_aaaa" not in cleaned
    assert "postgres://app:[REDACTED]@db.example.com" in cleaned


def test_redact_tree_handles_binary_and_large_files(tmp_path):
    (tmp_path / "transcript.jsonl").write_text(('{"t": 1, "x": "%s"}\n' % SECRET) * 20000)
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe" + SECRET.encode() + b"\x00\x01")
    (tmp_path / "clean.txt").write_text("nothing to see")
    assert redact_tree(tmp_path, [SECRET]) == 2
    assert SECRET not in (tmp_path / "transcript.jsonl").read_text()
    assert (tmp_path / "binary.bin").read_bytes() == b"\xff\xfe" + MASK.encode() + b"\x00\x01"
    assert (tmp_path / "clean.txt").read_text() == "nothing to see"


def test_screenshots_of_pages_that_showed_a_secret_are_deleted(tmp_path):
    for name, text in {"clean": "Welcome", "leak": f"DATABASE_URL=postgres://app:{SECRET}@db", "no-text": None}.items():
        (tmp_path / f"{name}.jpg").write_bytes(b"\xff\xd8" + name.encode())
        if text is not None:
            (tmp_path / f"{name}.txt").write_text(text)
    assert screen_screenshots(tmp_path, [SECRET]) == ["leak.jpg", "no-text.jpg"]
    assert sorted(p.name for p in tmp_path.glob("*.jpg")) == ["clean.jpg"]
    assert screen_screenshots(tmp_path / "missing", [SECRET]) == []


def test_redact_tree_leaves_images_alone(tmp_path):
    image = tmp_path / "home.jpg"
    image.write_bytes(b"\xff\xd8" + SECRET.encode())  # bytes that happen to spell a secret
    (tmp_path / "home.txt").write_text(SECRET)
    redact_tree(tmp_path, [SECRET])
    assert image.read_bytes() == b"\xff\xd8" + SECRET.encode()
    assert (tmp_path / "home.txt").read_text() == MASK
