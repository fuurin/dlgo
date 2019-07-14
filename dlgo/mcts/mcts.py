import random, math
from dlgo.gotypes import Player
from dlgo.agent.base import Agent
from dlgo.agent.naive_fast import FastRandomBot

class MCTSNode(object):
    def __init__(self, game_state, parent=None, move=None):
        self.game_state = game_state # 現在のゲーム状態
        self.parent = parent # 親のMCTSNode, NoneならRoot
        self.move = move # このノードに繋がった直前の着手

        # このノードから開始しtあロールアウトに関する統計情報
        self.win_counts = {
            Player.black: 0,
            Player.white: 0,
        }
        self.num_rollouts = 0

        # 全ての子のノードのリスト
        self.children = []

        # まだ木に追加されていない，この局面から伸びる全ての合法手のリスト
        self.unvisited_moves = game_state.legal_moves()

    def add_random_child(self):
        """
        新しい子をランダムに選び，木に追加する
        """
        index = random.randint(0, len(self.unvisited_moves) - 1)
        new_move = self.unvisited_moves.pop(index)
        new_game_state = self.game_state.apply_move(new_move)
        new_node = MCTSNode(new_game_state, self, new_move)
        self.children.append(new_node)
        return new_node
    
    def record_win(self, winner):
        """
        ロールアウトの統計を更新
        """
        self.win_counts[winner] += 1
        self.num_rollouts += 1
    
    def can_add_child(self):
        """
        この局面にまだ木に追加されていない合法手があるかどうかを返す
        """
        return len(self.unvisited_moves) > 0
    
    def is_terminal(self):
        """
        このノードでゲームが終了したかどうかを返す
        """
        return self.game_state.is_over()
    
    def winning_pct(self, player):
        """
        特定のプレイヤーが勝ったロールアウトの割合を返す
        """
        return float(self.win_counts[player]) / float(self.num_rollouts)
    
class MCTSAgent(Agent):
    def __init__(self, num_rounds, temperature):
        self.num_rounds = num_rounds
        self.temperature = temperature

    def select_move(self, game_state):
        """
        MCTSによって最善の枝(手)を選択する
        """

        # 現在のゲーム状態を根とする新しい木を生成
        root = MCTSNode(game_state)

        # 固定数の幅を持つ木を作る(固定数の時間でも良い)
        for i in range(self.num_rounds):
            node = root

            # 合法手が存在し，かつゲームが終了していないノードを見つける
            while (not node.can_add_child()) and \
                  (not node.is_terminal()):

                # UCTスコアに応じて次に探索を行うノードが選ばれる
                node = self.select_child(node)

            # そのノードに，ランダムに新たなノードを追加する
            if node.can_add_child():
                node = node.add_random_child()

            # その手を行なった時に勝利するプレイヤーを導く
            winner = self.simulate_random_game(node.game_state)

            # 木を辿り，スコアを伝播させる
            while node is not None:
                node.record_win(winner)
                node = node.parent

        # シミュレーションを行なった手の中から，最大の勝率を持つ手を選び，返す        
        best_move = None
        best_pct = -1.0
        for child in root.children:
            child_pct = child.winning_pct(game_state.next_player)
            if child_pct > best_pct:
                best_pct = child_pct
                best_move = child.move
        return best_move
    
    def select_child(self, node):
        """
        最大のUTCスコアを持つノードを返す
        次に探索を行うノードを選ぶのに使う
        """
        total_rollouts = sum(child.num_rollouts for child in node.children)
        best_score = -1
        best_child = None
        for child in node.children:
            score = self.uct_score(
                total_rollouts,
                child.num_rollouts,
                child.winning_pct(node.game_state.next_player),
                self.temperature
            )
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    @staticmethod
    def uct_score(parent_rollouts, child_rollouts, win_pct, temperature):
        exploration = math.sqrt(math.log(parent_rollouts) / child_rollouts)
        return win_pct + temperature * exploration

    @staticmethod
    def simulate_random_game(game):
        """
        このノードからロールアウトを開始
        is_over終了まで待つと異常に時間がかかるだろう
        winnerも内部で使っているcompute_game_resultが未実装なので動かない
        """
        bots = {
            Player.black: FastRandomBot(),
            Player.white: FastRandomBot(),
        }

        while not game.is_over():
            bot_move = bots[game.next_player].select_move(game)
            game = game.apply_move(bot_move)
        
        return game.winner()