import sys
import os
import glob
from tqdm import tqdm

from sklearn.model_selection import train_test_split

from ..tokenization import FullTokenizer

from ..utils import get_or_make_label_encoder, TRAIN, EVAL, PREDICT
from ..create_generators import create_single_problem_generator


def read_ctb_pos():
    file_list = glob.glob('data/ctb8.0/data/postagged/*')

    input_list = []
    target_list = []

    for file_path in file_list:
        with open(file_path, 'r', encoding='utf8') as f:
            raw_doc_list = f.readlines()
        text_row_ind = [i+1 for i,
                        text in enumerate(raw_doc_list) if '<S ID=' in text]

        sentence_list = [text for i,
                         text in enumerate(raw_doc_list) if i in text_row_ind]

        for sentence in sentence_list:
            input_list.append([])
            target_list.append([])
            for word_tag in sentence.split():
                if '_' not in word_tag:
                    continue
                word, tag = word_tag.split('_')
                for char_ind, char in enumerate(word):
                    if char_ind == 0:
                        loc_char = 'B'
                    else:
                        loc_char = 'I'
                    target_list[-1].append(loc_char +
                                           '-'+tag)
                    input_list[-1].append(char)
    return input_list, target_list


def ctb_pos(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)

    input_list, target_list = read_ctb_pos()

    if mode == 'train':
        input_list, _, target_list, _ = train_test_split(
            input_list, target_list, test_size=0.2, random_state=3721)
    else:
        _, input_list, _, target_list = train_test_split(
            input_list, target_list, test_size=0.2, random_state=3721)

    flat_target_list = [item for sublist in target_list for item in sublist]

    label_encoder = get_or_make_label_encoder(
        params, 'ctb_pos', mode, flat_target_list, zero_class='[PAD]')
    if mode == PREDICT:
        return input_list, target_list, label_encoder
    return create_single_problem_generator('ctb_pos',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def ctb_cws(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    file_list = glob.glob('data/ctb8.0/data/segmented/*')

    input_list = []
    target_list = []

    # Create possible tags for fast lookup
    possible_tags = []
    for i in range(1, 300):
        if i == 1:
            possible_tags.append('s')
        else:
            possible_tags.append('b' + 'm' * (i - 2) + 'e')

    for file_path in file_list:
        with open(file_path, 'r', encoding='utf8') as f:
            raw_doc_list = f.readlines()
        text_row_ind = [i+1 for i,
                        text in enumerate(raw_doc_list) if '<S ID=' in text]

        sentence_list = [text for i,
                         text in enumerate(raw_doc_list) if i in text_row_ind]

        for sentence in sentence_list:
            input_list.append([])
            target_list.append([])
            for word in sentence.split():
                if word and len(word) <= 299:
                    tag = possible_tags[len(word) - 1]
                    input_list[-1] += list(word)
                    target_list[-1] += list(tag)
                else:
                    continue

    if mode == 'train':
        input_list, _, target_list, _ = train_test_split(
            input_list, target_list, test_size=0.2, random_state=3721)
    else:
        _, input_list, _, target_list = train_test_split(
            input_list, target_list, test_size=0.2, random_state=3721)

    flat_target_list = [item for sublist in target_list for item in sublist]

    label_encoder = get_or_make_label_encoder(
        params, 'ctb_cws', mode, flat_target_list, zero_class='[PAD]')
    if mode == PREDICT:
        return input_list, target_list, label_encoder
    return create_single_problem_generator('ctb_cws',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)
