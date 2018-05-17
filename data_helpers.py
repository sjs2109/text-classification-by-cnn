# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import re
import os

def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()

def load_text_and_label(data_file):
    """
    Loads polarity data from files, splits the data into words and generates labels.
    Returns split sentences and labels.
    """
    # load data from file

    # splite by word
    dfRaw = pd.read_csv(data_file)
    dfRec = dfRaw[['Review Text', 'Recommended IND']].dropna()
    pos_examples = dfRec[dfRec['Recommended IND'] == 1]['Review Text'].tolist()
    neg_examples = dfRec[dfRec['Recommended IND'] == 0]['Review Text'].tolist()

    x_text = pos_examples + neg_examples
    x_text = np.array([clean_str(sentence) for sentence in x_text])
    # generate label (y)
    pos_labels = [[0,1] for _ in pos_examples]
    neg_labels = [[1,0] for _ in neg_examples]
    y = np.array(pos_labels + neg_labels)
    return [x_text, y]

def batch_iter(data, batch_size, num_epochs, shuffle=True):
    '''
    Generates a batch iterator for a dataset.
    '''
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int((data_size-1)/batch_size)+1
    for epoch in range(num_epochs):
        if shuffle:
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num*batch_size
            end_index = min((batch_num+1)*batch_size, data_size)
            yield shuffled_data[start_index:end_index]
