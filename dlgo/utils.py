import numpy as np
from dlgo import gotypes

COLS = 'ABCDEFGHIJKLMNOPQRST'
STONE_TO_CHAR = {
    None: '+',
    gotypes.Player.black: 'x',
    gotypes.Player.white: 'o',
}


def print_move(player, move):
    """ 着手の内容を表示．打石は 'black C3' のように表示 """
    if move.is_pass:
        move_str = 'passes'
    elif move.is_resign:
        move_str = 'resigns'
    else:
        move_str = '%s%d' % (COLS[move.point.col - 1], move.point.row)
    print('%s %s' % (player, move_str))


def print_board(board):
    """ 盤面全体の状況を表示 """
    for row in range(board.num_rows, 0, -1):
        bump = " " if row <= 9 else ""  # 二桁の行番号になったときのための空白
        line = []
        for col in range(1, board.num_cols + 1):
            stone = board.get(gotypes.Point(row=row, col=col))  # 全ての点の打石状況を確認
            line.append(STONE_TO_CHAR[stone])
        print('%s%d %s' % (bump, row, ''.join(line)))  # 空白，行番号，行の石
    print('    ' + ''.join(COLS[:board.num_cols]))  # 列記号，ABCD...


def point_from_coords(coords):
    """ 人間の入力をBoardの座標に変換 ex. C3 -> (3, 3) """
    col = COLS.index(coords[0]) + 1
    row = int(coords[1:])
    return gotypes.Point(row=row, col=col)


# NOTE: MoveAge is only used in chapter 13, and doesn't make it to the main text.
# This feature will only be implemented in goboard_fast.py so as not to confuse
# readers in early chapters.
class MoveAge():
    def __init__(self, board):
        self.move_ages = - np.ones((board.num_rows, board.num_cols))

    def get(self, row, col):
        return self.move_ages[row, col]

    def reset_age(self, point):
        self.move_ages[point.row - 1, point.col - 1] = -1

    def add(self, point):
        self.move_ages[point.row - 1, point.col - 1] = 0

    def increment_all(self):
        self.move_ages[self.move_ages > -1] += 1