from bench.redact import MASK, redact_text, redact_tree, secret_values

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
