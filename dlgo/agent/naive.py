import random
from dlgo.agent.base import Agent
from dlgo.agent.helpers import is_point_an_eye
from dlgo.goboard_slow import Move
from dlgo.gotypes import Point


class RandomBot(Agent):
    def select_move(self, game_state):
        """
            眼をつぶさないように，あとは禁じ手にならなければランダム.
            考えうる限り最弱のボット，30級程度
        """
        candidates = []
        for r in range(1, game_state.board.num_rows + 1):
            for c in range(1, game_state.board.num_cols + 1):
                candidate = Point(row=r, col=c)
                # 自殺手，劫なら次の手の候補ではない
                if not game_state.is_valid_move(Move.play(candidate)):
                    continue
                # 眼になっているところなら次の手の候補ではない
                if is_point_an_eye(game_state.board, candidate, game_state.next_player):
                    continue
                # 候補として追加
                candidates.append(candidate)

        # 打てるところが無ければパス
        if not candidates:
            return Move.pass_turn()

        move = Move.play(random.choice(candidates))
        return move
