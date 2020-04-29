# Created by lixingxing at 2019/3/7

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""


from collections import Counter, defaultdict

from image_handlers.ocr_correction.correct_eng_words import correction
import re
import os
import pandas as pd
from nltk import ngrams, collocations
from tqdm import tqdm


def get_big_en_corpus():
    def _text_handler(text):
        text = re.sub(r'[\t\n]', '', str(text))
        text = re.sub(r'[^a-z]', ' ', str(text).lower())
        return text

    big_text = pd.read_csv('/Users/lixingxing/IBM/reference/PCB_standard/my_eg_dict/big.txt', sep='\n',
                           error_bad_lines=False, header=None, warn_bad_lines=False)
    big_text = big_text.values.tolist()
    big_text = list(map(_text_handler, big_text))
    return big_text


def get_pcb_corpus():
    file_folder = '/Users/lixingxing/IBM/reference/PCB_standard/my_cn_dict/txt'
    file_contents = []
    for f in os.listdir(file_folder):
        file_path = os.path.join(file_folder, str(f))
        file_content = pd.read_csv(file_path, sep='\n', encoding='ISO-8859-1', header=None)
        file_content_list = file_content.values.tolist()
        file_contents.extend(file_content_list)

    new_content = [f[0] for f in file_contents]
    pcb_voc_list = list(map(lambda x: re.sub(r'[^a-z]', ' ', str(x).lower()), new_content))
    big_text = get_big_en_corpus()
    big_text.extend(pcb_voc_list)
    return big_text


def sentence_corpus_to_tokens():
    mix_big_text = get_pcb_corpus()
    tokens = [token for s in mix_big_text for token in s.split(' ') if token != '']
    return tokens


def get_score_dicts_from_tokens(tokens):
    uni_score_dict = defaultdict(lambda: 0)
    uni_gram = list(ngrams(tokens, 1))
    uni_score = Counter(uni_gram)
    for u_word in uni_score:
        uni_score_dict[u_word] = uni_score[u_word]

    bi_score_dict = defaultdict(lambda: 0)
    bgm = collocations.BigramAssocMeasures
    finder = collocations.BigramCollocationFinder.from_words(tokens)
    b_scored = finder.score_ngrams(bgm.likelihood_ratio)
    for b_s in b_scored:
        bi_score_dict[b_s[0]] = b_s[1]
    return uni_score_dict, bi_score_dict


def get_split(elements):
    if not elements:
        return [[]]

    max_step = 3

    results = []

    for i in range(1, 1 + max_step):
        if i <= len(elements):
            remain = get_split(elements[i:])
            for s in remain:
                results.append(elements[:i] + [None] + s)

    return results


def parse_result(r):
    string_repr = ''.join([str(e) if e else ' ' for e in r])
    return string_repr


def get_candidates_list(token_list):
    candidates_list = []
    for i, r in enumerate((get_split(token_list))):
        candidates_list.append([i for i in parse_result(r).split(' ') if i is not ''])
    return candidates_list


def connect_split_word_main(word_need_connect):
    def _max_total(_candidates_list):
        total_score = 0
        uni_candidate, bi_candidate = _candidates_list
        uni_candidate = list(uni_candidate)
        bi_candidate = list(bi_candidate)
        if bi_candidate is not []:
            for x in range(len(bi_candidate)):
                if uni_score_dict[uni_candidate[x]]:
                    p_x = uni_score_dict[uni_candidate[x]]
                    p_xy = bi_score_dict[bi_candidate[x]]
                    p_y_x = p_xy / p_x
                    total_score += p_y_x
                else:
                    total_score += 0
        else:
            total_score += uni_score_dict[uni_candidate[0]]
        return total_score

    words = word_need_connect.split(' ')
    candidates_list = get_candidates_list(words)

    candidate_group = []
    candidate_dict = {}
    for candi in tqdm(candidates_list):
        candi_condition = []
        new_candi = [correction(c.lower()) for c in candi]
        candi_bi = list(ngrams(new_candi, 2))
        candi_uni = list(ngrams(new_candi, 1))
        candi_condition.append(tuple(candi_uni))
        candi_condition.append(tuple(candi_bi))
        candidate_group.append(candi_condition)
        candidate_dict[tuple(candi_condition)] = new_candi

    tokens = sentence_corpus_to_tokens()
    uni_score_dict, bi_score_dict = get_score_dicts_from_tokens(tokens)
    connected_words = ' '.join(candidate_dict[tuple(max(candidate_group, key=_max_total))])
    return connected_words


if __name__ == '__main__':
    # words_token = 'The Bes ic confiqurat ions of Bo ards'
    words_token = 'Layer Conf i quration'
    connected = connect_split_word_main(words_token)
    print('original token is:{}'.format(words_token))
    print('connected token is:{}'.format(connected))
