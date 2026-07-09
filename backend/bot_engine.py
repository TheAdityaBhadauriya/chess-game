"""
bot_engine.py — custom minimax + alpha-beta chess bot (difficulty levels 1-4).
Levels 5-10 use Stockfish directly (added in Step 4).
"""

import chess
import random

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Encourages pawns to advance, knights/bishops toward center, etc.
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

PST = {chess.PAWN: PAWN_TABLE, chess.KNIGHT: KNIGHT_TABLE}


def evaluate_board(board: chess.Board, use_positional: bool = True) -> int:
    """
    Positive score favors White, negative favors Black.
    use_positional=False gives a pure material-count eval (used for weakest bot).
    """
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        if use_positional and piece.piece_type in PST:
            table = PST[piece.piece_type]
            idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
            value += table[idx]
        score += value if piece.color == chess.WHITE else -value

    return score
def minimax(board: chess.Board, depth: int, alpha: float, beta: float,
            maximizing: bool, use_positional: bool = True) -> float:
    """Returns the evaluation score of the best line found, depth plies deep."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board, use_positional)

    legal_moves = list(board.legal_moves)

    if maximizing:
        max_eval = float("-inf")
        for move in legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False, use_positional)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # alpha-beta prune
        return max_eval
    else:
        min_eval = float("inf")
        for move in legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, True, use_positional)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # alpha-beta prune
        return min_eval


def get_best_move(board: chess.Board, depth: int = 2,
                   use_positional: bool = True, randomness: float = 0.0) -> chess.Move:
    """
    Picks the best move for the side to move, searching `depth` plies ahead.
    randomness: 0.0 = always best move. Higher values let weaker bots
    occasionally pick a slightly-worse move (adds human-like imperfection).
    """
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    maximizing = board.turn == chess.WHITE
    best_move = None
    best_eval = float("-inf") if maximizing else float("inf")
    scored_moves = []

    for move in legal_moves:
        board.push(move)
        eval_score = minimax(board, depth - 1, float("-inf"), float("inf"),
                              not maximizing, use_positional)
        board.pop()
        scored_moves.append((move, eval_score))

        if maximizing and eval_score > best_eval:
            best_eval = eval_score
            best_move = move
        elif not maximizing and eval_score < best_eval:
            best_eval = eval_score
            best_move = move

    # Weakest bots occasionally play a random move instead of the best one
    if randomness > 0 and random.random() < randomness:
        return random.choice(legal_moves)

    return best_move
# ---------- difficulty config (levels 1-4, custom engine) ----------

CUSTOM_BOT_LEVELS = {
    1: {"name": "Pawn Shuffler",  "rating": 500,  "depth": 1, "positional": False, "randomness": 0.35},
    2: {"name": "Club Rookie",    "rating": 800,  "depth": 1, "positional": True,  "randomness": 0.15},
    3: {"name": "Club Player",    "rating": 1100, "depth": 2, "positional": True,  "randomness": 0.05},
    4: {"name": "Strong Club Player", "rating": 1400, "depth": 3, "positional": True, "randomness": 0.0},
}


def get_bot_move_for_level(board: chess.Board, level: int) -> chess.Move:
    config = CUSTOM_BOT_LEVELS.get(level)
    if not config:
        raise ValueError(f"Level {level} not handled by custom engine (use Stockfish for 5-10)")
    return get_best_move(
        board,
        depth=config["depth"],
        use_positional=config["positional"],
        randomness=config["randomness"],
    )