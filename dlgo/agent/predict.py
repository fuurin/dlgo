import numpy as np
from dlgo.agent.base import Agent
from dlgo.agent.helpers import is_point_an_eye
from dlgo import encoders
from dlgo import goboard
from dlgo import kerasutil


class DeepLearningAgent(Agent):
    """
    深層学習によるmodelとencoderからなる着手エージェント
    """

    def __init__(self, model, encoder):
        Agent.__init__(self)
        self.model = model
        self.encoder = encoder

    def predict(self, game_state):
        encoded_state = self.encoder.encode(game_state)
        input_tensor = np.array([encoded_state])
        return self.model.predict(input_tensor)[0]

    def select_move(self, game_state):
        num_moves = self.encoder.board_width * self.encoder.board_height
        move_probs = self.predict(game_state)

        # 可能性の高い着手と低い着手の距離を広げる
        move_probs = move_probs ** 3

        # (0, 1)の範囲に正規化
        eps = 1e-6
        move_probs = np.clip(move_probs, eps, 1 - eps)
        move_probs = move_probs / np.sum(move_probs)  # 確率分布にする

        # 着手先のインデックス
        candidates = np.arange(num_moves)

        # 作った確率分布を元に, 19*19個の候補を非復元抽出
        # つまり確率分布に従うランキングを作る
        ranked_moves = np.random.choice(
            candidates, num_moves, replace=False, p=move_probs
        )

        # ランキングの上位から調べていき，合法手を選んで打つ
        for point_idx in ranked_moves:
            point = self.encoder.decode_point_index(point_idx)
            if game_state.is_valid_move(goboard.Move.play(point)):
                if not is_point_an_eye(game_state.board, point, game_state.next_player):
                    return goboard.Move.play(point)

        # 合法手がなければパス
        return goboard.Move.pass_turn()

    def serialize(self, h5file):
        h5file.create_group('encoder')
        h5file['encoder'].attrs['name'] = self.encoder_name()
        h5file['encoder'].attrs['baord_width'] = self.encoder.board_width
        h5file['encoder'].attrs['baord_height'] = self.encoder.board_height
        h5file.create_group('model')
        kerasutil.save_model_to_hdf5_group(self.model, h5file['model'])


def load_prediction_agent(h5file):
    model = kerasutil.load_model_from_hdf5_group(h5file['model'])
    encoder_name = h5file['encoder'].attrs['name']
    if not isinstance(encoder_name, str):
        encoder_name = encoder_name.decode('ascii')
    board_width = h5file['encoder'].attrs['board_width']
    board_height = h5file['encoder'].attrs['board_height']
    encoder = encoders.get_encoder_by_name(
        encoder_name, (board_width, board_height)
    )
    return DeepLearningAgent(model, encoder)
