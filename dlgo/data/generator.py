import glob
import numpy as np
from keras.utils import to_categorical

class DataGenerator(object):
    """
    yieldによってデータを取得するためのクラス
    """
    def __init__(self, data_directory, samples):
        self.data_directory = data_directory
        self.samples = samples
        self.files = set(file_name for file_name, index in samples)
        self.num_samples = None
    
    def get_num_samples(self, batch_size=128, num_classes=19*19):
        if self.num_samples is not None:
            return self.num_samples # キャッシュ
        else:
            self.num_samples = 0
            for X, y in self._generate(batch_size, num_classes):
                self.num_samples += X.shape[0]
            return self.num_samples
    
    def generate(self, batch_size=128, num_classes=19*19):
        """
        yieldによってミニバッチを取得
        """
        while True:
            for item in self._generate(batch_size, num_classes):
                yield item

    def _generate(self, batch_size, num_classes):
        """
        GoDataProcessor.consolidate_gamesのyield版的なやつ
        """
        for zip_file_name in self.files:
            file_name = zip_file_name.replace('.tar.gz', '') + 'train'
            base = self.data_directory + '/' + file_name + '_features_*.npy'
            for feature_file in glob.glob(base):
                label_file = feature_file.replace('features', 'labels')
                X = np.load(feature_file)
                y = np.load(label_file)
                X = X.astype('float32')
                y = to_categorical(y.astype(int), num_classes)
                while X.shape[0] >= batch_size:
                    X_batch, X = X[:batch_size], X[batch_size:]
                    y_batch, y = y[:batch_size], y[batch_size:]
                    yield X_batch, y_batch
    
