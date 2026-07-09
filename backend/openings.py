"""
openings.py — loads the Lichess ECO opening dataset and identifies
which named opening a game's move sequence matches (longest match wins).
"""

import os
import csv

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TSV_FILES = ["a.tsv", "b.tsv", "c.tsv", "d.tsv", "e.tsv"]

# key: normalized move string, e.g. "e4 e5 Nf3 Nc6"
# value: {"eco": "C50", "name": "Italian Game"}
_OPENING_BOOK = {}


def _strip_move_numbers(pgn: str) -> str:
    """'1. e4 e5 2. Nf3 Nc6' -> 'e4 e5 Nf3 Nc6'"""
    tokens = pgn.split()
    return " ".join(t for t in tokens if not t[0].isdigit())


def load_openings():
    global _OPENING_BOOK
    _OPENING_BOOK = {}
    for filename in TSV_FILES:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                key = _strip_move_numbers(row["pgn"])
                _OPENING_BOOK[key] = {"eco": row["eco"], "name": row["name"]}
    return len(_OPENING_BOOK)


def identify_opening(san_move_history: list) -> dict:
    """
    Given a list of SAN moves played so far (e.g. ["e4", "e5", "Nf3", "Nc6"]),
    finds the longest matching named opening (walks backward if no exact match).
    Returns {"eco": ..., "name": ...} or None if no match at all.
    """
    if not _OPENING_BOOK:
        load_openings()

    for length in range(min(len(san_move_history), 20), 0, -1):
        key = " ".join(san_move_history[:length])
        if key in _OPENING_BOOK:
            return _OPENING_BOOK[key]
    return None