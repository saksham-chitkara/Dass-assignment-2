"""Module for Gobblet game implementation."""
# pylint: disable=no-member, too-few-public-methods, missing-function-docstring, missing-class-docstring, too-many-return-statements, too-many-branches, unnecessary-dunder-call

import sys
import pygame

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BOARD_SIZE = 3
CELL_SIZE = 120
MARGIN = 50
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
YELLOW = (220, 220, 50)
BOARD_COLOR = (210, 180, 140)
HIGHLIGHT_COLOR = (100, 180, 255, 128)
SMALL = 0
MEDIUM = 1
LARGE = 2
PIECE_SIZES = [25, 35, 45]
PIECE_NAMES = ["SMALL", "MEDIUM", "LARGE"]

class Piece:
    """Represent a game piece."""
    def __init__(self, size, color, player):
        """Initialize a piece with its size, color, and owning player."""
        self.size = size  # 0, 1 ya 2
        self.color = color
        self.player = player  # 0 ya 1 hoga
        self.rect = None
        self.position = None  # (row, col)

    def draw(self, surface, x, y):
        """Draw the piece on the surface at given coordinates."""
        radius = PIECE_SIZES[self.size]
        pygame.draw.circle(surface, self.color, (x, y), radius)
        pygame.draw.circle(surface, BLACK, (x, y), radius, 2)
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        return self.rect

class Cell:
    """Represent a cell on the game board."""
    def __init__(self, row, col):
        """Initialize a cell with its row and column."""
        self.row = row
        self.col = col
        self.stack = []  # stack ki tarah store krra gobblet ko

    def is_empty(self):
        """Return True if the cell stack is empty."""
        return len(self.stack) == 0

    def push(self, piece):
        """Push a piece onto the cell stack if allowed."""
        if not self.is_empty() and self.top().size >= piece.size:
            return False
        self.stack.append(piece)
        piece.position = (self.row, self.col)
        return True

    def pop(self):
        """Pop the top piece from the cell stack."""
        if self.is_empty():
            return None
        piece = self.stack.pop()
        piece.position = None
        return piece

    def top(self):
        """Return the top piece of the cell stack."""
        if self.is_empty():
            return None
        return self.stack[-1]

class GobbletGame:
    """Class for managing Gobblet game logic and interface."""
    def __init__(self):
        """Initialize game settings, board, and players."""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gobblet Jr.")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.board = [[Cell(row, col) for col in range(BOARD_SIZE)] for row in range(BOARD_SIZE)]
        self.setup_players()
        self.curr_player = 0  # 0 red hai and 1 yellow hai
        self.selected_piece = None
        self.game_over = False
        self.winner = None

    def setup_players(self):
        """Set up players and assign their reserve pieces."""
        self.players = [
            {"color": RED, "name": "Red", "reserve": []},
            {"color": YELLOW, "name": "Yellow", "reserve": []}
        ]
        for player in range(2):
            color = self.players[player]["color"]
            for size in [LARGE, MEDIUM, SMALL]:
                for _ in range(2):
                    self.players[player]["reserve"].append(Piece(size, color, player))

    def draw_board(self):
        """Draw the game board and its placed pieces."""
        self.screen.fill(WHITE)
        board_x = (SCREEN_WIDTH - BOARD_SIZE * CELL_SIZE) // 2
        board_y = (SCREEN_HEIGHT - BOARD_SIZE * CELL_SIZE) // 2
        pygame.draw.rect(self.screen, BOARD_COLOR, (board_x, board_y,
                                                    BOARD_SIZE * CELL_SIZE, BOARD_SIZE * CELL_SIZE))
        for i in range(BOARD_SIZE + 1):
            pygame.draw.line(self.screen, BLACK, (board_x + i * CELL_SIZE, board_y),
                            (board_x + i * CELL_SIZE, board_y + BOARD_SIZE * CELL_SIZE), 2)
            pygame.draw.line(self.screen, BLACK, (board_x, board_y + i * CELL_SIZE),
                            (board_x + BOARD_SIZE * CELL_SIZE, board_y + i * CELL_SIZE), 2)
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = self.board[row][col]
                if not cell.is_empty():
                    piece = cell.top()
                    center_x = board_x + col * CELL_SIZE + CELL_SIZE // 2
                    center_y = board_y + row * CELL_SIZE + CELL_SIZE // 2
                    piece.draw(self.screen, center_x, center_y)

    def draw_reserve_pieces(self):
        """Draw the reserve pieces for both players."""
        red_x = 60
        red_y = 150
        red_pieces = self.players[0]["reserve"]
        for piece in red_pieces:
            piece.draw(self.screen, red_x, red_y)
            red_y += (2 * PIECE_SIZES[piece.size])
        yellow_x = SCREEN_WIDTH - 60
        yellow_y = 150
        yellow_pieces = self.players[1]["reserve"]
        for piece in yellow_pieces:
            piece.draw(self.screen, yellow_x, yellow_y)
            yellow_y += (2 * PIECE_SIZES[piece.size])

    def draw_curr_player(self):
        """Display the current player's turn."""
        player_name = self.players[self.curr_player]["name"]
        text = self.font.render(f"Current Player: {player_name}", True, BLACK)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 20))

    def draw_game_over(self):
        """Display a game over overlay when the game ends."""
        if not self.game_over:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        if self.winner is not None:
            winner_name = self.players[self.winner]["name"]
            text = self.font.render(f"{winner_name} Wins!", True, WHITE)
        else:
            text = self.font.render("Game Over - Draw", True, WHITE)
        restart_text = self.font.render("Press R to Restart", True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                        SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                        SCREEN_HEIGHT // 2 + 20))

    def draw(self):
        """Draw the complete game state."""
        self.draw_board()
        self.draw_reserve_pieces()
        self.draw_curr_player()
        if self.selected_piece:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.selected_piece.draw(self.screen, mouse_x, mouse_y)
        self.draw_game_over()
        pygame.display.flip()

    def get_board_cell(self, pos):
        """Return the board cell (row, col) for a given position."""
        mouse_x, mouse_y = pos
        board_x = (SCREEN_WIDTH - BOARD_SIZE * CELL_SIZE) // 2
        board_y = (SCREEN_HEIGHT - BOARD_SIZE * CELL_SIZE) // 2
        if (board_x <= mouse_x <= board_x + BOARD_SIZE * CELL_SIZE and
            board_y <= mouse_y <= board_y + BOARD_SIZE * CELL_SIZE):
            col = (mouse_x - board_x) // CELL_SIZE
            row = (mouse_y - board_y) // CELL_SIZE
            return row, col
        return None

    def check_winner(self, last_move=None):
        """Check for a winning condition and return the winning player if any."""
        for row in range(BOARD_SIZE):
            for player in [0, 1]:
                if all(not self.board[row][col].is_empty() and
                        self.board[row][col].top().player == player for col in range(BOARD_SIZE)):
                    if last_move and last_move[0] == row and last_move[1] in range(BOARD_SIZE):
                        opponent = 1 - player
                        if player == opponent:
                            return opponent
                    return player
        for col in range(BOARD_SIZE):
            for player in [0, 1]:
                if all(not self.board[row][col].is_empty() and
                       self.board[row][col].top().player == player for row in range(BOARD_SIZE)):
                    if last_move and last_move[1] == col and last_move[0] in range(BOARD_SIZE):
                        opponent = 1 - player
                        if player == opponent:
                            return opponent
                    return player
        for player in [0, 1]:
            if all(not self.board[i][i].is_empty() and
                   self.board[i][i].top().player == player for i in range(BOARD_SIZE)):
                if last_move and last_move[0] == last_move[1] and last_move[0] in range(BOARD_SIZE):
                    opponent = 1 - player
                    if player == opponent:
                        return opponent
                return player
            if all(not self.board[i][BOARD_SIZE-1-i].is_empty() and
                   self.board[i][BOARD_SIZE-1-i].top().player == player for i in range(BOARD_SIZE)):
                if last_move and last_move[0] + last_move[1] == BOARD_SIZE - 1:
                    opponent = 1 - player
                    if player == opponent:
                        return opponent
                return player
        return None

    def handle_click(self, pos):
        """Handle a click event at the given position."""
        if self.game_over:
            return
        cell_pos = self.get_board_cell(pos)
        if self.selected_piece:
            if cell_pos:
                row, col = cell_pos
                cell = self.board[row][col]
                from_reserve = self.selected_piece in self.players[self.curr_player]["reserve"]
                prev_position = None
                if not from_reserve:
                    prev_position = self.selected_piece.position
                    if prev_position == (row, col):
                        self.selected_piece = None
                        return
                if cell.push(self.selected_piece):
                    if from_reserve:
                        self.players[self.curr_player]["reserve"].remove(self.selected_piece)
                    else:
                        prev_row, prev_col = prev_position
                        self.board[prev_row][prev_col].pop()
                    winner = self.check_winner(cell_pos)
                    if winner is not None:
                        self.game_over = True
                        self.winner = winner
                    else:
                        self.curr_player = 1 - self.curr_player
                    self.selected_piece = None
            else:
                self.selected_piece = None
        else:
            if cell_pos:
                row, col = cell_pos
                cell = self.board[row][col]
                if not cell.is_empty() and cell.top().player == self.curr_player:
                    self.selected_piece = cell.top()
            if not self.selected_piece:
                for piece in self.players[self.curr_player]["reserve"]:
                    if piece.rect and piece.rect.collidepoint(pos):
                        self.selected_piece = piece
                        break

    def restart(self):
        """Restart the game by reinitializing the game state."""
        self.__init__()

    def run(self):
        """Run the main game loop."""
        running = True
        while running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self.handle_click(mouse_pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.restart()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GobbletGame()
    game.run()
