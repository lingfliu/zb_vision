import numpy as np


def paired_shuffle(dats, labels):
    """return: shuffled data with indice
    """
    indice = [idx for idx in range(len(dats))]

    np.random.shuffle(indice)
    shuffled_dats = []
    shuffled_labels = []
    for idx in indice:
        shuffled_dats.append(dats[idx])
        shuffled_labels.append(labels[idx])
    return shuffled_dats, shuffled_labels, indice


def queue_sort(queue):
    """sort queue """
    input_ex =[]
    while True:
        try:
            (i, dat) =queue.get_nowait()
            input_ex.append((i, dat))
        except:
            break
    input_ex =sorted(input_ex, key=lambda x: x[0])
    return [item[1] for item in input_ex]


def to_categorical(input, num_classes):
    '''transform the last dim of input into class vectors'''
    cate_input = []
    for i in input:
        vec = [0]*num_classes
        vec[int(i)] = 1
        cate_input.append(vec)
    return cate_input

def kfold(n_sample, n_split=5, shuffle=False):
    """custom kfold generation
    :param shuffle, when True, will reshuffle the n_sample before the fold
    """
    indice = [idx for idx in range(n_sample)]
    if shuffle:
        np.random.shuffle(indice)

    split_size = n_sample // n_split
    for ns in range(n_split):
        if (ns+1)*split_size > n_sample:
            idx_val = indice[ns*split_size:]
        else:
            idx_val = indice[ns*split_size: (ns+1)*split_size]
        idx_train = [idx for idx in filter(lambda x: x not in idx_val, indice)]

        yield idx_train, idx_val

# insert an element at position pos of array, backshift all other elements in the array
def insert_list(array, array_buff, val, pos):
    if pos < 0 or pos > len(array):
        return

    inserted = False
    if pos == len(array):
        # insert at the end
        array_buff = [array[i] for i in range(len(array))]
        array_buff.append(val)
        return

    for i in range(len(array_buff)):
        if pos == i:
            inserted = True
            array_buff[i] = val
        else:
            if inserted:
                array_buff[i] = array[i-1]
            else:
                array_buff[i] = array[i]
    if not inserted:
        array_buff.append(val)

def delete_list(array, array_delete, pos):
    if pos < 0 or pos >= len(array):
        return

    deleted = False
    for i in range(len(array_delete)):
        if pos == i:
            deleted = True
            array_delete[i] = array[i+1]
        else:
            if deleted:
                array_delete[i] = array[i+1]
            else:
                array_delete[i] = array[i]
