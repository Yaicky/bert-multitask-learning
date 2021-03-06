import sys
import os
import glob
from tqdm import tqdm

from sklearn.model_selection import train_test_split

from ..tokenization import FullTokenizer

from ..utils import get_or_make_label_encoder, TRAIN, EVAL, PREDICT
from ..create_generators import create_single_problem_generator


def process_line_msr_pku(l):
    decoded_line = l.strip().split('  ')
    return [w.strip('\r\n') for w in decoded_line]


def process_line_as_training(l):
    decoded_line = l.strip().split('\u3000')
    return [w.strip('\r\n') for w in decoded_line]


def process_line_cityu(l):
    decoded_line = l.strip().split(' ')
    return [w.strip('\r\n') for w in decoded_line]


def get_process_fn(filename):

    if 'msr' in filename or 'pk' in filename:
        return process_line_msr_pku

    elif 'as' in filename:
        return process_line_as_training

    elif 'cityu' in filename:
        return process_line_cityu


def _process_text_files(path_list):

    # Create possible tags for fast lookup
    possible_tags = []
    for i in range(1, 300):
        if i == 1:
            possible_tags.append('s')
        else:
            possible_tags.append('b' + 'm' * (i - 2) + 'e')

    inputs = []
    target = []

    for s in range(len(path_list)):
        filename = path_list[s]

        # Init left and right queue

        with open(filename, 'r', encoding='utf8') as f:

            input_list = f.readlines()

            process_fn = get_process_fn(os.path.split(filename)[-1])

            for l in tqdm(input_list):
                pos_tag = []
                final_line = []

                decoded_line = process_fn(l)

                for w in decoded_line:
                    if w and len(w) <= 299:
                        final_line.append(w)
                        pos_tag.append(possible_tags[len(w) - 1])

                decode_str = ''.join(final_line)

                pos_tag_str = ''.join(pos_tag)

                if len(pos_tag_str) != len(decode_str):
                    print('Skip one row. ' + pos_tag_str + ';' + decode_str)
                    continue

                inputs.append(list(decode_str))
                target.append(list(pos_tag_str))

    return inputs, target


def CWS(params, mode):
    # ctb data

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

    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/*.utf8')
    else:
        file_list = [  # 'as_testing_gold.utf8',
            'cityu_test_gold.utf8', 'msr_test_gold.utf8', 'pku_test_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    icwb_inputs, icwb_target = _process_text_files(file_list)

    input_list += icwb_inputs
    target_list += icwb_target

    label_encoder = get_or_make_label_encoder(
        params, 'CWS', mode, ['b', 'm', 'e', 's'], zero_class='[PAD]')
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('CWS',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def as_cws(params, mode):

    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/as_*.utf8')
    else:
        file_list = ['as_testing_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    label_encoder = get_or_make_label_encoder(
        params, 'as_cws', mode, ['b', 'm', 'e', 's'], zero_class='[PAD]')
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('as_cws',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def msr_cws(params, mode):

    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/msr_*.utf8')
    else:
        file_list = ['msr_test_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    label_encoder = get_or_make_label_encoder(
        params, 'msr_cws', mode, ['b', 'm', 'e', 's'], zero_class='[PAD]')
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('msr_cws',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def pku_cws(params, mode):

    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/pku_*.utf8')
    else:
        file_list = ['pku_test_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    label_encoder = get_or_make_label_encoder(
        params, 'pku_cws', mode, ['b', 'm', 'e', 's'], zero_class='[PAD]')
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('pku_cws',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def city_cws(params, mode):

    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/cityu_*.utf8')
    else:
        file_list = ['cityu_test_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    label_encoder = get_or_make_label_encoder(
        params, 'city_cws', mode, ['b', 'm', 'e', 's'], zero_class='[PAD]')
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('city_cws',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def as_domain(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/as_*.utf8')
    else:
        file_list = ['as_testing_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    target_list = ['as_cws' for _ in target_list]
    flat_target_list = ['as_cws', 'pku_cws', 'city_cws', 'msr_cws']
    label_encoder = get_or_make_label_encoder(
        params, 'cws_domain', mode, flat_target_list)
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('as_domain',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def msr_domain(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/msr_*.utf8')
    else:
        file_list = ['msr_test_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    target_list = ['msr_cws' for _ in target_list]
    flat_target_list = ['as_cws', 'pku_cws', 'city_cws', 'msr_cws']
    label_encoder = get_or_make_label_encoder(
        params, 'cws_domain', mode, flat_target_list)
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('msr_domain',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def pku_domain(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/pku_*.utf8')
    else:
        file_list = ['pku_test_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    target_list = ['pku_cws' for _ in target_list]
    flat_target_list = ['as_cws', 'pku_cws', 'city_cws', 'msr_cws']
    label_encoder = get_or_make_label_encoder(
        params, 'cws_domain', mode, flat_target_list)
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('pku_domain',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)


def cityu_domain(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    if mode == 'train':
        file_list = glob.glob('data/cws/training/cityu_*.utf8')
    else:
        file_list = ['cityu_test_gold.utf8']
        # file_list = ['msr_test_gold.utf8']
        file_list = [os.path.join('data/cws/gold', f) for f in file_list]

    input_list, target_list = _process_text_files(file_list)

    target_list = ['city_cws' for _ in target_list]
    flat_target_list = ['as_cws', 'pku_cws', 'city_cws', 'msr_cws']
    label_encoder = get_or_make_label_encoder(
        params, 'cws_domain', mode, flat_target_list)
    if mode == PREDICT:
        return input_list, target_list, label_encoder

    return create_single_problem_generator('cityu_domain',
                                           input_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer,
                                           mode)
