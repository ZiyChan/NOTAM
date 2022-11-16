import pandas as pd
import nltk
import spacy

nlp = spacy.load("en_core_web_sm")


def load_dic():
    df = pd.read_excel('dic_hk.xlsx')
    dfa = pd.read_csv('HongKong.csv')
    dfb = pd.read_csv('abbreviation_China.csv').iloc[:, 1:3]

    # df=df.append([dfb])
    df = pd.concat([df, dfb])

    return df


def tran(s):
    s = s.lower()
    s = ' ' + s + ' '
    df = load_dic()
    length = df.shape[0]
    # df1=df1.str.replace('.',' . ')
    # df1=df1.str.replace('：',' ： ')
    # df1=df1.str.replace(' - ',' ')
    for i in range(length):
        key = ' ' + df.iloc[i, 0].strip().lower() + ' '
        value = ' ' + df.iloc[i, 1].strip().lower() + ' '
        s = s.replace(key, value)
        key = ' ' + df.iloc[i, 0].strip().lower() + '.'
        value = ' ' + df.iloc[i, 1].strip().lower() + '.'
        s = s.replace(key, value)

    s = s.replace(' rwy', ' runway ')
    s = s.replace(' runway runway ', ' runway ')
    s = s.replace(' take off ', ' takeoff ')
    s = s.replace(' do is not ', ' do not ')
    s = s.replace(' to to ', ' to ')
    # s=s.replace(' . ','. ')
    # s=s.replace(' ： ','：')
    s = s.replace(' u/s\)', ' is unserviceable ')
    s = s.replace(' is not is available ', ' is not available ')
    s = s.replace(' unserviceable ', ' is unserviceable ')
    # s=s.replace('\. \.','.')
    return s


def tran_inv(s):
    s = s.lower()
    s = ' ' + s + ' '
    df = load_dic()
    length = df.shape[0]
    for i in range(length):
        key = ' ' + df.iloc[i, 0].strip().lower() + ' '
        value = ' ' + df.iloc[i, 1].strip().lower() + ' '
        s = s.replace(value, key)
        key = ' ' + df.iloc[i, 0].strip().lower() + '.'
        value = ' ' + df.iloc[i, 1].strip().lower() + '.'
        s = s.replace(value, key)

    s = s.replace(' is ', '  ')
    return s.upper()


def find_rwy(s0):
    s0 = s0.lower()
    rwy = []
    s = s0
    s = s.replace('rwy', 'rwy ')
    flag = s.find('rwy ', 0)
    while flag != -1:
        s = s[flag:]
        b = s.split()
        ind = b.index('rwy')
        sele = b[ind:ind + 2]
        sele = " ".join(sele)
        rwy = rwy + [sele]
        flag = s.find('rwy ', flag + 1)

    rwy = str(rwy)
    rwy = rwy.replace("['", "")
    rwy = rwy.replace("']", "")
    rwy = rwy.replace("[", "")
    rwy = rwy.replace("]", "")
    return rwy


def load(file):  # 规则表
    # file='verb.xlsx'
    df = pd.read_excel(file)
    v = df.values.reshape(-1, ).tolist()
    return v


def first(s):
    s = tran_inv(s)
    s = s.lower()

    subject = ''
    verb = ''
    after_v = ''
    reason = ''
    restrict = ''
    rwy = ''
    rmk = ''

    s = s.strip()
    if s[-1] == '.': s = s[:-1]

    rmk_list = load('备注list.xlsx')
    flag = -1
    for i in rmk_list:
        flag = max(flag, s.find(i.lower()))

    u = s.find('following characteristics:')
    if u != -1: flag = min(u, flag)

    if flag != -1:
        rmk = s[flag:].strip()
        s = s[:flag].strip()

    if s != '':
        if s[-1] == '.': s = s[:-1].strip()

    b = s.split()
    s = " ".join(b)

    flag = s.find('u/s')
    if flag != -1:  # U/S   df_us = df_eng[df_eng['us']!=-1]

        # a0,a1=s.split('u/s',1)
        if s[-3:] == 'u/s':  # df_us_last =df_us[df_us['E项'].str]
            if len(s) < 70:  # df_us_last_less70
                subject = s[:-3]
                verb = 'U/S'
            else:  # df_us_last['len']>=70
                return False  # df_us_last_more70
        else:  # df_us_mid  =df_us[df_us['E项'].str[-3:]!='u/s']
            flag = s.find('u/s due')
            if flag != -1:  # df_us_due
                subject, reason = s.split('u/s due', 1)
                verb = 'U/S'
                flag = reason.find('do not use')
                if flag != -1:
                    s0 = reason
                    reason = s0[:flag]  # do not use前
                    after_v = s0[flag:]  # do not use后
            else:  # df_us_ndue
                return False


    else:  # df_non_us
        # if len(s)>84:return False #df_n_avbl_more84

        flag = s.find('exc')  # 限制
        if flag != -1:
            restrict = s[flag:]
            s = s[:flag]

        flag = max(s.find('due '), s.find('for m'))  # 原因
        if flag != -1:
            reason = s[flag:]
            s = s[:flag]

        flag = s.find('do not use')  # 动作后
        if flag != -1:
            after_v = s[flag:]
            s = s[:flag]

        s_1 = s  # 备用
        v_list = load('verb_list.xlsx')
        count = 0
        for i1 in v_list:
            i = i1.lower()
            flag = s.find(i)
            if flag != -1:
                sub0, a = s.split(i, 1)

                if sub0 != '':
                    flag = nltk.word_tokenize(sub0)
                    flag1 = nltk.pos_tag(flag)
                    word = flag1[-1][0]
                    flag = flag1[-1][1]  # 最后一个单词词性
                    if flag == 'IN' or flag == ',':
                        s = sub0 + a
                        continue  # for 介词

                    # print(sub0,'*',i,'*',a)
                    if flag == 'CC':  # and flag1[-2][1]!=',':
                        # print('双动词',i,s_1,'$$',word,'##')
                        s1, s2 = s_1.split(' ' + word + ' ', 1)
                        # print(s1,'\n',s2,'\n\n\n')

                        f1 = first(s1)
                        f2 = first(s2)
                        # print(f1)
                        # print(f2)

                        # return [f1,f2,]
                        if f1 != False and f2 != False:
                            return [f1, f2, ]
                        elif f1 != False:
                            return f1
                        elif f2 != False:
                            return f2
                        else:
                            return False

                verb = i
                subject, after_v = s_1.split(i, 1)

                s = sub0 + a
                count = count + 1

                # print(count,sub0,'*',i,'*',after_v)

                # break
        if verb == '': return False  # df_nus_other
        if count != 1: return False, '*', count

        rwy = find_rwy(s)

    subject.replace('on test', '')
    if after_v.find('north') != -1:
        subject = subject + after_v
        after_v = ''

    return [subject, verb, after_v, reason, rwy]


def second(text):  # input缩写  nlp方法
    reason = ''

    s = text
    flag = max(s.find('due '), s.find('for m'))  # 原因
    if flag != -1:
        reason = s[flag:]
        s = s[:flag]

    rwy = find_rwy(s)

    text = tran(s)
    doc = nlp(text)
    b = []

    # 词性分析
    for token in doc:
        # a=[token.text, token.tag_, token.pos_, token.dep_,token.head.text]
        a = [token.text,
             spacy.explain(token.tag_),
             spacy.explain(token.pos_),
             spacy.explain(token.dep_), token.head.text,
             str(list(token.children))[1:-1], ]
        b = b + [a]
    df = pd.DataFrame(b, columns=['文本', '词性tag', 'pos',
                                  'dependence', 'head', 'children'])

    # 动词分析 预处理
    def match(target, df):
        l = len(target)
        if l != len(df): return 0
        flag = 1
        for i in range(l):
            if df.iloc[i, 2] != target[i]: flag = 0
        return flag

    target_all = [(['auxiliary', 'particle', 'verb'], -2),
                  (['auxiliary', 'verb'], -1),
                  (['auxiliary', 'particle', 'verb'], 0),
                  (['auxiliary', 'adjective', 'verb'], -2),
                  (['auxiliary', 'particle', 'adjective'], -2),
                  (['auxiliary', 'particle', 'adjective'], 0),
                  (['auxiliary', 'adjective'], 0),  # root auxiliary
                  (['auxiliary', 'noun'], 0),
                  (['verb'], 0),
                  ]

    # 动词匹配
    b = []
    for j in target_all:
        target = j[0]
        bias = j[1]
        lt = len(target)
        root_index = df[(df.dependence == 'root')].index.tolist()
        if root_index == []: return False  # 没有root
        i = root_index[0]
        flag = match(target, df.iloc[i + bias:i + lt + bias, :])
        if flag == 1:
            subject = doc[0:i + bias].text
            predicate = doc[i + bias:i + lt + bias].text
            other = doc[i + lt + bias:].text

            b = [tran_inv(subject),
                 tran_inv(predicate),
                 tran_inv(other),
                 reason, rwy]
            return b

    # 单个动词匹配
    # verb = df[(df.pos=='verb')].index.tolist()
    # if verb==[]:
    #     return False #没有verb
    # else:  #按照动词分
    #     verb=verb[0]
    #     subject  =doc[0   :verb  ].text
    #     predicate=doc[verb:verb+1].text
    #     other    =doc[verb+1    :].text
    #     b=[subject,predicate,other]
    #     return b

    return False


def sentence_parse(s1):
    s = tran_inv(s1)
    a = first(s)
    if a == False:
        a = second(s1)
        if a == False: return False, [[]]
        return True, [a]

    else:
        # 检查多个动词
        if a[1] == '*': return False, [[]]
        if len(a) == 5:
            return True, [a]
        else:
            if a[1][0] == '' and a[1][2] == '':
                a[0][2] = a[0][2] + a[1][1]
                del a[1]
            return True, a


def notam_decode(s):
    s = s.lower()
    s = ' ' + s + ' '
    df = load_dic()
    length = df.shape[0]
    # df1=df1.str.replace('.',' . ')
    # df1=df1.str.replace('：',' ： ')
    # df1=df1.str.replace(' - ',' ')
    for i in range(length):
        key = ' ' + df.iloc[i, 0].strip().lower() + ' '
        value = ' ' + df.iloc[i, 1].strip().lower() + ' '
        s = s.replace(key, value)
        key = ' ' + df.iloc[i, 0].strip().lower() + '.'
        value = ' ' + df.iloc[i, 1].strip().lower() + '.'
        s = s.replace(key, value)

    s = s.replace(' rwy', ' runway ')
    s = s.replace(' runway runway ', ' runway ')
    s = s.replace(' take off ', ' takeoff ')
    s = s.replace(' do is not ', ' do not ')
    s = s.replace(' to to ', ' to ')
    # s=s.replace(' . ','. ')
    # s=s.replace(' ： ','：')
    s = s.replace(' u/s\)', ' is unserviceable ')
    s = s.replace(' is not is available ', ' is not available ')
    s = s.replace(' unserviceable ', ' is unserviceable ')
    # s=s.replace('\. \.','.')
    return s
