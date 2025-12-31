import pandas as pd
import general_utils
import logging 

logger = logging.getLogger(__name__)
general_utils.setup_logging()

class SudokuBoard():
    """
    Represent the state of the Sudoku board
    """
    def __init__(self):
        A = []
        # create a blank Sudoku board dataframe
        for row_n in range(9):
            for col_n in range(9):
                A.append({'row_n': row_n,
                          'col_n': col_n,
                          'sqr_n': 3*(row_n//3) + col_n//3,
                          'poss': set([1,2,3,4,5,6,7,8,9]),
                          'ans': None})
        self.df = pd.DataFrame(A)

    def set_cell(self, row_n: int, col_n: int, ans: int):
        """
        Fill in answer in cell and clear the set of possible values

        Args:
            row_n (int): cell row number (0-8)
            col_n (int): cell column number (0-8)
            ans (int or str): answer to fill in cell

        Raises:
            ValueError: Entries must be between 1 and 9
        """
        try:
            if not ans in {1,2,3,4,5,6,7,8,9,'1','2','3','4','5','6','7','8','9'}:
                raise ValueError
            self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'ans'] = int(ans)
            self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'poss'].values[0].clear()
            self.update_poss(row_n, col_n)
        except ValueError:
            logger.exception("Entries must be between 1 and 9")
        except:
            logger.exception("set_cell error")

    def set_cell_bt(self, row_n: int, col_n: int, ans: int|None):
        """
        Fill in answer without modifying the possibility column. 
        Only used for backtracking solver.

        Args:
            row_n (int): cell row number (0-8)
            col_n (int): cell column number (0-8)
            ans (int | None): answer to fill in cell
        """
        self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'ans'] = ans

    def set_poss(self, row_n: int, col_n: int, poss: set[int]):
        """
        Clear the possibilities and write in a new set. Mainly used for hidden pairs and triplets.

        Args:
            row_n (int): cell row number (0-8)
            col_n (int): cell column number (0-8)
            poss (set[int]): set of possibilities to update cell with
        """
        self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'poss'].values[0].clear()
        for poss_item in poss:
            self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'poss'].values[0].add(poss_item)

    def set_puzzle(self, starting_board: list[list[int]]):
        """
        Setup board according to 9x9 list of list of int provided

        Args:
            starting_board (list[list[int]]): 9x9 array of numbers as list, consisting 9 lists of 9 numbers.
                                            Use 0 to denote a blank cell. i.e. this creates a blank puzzle:
                                            new_puzzle = set_puzzle([[0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0],
                                                                     [0,0,0,0,0,0,0,0,0]])
        """
        A = []
        for row_n in range(9):
            for col_n in range(9):
                A.append({'row_n': row_n,
                          'col_n': col_n,
                          'sqr_n': 3*(row_n//3) + col_n//3,
                          'poss': set([1,2,3,4,5,6,7,8,9]),
                          'ans': None})
        self.df = pd.DataFrame(A)
        try:
            for row_n in range(9):
                for col_n in range(9):
                    if not int(starting_board[row_n][col_n])==0: # 0 are blanks
                        self.set_cell(row_n, col_n, int(starting_board[row_n][col_n]))
        except IndexError:
            logger.exception("Starting puzzle board must be a 9x9 list[list[int]]")
        except:
            logger.exception("set_puzzle error")

    def rm_poss(self, row_n: int, col_n: int, poss_to_rm: int):
        """
        Remove specified value from set of possibilities in cell

        Args:
            row_n (int): cell row number (0-8)
            col_n (int): cell column number (0-8)
            poss_to_rm (int): value to remove from set of possibilities
        """
        self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'poss'].values[0].discard(poss_to_rm)

    def load_puzzle(self, filename: str):
        """
        Load a Sudoku board from a txt file with 9x9 integers separated by commas.
        Use 0 to denote a blank.

        Args:
            filename (str): txt file name to load from
        """
        A = []
        try:
            with open(filename) as f:
                for _ in range(9):
                    line = f.readline().rstrip('\n').split(',')
                    A.append(line)
            self.set_puzzle(A)
            logger.info(f"board loaded from {filename}")
        except:
            logger.exception("load_puzzle error")
            raise Exception

    def save_puzzle(self, filename: str):
        """
        Save current state of the board to a txt file with 9x9 integer separated by commas

        Args:
            filename (str): txt file name to save to
        """
        try:
            with open(filename, 'w') as f:
                for row_n in range(9):
                    for col_n in range(9):
                        ans = self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'ans'].values[0]
                        if ans:
                            f.write(str(ans))
                        else:
                            f.write('0')
                        if col_n<8:
                            f.write(',')
                    if row_n<8:
                        f.write('\n')
            logger.info(f"board saved to {filename}")
        except:
            logger.exception("save_puzzle error")

    def update_poss(self, row_n: int, col_n: int):
        """
        Check answers entered in the cell, and remove that 
        value from set of possibilities in the row/col/sqr

        Args:
            row_n (int): cell row number (0-8)
            col_n (int): cell column number (0-8)
        """
        ans = self.df.loc[(self.df['row_n']==row_n)&(self.df['col_n']==col_n), 'ans'].values[0]
        # update row
        for col in range(9):
            self.rm_poss(row_n, col, ans)
        # update column
        for row in range(9):
            self.rm_poss(row, col_n, ans)
        # update square
        A = self.df.loc[self.df['sqr_n']==3*(row_n//3) + col_n//3]
        for indx in A.index:
            self.rm_poss(self.df.iloc[indx]['row_n'], self.df.iloc[indx]['col_n'], ans)

    def check4errors(self, row_n: int, col_n: int):
        """
        Check to make sure that there are no repeated answers w.r.t. a specific cell,
        i.e. in the row/col/sqr corresponding to that cell

        Args:
            row_n (int): row number of the cell in question
            col_n (int): column number of the cell in question

        Returns:
            bool: True if an error is found
        """
        A = self.df.loc[self.df['row_n']==row_n, 'ans']
        if any(A.value_counts()>1):
            return True
        A = self.df.loc[self.df['col_n']==col_n, 'ans']
        if any(A.value_counts()>1):
            return True
        A = self.df.loc[self.df['sqr_n']==3*(row_n//3) + col_n//3, 'ans']
        if any(A.value_counts()>1):
            return True
        return False

    def check4errors_full(self):
        """
        Check to make sure there are no repeated answers in each row/col/sqr

        Returns:
            bool: True if an error is found
        """
        # scan row by row
        for row_n in range(9):
            A = self.df.loc[self.df['row_n']==row_n, 'ans']
            if any(A.value_counts()>1):
                logger.info(f"Error in row {row_n}!")
                return True
            
        # scan column by column
        for col_n in range(9):
            A = self.df.loc[self.df['col_n']==col_n, 'ans']
            if any(A.value_counts()>1):
                logger.info(f"Error in column {col_n}!")
                return True
            
        # scan square by square
        for sqr_n in range(9):
            A = self.df.loc[self.df['sqr_n']==sqr_n, 'ans']
            if any(A.value_counts()>1):
                logger.info(f"Error in square {sqr_n}!")
                return True
        
        # check that cells with no answers should have possibilities left
        for cell_n in range(81):
            if (self.df.iloc[cell_n]['poss']==set()) & (self.df.iloc[cell_n]['ans']==None):
                logger.info(f"No possible answer left in row {cell_n//9}, column {cell_n%9})")
                return True
        return False
    
    def show_puzzle(self):
        """
        Display the current board state in txt form
        """
        for row_n in range(9):
            for col_n in range(9):
                ans = self.df.loc[(self.df['row_n']==row_n) & (self.df['col_n']==col_n), 'ans'].values[0]
                if not ans:
                    print(".", end=' ')
                else:
                    print(f"{ans}", end=' ')

                if col_n == 2 or col_n == 5:
                    print("|", end=' ')
                elif col_n == 8:
                    print("")
            if row_n == 2 or row_n == 5:
                print("---------------------")
            
    def puzzle_completed(self):
        """
        Check if puzzle is completed

        Returns:
            bool: True if all cells have answers entered, and there are no repeats in any row/col/sqr
        """
        logger.info("Checking puzzle completion...")
        return (not any(self.df['ans'].isna())) & (not self.check4errors_full()) 