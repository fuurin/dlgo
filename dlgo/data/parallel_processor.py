import os.path, multiprocessing
from dlgo.data.index_processor import KGSIndex
from dlgo.data.processor import GoDataProcessor
from dlgo.data.sampling import Sampler
from dlgo.data.generator import DataGenerator
from dlgo.encoders.base import get_encoder_by_name

def worker(jobinfo):
    try:
        # zips_to_processを受け取る
        clazz, encoder, zip_file, data_file_name, game_list = jobinfo

        # ParallelGoDataProcessorのprocess_zipを使う
        clazz(encoder=encoder).process_zip(zip_file, data_file_name, game_list)
    except (KeyboardInterrupt, SystemExit):
        raise Exception('>>> Exiting child process.')

DATA_DIRECTORY = "../datasets/dlgo/kgs"

class ParallelGoDataProcessor(GoDataProcessor):
    def __init__(self, encoder='simple', data_directory=DATA_DIRECTORY):
        # process_zipを行い，ファイルを特徴量とラベルに変換するエンコーダ
        self.encoder_string = encoder 
        self.encoder = get_encoder_by_name(encoder, 19)
        self.data_dir = data_directory

    def load_go_data(self, data_type='train', num_samples=1000, use_generator=True, download=False):
        """
        ファイルの読み込みを並列で行いながら特徴量とラベルを取得する

        Parameters
        ----------
        data_type : str
            'train'または'test'
        num_samples : int
            取得する棋譜の数
        use_generator : bool
            yieldによるミニバッチの取得を行う
        download : bool
            ファイルのダウンロードを行う
        
        Returns
        -------
        次のいずれか
        generator : generator
            ミニバッチの取得を行うgeneratorを返す
        features_and_labels : tuple
            特徴量とラベルを一度に取得する
        """

        if download:
            index = KGSIndex(data_directory=self.data_dir)
            index.download_files()

        sampler = Sampler(data_dir=self.data_dir)
        data = sampler.draw_data(data_type, num_samples)

        self.map_to_workers(data_type, data)
        if use_generator:
            # generatorではすべてのデータをメモリに持つわけではない
            # なので取得データの保存は行わない
            generator = DataGenerator(self.data_dir, data)
            return generator
        else:
            features_and_labels = self.consolidate_games(data_type, data)
            return features_and_labels
    
    def map_to_workers(self, data_type, samples):
        """
        棋譜データの特徴量とラベルへの変換を複数のCPUで並列処理させる

        Parameters
        ----------
        data_type : str
            'train'または'test'
        samples : list
            ファイル名と棋譜のインデックスがペアになったリスト
        """

        # 解凍対象となるファイル名をsetにまとめる
        # 同時に，各ファイルで必要となる棋譜データのインデックスをまとめる
        zip_names = set()
        indices_by_zip_name = {}
        for filename, index in samples:
            zip_names.add(filename)
            if filename not in indices_by_zip_name:
                indices_by_zip_name[filename] = []
            indices_by_zip_name[filename].append(index)

        # まだ処理されていないファイルをまとめる
        zips_to_process = []
        for zip_name in zip_names:
            base_name = zip_name.replace('.tar.gz', '')
            data_file_name = base_name + data_type
            if not os.path.isfile(self.data_dir + '/' + data_file_name):
                zips_to_process.append((self.__class__, self.encoder_string, zip_name,
                                        data_file_name, indices_by_zip_name[zip_name]))

        # 並列処理で使用するcpuの個数を決定．ここでは全部使う
        cores = multiprocessing.cpu_count()

        # 並列処理のコントローラーオブジェクト
        pool = multiprocessing.Pool(processes=cores) # デフォルトはos.cpu_count()

        # 選ばれたファイルを非同期で特徴量とラベルに変換して保存
        p = pool.map_async(worker, zips_to_process)

        # KeyboardInterruptがあったら全プロセスを終了させる
        try:
            _ = p.get() # 終了を待つ
        except KeyboardInterrupt: # 待ってる間の例外を待つ
            pool.terminate()
            pool.join()
            sys.exit(-1)
        
        pool.terminate()
        pool.join()