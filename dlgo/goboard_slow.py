import copy
from .gotypes import Player

class Move():
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign # どれかひとつしか受け付けないってこと
        self.point = point
        self.is_play = (self.point is not None)
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
    def __init__(self, color, stones, liberties):
        self.color = color
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
            
            # 
            for other_color_string in adjacent_opposite_color:
                other_color_string.remove_liberty(point)
            


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
    
    # 盤面上のある点を含む連全体(GoString)を返す．何もなければNone
    def get_go_string(self, point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string
