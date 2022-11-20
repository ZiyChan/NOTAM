from typing import List
from deepmultilingualpunctuation import PunctuationModel
from transformers import pipeline
import nltk
from Exiang import chinese_or_not
from Exiang import chinese_svo
import notam
import re
import warnings
import pandas as pd
import sentence_tools
from debuggg import verify


S = """(A1912/15 NOTAMN
Q) LOVV/QWPLW/IV/BO/W/000/130/4809N01610E001
A) LOVV B) 1509261100 C) 1509261230
E) PJE WILL TAKE PLACE AT AREA LAAB IN WALDE
F) GND G) FL130)"""


SHEET_NAME = "相对简单"
warnings.filterwarnings("ignore")
print("Loading model...")
MODEL = PunctuationModel()
print("Loading model... Done")
verbs = sentence_tools.action_words.split('|')
limits = sentence_tools.LIMIT_WORDS.split('|')


# 解析 TODO: 去除非E项内容
def notam_parse_single(e_option_noisy: str) -> str:
    # 去除E):
    e_option = e_option_noisy.replace('E)：', '')
    # 处理换行符
    e_option = e_option.rstrip('\n')
    e_option = e_option.replace('\n', '. ')
    # 处理括号
    e_option = re.sub(r'(Runway|RUNWAY|RWY|TWY) ?\(([0-9/LRC]+?)\)', r'\1 \2', e_option)
    e_option = re.sub(r"\((TEL.*?)\)", r"\1", e_option)
    e_option = re.sub('\(.*?\)', '', e_option)
    # RWY和数字分开
    e_option = re.sub(r"(Runway|RUNWAY|RWY|TWY)([0-9/]+)", r"\1 \2", e_option)
    # 数字和CLSD之间的-去掉
    e_option = re.sub(r"([0-9/LRC]+)[ ]*(-)[ ]*(CLSD|Closed|CLOSED|CLS|Close)", r"\1 \3", e_option)
    # 处理逗号冒号
    e_option = e_option.replace(',', ", ")
    e_option = e_option.replace(':', ": ")
    # 空格合并
    e_option = ' '.join(e_option.split())
    return e_option


# 解码
def notam_decode(e_option: str) -> str:
    # 整理调包格式
    s_new = S.split("E)")[0] + "E) " + e_option + "\nF)" + S.split("E)")[1].split("F)")[1]
    res = notam.Notam.from_str(s_new)
    e_option_text = res.decoded().split("E)")[1].split("F)")[0].rstrip("\n").lstrip(' ').replace('\n', ' ')
    return e_option_text


verbs_human = []
limits_human = []
for verb in verbs:
    verbs_human.append(notam_decode(verb))
for limit in limits:
    limits_human.append(notam_decode(limit))


def bad_case_or_not(e_option_text: str) -> bool:
    # 简单句第一句
    keyword = ['FOLLOWING CONDITIONS:X-WIND COMPONENT', 'REF AIP SUP 12/21 PARAS 2.3',
               'REF AIP SUP A24/21 WEF 20 SEP 2021', 'REF AIP-AD2-LGPZ-ADC', 'REF AIP SUP 166/21 ITEM',
               'RUNWAYS RESTRICTIONS DUE TO ON RUNWAYS DECK LANDING', 'SUSPENDING ILS/GP RWY 07R UNTIL',
               'PORTION WITH CRACKED SFC ON RWY 29R', '22 FIREWORKS 1 NM NW THR . MAX',
               'EFFECTIVE ONLY AT THE EXTREMITIES']

    for key in keyword:
        if key in e_option_text:
            return True

    return False


def bad_case_svo(e_option_text: str) -> List[List[str]]:
    if 'FOLLOWING CONDITIONS:X-WIND COMPONENT' in e_option_text:
        res = sentence_tools.sentence_parse(e_option_text)
        if res[0]:
            return res[1]

    # 实体，动作，原因，限制，限制-翼展，限制-重量，来源
    if 'REF AIP SUP 12/21 PARAS 2.3' in e_option_text:
        return [['CLOSURE OF CENTRE RWY (07C/25C) AND VHHH ON DUAL RWY OPS DRG 252316 -262315', ['RWY (07C/25C)'], 'IS CNL',
                 'DUE HKIA CARGO STAND RE-DESIGNATION', '', '', '', 'REF AIP SUP 12/21 PARAS 2.3 - 2.4 AND NOTAM A1171/21']]

    if 'REF AIP SUP A24/21 WEF 20 SEP 2021' in e_option_text:
        return [['RUNWAY 25R/07L AND TAXIWAYS', ['RUNWAY 25R/07L'], 'TEMPORARY CLOSURE',
                 "CONSTRUCTION OF PHASE 2 - PERIOD 2 - PROJECT 'CONSTRUCTING, UPGRADING RUNWAY , TAXIWAYS AT TAN SON NHAT INTERNATIONAL AIRPORT",
                 '', '', '', 'REF AIP SUP A24/21 WEF 20 SEP 2021'],
                ['GP 07R', [], 'TEMPO SUSPENDED', '', 'UNTIL 0700 ON 10 MAR 2022', '', '', 'REF AIP SUP A24/21 WEF 20 SEP 2021']]

    if 'REF AIP-AD2-LGPZ-ADC' in e_option_text:
        return [['PART OF RWY 07R/25L USED AS TWY BETWEEN INTERSECTIONS B AND F', ['RWY 07R/25L'], 'CLOSED', '',
                 'INTERSECTIONS B AND F NOT AFFECTED. CLOSED PART MARKED AND LIGHTED', '', '',
                 'REF AIP-AD2-LGPZ-ADC']]

    if 'REF AIP SUP 166/21 ITEM' in e_option_text:
        return [['TWY:48 TWY A(BTN R AND W) FOR ACFT WITH WINGSPAN MORE THAN 68.40M', [], 'NOT AVBL', '', '',
                 '', '', 'REF AIP SUP 166/21 ITEM']]

    if 'RUNWAYS RESTRICTIONS DUE TO ON RUNWAYS DECK LANDING' in e_option_text:
        limit = '''DAILY
        PROGRAM KNOWN FROM 'OQCLA' : +33(0)2 97 12 90 25 ACTUAL ACTIVITY KNOWLEDGE
        AVBL ON ATIS 129.125MHZ DURING SLOTS ACTIVITY : - POSSIBLE REGULATION ON DEPARTURE ,
        AND ON ARRIVAL - DECK LANDING MIRRORS, 13FT HEIGHT, 200M BEFORE RUNWAY IN USE THR, 2M
        FROM THE RWY LEFT EDGE (LOCATION IN USE) - UNBASED ACFT MOVEMENT AND CIVILIAN ACFT
        MOVEMENT PROHIBITED WHEN LANDING MIRROR IN USE .
        '''
        return[['RUNWAYS', ['RUNWAYS'], 'RESTRICTIONS', 'DUE TO ON RUNWAYS DECK LANDING SIMULATION',
                limit, '', '', '']]

    if 'SUSPENDING ILS/GP RWY 07R UNTIL' in e_option_text:
        return [['ILS/GP RWY 07R', ['RWY 07R'], 'TEMPO SUSPENDING', '', 'UNTIL 0700 ON 30 APR 2022',
                 '', '', 'REF AIP SUP A08/22 WEF 21 FEB 2022 ITEM 2.1.1 B.']]

    if 'PORTION WITH CRACKED SFC ON RWY 29R' in e_option_text:
        return [['RWY 29R 2M SOUTH AND NORTH OF RCL, BTN TWY A4 AND A5', ['RWY 29R'], 'SOME PORTION WITH CRACKED SFC',
                 '', '', '', '', '']]

    if '22 FIREWORKS 1 NM NW THR . MAX' in e_option_text:
        return [['RWY 22', ['RWY 22'], 'FIREWORKS', '', '1 NM NW THR . MAX 350FT AGL / 1800FT AMSL.', '', '', '']]

    if 'EFFECTIVE ONLY AT THE EXTREMITIES' in e_option_text:
        return [['THE EXTREMITIES OF RWY 16/34 FOR ALL ACFT TYPES', ['RWY 16/34'],
                 'BACKTRACK OPERATIONS, AFTER LANDING OR PRIOR', '', '', '',
                 'TO TAKE-OFF, EXCEPT FOR ACFT LESS THAN FIVE THOUSAND SEVEN HUNDRED KGR 5700 MTOW', '']]

    return [['', [], '', '', '', '', '', '']]


# 标点
def punctuation(e_option_text: str) -> str:
    e_option_text_punc = MODEL.restore_punctuation(e_option_text)
    # 去掉RWY和数字之间的句号
    e_option_text_punc = re.sub(r"(Runway|RUNWAY|RWY|TWY).?(?=[0-9 LRC/]+)", r"\1 ", e_option_text_punc)
    # 去掉数字和常见非开头词之间的句号
    e_option_text_punc = re.sub(r"([0-9LRC/]+)[:\. ]*(?=Unserviceable|CLSD|Closed|CLS|closed|Work In Progress)", r"\1 ", e_option_text_punc)
    # 动词表里的词不可以开头
    for verb in verbs_human:
        e_option_text_punc = re.sub(rf"(.*?) *\. *(?={verb}[ \.:,]+)", r"\1 ", e_option_text_punc)
    # 去掉TEL和数字之间的句号
    e_option_text_punc = re.sub(r"(Contact TEL|CONTACT TEL|APPROVAL ONLY TEL|Approved ONLY TEL)[:\. ]*(\+?[0-9 ]*)", r"\1 \2", e_option_text_punc)
    # 去掉工作计划中间的句号
    e_option_text_punc = re.sub(r"(Refer|REFER)[\. ]*(To|TO|to)?[\. ]*(METHOD OF WORKING)[\. ]*(PLAN)[\. ]*",
                                r"\1 \2 \3 \4", e_option_text_punc)
    # 合并空格
    e_option_text_punc = ' '.join(e_option_text_punc.split())
    # 去掉管理员批准中间的句号
    e_option_text_punc = re.sub(r"(Aerodrome)[\. ]*(OPERATOR (?:APPROVAL|Approved) ONLY)", r"\1 \2", e_option_text_punc)
    e_option_text_punc = e_option_text_punc.replace("APPROVAL ONLY. TEL", "APPROVAL ONLY TEL")
    # 去掉通知时间中间的句号
    e_option_text_punc = re.sub(r"(MINUTES|Minutes|MIN|)[\. ]*(Prior|PRIOR)[\. ]*(NOTICE|Notice|NOTIFICATION|Permission|PERMISSION)",
               r"\1 \2 \3", e_option_text_punc)
    # 去掉联系方式一整句话前面的句号
    e_option_text_punc = re.sub(r"\. *(Contact|CONTACT)[: +]*(?:TEL)*[: +]*([0-9 -]*\.)", r" \1 \2", e_option_text_punc)
    # WHEN不可以放句尾
    e_option_text_punc = e_option_text_punc.replace("WHEN.", "WHEN")
    # 去掉数字后冗余的句号
    e_option_text_punc = e_option_text_punc.replace("...", "呜呜呜")
    e_option_text_punc = e_option_text_punc.replace("..", '.')
    e_option_text_punc = e_option_text_punc.replace("呜呜呜", "...")
    # bad_cases
    e_option_text_punc = e_option_text_punc.replace("IS PROHIBITED. FROM INTERSECTION Taxiway C1.", "IS PROHIBITED FROM INTERSECTION Taxiway C1.")
    e_option_text_punc = e_option_text_punc.replace("CLOSED. ALL TRAINING AND VFR FLIGHTS.", "CLOSED ALL TRAINING AND VFR FLIGHTS.")
    e_option_text_punc = e_option_text_punc.replace("Closed FOR Landing AND Take-off TAXIING OF Aircraft ON Runway ", "Closed FOR Landing AND Take-off. TAXIING OF Aircraft ON Runway ")
    return e_option_text_punc


# 判断摘要
def summarization_or_not(e_option_text_punc: str) -> bool:
    return False


# 摘要
def summarization(text: str) -> str:
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return summary[0]["summary_text"]


# 分句
def sentence_tokenize(text: str) -> List[str]:
    sentences = []
    temp = ''
    # 句子变形以解决不分句bug
    text = re.sub(r"(CAT) (I+)(\.)", r"\1 \2I\3", text)
    text = re.sub(r"(Taxiway) ([A-Z]+)(\.)", r"\1 \2A\3",  text)
    # 加载punkt句子分割器
    sen_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    # 对句子进行分割
    sentences_ori = sen_tokenizer.tokenize(text)
    # 句子若仅含实体则与后一个句子合并
    for sentence_ori in sentences_ori:
        # 句子还原
        sentence_ori = re.sub(r"(CAT) (I+)I(\.)", r"\1 \2\3", sentence_ori)
        sentence_ori = re.sub(r"(Taxiway) ([A-Z]+)A(\.)", r"\1 \2\3",  sentence_ori)
        x = re.match(r"^(?:Runway|RUNWAY|RWY|TWY)[:\. ]?[0-9/A-Z]*\.$", sentence_ori)
        if x is None:
            sentences.append(temp + sentence_ori)
            temp = ''
        else:
            temp = sentence_ori
    sentences = verify(sentences)
    return sentences


# 编码
def encode(sentence: str) -> str:
    # 整理调包格式
    s_new = S.split("E)")[0] + "E) " + sentence + "\nF)" + S.split("E)")[1].split("F)")[1]
    res = notam.Notam.from_str(s_new)
    sentence_code = res.encoded().split("E)")[1].split("F)")[0].rstrip("\n").lstrip(' ').replace('\n', ' ')
    return sentence_code


NOTAM = pd.read_excel("data/data.xlsx", sheet_name=SHEET_NAME)
print("NOTAM数据读取完毕")
NOTAM["E项-人类语"] = "null"
NOTAM["E项-人类语标点符号预测"] = ''
NOTAM["E项-人类语分句"] = ''
NOTAM["是否使用分句及原因"] = ''


for i, v in enumerate(NOTAM["E项"]):
    NOTAM["E项"][i] = notam_parse_single(v)

for i, v in enumerate(NOTAM["E项"]):
    NOTAM["E项-人类语"][i] = notam_decode(v)

# 中间结果
print("开始解析中间结果")

for i, v in enumerate(NOTAM["E项"]):
    cnt_verbs_human = 0
    cnt_ent_limits_human = 0
    # 中文处理
    if chinese_or_not(v):
        NOTAM["是否使用分句及原因"][i] = "中文---单独处理"
    # 英文处理
    else:
        # 全部标点，分句
        v_punct = punctuation(NOTAM["E项-人类语"][i])
        NOTAM["E项-人类语标点符号预测"][i] = v_punct
        sentences = sentence_tokenize(v_punct)
        NOTAM["E项-人类语分句"][i] = sentences
        # 判断是否使用分句
        if bad_case_or_not(v):
            NOTAM["是否使用分句及原因"][i] = "不使用分句，因为是bad_case，需要整体解析"
        elif len(sentences) == 1:
            NOTAM["是否使用分句及原因"][i] = "不使用分句，因为只有一句话"
        elif len(re.findall(r"(RWY|TWY|Runway|RUNWAY|GP)", v)) == 1:
            NOTAM["是否使用分句及原因"][i] = "不使用分句，因为只有单一实体"
        else:
            for j in sentences:
                flag1 = False
                flag2 = False
                # 判断是否有动词
                for x in verbs_human:
                    if j.__contains__(x):
                        flag1 = True
                        break
                # 判断是否有实体+限制
                for x in limits_human:
                    if j.__contains__(x) and (j.__contains__("TAXIWAY") or j.__contains__("Taxiway") or j.__contains__("Runway") or j.__contains__("RUNWAY") or j.__contains__("Glide Path")):
                        flag2 = True
                        break
                if flag1:
                    cnt_verbs_human += 1
                if flag2:
                    cnt_ent_limits_human += 1
            if cnt_verbs_human >= 2:
                NOTAM["是否使用分句及原因"][i] = "使用分句，因为有两句话及以上---存在动词表里的动词"
            elif cnt_ent_limits_human >= 2:
                NOTAM["是否使用分句及原因"][i] = "使用分句，因为有两句话及以上---同时存在实体和限制条件"
            else:
                NOTAM["是否使用分句及原因"][i] = "不使用分句，因为没有两句话及以上---存在动词表里的动词或同时存在实体和限制条件"

NOTAM.to_excel("data/中间结果-" + SHEET_NAME + ".xlsx",index=False)
print("中间结果写入完毕")


# 最终结果
print("开始解析最终结果")
NOTAM["cache"] = ''


for i, v in enumerate(NOTAM["E项"]):
    if chinese_or_not(v):
        svo_all = chinese_svo(v)
    elif bad_case_or_not(v):
        svo_all = bad_case_svo(v)
    elif NOTAM["是否使用分句及原因"][i] == "使用分句，因为有两句话及以上---存在动词表里的动词" or NOTAM["是否使用分句及原因"][i] == "使用分句，因为有两句话及以上---同时存在实体和限制条件":
        svo_all = []
        sentences = NOTAM["E项-人类语分句"][i]
        # 遍历一个E项所有待解析单句
        for k in sentences:
            res = sentence_tools.sentence_parse(encode(k))
            # 把所有解析出来的结果汇总
            if res[0]:
                for m in res[1]:
                    svo_all.append(m)
    else:
        svo_all = sentence_tools.sentence_parse(v)[1]

    # svo_all 加到对应表格
    cache = ""
    for n in svo_all:
        # resul是一个解析结果（用in间隔）
        result_single = n[0] + "/in/" + str(n[1]).strip("[]").replace('\'', '').replace('\"', '') + "/in/" + n[2] + "/in/"+ n[3] + "/in/" + n[4] + "/in/" + n[5] + "/in/" + n[6] + "/in/" + n[7]
        cache += "/out/"
        cache += result_single
        cache = cache.lstrip("/out/")
    NOTAM["cache"][i] = cache

    # debug
    # print("第{}个E项解析出来的: ".format(i+1), svo_all)
    # if i == 11:
    #     break


# 拆分多个行
NOTAM["cache"] = NOTAM["cache"].str.split("/out/")
NOTAM = NOTAM.explode("cache")

# 拆分多个列
NOTAM_cache =NOTAM["cache"].str.split('/in/', expand=True)
NOTAM = NOTAM[~NOTAM.index.duplicated(keep="first")].drop(["cache"],axis=1).join(NOTAM_cache, how="right")

# rename
NOTAM.columns = ['类型', 'E项', 'E项-人类语', "E项-人类语标点符号预测", "E项-人类语分句", "是否使用分句及原因", '实体', "跑道实体", '动作', "原因", "限制", "限制_翼展", "限制_重量", "来源"]

# 保存
excel_name = "data/" + SHEET_NAME + ".xlsx"
NOTAM.to_excel(excel_name)
print("最终结果写入完毕：", excel_name)
