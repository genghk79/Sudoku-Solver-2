import logging
import general_utils
import sys
import time
import os
from board_utils import SudokuBoard

logger = logging.getLogger(__name__)
general_utils.setup_logging()

class Backtrack():
    """
    Applies the backtracking algorithm to solve the puzzle
    """
    def __init__(self, board: SudokuBoard):
        """
        Initialise the solver

        Args:
            board (SudokuBoard): SudokuBoard object containing the puzzle to be solved
        """
        self.board = board
        self.history = []

    def forward_fill(self):
        """
        Fill the next empty cell in the board with the first possibility.

        Returns:
            (int, int): row and column numbers of filled cell
        """
        # look from the last filled cell, for the next empty cell
        if len(self.history)==0:
            indx = 0     
        else:
            indx = self.history[-1]['indx'] + 1
        try:
            while self.board.df.iloc[indx]['ans']:
                indx += 1
        except IndexError:
            logger.exception("Cannot forward fill a full board!")
            sys.exit(1)

        # fill the cell with the first possibility, and make a record in the history
        poss_left = list(tuple(self.board.df.iloc[indx]['poss']))
        poss_left.sort(reverse=True)
        ans = poss_left.pop()
        self.history.append({'indx': indx, 'poss_left': poss_left, 'ans': ans})
        self.board.set_cell_bt(indx//9, indx%9, ans)

        return self.board.df.iloc[indx]['row_n'], self.board.df.iloc[indx]['col_n']

    def takeback_n_fill(self):
        """
        Change answer in the latest filled cell to the next possibility.
        If that cell has no more possibilities left, clear the cell and 
        try to change the second latest cell. Keep moving back until a cell
        can be found that has a possibility left that the answer can be changed
        to.

        Returns:
            (int, int): row and column numbers of filled cell
        """
        try:
            # if the last filled cell has no more possibilities left
            # clear it and delete it from history
            while len(self.history[-1]['poss_left'])==0:
                indx = self.history[-1]['indx']
                self.board.set_cell_bt(indx//9, indx%9, None)
                self.history = self.history[:-1]
            # change the last filled cell in history with the next possibility
            indx = self.history[-1]['indx']
            ans = self.history[-1]['poss_left'].pop()
            self.history[-1]['ans'] = ans
            self.board.set_cell_bt(indx//9, indx%9, ans)

            return self.board.df.iloc[indx]['row_n'], self.board.df.iloc[indx]['col_n']
        except IndexError:
            logger.exception("Takeback hit an empty history!")
            sys.exit(1)

    @staticmethod
    def num_poss(board: SudokuBoard):
        """
        Calculate the number of possible combinations left on the current board

        Args:
            board (SudokuBoard): the current board

        Returns:
            int: number of possible combinations left on the current board
        """
        poss_count = 1
        A = board.df.loc[board.df['ans'].isna(), 'poss']
        for indx in range(len(A)):
            poss_count *= len(A.iloc[indx])
        return poss_count

    @staticmethod
    def clear_screen():
        """
        Clear the terminal screen
        """
        # 'nt' refers to Windows
        if os.name == 'nt':
            _ = os.system('cls')
        # 'posix' refers to Linux, macOS, and other Unix-like systems
        else:
            _ = os.system('clear')


    def solve(self):
        """
        Solve the board by running the backtracking algorithm.
        """
        A = self.board.df.loc[self.board.df['ans'].isna()]
        last_indx = A.index[-1]
        
        print()
        print("Note that this can take a long time to reach a solution.") 
        print()
        input("You may use ctrl+C to kill the process at any time. Hit Enter to continue.")
        poss_count = 0
        scan_speed = 0
        start_time = time.time()
        logger.info("Backtracking solver started")
        while not self.board.puzzle_completed():
            self.clear_screen()
            print('-' * 20)
            print("Current board status")
            print('-' * 20)
            self.board.show_puzzle()
            print()
            logger.info(f"Estimated scan speed: {int(scan_speed)} sec / (thousand possibilities)")
            logger.info(f"Current board has {self.num_poss(self.board)//1000:,} thousand possibilities left")
            print()
            
            row_n, col_n = self.forward_fill()
            # as long as the forward fill does not complete the board or produce 
            # an error, keep forward filling
            while (not self.board.check4errors(row_n, col_n)) & \
                (self.board.df.iloc[last_indx]['ans']==None):
                row_n, col_n = self.forward_fill()
                logger.info(f"Forward filled ({row_n}, {col_n})")
                poss_count += 1 
                if poss_count%1000==0:
                    scan_speed = (time.time()-start_time)/(poss_count/1000)

            # as long as the cell still causes an error, take a backtrack step
            while self.board.check4errors(row_n, col_n):
                row_n, col_n = self.takeback_n_fill()
                logger.info(f"Took back and filled ({row_n}, {col_n})")
                poss_count += 1
                if poss_count%1000==0:
                    scan_speed = (time.time()-start_time)/(poss_count/1000)

        print()
        print('-' * 20)
        print("Completed board")
        print('-' * 20)
        self.board.show_puzzle()
        print()
        logger.info(f"Managed to find the solution in {poss_count//1000:,} scans and {time.time()-start_time} sec!")
