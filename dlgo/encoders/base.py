import importlib

class Encoder():
    def name(self):
        """ ログ, 保存 """
        raise NotImplementedError()
    
    def encode(self, game_state):
        """ 盤面->数値データ """
        raise NotImplementedError()
    
    def encode_point(self, point):
        """ 盤上の点->整数インデックス """
        raise NotImplementedError()
    
    def decode_point_index(self, index):
        """ 整数インデックス->盤上の点 """
        raise NotImplementedError()
    
    def num_points(self):
        """ 盤上の点の数(盤の幅*高さ) """
        raise NotImplementedError()
    
    def shape(self):
        """ エンコードされた盤面の構造の形状 """
        raise NotImplementedError()


def get_encoder_by_name(name, board_size):
    """ 色々エンコーダを作るので，importではなく文字列で取得したい """
    if isinstance(board_size, int):
        board_size = (board_size, board_size)
    module = importlib.import_module("dlgo.encoders." + name)
    constructor = getattr(module, 'create')
    return constructor(board_size)