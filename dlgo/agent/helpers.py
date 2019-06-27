from dlgo.gotypes import Point

def is_point_an_eye(board, point, color):
    
    # 石があれば眼じゃない
    if board.get(point) is not None:
        return False
    
    # 隣接点にはすべて味方の石が存在する必要がある
    for neighbor in point.neighbors():
        if board.is_on_grid(neighbor):
            neighbor_color = board.get(neighbor)
            if neighbor_color != color: # Noneもだめ
                return False
    
    # さらに，その点の角(斜めの位置)のうち，3つ以上の角を支配する必要がある

    friendly_corners = 0 # 味方が支配している角の数
    off_board_corners = 0 # 盤の外として，支配されている角の数
    corners = [ 
        Point(point.row - 1, point.col - 1),
        Point(point.row - 1, point.col + 1),
        Point(point.row + 1, point.col - 1),
        Point(point.row + 1, point.col + 1)
    ]
    for corner in corners:
        if board.is_on_grid(corner):
            corner_color = board.get(corner)
            if corner_color == color:
                friendly_corners += 1
        else:
            off_board_corners += 1
    
    # 点が辺または角にあるとき
    if off_board_corners > 0:
        return off_board_corners + friendly_corners == 4
    
    # 点が辺または角にない(中央)とき
    return friendly_corners >= 3