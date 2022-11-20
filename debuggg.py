import re


def verify(sentence_list):
    if not sentence_list:
        return sentence_list
    due_list = []
    ref_list = []

    def is_refstart(sentence):
        keyword = ['refer', 'Refer', 'REFER']
        for word in keyword:
            if sentence.startswith(word):
                return True
        return False

    def is_duestart(sentence):
        keyword = ['due', 'DUE', 'Due']
        for word in keyword:
            if sentence.startswith(word):
                return True
        return False

    for index, sentence in enumerate(sentence_list[1:]):
        if is_duestart(sentence):
            due_list.append(index + 1)
        if is_refstart(sentence):
            ref_list.append(index + 1)

    if not due_list and not ref_list:
        return sentence_list

    num_of_entity = len(
        list(set(re.findall(r"(?:RWY|RUNWAY|Runway) *(?:[0-9]+[LRC/]*[0-9LRC]*)", '.'.join(sentence_list)))))

    def process_due(sentence_list, due_list, ref_list):
        if num_of_entity > 1:
            for index in due_list:
                if is_refstart(sentence[index - 1]) and index - 2 >= 0:
                    sentence_list[index - 2] += ' ' + sentence_list[index]
                else:
                    sentence_list[index - 1] += ' ' + sentence_list[index]
            for index in sorted(due_list, reverse=True):
                sentence_list.pop(index)
            return sentence_list, ref_list
        else:
            if len(due_list) > 1:
                return sentence_list
            else:
                for index in range(len(sentence_list)):
                    if is_refstart(sentence_list[index]) or is_duestart(sentence_list[index]):
                        continue
                    sentence_list[index] += ' ' + sentence_list[due_list[0]]
                tmp = []
                for index in ref_list:
                    if index > due_list[0]:
                        tmp.append(index - 1)
                    else:
                        tmp.append(index)
                sentence_list.pop(due_list[0])
                return sentence_list, tmp

    def process_ref(sentence_list, ref_list):
        if num_of_entity > 1:
            for index in ref_list:
                if is_refstart(sentence[index - 1]) and index - 2 >= 0:
                    sentence_list[index - 2] += ' ' + sentence_list[index]
                else:
                    sentence_list[index - 1] += ' ' + sentence_list[index]
            for index in sorted(ref_list, reverse=True):
                sentence_list.pop(index)
            return sentence_list
        else:
            if len(ref_list) > 1:
                return sentence_list
            else:
                for index in range(len(sentence_list)):
                    if is_refstart(sentence_list[index]) or is_duestart(sentence_list[index]):
                        continue
                    sentence_list[index] += ' ' + sentence_list[ref_list[0]]
                sentence_list.pop(ref_list[0])
                return sentence_list

    if due_list:
        sentence_list, ref_list = process_due(sentence_list, due_list, ref_list)

    if ref_list:
        sentence_list = process_ref(sentence_list, ref_list)

    return sentence_list
