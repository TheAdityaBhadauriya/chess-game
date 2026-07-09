"""
stockfish_engine.py — Stockfish integration for difficulty levels 5-10.
"""

from stockfish import Stockfish

STOCKFISH_PATH = r"C:\stockfish\stockfish.exe"

STOCKFISH_BOT_LEVELS = {
    5:  {"name": "Candidate Master",       "rating": 1700, "skill": 2},
    6:  {"name": "National Master",        "rating": 2000, "skill": 5},
    7:  {"name": "Judit Polgar-level",      "rating": 2300, "skill": 9},
    8:  {"name": "Viswanathan Anand-level", "rating": 2500, "skill": 13},
    9:  {"name": "Bobby Fischer-level",     "rating": 2700, "skill": 17},
    10: {"name": "Magnus Carlsen-level",    "rating": 2850, "skill": 20},
}

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = Stockfish(path=STOCKFISH_PATH, depth=15)
    return _engine


def get_stockfish_move(fen: str, level: int) -> str:
    """Returns the best move in UCI format for a given FEN and difficulty level (5-10)."""
    config = STOCKFISH_BOT_LEVELS.get(level)
    if not config:
        raise ValueError(f"Level {level} not handled by Stockfish (use custom engine for 1-4)")

    engine = get_engine()
    engine.set_skill_level(config["skill"])
    engine.set_fen_position(fen)
    return engine.get_best_move()