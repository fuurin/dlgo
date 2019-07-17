import numpy as np

from dlgo.encoders.base import Encoder
from dlgo.goboard import Move, Point


class SevenPlaneEncoder(Encoder):
    """
    盤面を7チャンネルにエンコード
    基本的には，呼吸点の数ごとにチャンネルを分ける
    """

    def __init__(self, board_size):
        self.board_width, self.board_height = board_size
        self.num_planes = 7

    def name(self):
        return 'sevenplane'

    def encode(self, game_state):
        # 空箱
        board_tensor = np.zeros(self.shape())

        # 白は0,1,2黒は3,4,5を使うためにズラすとき使う
        base_plane = {
            game_state.next_player: 0,
            game_state.next_player.other: 3
        }

        # 全ての盤上の点を探索
        for row in range(self.board_height):
            for col in range(self.board_width):

                p = Point(row=row+1, col=col+1)
                go_string = game_state.board.get_go_string(p)

                # 石が置かれていない点は劫かどうかだけ調べればよい
                if go_string is None:
                    if game_state.does_move_violate_ko(game_state.next_player, Move.play(p)):
                        board_tensor[6][row][col] = 1
                else:
                    # 呼吸点が3以上か，2か，1か
                    liberty_plane = min(3, go_string.num_liberties) - 1
                    liberty_plane += base_plane[go_string.color]
                    board_tensor[liberty_plane][row][col] = 1

        return board_tensor

    def encode_point(self, point):
        return self.board_width * (point.row - 1) + (point.col - 1)

    def decode_point_index(self, index):
        row = index // self.board_height
        col = index % self.boad_width
        return Point(row=row+1, col=col+1)

    def num_points(self):
        return self.board_width * self.board_height

    def shape(self):
        return (self.num_planes, self.board_height, self.board_width)


def create(board_size):
    return SevenPlaneEncoder(board_size)
