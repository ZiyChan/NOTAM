# -*- coding:utf-8 -*-
import jieba
import jieba.posseg as pseg
import re
from typing import List


def navl_program(s):
    s = "E)：" + s
    s = s.replace('跑道', 'RWY')
    en_pattern = '[：:]([^\u4e00-\u9fa5]*)'
    reson_pattern ='因(.*?)[：:]'
    en_result = re.findall(en_pattern, s)
    en_result = [res.strip() for res in en_result if len(res) > 5]
    reason_result = re.findall(reson_pattern, s)
    main_result = []
    main_result.append(','.join(en_result))  # 实体
    main_result.append('程序不可用') #　动作
    main_result.append(','.join(reason_result)) # 原因
    main_result.append(' ')
    main_result.append(' ')
    main_result.append(' ')
    main_result.append(' ')
    # 实体，动作，原因，限制，限制-翼展，限制-重量，来源
    return [main_result]


def verify_plan(s):
    s = "E)：" + s
    s = s.replace('跑道', 'RWY')

    date_pattern = '\d.*月.*日'
    en_pattern = '校验([^计划].*)[^\u4e00-\u9fa5].'
    reason_pattern = '[:：].*?(.*计划)'
    en_result = re.findall(en_pattern, s)
    if en_result:
        en_result = en_result[0].split(',')
    else:
        en_result = []
    en_result = [res.strip() for res in en_result if res.strip()]
    main_result = []
    main_result.append(','.join(en_result))  # 实体
    main_result.append('校验')  # 动作
    reason_result = re.findall(reason_pattern, s)
    main_result.append(','.join(reason_result))  # 原因
    limit_result = re.findall(date_pattern, s)
    if limit_result:
        limit_result = limit_result[0]    # 限制条件
    else:
        limit_result = ''
    main_result.append(limit_result)
    main_result.append(' ')
    main_result.append(' ')
    main_result.append(' ')
    # 实体，动作，原因，限制，限制-翼展，限制-重量，来源
    return [main_result]

def barrier(s):
    s = "E)：" + s
    s = s.replace('跑道', 'RWY')

    res_pattern = '[:：].*?(.*?障碍物)'
    limit_pattern = '(障碍物名称.*)'
    res = re.findall(res_pattern, s)
    predicate = 0
    for index, value in enumerate(pseg.cut(res[0])):
        if 'v' in value:
            predicate = index
    res = list(jieba.cut(res[0]))
    limit_result = re.findall(limit_pattern, s)
    main_result = []
    main_result.append(','.join(res[:predicate]))  # 实体
    main_result.append(''.join(res[predicate:]))  # 动作
    main_result.append('')  # 原因
    # rwy_pattern = '\d.?\)([^\u4e00-\u9fa5]*?)\('
    # rwy_result = re.findall(rwy_pattern, s)
    # main_result.append(','.join(rwy_result))
    if limit_result:
        limit_result = limit_result[0]   # 限制条件
    else:
        limit_result = ''
    main_result.append(limit_result)
    main_result.append(' ')
    main_result.append(' ')
    main_result.append(' ')
    # 实体，动作，原因，限制，限制-翼展，限制-重量，来源
    return [main_result]


def chinese_svo(e_option_text: str) -> List[List[str]]:
    if '程序不可用' in e_option_text:
        return navl_program(e_option_text)
    if '校验' in e_option_text and '计划' in e_option_text:
        return verify_plan(e_option_text)
    if '障碍物' in e_option_text:
        return barrier(e_option_text)
    def cn_start(e_option_text):
        l = len(e_option_text)
        for i in range(l):
            if '\u4e00' <= e_option_text[i] <= '\u9fa5': return i
    if e_option_text.startswith('1'):
        res = e_option_text.split('\n')
        res = [i[2:].strip() for i in res if i]
        main_result = []
        for s in res:
            for each in chinese_svo(s):
                main_result.append(each)
        return main_result
    if e_option_text[-1] != '.' and e_option_text[-1] != '。': s = e_option_text + '.'
    s = e_option_text.replace('跑道', 'RWY')
    s = s.replace('RWY ', 'RWY')

    flag = cn_start(s)
    en = s[:flag]
    if '：' in en:
        en = en[en.find('：') + 1 :].strip()
    cn = s[flag:]
    cn = cn.replace('\n', '').replace('\t', '').replace(' ', '')
    flag = cn.find('因')
    if flag == -1: flag = cn.find('由于')
    action = cn[:flag]
    reason = cn[flag:].replace('.', '').replace('。', '')

    rwy = en.split(' ')[0]
    if rwy[0:3] != 'RWY': rwy = ''

    # limit_air
    l = cn.find('不提供')
    r = cn.rfind('机型')
    words = cn[l:r]
    words = words[3:]
    words = pseg.cut(words)
    a = ''
    for word, flag in words:
        if flag == 'eng': a = a + '  ' + word
        if flag == 'x':  a = a + word
    a = a.strip().replace(',', '').replace('。', '').replace('，', '')
    # limit=a
    if len(action) > 40:
        action = list(jieba.cut(action))[0]
        # 实体，动作，原因，限制，限制-翼展，限制-重量，来源
    return [[en, action, reason, '', '', '', '']]

def chinese_or_not(e_option_text: str) -> bool:
    '''
    判断传入字符串是否包含中文
    :param word: 待判断字符串
    :return: True:包含中文  False:不包含中文
    '''
    zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')
    match = zh_pattern.findall(e_option_text)

    return False if not match else True

