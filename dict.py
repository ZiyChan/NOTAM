import _abbr


dict_decode = _abbr.ICAO_abbr

# 保存decode字典到_abbr.py文件中, 每个key占一行
with open('_abbr.py', 'w') as f:
    f.write('ICAO_abbr = {\n')
    for key, value in dict_decode.items():
        f.write("    '{}': '{}',\n".format(key, value))
    f.write('}')

# 翻转decode字典得到encode字典
dict_encode = {v: k for k, v in dict_decode.items()}

# 保存encode字典到_abbr2.py文件, 每个key占一行
with open('_abbr2.py', 'w') as f:
    f.write('ICAO_abbr = {\n')
    for key, value in dict_encode.items():
        f.write("    '{}': '{}',\n".format(key, value))
    f.write('}')

print("len of dict_decode: ", len(dict_decode))
print("len of dict_encode: ", len(dict_encode))
