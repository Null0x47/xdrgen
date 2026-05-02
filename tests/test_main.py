from __future__ import annotations

import json
import pathlib

import pytest
import typer
from typer.testing import CliRunner

import main as main_module
from main import _load_profile, app


@pytest.fixture
def runner() -> CliRunner:
    # GitHub Actions runners set COLUMNS=0, which makes Rich (used by Typer
    # for error rendering) wrap long flag names like `--kafka-bootstrap`
    # mid-word and break substring assertions on error output. Pin a wide
    # width so error text stays on one line regardless of the host env.
    return CliRunner(env={"COLUMNS": "200"})


def test_load_profile_accepts_known_tables(tmp_path: pathlib.Path):
    profile = tmp_path / "tables.yaml"
    profile.write_text("tables:\n  - CloudAppEvents\n", encoding="utf-8")

    prof = _load_profile(profile)
    assert prof.tables == ["CloudAppEvents"]
    assert prof.overrides is None


def test_load_profile_allows_missing_tables_key(tmp_path: pathlib.Path):
    """Tables is optional — an overrides-only YAML must validate cleanly."""
    profile = tmp_path / "no_tables.yaml"
    profile.write_text("overrides:\n  tenant_domain: northwind.com\n", encoding="utf-8")

    prof = _load_profile(profile)
    assert prof.tables is None
    assert prof.overrides is not None
    assert prof.overrides.tenant_domain == "northwind.com"


def test_load_profile_allows_empty_tables_list(tmp_path: pathlib.Path):
    profile = tmp_path / "empty.yaml"
    profile.write_text("tables: []\n", encoding="utf-8")

    prof = _load_profile(profile)
    assert prof.tables == []


def test_load_profile_rejects_unknown_top_level_key(tmp_path: pathlib.Path):
    profile = tmp_path / "garbage.yaml"
    profile.write_text("not_tables: []\n", encoding="utf-8")

    with pytest.raises(typer.BadParameter, match="not_tables"):
        _load_profile(profile)


def test_load_profile_rejects_unknown_generator(tmp_path: pathlib.Path):
    profile = tmp_path / "unknown.yaml"
    profile.write_text("tables:\n  - DoesNotExist\n", encoding="utf-8")

    with pytest.raises(typer.BadParameter, match="No generator for: DoesNotExist"):
        _load_profile(profile)


def test_load_profile_returns_validated_overrides_model(tmp_path: pathlib.Path):
    profile = tmp_path / "with_overrides.yaml"
    profile.write_text(
        "tables:\n"
        "  - CloudAppEvents\n"
        "overrides:\n"
        "  tenant_id: 99999999-aaaa-bbbb-cccc-dddddddddddd\n"
        "  tenant_domain: northwind.com\n",
        encoding="utf-8",
    )

    prof = _load_profile(profile)
    assert prof.tables == ["CloudAppEvents"]
    assert prof.overrides is not None
    assert prof.overrides.tenant_id == "99999999-aaaa-bbbb-cccc-dddddddddddd"
    assert prof.overrides.tenant_domain == "northwind.com"


def test_load_profile_rejects_unknown_override_key(tmp_path: pathlib.Path):
    profile = tmp_path / "bad_overrides.yaml"
    profile.write_text(
        "tables:\n  - CloudAppEvents\noverrides:\n  not_a_real_key: oops\n",
        encoding="utf-8",
    )

    with pytest.raises(typer.BadParameter, match="not_a_real_key"):
        _load_profile(profile)


def test_load_profile_rejects_users_missing_required_fields(tmp_path: pathlib.Path):
    profile = tmp_path / "bad_users.yaml"
    profile.write_text(
        "tables:\n  - CloudAppEvents\n"
        "overrides:\n  users:\n    - upn: lonely@northwind.com\n",
        encoding="utf-8",
    )

    # display_name and object_id are required on User — pydantic must say so.
    with pytest.raises(typer.BadParameter, match="display_name|object_id"):
        _load_profile(profile)


class _StubEvent:
    """Stand-in BaseModel-shaped object returned by stub generators. Mirrors
    the subset of the Pydantic v2 surface that `main._write_events` calls."""

    def __init__(self, name: str) -> None:
        self._name = name

    def model_dump_json(self, by_alias: bool = False, indent: int | None = None) -> str:
        return json.dumps({"table": self._name}, indent=indent)

    def model_dump(self, mode: str = "python", by_alias: bool = False) -> dict:
        return {"table": self._name}


def _install_stub_generators(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = {"CloudAppEvents": lambda _w: _StubEvent("CloudAppEvents")}
    # main.py imports GENERATORS at module load — patch the bound name there.
    monkeypatch.setattr(main_module, "GENERATORS", stub)


def test_banner_prints_with_version(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _install_stub_generators(monkeypatch)
    monkeypatch.setattr(main_module, "_get_version", lambda: "9.9.9")
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "1", "-i", "0", "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert "░██" in result.output
    assert "v9.9.9" in result.output


def test_generate_writes_single_json_array(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _install_stub_generators(monkeypatch)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "5", "-i", "0", "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 5
    for item in payload:
        assert item == {"table": "CloudAppEvents"}


def test_generate_default_output_is_telemetry_json(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Without `-o`, the default file is `./telemetry.json` in cwd. Run the
    CLI from a tmp dir so we don't pollute the repo working tree."""
    _install_stub_generators(monkeypatch)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["generate", "-n", "2", "-i", "0"])

    assert result.exit_code == 0, result.output
    default = tmp_path / "telemetry.json"
    assert default.exists()
    assert json.loads(default.read_text(encoding="utf-8")) == [
        {"table": "CloudAppEvents"},
        {"table": "CloudAppEvents"},
    ]


def test_generate_flushes_buffer_periodically(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Flush boundary: with `--flush-every 3` and `-n 7`, the sink must
    receive multiple write() calls — proving events don't accumulate
    unboundedly in memory. We verify by counting writes via a custom sink
    that records each batch."""
    _install_stub_generators(monkeypatch)

    batches: list[int] = []
    real_build_sink = main_module._build_sink

    def recording_build_sink(*args, **kwargs):
        sink = real_build_sink(*args, **kwargs)
        original_write = sink.write

        def write(batch):
            batches.append(len(batch))
            original_write(batch)

        sink.write = write  # type: ignore[method-assign]
        return sink

    monkeypatch.setattr(main_module, "_build_sink", recording_build_sink)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "7", "-i", "0", "-o", str(output), "--flush-every", "3"],
    )

    assert result.exit_code == 0, result.output
    # 7 events / threshold 3 → two full flushes (3, 3) plus the final remainder (1).
    assert batches == [3, 3, 1]
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload) == 7
    assert all(item == {"table": "CloudAppEvents"} for item in payload)


def test_generate_flush_every_rejects_zero(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """`--flush-every 0` would mean never flush; Typer's `min=1` rejects it."""
    _install_stub_generators(monkeypatch)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "1", "-i", "0", "-o", str(output), "--flush-every", "0"],
    )

    assert result.exit_code != 0
    assert "flush-every" in result.output.lower() or "0" in result.output


def test_generate_per_table_writes_one_file_per_event(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """`--per-table` treats `-o` as a directory and writes one JSON file per
    event named `{TableName}-{n:04d}.json`, with `n` scoped per table."""
    stub = {
        "Alpha": lambda _w: _StubEvent("Alpha"),
        "Beta": lambda _w: _StubEvent("Beta"),
    }
    monkeypatch.setattr(main_module, "GENERATORS", stub)
    out_dir = tmp_path / "split"

    result = runner.invoke(
        app,
        ["generate", "-n", "20", "-i", "0", "-o", str(out_dir), "--per-table"],
    )

    assert result.exit_code == 0, result.output
    files = sorted(p.name for p in out_dir.iterdir())
    assert len(files) == 20
    # Filenames are zero-padded and per-table-counter scoped.
    by_table: dict[str, list[str]] = {}
    for name in files:
        prefix, _, _ = name.partition("-")
        by_table.setdefault(prefix, []).append(name)
    assert set(by_table) <= {"Alpha", "Beta"}
    for table, names in by_table.items():
        for i, name in enumerate(sorted(names)):
            assert name == f"{table}-{i:04d}.json"
        # Each file is a valid JSON object that round-trips.
        sample = json.loads((out_dir / names[0]).read_text(encoding="utf-8"))
        assert sample == {"table": table}


def test_generate_with_overrides_only_profile_runs_all_tables(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """A profile with `overrides:` but no `tables:` falls back to every
    registered generator — proves the optional-tables wiring runs end-to-end."""
    _install_stub_generators(monkeypatch)
    profile = tmp_path / "overrides_only.yaml"
    profile.write_text("overrides:\n  tenant_domain: northwind.com\n", encoding="utf-8")
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", str(profile), "-n", "4", "-i", "0", "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == [{"table": "CloudAppEvents"}] * 4


def test_generate_echo_flag_streams_lines_to_stdout(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _install_stub_generators(monkeypatch)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "3", "-i", "0", "-o", str(output), "--echo"],
    )

    assert result.exit_code == 0, result.output
    # One stdout line per generated event, plus the start/end status lines.
    event_lines = [
        line
        for line in result.output.splitlines()
        if line == json.dumps({"table": "CloudAppEvents"})
    ]
    assert len(event_lines) == 3


def test_generate_without_echo_does_not_stream_events(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _install_stub_generators(monkeypatch)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "3", "-i", "0", "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert json.dumps({"table": "CloudAppEvents"}) not in result.output


def test_generate_without_profile_uses_all_registered_generators(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    stub = {
        "Alpha": lambda _w: _StubEvent("Alpha"),
        "Beta": lambda _w: _StubEvent("Beta"),
    }
    monkeypatch.setattr(main_module, "GENERATORS", stub)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "1", "-i", "0", "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    # The header line lists the tables that will be sampled from.
    assert "tables=['Alpha', 'Beta']" in result.output


def test_generate_with_profile_only_uses_listed_tables(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    stub = {
        "Alpha": lambda _w: _StubEvent("Alpha"),
        "Beta": lambda _w: _StubEvent("Beta"),
    }
    monkeypatch.setattr(main_module, "GENERATORS", stub)

    profile = tmp_path / "profile.yaml"
    profile.write_text("tables:\n  - Alpha\n", encoding="utf-8")
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", str(profile), "-n", "5", "-i", "0", "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == [{"table": "Alpha"}] * 5


def _stub_kafka_build(monkeypatch: pytest.MonkeyPatch, captured: dict, sent: list):
    """Replace `kafka_sink.build` with a stub that records the build kwargs and
    every sent event — keeps the Kafka path testable without a broker."""

    class _StubKafkaSink:
        def write(self, batch):
            for table, event in batch:
                sent.append((table, event.model_dump_json(by_alias=True)))

        def close(self):
            pass

    def fake_build(*, bootstrap_servers, per_table, topic, topic_prefix):
        captured.update(
            bootstrap_servers=bootstrap_servers,
            per_table=per_table,
            topic=topic,
            topic_prefix=topic_prefix,
        )
        return _StubKafkaSink()

    monkeypatch.setattr(main_module.kafka_sink, "build", fake_build)


def test_generate_sink_kafka_routes_to_kafka_only(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """`--sink kafka` produces events to the broker and writes nothing to disk."""
    _install_stub_generators(monkeypatch)
    sent: list[tuple[str, str]] = []
    captured: dict = {}
    _stub_kafka_build(monkeypatch, captured, sent)

    output = tmp_path / "should_not_exist.json"
    result = runner.invoke(
        app,
        [
            "generate",
            "-n",
            "3",
            "-i",
            "0",
            "-o",
            str(output),
            "--sink",
            "kafka",
            "--kafka-bootstrap",
            "localhost:9092",
            "--kafka-topic",
            "xdrgen-test",
        ],
    )

    assert result.exit_code == 0, result.output
    assert not output.exists()
    assert len(sent) == 3
    assert all(table == "CloudAppEvents" for table, _ in sent)
    assert captured == {
        "bootstrap_servers": "localhost:9092",
        "per_table": False,
        "topic": "xdrgen-test",
        "topic_prefix": "xdrgen.",
    }


def test_generate_sink_kafka_requires_bootstrap(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """`--sink kafka` without `--kafka-bootstrap` must fail fast."""
    _install_stub_generators(monkeypatch)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "1", "-i", "0", "-o", str(output), "--sink", "kafka"],
    )

    assert result.exit_code != 0
    assert "--kafka-bootstrap" in result.output


def test_generate_sink_kafka_per_table_passes_through(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """`--per-table` and `--kafka-topic-prefix` must reach the Kafka sink."""
    stub = {
        "Alpha": lambda _w: _StubEvent("Alpha"),
        "Beta": lambda _w: _StubEvent("Beta"),
    }
    monkeypatch.setattr(main_module, "GENERATORS", stub)
    captured: dict = {}
    _stub_kafka_build(monkeypatch, captured, [])

    out_dir = tmp_path / "split"
    result = runner.invoke(
        app,
        [
            "generate",
            "-n",
            "3",
            "-i",
            "0",
            "-o",
            str(out_dir),
            "--sink",
            "kafka",
            "--per-table",
            "--kafka-bootstrap",
            "localhost:9092",
            "--kafka-topic-prefix",
            "xdrgen.",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["per_table"] is True
    assert captured["topic_prefix"] == "xdrgen."


def test_generate_default_sink_is_file(
    runner: CliRunner,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """No `--sink` flag → the file sink runs (and Kafka is never touched)."""
    _install_stub_generators(monkeypatch)

    def fake_kafka_build(**_kw):  # would explode if kafka path were taken
        raise AssertionError("Kafka sink built when --sink defaulted to file.")

    monkeypatch.setattr(main_module.kafka_sink, "build", fake_kafka_build)
    output = tmp_path / "out.json"

    result = runner.invoke(
        app,
        ["generate", "-n", "2", "-i", "0", "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload) == 2
