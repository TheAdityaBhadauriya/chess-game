"""
game_analysis.py — post-game analysis engine.
Replays a finished game through Stockfish at high depth, evaluates every
position, and classifies each move by how much it changed the evaluation.
"""

import chess
from stockfish_engine import get_engine

# centipawn loss thresholds for classification (from the mover's perspective)
THRESHOLDS = {
    "best": 0,
    "good": 20,
    "inaccuracy": 50,
    "mistake": 100,
    "blunder": 9999,  # anything above "mistake" threshold
}


def _evaluate_position(engine, board: chess.Board) -> int:
    """Returns centipawn eval from White's perspective (positive = White better)."""
    engine.set_fen_position(board.fen())
    evaluation = engine.get_evaluation()

    if evaluation["type"] == "mate":
        mate_in = evaluation["value"]
        raw = 100000 if mate_in > 0 else -100000
    else:
        raw = evaluation["value"]

    # the stockfish package returns eval relative to the side to move,
    # so normalize it to always be White's perspective
    if board.turn == chess.BLACK:
        raw = -raw

    return raw

def _classify(centipawn_loss: int) -> str:
    if centipawn_loss <= THRESHOLDS["best"]:
        return "best"
    if centipawn_loss <= THRESHOLDS["good"]:
        return "good"
    if centipawn_loss <= THRESHOLDS["inaccuracy"]:
        return "inaccuracy"
    if centipawn_loss <= THRESHOLDS["mistake"]:
        return "mistake"
    return "blunder"


def analyze_game(uci_moves: list, san_moves: list) -> dict:
    """
    Replays the full game move-by-move, evaluating each resulting position.
    Returns per-move classification, eval graph data, and accuracy % per side.
    """
    engine = get_engine()
    engine.set_depth(15)

    board = chess.Board()
    eval_before = _evaluate_position(engine, board)  # 0 at start

    move_analysis = []
    eval_graph = [{"move_number": 0, "eval": eval_before}]

    white_losses = []
    black_losses = []

    for i, uci in enumerate(uci_moves):
        move = chess.Move.from_uci(uci)
        mover_is_white = board.turn == chess.WHITE

        board.push(move)
        eval_after = _evaluate_position(engine, board)

        # centipawn loss is from the mover's perspective:
        # if White moved, loss = eval_before - eval_after (want eval to stay high for White)
        # if Black moved, loss = eval_after - eval_before (want eval to go low/negative for Black)
        if mover_is_white:
            loss = max(0, eval_before - eval_after)
            white_losses.append(loss)
        else:
            loss = max(0, eval_after - eval_before)
            black_losses.append(loss)

        classification = _classify(loss)

        move_analysis.append({
            "move_number": i + 1,
            "san": san_moves[i],
            "uci": uci,
            "player": "white" if mover_is_white else "black",
            "eval_after": eval_after,
            "centipawn_loss": loss,
            "classification": classification,
        })

        eval_graph.append({"move_number": i + 1, "eval": eval_after})
        eval_before = eval_after

    def accuracy_from_losses(losses):
        if not losses:
            return 100.0
        avg_loss = sum(losses) / len(losses)
        # simple accuracy heuristic: 100% at 0 avg loss, decaying with higher loss
        accuracy = 100 * (0.95 ** (avg_loss / 10))
        return round(max(0, min(100, accuracy)), 1)

    return {
        "moves": move_analysis,
        "eval_graph": eval_graph,
        "white_accuracy": accuracy_from_losses(white_losses),
        "black_accuracy": accuracy_from_losses(black_losses),
    }