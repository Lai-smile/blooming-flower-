def dict_to_str(dict_val):
    keys = list(dict_val.keys())

    list_val = []

    for key in keys:
        if isinstance(key, tuple):
            new_key = "_".join(map(str, key))
            list_val.append({new_key, dict_val.get(key)})
        else:
            list_val.append({key, dict_val.get(key)})

    str_val = list_to_str(list_val)

    return str_val


def list_to_str(list_val):
    str_val = ",".join(map(str, list_val))

    return str_val


if __name__ == '__main__':
    # dict_val = {(0.12439, 0.13439, -1.4276499999999999, -1.41765): '过孔', (0.12439, 0.13439, -1.4125499999999995, -1.4025499999999997): '过孔'}

    dict_val = {1: '过孔', 2: '过孔'}

    print(type(dict_val))

    str_val = dict_to_str(dict_val)

    print(str_val)

    val = [[1, [1, 2, 3, 4], [1, 2, 3, 4]], [2, [1, 2, 3, 4], [1, 2, 3, 4]]]

    print(type(val))

    str_val1 = list_to_str(val)

    print(str_val1)
