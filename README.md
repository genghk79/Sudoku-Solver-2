# Sudoku Solver

A Python-based Sudoku solver that implements two solving approaches: logical deduction strategies and brute-force backtracking.

## Introduction

This project provides a command-line Sudoku solver with two distinct solving methods:

1. **Strategy-based solver** - Uses human-like logical deduction techniques including singles, pairs, triplets, and pointing sets
2. **Backtracking solver** - Uses a brute-force search algorithm with backtracking

The solver supports loading puzzles from text files, manual entry via CLI, and saving puzzle states for later use.

## Board State Representation

The Sudoku board is managed by the `SudokuBoard` class in `src/board_utils.py`. The board state is stored as a pandas DataFrame with 81 rows (one per cell in the 9x9 grid).

Each cell tracks the following information:

| Column   | Description                                           |
|----------|-------------------------------------------------------|
| `row_n`  | Row number (0-8)                                      |
| `col_n`  | Column number (0-8)                                   |
| `sqr_n`  | 3x3 square number (0-8), calculated as `3*(row_n//3) + col_n//3` |
| `poss`   | Set of possible values (1-9) for unsolved cells       |
| `ans`    | The answer (1-9) or `None` if the cell is empty       |

Key operations include:
- **Setting a cell**: Updates the answer and propagates constraints to remove that value from possibilities in the same row, column, and square
- **Error checking**: Validates for duplicate values and dead-end cells (empty cells with no remaining possibilities)
- **Save/Load**: Persists board state to text files for later use

## Strategy-Based Solver

The `SudokuStrats` class in `src/strategies.py` implements seven logical deduction strategies:

1. **Obvious Singles** - Fills cells that have only one remaining possibility
2. **Hidden Singles** - Finds values that can only go in one cell within a row, column, or square
3. **Obvious Pairs** - Identifies two cells with identical 2-value possibility sets and removes those values from other cells in the same group
4. **Hidden Pairs** - Finds two values that appear in only two cells within a group, reducing those cells to only those two values
5. **Obvious Triplets** - Extends the pairs logic to three cells with three combined possibilities
6. **Hidden Triplets** - Extends hidden pairs logic to three values appearing in only three cells
7. **Pointing Sets** - Uses row/column and square intersection constraints to eliminate possibilities

The solver applies strategies in order of increasing complexity, returning to simpler strategies whenever progress is made.

## Backtracking Solver

The `Backtrack` class in `src/backtrack.py` implements a brute-force search algorithm:

1. **Forward fill**: Find the next empty cell and fill it with the first available possibility
2. **Constraint check**: Verify no conflicts exist in the affected row, column, and square
3. **Backtrack**: If a conflict is detected, undo the last move and try the next possibility
4. **Repeat**: Continue until the puzzle is complete or all possibilities are exhausted

The solver maintains a history stack to track filled cells and their remaining untried possibilities, enabling efficient backtracking.

## Running the Solver

### Requirements

- Python 3.x
- pandas
- PyYAML

### Usage

Run the solver from the project root:

```bash
python src/main.py
```

The interactive menu will prompt you to:

1. **Choose puzzle input method**:
   - Load from a text file (comma-separated values, 0 for blank cells) - the last used puzzle can be loaded from here
   - Enter a new puzzle manually row by row - you will be asked to provide a filename to save the puzzle to

2. **Choose solving method**:
   - Strategy-based solver (logical deduction)
   - Backtracking solver (brute force)

### Puzzle File Format

Puzzle files are plain text with 9 rows of comma-separated integers:
- Values 1-9 represent given clues
- Value 0 represents an empty cell

Example:
```
5,3,0,0,7,0,0,0,0
6,0,0,1,9,5,0,0,0
0,9,8,0,0,0,0,6,0
8,0,0,0,6,0,0,0,3
4,0,0,8,0,3,0,0,1
7,0,0,0,2,0,0,0,6
0,6,0,0,0,0,2,8,0
0,0,0,4,1,9,0,0,5
0,0,0,0,8,0,0,7,9
```
