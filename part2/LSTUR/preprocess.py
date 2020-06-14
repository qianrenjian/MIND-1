from tensorflow.keras.preprocessing.text import Tokenizer, text_to_word_sequence
import numpy as np
import json
import os
import random


MAX_TITLE_LENGTH = 30
MAX_ABSTRACT_LENGTH = 100
MAX_BROWSED = 50
NEG_SAMPLE = 1


def preprocess_user_data(filename):
    print("Preprocessing user data...")
    browsed_news = []
    impression_news = []
    user_id = []
    user_index = {}
    with open(filename, "r") as f:
        data = f.readlines()
    random.seed(212)
    random.shuffle(data)
    use_num = int(len(data) * 1)
    use_data = data[:use_num]
    for l in use_data:
        userID, time, history, impressions = l.strip('\n').split('\t')
        history = history.split()
        browsed_news.append(history)
        impressions = [x.split('-') for x in impressions.split()]
        impression_news.append(impressions)
        if userID not in user_index:
            user_index[userID] = len(user_index)
        user_id.append(user_index[userID])
    impression_pos = []
    impression_neg = []
    for impressions in impression_news:
        pos = []
        neg = []
        for news in impressions:
            if int(news[1]) == 1:
                pos.append(news[0])
            else:
                neg.append(news[0])
        impression_pos.append(pos)
        impression_neg.append(neg)
    all_browsed_news = []
    all_click = []
    all_unclick = []
    all_candidate = []
    all_label = []
    all_user = []
    for k in range(len(browsed_news)):
        browsed = browsed_news[k]
        pos = impression_pos[k]
        neg = impression_neg[k]
        id = user_id[k]
        for pos_news in pos:
            all_browsed_news.append(browsed)
            all_click.append([pos_news])
            neg_news = random.sample(neg, NEG_SAMPLE)
            all_unclick.append(neg_news)
            all_candidate.append([pos_news]+neg_news)
            all_label.append([1] + [0] * NEG_SAMPLE)
            all_user.append([id])
            
    print('original behavior: ', len(browsed_news))
    print('processed behavior: ', len(all_browsed_news))
    return all_browsed_news, all_click, all_unclick, all_candidate, all_label, all_user, user_index


def preprocess_test_user_data(filename, user_index):
    print("Preprocessing test user data...")
    with open(filename, 'r') as f:
        data = f.readlines()
    random.seed(212)
    random.shuffle(data)
    use_num = int(len(data) * 0.1)
    use_data = data[:use_num]
    impression_index = []
    user_browsed_test = []
    all_candidate_test = []
    all_label_test = []
    user_index_test = {}
    all_user_test = []
    for l in use_data:
        userID, time, history, impressions = l.strip('\n').split('\t')
        if userID not in user_index:
            user_index[userID] = len(user_index)
        if user_index[userID] not in user_index_test:
            user_index_test[user_index[userID]] = len(user_index_test)
            history = history.split()
            user_browsed_test.append(history)
        impressions = [x.split('-') for x in impressions.split()]
        begin = len(all_candidate_test)
        end = len(impressions) + begin
        impression_index.append([begin, end])
        for news in impressions:
            all_user_test.append(user_index[userID])
            all_candidate_test.append([news[0]])
            all_label_test.append([int(news[1])])
    print('test samples: ', len(all_label_test))
    print('Found %s unique users.' % len(user_index))
    print('Found %s unique test users.' % len(user_index_test))
    return impression_index, user_index, user_browsed_test, all_user_test, all_candidate_test, all_label_test, user_index_test


def preprocess_news_data(filename, filename_2):
    print('Preprocessing news...')
    category_map = {}
    subcategory_map = {}
    titles = []
    categories = []
    subcategories = []
    news_index = {}

    with open(filename, 'r') as f:
        for l in f:
            id, category, subcategory, title, abstract, url, entity = l.strip('\n').split('\t')
            if id not in news_index:
                news_index[id] = len(news_index)
            title = title.lower()
            # map every category to a number
            if category not in category_map:
                category_map[category] = len(category_map)
            # map every subcategory to a number
            if subcategory not in subcategory_map:
                subcategory_map[subcategory] = len(subcategory_map)
            titles.append(title)
            categories.append(category)
            subcategories.append(subcategory)
    news_index_test = {}
    titles_test = []
    categories_test = []
    subcategories_test = []
    with open(filename_2, 'r') as f:
        for l in f:
            id, category, subcategory, title, abstract, url, entity = l.strip('\n').split('\t')
            if id not in news_index:
                news_index[id] = len(news_index)
                title = title.lower()
                # map every category to a number
                if category not in category_map:
                    category_map[category] = len(category_map)
                # map every subcategory to a number
                if subcategory not in subcategory_map:
                    subcategory_map[subcategory] = len(subcategory_map)
                titles.append(title)
                categories.append(category)
                subcategories.append(subcategory)
            if id not in news_index_test:
                news_index_test[id] = len(news_index_test)
                title = title.lower()
                titles_test.append(title)
                categories_test.append(category)
                subcategories_test.append(subcategory)

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(titles)
    word_index = tokenizer.word_index # a dict: word_index[word]=index
    print('Found %s unique news.' % len(news_index))
    print('Found %s unique tokens.' % len(word_index))
    # print(word_index)

    # title
    news_title = np.zeros((len(titles), MAX_TITLE_LENGTH), dtype='int32')
    news_title_test = np.zeros((len(titles_test), MAX_TITLE_LENGTH), dtype='int32')
    for i, title in enumerate(titles):
        wordTokens = text_to_word_sequence(title)
        k = 0
        for _, word in enumerate(wordTokens):
            if k < MAX_TITLE_LENGTH:
                news_title[i, k] = word_index[word]
                k = k + 1
    for i, title in enumerate(titles_test):
        wordTokens = text_to_word_sequence(title)
        k = 0
        for _, word in enumerate(wordTokens):
            if k < MAX_TITLE_LENGTH:
                news_title_test[i, k] = word_index[word]
                k = k + 1

    # category & subcategory
    news_category = np.zeros((len(categories), 1), dtype='int32')
    news_category_test = np.zeros((len(categories_test), 1), dtype='int32')
    k = 0
    for category in categories:
        news_category[k][0] = category_map[category]
        k += 1
    k = 0
    for category in categories_test:
        news_category_test[k][0] = category_map[category]
        k += 1
    news_subcategory = np.zeros((len(subcategories), 1), dtype='int32')
    news_subcategory_test = np.zeros((len(subcategories_test), 1), dtype='int32')
    k = 0
    for subcategory in subcategories:
        news_subcategory[k][0] = subcategory_map[subcategory]
        k += 1
    k = 0
    for subcategory in subcategories_test:
        news_subcategory_test[k][0] = subcategory_map[subcategory]
        k += 1

    all_news_test = np.concatenate((news_title_test, news_category_test, news_subcategory_test), axis=-1)
    # print(all_news_test.shape)
    return word_index, category_map, subcategory_map, news_category, news_subcategory, news_title, news_index, news_index_test, all_news_test