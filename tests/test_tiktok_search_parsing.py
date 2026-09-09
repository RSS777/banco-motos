import json
from pathlib import Path

from pipeline.collectors.tiktok import build_candidate_from_search_entry

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "tiktok_search_general_full.json").read_text(
        encoding="utf-8"
    )
)


def test_video_entry_becomes_a_candidate():
    entries = FIXTURE["data"]
    candidate = build_candidate_from_search_entry(entries[0], term="moto elétrica")

    assert candidate is not None
    assert candidate.platform == "tiktok"
    assert candidate.url == "https://www.tiktok.com/@suprabike/video/7657539926774254855"
    assert candidate.raw_metadata["duration_seconds"] == 71
    assert "scootereletrica" in candidate.raw_metadata["hashtags"]
    assert candidate.raw_metadata["play_count"] == 763100
    assert candidate.raw_metadata["search_term"] == "moto elétrica"


def test_non_video_entry_is_ignored():
    entries = FIXTURE["data"]
    related_search_entry = entries[1]
    assert related_search_entry["type"] != 1

    candidate = build_candidate_from_search_entry(related_search_entry, term="moto elétrica")

    assert candidate is None


def test_second_video_entry_also_maps_correctly():
    entries = FIXTURE["data"]
    candidate = build_candidate_from_search_entry(entries[2], term="moto elétrica")

    assert candidate is not None
    assert candidate.url == "https://www.tiktok.com/@motoreviewsbr/video/7699999999999999999"
    assert candidate.raw_metadata["hashtags"] == ["motoeletrica"]


def test_entry_missing_author_or_id_is_ignored():
    broken_entry = {"type": 1, "item": {"desc": "sem autor", "video": {}, "stats": {}}}

    candidate = build_candidate_from_search_entry(broken_entry, term="moto elétrica")

    assert candidate is None
