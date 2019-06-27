import copy
from .gotypes import Player

class Move():
    """ターン，着手のクラス．打石，パス，投了のいずれか"""
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign # どれかひとつしか受け付けないってこと
        self.point = point
        self.is_play = (self.point is not None) # 打石であるかどうか
        self.is_pass = is_pass
        self.is_resign = is_resign
        
    # classmethod アノテーションでインスタンス化なしで利用可能なメソッドを指定
    @classmethod
    def play(cls, point):
        return Move(point=point)
    
    @classmethod
    def pass_turn(cls):
        return Move(is_pass=True)
    
    @classmethod
    def resign(cls):
        return Move(is_resign=True)


class GoString():
    """石の並び，連のクラス"""
    def __init__(self, color, stones, liberties):
        self.color = color

        # 連を構成する石，および呼吸点はsetとして保持する
        self.stones = set(stones)
        self.liberties = set(liberties)
    
    def remove_liberty(self, point):
        self.liberties.remove(point)
    
    def add_liberty(self, point):
        self.liberties.add(point)
    
    # プレイヤーが石を置いて二つのグループを連結するときに呼び出される
    def merged_with(self, go_string):
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | go_string.liberties) - combined_stones
        )

    @property
    def num_liberties(self):
        return len(self.liberties)
    
    def __eq__(self, other):
        return isinstance(other, GoString) and \
            self.color == other.color and \
            self.stones == other.stoners and \
            self.liberties == other.liberties
    

class Board():
    """石を置くためのルールと取るためのルール"""
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {} # GoStringを格納する辞書

    def place_stone(self, player, point):
        assert self.is_on_grid(point) # 打石点が盤面の範囲内にある
        assert self._grid.get(point) is None # まだその点には打たれていない
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []

        # 打石点の隣接4点について処理を行う
        for neighbor in point.neighbors():

            # 隣接点が盤面の範囲外ならcontinue
            if not self.is_on_grid(neighbor):
                continue
            
            # 隣接点にある連についてしらべる
            neighbor_string = self._grid.get(neighbor)

            # 隣接点に連がなければ，そこにはなにもないので呼吸点として追加する
            if neighbor_string is None:
                liberties.append(neighbor)

            # 隣接点に連があって，playerの色であるとき，敵or自分のadjacentリストに追加
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
                else:
                    if neighbor_string not in adjacent_opposite_color:
                        adjacent_opposite_color.append(neighbor_string)
            
            new_string = GoString(player, [point], liberties)

            # 周囲にある連を全てマージする
            for same_color_string in adjacent_same_color:
                new_string = new_string.merged_with(same_color_string)
            
            # マージした連の石一つ一つのポイントから，新しくできた連にアクセスできるようにする
            for new_string_point in new_string.stones:
                self._grid[new_string_point] = new_string
            
            # 隣接する相手の連から，この石の場所の呼吸点を取り除く
            for other_color_string in adjacent_opposite_color:
                other_color_string.remove_liberty(point)
            
            # 隣接する相手の連の呼吸点が0になったらその連を取り除く
            for other_color_string in adjacent_opposite_color:
                if other_color_string.num_liberties == 0:
                    self._remove_string(other_color_string)

    def _remove_string(self, string):
        # 二重ループ，取り除かれる連の各石 -> その石の隣接点
        for point in string.stones:
            for neighbor in point.neighbors():

                # 石が取り除かれることによる呼吸点の追加
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    # ただし，取り除かれる連：自分自身の呼吸点は追加しない
                    neighbor_string.add_liberty(point)
            
            # 石を取り除く．(石のある点のアクセス先の連をなくす)
            self._grid[point] = None



    # pointが盤面の範囲内に含まれているか
    def is_on_grid(self, point):
        return  1 <= point.row <= self.num_rows and \
                1 <= point.col <= self.num_cols
    
    # 盤面上の点の内容．何もなければNone, 石があればPlayerを返す
    def get(self, point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color
    
    # 盤面上のある点を含む連を返す．何もなければNone
    def get_go_string(self, point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string


class GameState():
    """ゲーム状態: 次のプレイヤー，前のゲーム状態，最後の着手"""
    def __init__(self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous = previous
        self.move = move
    
    def apply_move(self, move):
        # 着手が打石ならば，石を置いたときの盤面の変化を計算
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            # パスや投了ならそのまま
            next_board = self.board
        
        # 新しいゲーム状態を返す
        return GameState(next_board, self.next_player.other, self, move)
    
    @classmethod
    def new_game(cls, board_size):
        """ ゲームの初期化 """
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)
    
    def is_over(self):
        """ 終局判定 """
        # last_moveが未定義(打石した)なら続行
        if self.last_move is None:
            return False
        
        # どちらかが投了していたら終局
        if self.last_move.is_resign:
            return True
        
        # 連続でパスされていなければ(前の前の手が打石なら，片方がパスしてても)続行
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        
        # 連続でパスされていれば終局，そうでなければ続行
        return self.last_move.is_pass and second_last_move.is_pass
    
    def is_move_self_capture(self, player, move):
        """ 自殺手(自らのある連の呼吸点を全て潰す手)かどうか """
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)

        # 一旦打ってみて，その打った手によってできる連の呼吸点が0かを返す
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0
    
    @property
    def situation(self):
        return (self.next_player, self.board)
    
    def does_move_violate_ko(self, player, move):
        if not move.is_play:
            return False
        
        # 新しい打石があるたびに
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board)
        past_state = self.previous_state

        # 過去の全ての盤を遡り，同じ盤面にならないかを調べる(遅いので後で改良)
        while past_state is not None:
            if past_state.situation == next_situation:
                return True
            past_state = past_state.previous_state

        # 過去に同じ盤面が存在しないなら劫に違反していない
        return False

    def is_valid_move(self, move):
        # すでに終局しているなら次の着手はない
        if self.is_over():
            return False
        
        # 終局していないなら，パス，もしくは投了を選択することができる
        if move.is_pass or move.is_resign:
            return True
        
        # 打石の場合は，盤面内への打石で，自殺手でも劫でもないことが必要
        return (
            self.board.get(move.point) is None and
            not self.is_move_self_capture(self.next_player, move) and
            not self.does_move_violate_ko(self.next_player, move)
        )
    
    