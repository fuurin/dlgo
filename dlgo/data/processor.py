import os.path
import tarfile, gzip, shutil, glob
import numpy as np
from keras.utils import to_categorical

from dlgo.gosgf.sgf import Sgf_game
from dlgo.goboard_fast import Board, GameState, Move
from dlgo.gotypes import Player, Point
from dlgo.encoders.base import get_encoder_by_name

from dlgo.data.index_processor import KGSIndex
from dlgo.data.sampling import Sampler
from dlgo.data.generator import DataGenerator

DATA_DIRECTORY = "../datasets/dlgo/kgs"

class GoDataProcessor():
    def __init__(self, encoder='oneplane', data_directory=DATA_DIRECTORY):
        self.encoder = get_encoder_by_name(encoder, 19)
        self.data_dir = data_directory
    
    def load_go_data(self, data_type='train', num_samples=1000, download=False):
        """
        棋譜データの読み込み
        
        Parameters
        ----------
        data_type : str
            trainまたはtest
        num_samples : int
            読み込むゲームの数
        download : bool
            データのwebからのダウンロードを行うかどうか
        
        Returns
        -------
        features_and_labels
            [0]: 特徴量のリスト
            [1]: ラベルのリスト
        """

        # 必要なら棋譜データをダウンロード
        if download:
            index = KGSIndex(data_directory=self.data_dir)
            index.download_files()

        # Samplerによって必要数のゲーム数を含む(zipファイル名,ゲームインデックス)のリストを取得
        # なお，Samplerは2014年より前の棋譜か後の棋譜かでtestとtrainを分けている
        sampler = Sampler(data_dir=self.data_dir)
        data = sampler.draw_data(data_type, num_samples)

        # ファイル名のsetと「ファイル名->ゲームインデックスのリスト」となる辞書を作成
        zip_names = set()
        indices_by_zip_name = {}
        for filename, index in data:
            zip_names.add(filename)
            if filename not in indices_by_zip_name:
                indices_by_zip_name[filename] = []
            indices_by_zip_name[filename].append(index)

        # setに入っている必要なtar.gzを，未解凍なら解凍        
        for zip_name in zip_names:
            base_name = zip_name.replace('.tar.gz', '')
            data_file_name = base_name + data_type
            if not os.path.isfile(self.data_dir + '/' + data_file_name):
                self.process_zip(zip_name, data_file_name, indices_by_zip_name[zip_name])
        
        # 必要なデータが分かったので特徴量とラベルを取得する
        features_and_labels = self.consolidate_games(data_type, data)
        return features_and_labels

    def unzip_data(self, zip_file_name):
        """
        .tar.gzを.tarファイルに解凍

        Parameters
        ----------
        zip_file_name : str
            .tar.gz形式のファイル名orパス
        
        Returns
        -------
        tar_file : str
            解凍したtarファイルの名前
        """
        
        # gzipファイルを解凍して内容を取得
        this_gz = gzip.open(self.data_dir + '/' + zip_file_name)

        # 解凍先のtarファイルを作成
        tar_file = zip_file_name[0:-3]
        this_tar = open(self.data_dir + '/' + tar_file, 'wb')

        # gzipファイルの内容をtarファイルに書き込み
        shutil.copyfileobj(this_gz, this_tar)

        # 書き込み完了，解凍先ファイル名を返す
        this_tar.close()
        return tar_file
    
    def process_zip(self, zip_file_name, data_file_name, game_list):
        """
        .tar.gzファイルを解凍し，
        必要なゲームだけ特徴量とラベルに変換して任意の名前で保存
        1024の着手データごとに一つのファイルに保存する
        これにより，動的ロードによるメモリの節約ができる

        Parameters
        ----------
        zip_file_name : str
            解凍対象となるファイルパス
        data_file_name : str
            特徴量とラベルの保存先パス
        game_list : list
            解凍対象から選ばれるゲームのインデックスのリスト
        """

        # ファイルを解凍し，必要な棋譜データの数を取得
        tar_file = self.unzip_data(zip_file_name)
        zip_file = tarfile.open(self.data_dir + '/' + tar_file)
        name_list = zip_file.getnames()
        total_examples = self.num_total_examples(zip_file, game_list, name_list)

        # 空の特徴量とラベルを用意
        shape = self.encoder.shape()
        feature_shape = np.insert(shape, 0, total_examples)
        features = np.zeros(feature_shape)
        labels = np.zeros((total_examples,))

        # 必要な全てのゲームインデックスのゲームを再生しながら記録していく
        counter = 0 # 着手数
        for index in game_list:

            # 対象となるsgfファイルの棋譜データを読み込み
            name = name_list[index+1]
            if not name.endswith('.sgf'):
                raise ValueError(name + ' is not a valid sgf')
            # メンバーをファイルオブジェクトとして抽出
            sgf_content = zip_file.extractfile(name).read()
            sgf = Sgf_game.from_string(sgf_content)

            # ハンディキャップの適用
            game_state, first_move_done = self.get_handicap(sgf)

            # 対局再生
            for item in sgf.main_sequence_iter():
                color, move_tuple = item.get_move()
                # 着手
                if color is not None:
                    # 打石
                    if move_tuple is not None:
                        row, col = move_tuple
                        point = Point(row+1, col+1)
                        move = Move.play(point)
                    # パス
                    else:
                        move = Move.pass_turn()

                    # 初手は盤面が空である．空の盤面はデータに加えない．
                    if first_move_done:
                        # 現在の盤面を特徴量として，
                        features[counter] = self.encoder.encode(game_state)

                        # その盤面に対するこのターンの着手をラベルとして記録
                        labels[counter] = self.encoder.encode_point(point)

                        # 着手数をカウント
                        counter += 1
                    
                    # 着手を適用
                    game_state = game_state.apply_move(move)
                    first_move_done = True
        
        # 保存するファイル名のプレースホルダ
        feature_file_base = self.data_dir + '/' + data_file_name + '_features_%d'
        label_file_base = self.data_dir + '/' + data_file_name + '_labels_%d'

        # 全てのデータを一つに保存するのではなく，chunk_sizeで区切って保存
        chunk = 0
        chunk_size = 1024
        while features.shape[0] >= chunk_size:
            feature_file = feature_file_base % chunk
            label_file = label_file_base % chunk
            chunk += 1
            
            # chunk_sizeでfeaturesとlabelsを区切っていく
            current_features, features = features[:chunk_size], features[chunk_size:]
            current_labels, labels = labels[:chunk_size], labels[chunk_size:]
            
            # 区切ったfeaturesとlabelsを保存
            np.save(feature_file, current_features)
            np.save(label_file, current_labels)

    def num_total_examples(self, zip_file, game_list, name_list):
        """
        .tar.gzファイルで必要となる棋譜の着手の総数を取得

        Parameters
        ----------
        zip_file : str
            .tar.gzファイルのパス
        game_list : list
            必要となる棋譜のインデックスのリスト
        name_list : list
            .tar.gzに入っているファイル名のリスト
        
        Returns
        -------
        total_examples : int
            結果となる着手の総数
        """
        
        total_examples = 0

        # game_listの全ての棋譜インデックスについて着手を回す
        for index in game_list:
            name = name_list[index + 1] # 多分name_list[0]は特殊な何か
            if name.endswith('.sgf'):
                sgf_content = zip_file.extractfile(name).read()
                sgf = Sgf_game.from_string(sgf_content)
                game_state, first_move_done = self.get_handicap(sgf)

                num_moves = 0
                for item in sgf.main_sequence_iter():
                    # 実際に再生は行わず，着手の数だけカウントしていく
                    color, move = item.get_move()
                    if color is not None:
                        if first_move_done:
                            num_moves += 1
                        first_move_done = True
                total_examples = total_examples + num_moves
            else:
                raise ValueError(name + ' is not a valid sgf')
        
        return total_examples
    
    @staticmethod
    def get_handicap(sgf):
        """
        sgfファイルの初期ハンディキャップを適用した盤を返す

        Parameters
        ----------
        sgf : str
            sgfの棋譜データコンテンツ
        
        Returns
        -------
        game_state : GameState
            ハンディキャップ適用後の盤
        first_move_done : bool
            ハンディキャップ適用があったか(盤面が空でないか)
        """
        go_board = Board(19, 19)
        first_move_done = False
        move = None
        game_state = GameState.new_game(19)
        if sgf.get_handicap() != None and sgf.get_handicap() != 0:
            for setup in sgf.get_root().get_setup_stones():
                for move in setup:
                    row, col = move
                    go_board.place_stone(Player.black, Point(row+1, col+1))
            first_move_done = True
            game_state = GameState(go_board, Player.white, None, move)

        return game_state, first_move_done
    
    def consolidate_games(self, data_type, samples):
        """
        process_zipで保存したデータをロードし，一つの大きなセットにして返す

        Parameters
        ----------
        data_type : str
            'train'または'test'
        samples : list
            ファイル名と棋譜インデックスのタプルからなるリスト
        
        Returns
        -------
        features : list
            盤面特徴量のリスト
        labels : list
            正解データとしての盤面に対して行われた着手のリスト
        """

        # 対象となるファイルのset
        files_needed = set(file_name for file_name, index in samples)
        file_names = []

        # 対象となるファイル名のリスト
        for zip_file_name in files_needed:
            file_name = zip_file_name.replace('.tar.gz', '') + data_type
            file_names.append(file_name)
        
        # process_zipで保存されたデータを読み込む
        feature_list = []
        label_list = []
        for file_name in file_names:
            file_prefix = file_name.replace('.tar.gz', '')
            # chunkのためglobを使って複数の対象となるファイルを取得
            base = self.data_dir + '/' + file_prefix + '_features_*.npy'
            for feature_file in glob.glob(base):
                label_file = feature_file.replace('features', 'labels')
                # ファイルを読み込み
                X = np.load(feature_file)
                y = np.load(label_file)
                # 特徴量はfloat32に，yは19*19次元のone-hotベクトルに
                X = X.astype('float32')
                y = to_categorical(y.astype(int), 19 * 19)
                feature_list.append(X)
                label_list.append(y)
        
        # リスト内結合
        features = np.concatenate(feature_list, axis=0)
        labels = np.concatenate(label_list, axis=0)

        # ここで作成されたfeaturesとlabelsは保存しておく
        np.save(f'{self.data_dir}/features_{data_type}.npy', features)
        np.save(f'{self.data_dir}/labels_{data_type}.npy', labels)

        # 完成したfeaturesとlabelsを返す
        return features, labels
        