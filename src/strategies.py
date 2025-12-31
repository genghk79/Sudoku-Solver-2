import functools
import logging
import general_utils
import pandas as pd
import time
from board_utils import SudokuBoard

logger = logging.getLogger(__name__)
general_utils.setup_logging()

def track_change(attr_name='board'):
    """
    Decorator to check if wrapped method has made a change to the board.

    Args:
        attr_name (_type_): the SudokuBoard object to be tracked, defaults to 'board'
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # save the possibilities in tuples to make the immutable
            board_obj = getattr(self, attr_name)
            old_state = list(zip(board_obj.df['ans'], 
                                 [tuple(p) for p in board_obj.df['poss']]))

            func(self, *args, **kwargs)

            new_state = list(zip(board_obj.df['ans'], 
                                 [tuple(p) for p in board_obj.df['poss']]))

            # note any differences
            diff_indices = [i for i in range(81) if old_state[i] != new_state[i]]
            return len(diff_indices)>0
            
        return wrapper
    return decorator

class SudokuStrats():
    """
    Applies strategies as described in www.sudoku.com to solve the puzzle
    """
    def __init__(self, board: SudokuBoard):
        """
        Initialise the solver

        Args:
            board (SudokuBoard): SudokuBoard object containing the puzzle to be solved
        """
        self.board = board

    def make_entry(self, row_n: int, col_n: int, ans: int):
        """
        Enter an answer to a cell, update the sets of possibilities affected, and check for errors

        Args:
            row_n (int): cell row number (0-8)
            col_n (int): cell column number (0-8)
            ans (int): answer to be entered to cell

        Raises:
            RuntimeError: answer entered is wrong
        """
        try:
            self.board.set_cell(row_n, col_n, ans)
            if self.board.check4errors(row_n, col_n):
                raise RuntimeError
        except RuntimeError:
            logger.exception(f"Entry at row {row_n}, col {col_n} has caused error.")
        
    @staticmethod
    def find_cell_with_poss(df: pd.DataFrame, poss: list[int]):
        """
        Find the cells in the given row/col/sqr that contain the given possibility

        Args:
            df (pd.DataFrame): row/col/sqr extracted from the board
            poss (int): possibility to find

        Returns:
            list[int]: list of cell indices that contain the possibility
        """
        indx = []
        for n in range(9):
            if poss in df.iloc[n]['poss']:
                indx.append(df.index[n])
        return indx

    @track_change()
    def obvious_singles(self):
        """
        If a cell has only one possibility left, enter it as answer
        """
        A = self.board.df.loc[self.board.df['poss'].apply(len)==1]
        for indx in A.index:
            row_n = self.board.df.iloc[indx]['row_n']
            col_n = self.board.df.iloc[indx]['col_n']
            ans = list(self.board.df.iloc[indx]['poss'])[0]
            self.make_entry(row_n, col_n, ans)
            logger.info(f"obvious single, filled in ans: {ans}, in cell ({row_n}, {col_n})")

    def hidden_singles(self, df: pd.DataFrame):
        """
        If any possibility only exist in one cell of a row/col/sqr, enter it as answer

        Args:
            df (pd.DataFrame): row/col/sqr extracted from the board
        """
        # compile list of all possibilities along row/col/sqr, with repeats
        all_poss = []
        for indx in range(9):
            all_poss.extend(list(df.iloc[indx]['poss']))
        # if any possibility only shows up only once, find that cell and enter answer
        for poss in set(all_poss):
            if all_poss.count(poss) == 1:
                indx = self.find_cell_with_poss(df, poss)[0]
                row_n = self.board.df.iloc[indx]['row_n']
                col_n = self.board.df.iloc[indx]['col_n']
                self.make_entry(row_n, col_n, poss)
                logger.info(f"hidden single, filled in ans: {poss}, in cell ({row_n}, {col_n})")

    @track_change()
    def hidden_singles_scan(self):
        """
        Scan for hidden singles.
        """
        # scan row by row
        for row_n in range(9):
            self.hidden_singles(self.board.df.loc[self.board.df['row_n']==row_n])    
        # scan column by column
        for col_n in range(9):
            self.hidden_singles(self.board.df.loc[self.board.df['col_n']==col_n])
        # scan square by square
        for sqr_n in range(9):
            self.hidden_singles(self.board.df.loc[self.board.df['sqr_n']==sqr_n])
    
    def obvious_pairs(self, df:pd.DataFrame, indx_0: int):
        """
        If any cell further down in the given row/col/sqr has the identical two possibilities 
        as the indicated cell, remove these possibilities from other cells in the row/col/sqr.

        Args:
            df (pd.DataFrame): row/col/sqr extracted from the board
            indx_0 (int): index of reference cell
        """
        poss_set = df.loc[df.index==indx_0, 'poss'].values[0]
        for indx in df.index:
            # since we're scanning the cells in order, there's no need to check earlier cells
            if indx<=indx_0:
                continue
            # if there is a match, clear these two possibilities from
            # other cells in the row/col/sqr
            if df.loc[df.index==indx, 'poss'].values[0]==poss_set:
                for indx_1 in df.index:
                    if (indx_1==indx_0)|(indx_1==indx):
                        continue
                    for poss in poss_set:
                        self.board.rm_poss(self.board.df.iloc[indx_1]['row_n'],
                                           self.board.df.iloc[indx_1]['col_n'],
                                           poss)
                logger.info(f"obvious pair {poss_set} found in cells ({self.board.df.iloc[indx_0]['row_n']}, {self.board.df.iloc[indx_0]['col_n']}) & ({self.board.df.iloc[indx]['row_n']}, {self.board.df.iloc[indx]['col_n']})")
                break

    @track_change()
    def obvious_pairs_scan(self):
        """
        Scan for obvious pairs.
        """
        # Find the cells with only two possibilities, then look 
        # down the row/col/sqr for a matching cell
        A = self.board.df.loc[self.board.df['poss'].apply(len)==2]
        for indx in A.index:
            # scan down the row
            row_n = self.board.df.iloc[indx]['row_n']
            self.obvious_pairs(self.board.df.loc[self.board.df['row_n']==row_n], indx)
            # scan down the column
            col_n = self.board.df.iloc[indx]['col_n']
            self.obvious_pairs(self.board.df.loc[self.board.df['col_n']==col_n], indx)
            # scan down the square (row first then column)
            sqr_n = self.board.df.iloc[indx]['sqr_n']
            self.obvious_pairs(self.board.df.loc[self.board.df['sqr_n']==sqr_n], indx)

    def hidden_pairs(self, df: pd.DataFrame):
        """
        If on any row/col/sqr, there are two possibilities that exist only in two cells,
        all other possibilities in those cells can be removed.

        Args:
            df (pd.DataFrame): row/col/sqr extracted from the board
        """
        # compile list of all possibilities along row/col/sqr, with repeats
        all_poss = []
        for indx in range(9):
            all_poss.extend(list(df.iloc[indx]['poss']))
        # if any possibility only shows up twice, check if they are in the same two cells
        all_poss_iter = list(set(all_poss))
        for n, poss in enumerate(all_poss_iter):
            if all_poss.count(poss) == 2:
                for poss_1 in all_poss_iter[n+1:]:
                    if all_poss.count(poss_1) == 2:
                        indices = self.find_cell_with_poss(df, poss)
                        # if it's the same two cells, clear all other possibilities from those cells
                        if indices==self.find_cell_with_poss(df, poss_1):
                            for indx in indices:
                                self.board.set_poss(self.board.df.iloc[indx]['row_n'],
                                                    self.board.df.iloc[indx]['col_n'],
                                                    set([poss, poss_1]))
                            logger.info(f"hidden pair {set([poss, poss_1])} found in cells ({self.board.df.iloc[indices[0]]['row_n']}, {self.board.df.iloc[indices[0]]['col_n']}) & ({self.board.df.iloc[indices[1]]['row_n']}, {self.board.df.iloc[indices[1]]['col_n']})")

    @track_change()
    def hidden_pairs_scan(self):
        """
        Scan for hidden pairs
        """
        # scan row by row
        for row_n in range(9):
            self.hidden_pairs(self.board.df.loc[self.board.df['row_n']==row_n])
        # scan column by column
        for col_n in range(9):
            self.hidden_pairs(self.board.df.loc[self.board.df['col_n']==col_n])
        # scan square by square
        for sqr_n in range(9):
            self.hidden_pairs(self.board.df.loc[self.board.df['sqr_n']==sqr_n])

    def obvious_triplets(self, df: pd.DataFrame):
        """
        If any set of three possibilities make up the only possibilities in three cells in a row/col/sqr,
        remove these possibilities from other cells in the row/col/sqr

        Args:
            df (pd.DataFrame): row/col/sqr extracted from the board
        """
        A = df[(df['poss'].apply(len)==3)|(df['poss'].apply(len)==2)]
        if len(A)>=3:
            # scan through groups of 3 cells
            for indx_1 in range(len(A)):
                for indx_2 in range(indx_1+1,len(A)):
                    for indx_3 in range(indx_2+1,len(A)):
                        # if the group of 3 cells together has only 3 possibilities, they are an obvious triplet
                        poss_union = A.iloc[indx_1]['poss']|A.iloc[indx_2]['poss']|A.iloc[indx_3]['poss']
                        if len(poss_union)==3:
                            for indx in df.index:
                                # clear those 3 possibilities from all other cells
                                if indx in set([A.index[indx_1], A.index[indx_2], A.index[indx_3]]):
                                    continue
                                for poss_to_rm in poss_union:
                                    self.board.rm_poss(self.board.df.iloc[indx]['row_n'], 
                                                       self.board.df.iloc[indx]['col_n'], poss_to_rm)
                            logger.info(f"obvious triplets {poss_union} found in cells ({self.board.df.iloc[indx_1]['row_n']}, {self.board.df.iloc[indx_1]['col_n']}) & ({self.board.df.iloc[indx_2]['row_n']}, {self.board.df.iloc[indx_2]['col_n']}) & ({self.board.df.iloc[indx_3]['row_n']}, {self.board.df.iloc[indx_3]['col_n']})")

    @track_change()
    def obvious_triplets_scan(self):
        """
        Scan for obvious triplets
        """
        # scan row by row
        for row_n in range(9):
            self.obvious_triplets(self.board.df.loc[self.board.df['row_n']==row_n])
        # scan column by column
        for col_n in range(9):
            self.obvious_triplets(self.board.df.loc[self.board.df['col_n']==col_n])
        # scan square by square
        for sqr_n in range(9):
            self.obvious_triplets(self.board.df.loc[self.board.df['sqr_n']==sqr_n])

    def hidden_triplets(self, df: pd.DataFrame):
        """
        If on any row/col/sqr, there are three possibilities that exist only in three cells,
        all other possibilities in those cells can be removed.

        Args:
            df (pd.DataFrame): row/col/sqr extracted from the board
        """
        # compile list of all possibilities along row/col/sqr, with repeats
        all_poss = []
        for indx in range(9):
            all_poss.extend(list(df.iloc[indx]['poss']))
        # look for three possibilities that show up only twice or trice, and
        # check if they come from a set of three cells
        all_poss_iter = list(set(all_poss))
        for n_1, poss_1 in enumerate(all_poss_iter):
            if (all_poss.count(poss_1) == 2)|(all_poss.count(poss_1) == 3):
                for n_2, poss_2 in enumerate(all_poss_iter[n_1+1:]):
                    if (all_poss.count(poss_2) == 2)|(all_poss.count(poss_2) == 3):
                        for poss_3 in all_poss_iter[n_1+n_2+2:]:
                            if (all_poss.count(poss_3) == 2)|(all_poss.count(poss_3) == 3):
                                indices_1 = self.find_cell_with_poss(df, poss_1)
                                indices_2 = self.find_cell_with_poss(df, poss_2)
                                indices_3 = self.find_cell_with_poss(df, poss_3)
                                indices = [set(indices_1+indices_2+indices_3)]
                                # if yes, they are a hidden triplet
                                if len(indices)==3:
                                    for indx in indices:
                                        original_poss = self.board.df.iloc[indx]['poss']
                                        self.board.set_poss(self.board.df.iloc[indx]['row_n'],
                                                            self.board.df.iloc[indx]['col_n'],
                                                            set([poss_1, poss_2, poss_3]) & original_poss)
                                    logger.info(f"obvious triplets {set([poss_1, poss_2, poss_3])} found in cells ({self.board.df.iloc[indices[0]]['row_n']}, {self.board.df.iloc[indices[0]]['col_n']}) & ({self.board.df.iloc[indices[1]]['row_n']}, {self.board.df.iloc[indices[1]]['col_n']}) & ({self.board.df.iloc[indices[2]]['row_n']}, {self.board.df.iloc[indices[2]]['col_n']})")

    @track_change()
    def hidden_triplets_scan(self):
        """
        Scan for hidden triplets
        """
        # scan row by row
        for row_n in range(9):
            self.hidden_triplets(self.board.df.loc[self.board.df['row_n']==row_n])
        # scan column by column
        for col_n in range(9):
            self.hidden_triplets(self.board.df.loc[self.board.df['col_n']==col_n])
        # scan square by square
        for sqr_n in range(9):
            self.hidden_triplets(self.board.df.loc[self.board.df['sqr_n']==sqr_n])

    @track_change()
    def pointing_sets(self):
        """
        If there is a possibility in a row/col that only exists in one sqr, then this possibility cannot
        be anywhere else in that sqr. Similarly, if there is a possibility in a sqr that only exist in
        one row/col, then this possibility cannot be anywhere else along that row/col.
        """
        # scan row by row
        for row_n in range(9):
            A = self.board.df.loc[self.board.df['row_n']==row_n]
            # for each possibilities, compile which square they reside in
            for poss in range(1,10):
                sqrs = []
                for indx in range(9):
                    if poss in A.iloc[indx]['poss']:
                        sqrs.append(A.iloc[indx]['sqr_n'])
                # if they're only in one square, then this possibility cannot be elsewhere in the square
                if len(set(sqrs))==1:
                    B = self.board.df.loc[(self.board.df['sqr_n']==sqrs[0])&
                                          (self.board.df['row_n']!=row_n)]
                    for indx in B.index:
                        self.board.rm_poss(self.board.df.iloc[indx]['row_n'],
                                           self.board.df.iloc[indx]['col_n'],
                                           poss)
                    logger.info(f"Pointing set of {poss} found in row {row_n}, removing {poss} from the set of possibilities from the rest of square {sqrs[0]}")
        # scan column by column
        for col_n in range(9):
            A = self.board.df.loc[self.board.df['col_n']==col_n]
            for poss in range(1,10):
                sqrs = []
                for indx in range(9):
                    if poss in A.iloc[indx]['poss']:
                        sqrs.append(A.iloc[indx]['sqr_n'])
                if len(set(sqrs))==1:
                    B = self.board.df.loc[(self.board.df['sqr_n']==sqrs[0])&
                                          (self.board.df['col_n']!=col_n)]
                    for indx in B.index:
                        self.board.rm_poss(self.board.df.iloc[indx]['row_n'],
                                           self.board.df.iloc[indx]['col_n'],
                                           poss)
                    logger.info(f"Pointing set of {poss} found in column {col_n}, removing {poss} from the set of possibilities from the rest of square {sqrs[0]}")
        # scan square by square
        for sqr_n in range(9):
            A = self.board.df.loc[self.board.df['sqr_n']==sqr_n]
            for poss in range(1,10):
                rows = []
                cols = []
                for indx in range(9):
                    if poss in A.iloc[indx]['poss']:
                        rows.append(A.iloc[indx]['row_n'])
                        cols.append(A.iloc[indx]['col_n'])
                if len(set(rows))==1:
                    B = self.board.df.loc[(self.board.df['row_n']==rows[0])&
                                          (self.board.df['sqr_n']!=sqr_n)]
                    for indx in B.index:
                        self.board.rm_poss(self.board.df.iloc[indx]['row_n'],
                                           self.board.df.iloc[indx]['col_n'],
                                           poss)
                    logger.info(f"Pointing set of {poss} found in square {sqr_n}, removing {poss} from the set of possibilities from the rest of row {rows[0]}")
                if len(set(cols))==1:
                    B = self.board.df.loc[(self.board.df['col_n']==cols[0])&
                                          (self.board.df['sqr_n']!=sqr_n)]
                    for indx in B.index:
                        self.board.rm_poss(self.board.df.iloc[indx]['row_n'],
                                           self.board.df.iloc[indx]['col_n'],
                                           poss)
                    logger.info(f"Pointing set of {poss} found in square {sqr_n}, removing {poss} from the set of possibilities from the rest of column {cols[0]}")
    
    def apply_singles(self):
        """
        Apply the obvious and hidden singles to fill in cells after possibilities have been trimmed.
        """
        print("Applying obvious singles and hidden singles...")
        while self.obvious_singles() or self.hidden_singles_scan():
            pass
        print('-' * 20)
        print("Current board status")
        print('-' * 20)
        self.board.show_puzzle()
        print()

    def solve(self):
        """
        Solve the board by running the various strategies in a loop.
        """
        logger.info("Sudoku strategies solver started")
        print('-' * 20)
        print("Current board status")
        print('-' * 20)
        self.board.show_puzzle()
        print()
        start_time = time.time()

        while True:
            self.apply_singles()
            if self.board.puzzle_completed():
                break

            print("Applying obvious pairs and hidden pairs...")
            self.obvious_pairs_scan()
            self.hidden_pairs_scan()
            self.apply_singles()
            if self.board.puzzle_completed():
                break

            print("Applying obvious triplet and hidden triplets...")
            self.obvious_triplets_scan()
            self.hidden_triplets_scan()
            self.apply_singles()
            if self.board.puzzle_completed():
                break

            print("Applying pointing sets...")
            self.pointing_sets()

        print()
        logger.info(f"Completed in {time.time()-start_time} sec!")


