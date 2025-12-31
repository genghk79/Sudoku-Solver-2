from board_utils import SudokuBoard
from strategies import SudokuStrats
from backtrack import Backtrack
import general_utils
import logging
import sys

logger = logging.getLogger(__name__)
general_utils.setup_logging()

class UserQuit(Exception):
    pass

# Start of the Sudoku solver
# The Sudoku solver goes through the following steps:
# 1. Asks the user to choose to load a board/puzzle or to enter a new puzzle
# 2. Asks the user if the puzzle should be solved by the backtracking method or using Sudoku strategies
# 3. Run the selected solver and display the results
print("=" * 60)
print("Welcome to the Sudoku solver!")
print("=" * 60)
print()
print("Would you like to:")
print("1. Load a board/puzzle from a txt file, or")
print("2. Reuse the previous board/puzzle, or")
print("3. Enter a new board/puzzle?")
choice = 0
while not choice in {1,2,3}:
    choice = input("Please choose option 1,2 or 3: ")
    try:
        choice = int(choice)
    except:
        pass
print()

board = SudokuBoard()

if choice == 1:
    filename = input("Please enter the full name of the file to load: ")
    try:
        board.load_puzzle(filename)        
    except Exception:
        logger.exception(f"Failed to load file {filename}.")
        sys.exit(1)
    
if choice == 2:
    print("Load the previous board/puzzle")
    try:
        filename = 'savefiles/last_used_puzzle.txt'
        board.load_puzzle(filename)
    except Exception:
        logger.exception(f"Failed to load file {filename}.")
        sys.exit(1)
    
if choice == 3:
    print("Please enter the puzzle to solve row-by-row as comma separated rows of 9 numbers each.")
    print("You may use the following as a template:")
    print("0, 0, 0, 0, 0, 0, 0, 0, 0")
    print()
    print("'0' represents a blank cell. Replace them with numbers 1-9 for cells with known values.")
    print()

    # Take input to populate the Sudoku board
    board_input = []
    row_n = 0
    while row_n<9:
        try:
            row_input = input(f"Enter row {row_n}: ")
            if row_input == 'q':
                raise UserQuit
            row_input = [int(x) for x in row_input.split(',')]
            board_input.append(row_input)
            row_n += 1
        except UserQuit:
            print("quitting...")
            sys.exit(0)
        except:
            print("Entered row not valid, please try again, or enter 'q' to quit.")
            print()
    board.set_puzzle(board_input)
    logger.info("New puzzle successfully entered from CLI.")

if choice in {1,3}:
    board.save_puzzle('savefiles/last_used_puzzle.txt')

print('-' * 20)
print("Puzzle to solve")
print('-' * 20)
board.show_puzzle()
print()

print("-" * 60)
print()

print("We shall proceed to solve the puzzle. Would you like to use: ")
print("1. strategies as taught on sudoku.com, or")
print("2. brute force i.e. backtracking algorithm?")
solve_by = 0
while not solve_by in {1,2}:
    solve_by = input("Please choose option 1 or 2 (or 'q' to quit): ")
    try:
        if solve_by == 'q':
            raise UserQuit
        solve_by = int(solve_by)
    except UserQuit:
        print("quitting...")
        sys.exit(0)
    except:
        pass
if solve_by == 1:
    strat = SudokuStrats(board)
    strat.solve()
else:
    bt = Backtrack(board)
    bt.solve()

print("-" * 60)
print()
print('End!')
sys.exit(0)