import random
from gotypes import Player, Point

"""
    碁盤のゾブリストハッシュ生成用スクリプト
    19 * 19碁盤のゾブリストハッシュ生成
    出力をzobrist.pyに書き出す
"""


def to_python(state):
    if state is None:
        return 'None'
    if state == Player.black:
        return Player.black
    return Player.white


MAX63 = 0x7fffffffffffffff

table = {}
empty_board = 0
for row in range(1, 20):
    for col in range(1, 20):
        for state in (Player.black, Player.white):
            code = random.randint(0, MAX63)
            table[Point(row, col), state] = code

print('from .gotypes import Player, Point')
print('')
# from zobrish import * で取得する変数を指定している
print("__all__ = ['HASH_CODE', 'EMPTY_BOARD']")
print('')
print('HASH_CODE = {')
for (pt, state), hash_code in table.items():
    print('    (%r, %s): %r,' % (pt, to_python(state), hash_code))
print('}')
print('EMPTY_BOARD = %d' % (empty_board,))
