from typing import Tuple
from typing import List
from deepmultilingualpunctuation import PunctuationModel
from transformers import pipeline
import nltk
from Exiang import bad_case_or_not
from Exiang import bad_case_svo
from lijinyuan import sentence_parse
import notam
import re
import warnings
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd


S = """(A1912/15 NOTAMN
Q) LOVV/QWPLW/IV/BO/W/000/130/4809N01610E001
A) LOVV B) 1509261100 C) 1509261230
E) PJE WILL TAKE PLACE AT AREA LAAB IN WALDE
F) GND G) FL130)"""


warnings.filterwarnings("ignore")
MODEL = PunctuationModel()


# 解析 TODO: 去除非E项内容
def notam_parse_single(e_option_noisy: str) -> str:
    e_opition = e_option_noisy.replace('E)：', '')
    e_opition = e_opition.replace('\n', '.')
    # 去除括号里内容
    e_opition = re.sub('\(.*?\)', '', e_opition)
    return e_opition

# 解码
def notam_decode(e_option: str) -> str:
    s_new = S.split("E)")[0] + "E) " + e_option + "\nF)" + S.split("E)")[1].split("F)")[1]
    print(s_new)
    res = notam.Notam.from_str(s_new)
    e_option_text = res.decoded().split("E)")[1].split("F)")[0].rstrip("\n").lstrip(' ').replace('\n', ' ')
    e_option_text = e_option_text.replace("MTOW", "Maximum takeoff weight")
    return e_option_text

# 标点
def punctuation(e_option_text: str) -> str:
    e_option_text_punc = MODEL.restore_punctuation(e_option_text)
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
    # 加载punkt句子分割器
    sen_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    # 对句子进行分割
    e_final = sen_tokenizer.tokenize(text)
    return e_final

# 解析E项
def parse(e_final: List[str]) -> Tuple[List[str], str, str, str]:
    restrict = ''
    restrict_span = ''
    restrict_weight = ''
    # 遍历E项单句列表
    for index, value in enumerate(e_final):
        for key in ["EXCEPT FOR", "Except FOR"]:
            # 含关键字则拆分
            if value.__contains__(key):
                e_final[index] = value.split(key)[0].rstrip(' ')
                restrict = value.split(key)[1].strip(' ')
    # 判断翼展和重量
    if restrict.__contains__("Maximum takeoff weight"):
        restrict_weight = restrict
    return e_final, restrict, restrict_span, restrict_weight

# 合并居中单元格并保存
def to_merge(df, excel_name):
    # 按照'E项'列进行每行单元格合并
    # 'E项'列去重，确定一列需要合并成几个值
    df_key = list(set(df['E项'].values))
    wb = Workbook()
    ws = wb.active
    # 将每行数据写入ws中
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)
    # 遍历去重后E项
    for i in df_key:
        # 获取E项等于指定值的几行数据
        df_id = df[df.E项 == i].index.tolist() # 索引值从0开始
        # 遍历，需要合并7列，openyxl中，读excel等的序号都是从1开始，所以合并7列，需要遍历range(1, 8)
        for j in range(1, 8):
            ws.merge_cells(start_row=df_id[0] + 2, end_row=df_id[-1] + 2, start_column=j, end_column=j) # 序号从1开始，所以行序号需要加2

    # save
    wb.save(excel_name)
    print('合并成功！')


qqq = '''RWY 06/24-CLSD DUE TO CRANE EXIST RMK/1 EXCEPT FOR ACFT LESS THAN FIVE THOUSAND SEVEN HUNDRED KGR 5700 MTOW
REFER TO SUP 122/22'''
print(("原始E项：", qqq))
qqq_decode = notam_decode(notam_parse_single(qqq))
print("解码：", qqq_decode)
qqq_punct = punctuation(qqq_decode)
print("标点：", qqq_punct)
qqq_list = sentence_tokenize(qqq_punct)
print("分句：", qqq_list)
qqq_final, restrict, restrict_span, restrict_weight = parse(qqq_list)
print("解析：", qqq_final, restrict, restrict_span, restrict_weight)
