from board_utils import SudokuBoard
from strategies import SudokuStrats
from backtrack import Backtrack
import general_utils
import logging
import sys
import os
import inquirer

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

questions = [
    inquirer.List(
        "choice",
        message="Your latest board can be found in the savefile 'last_used_puzzle.txt'.\n\tWould you like to",
        choices=[
            ("Load a board/puzzle from a txt file in the 'savefiles' directory", 1),
            ("Enter a new board/puzzle", 2),
        ],
    ),
]
answer = inquirer.prompt(questions)
choice = answer["choice"]  # Returns 1, 2, or 3

board = SudokuBoard()
if choice == 1:
    savefiles_dir = "savefiles"
    files = sorted(
        [f for f in os.listdir(savefiles_dir) if f.endswith(".txt")],
        key=lambda f: os.path.getmtime(os.path.join(savefiles_dir, f)),
        reverse=True
    )

    if not files:
        print("No saved puzzles found.")
        sys.exit(1)

    questions = [
        inquirer.List(
            "filename",
            message="Select a puzzle to load",
            choices=files,
        ),
    ]
    answer = inquirer.prompt(questions)
    filename = os.path.join(savefiles_dir, answer["filename"])
    board.load_puzzle(filename)    
    
else:
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
    print()

    questions = [inquirer.Text("savename", message="Please provide a file name to save this puzzle to")]
    answer = inquirer.prompt(questions)
    savename = answer['savename']
    if savename.split('.')[-1] != 'txt':
        savename = savename + '.txt'
    board.save_puzzle('savefiles/'+savename)

board.save_puzzle('savefiles/last_used_puzzle.txt')

print('-' * 20)
print("Puzzle to solve")
print('-' * 20)
board.show_puzzle()
print()

print("-" * 60)
print()

questions = [
        inquirer.List(
            "solve_by",
            message="We can now proceed to solve the puzzle. How would you like to do it?",
            choices=[("Using strategies as taught on sudoku.com", 1),
                     ("By brute force i.e. backtracking algorithm", 2),
                     ("I don't want to solve the puzzle, let's quit", 3)],
        ),
    ]
answer = inquirer.prompt(questions)
solve_by = answer['solve_by']

if solve_by == 1:
    strat = SudokuStrats(board)
    strat.solve()
elif solve_by == 2:
    bt = Backtrack(board)
    bt.solve()
else:
    print("quitting...")
    sys.exit(0)

print("-" * 60)
print()
print('End!')
sys.exit(0)