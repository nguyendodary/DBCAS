"""Source-level validation of the authored concept metadata.

These checks need no database and no provider. They keep the canonical
metadata file, the three import packs and the activated-bank snapshot in
sync so a regenerated pack cannot silently drop curriculum metadata.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METADATA = ROOT / "db/concept_metadata.json"
PACKS = (
    ROOT / "db/benchmark_pack.json",
    ROOT / "db/sql_knowledge_pack.json",
    ROOT / "db/postgres_knowledge_pack.json",
)
SNAPSHOT = Path(__file__).with_name("fixtures") / "release_content_snapshot.json"
PACKED_CODES = {"E2E-TC1", "E2E-TC2"}


def load_metadata():
    return json.loads(METADATA.read_text(encoding="utf-8"))["concepts"]


def test_metadata_covers_every_activated_concept():
    metadata = load_metadata()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert set(metadata) == {row["concept_code"] for row in snapshot["concepts"]}
    assert len(metadata) == 82


def test_metadata_is_meaningful_and_unique():
    metadata = load_metadata()
    objectives = {}
    for code, item in metadata.items():
        assert isinstance(item["description"], str) and len(item["description"].strip()) >= 20, code
        assert 3 <= len(item["keywords"]) <= 30, code
        assert 3 <= len(item["learning_objectives"]) <= 20, code
        assert len(set(item["keywords"])) == len(item["keywords"]), code
        assert len(set(item["learning_objectives"])) == len(item["learning_objectives"]), code
        for keyword in item["keywords"]:
            assert 0 < len(keyword) <= 100, code
        for objective in item["learning_objectives"]:
            assert 0 < len(objective) <= 1000, code
            assert objective not in objectives, f"{code} duplicates {objectives.get(objective)}"
            objectives[objective] = code


def test_import_packs_carry_the_same_metadata():
    metadata = load_metadata()
    packed = set()
    for path in PACKS:
        pack = json.loads(path.read_text(encoding="utf-8"))
        for concept in pack["concepts"]:
            code = concept["concept_code"]
            packed.add(code)
            assert concept["description"] == metadata[code]["description"], f"{path.name}:{code}"
            assert concept["keywords"] == metadata[code]["keywords"], f"{path.name}:{code}"
            assert concept["learning_objectives"] == metadata[code]["learning_objectives"], f"{path.name}:{code}"
    assert packed == set(metadata) - PACKED_CODES
