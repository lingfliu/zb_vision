import time

def current_time_ms():
    return int(time.time()*1000)

'''转换颜色至rgb, 如果没有对应的颜色， 则返回[-1,-1,-1]'''
def color2rgb(color):
    # color_up = ['black', 'white', 'red', 'purple', 'yellow', 'gray', 'blue', 'green']
    # color_down = ['black', 'white', 'pink', 'purple', 'yellow', 'gray', 'blue', 'green', 'brown']

    if color == 'black':
        return [0,0,0]

    if color == 'white':
        return [255,255,255]

    if color == 'gray':
        return [156,156,156]

    if color == 'red':
        return [255,0,0]

    if color == 'pink':
        return [255,192,203]

    if color == 'yellow':
        return [255,255,0]

    if color == 'blue':
        return [0,0,255]

    if color == 'green':
        return [0,255,0]

    if color == 'purple':
        return [160, 32, 240]

    if color == 'brown':
        return [165,42,42]

    return [-1,-1,-1]