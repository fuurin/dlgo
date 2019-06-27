class Agent():
    """ 全てのボットのインタフェース """
    def __init__(self):
        pass
    
    def select_move(self, game_state):
        raise NotImplementedError()