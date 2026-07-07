"""
game_engine.py
Wraps python-chess to manage a single game's state and expose
clean, JSON-friendly methods for the Flask API layer.
"""

import chess
import chess.pgn


class ChessGame:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.board = chess.Board()
        self.move_history = []   # SAN strings, in order
        self.uci_history = []    # UCI strings, in order

    # ---------- state ----------

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "move_history": self.move_history,
            "uci_history": self.uci_history,
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "is_game_over": self.board.is_game_over(),
            "result": self._result_string(),
            "half_move_clock": self.board.halfmove_clock,
            "full_move_number": self.board.fullmove_number,
        }

    def _result_string(self):
        if not self.board.is_game_over():
            return None
        if self.board.is_checkmate():
            winner = "black" if self.board.turn == chess.WHITE else "white"
            return f"checkmate_{winner}_wins"
        if self.board.is_stalemate():
            return "draw_stalemate"
        if self.board.is_insufficient_material():
            return "draw_insufficient_material"
        if self.board.is_seventyfive_moves():
            return "draw_75_move_rule"
        if self.board.is_fivefold_repetition():
            return "draw_fivefold_repetition"
        if self.board.can_claim_draw():
            return "draw_claimable"
        return "draw"

    # ---------- moves ----------

    def legal_moves_uci(self) -> list:
        return [m.uci() for m in self.board.legal_moves]

    def legal_moves_from_square(self, square_name: str) -> list:
        try:
            square = chess.parse_square(square_name)
        except ValueError:
            return []
        return [m.uci() for m in self.board.legal_moves if m.from_square == square]

    def push_move(self, uci_move: str) -> dict:
        try:
            move = chess.Move.from_uci(uci_move)
        except ValueError:
            raise ValueError(f"Malformed UCI move: {uci_move}")

        if move not in self.board.legal_moves:
            raise ValueError(f"Illegal move: {uci_move}")

        san = self.board.san(move)
        self.board.push(move)
        self.move_history.append(san)
        self.uci_history.append(uci_move)
        return self.to_dict()

    def undo_last_move(self) -> dict:
        if self.board.move_stack:
            self.board.pop()
            self.move_history.pop()
            self.uci_history.pop()
        return self.to_dict()

    def reset(self):
        self.board = chess.Board()
        self.move_history = []
        self.uci_history = []

    # ---------- export ----------

    def to_pgn(self) -> str:
        game = chess.pgn.Game()
        node = game
        for uci in self.uci_history:
            move = chess.Move.from_uci(uci)
            node = node.add_variation(move)
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        return game.accept(exporter)