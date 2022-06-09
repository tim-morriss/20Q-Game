# -*- coding: utf-8 -*-
"""IR_Modified.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12N6d-yQtBIwqKPLI-JZsOytUr_INMEqg
"""

# @title Imports
import json
import urllib.request
import numpy as np
import scipy.stats
import operator
from random import randint
import math
import matplotlib.pyplot as plt

# @title Data Structures
layer_to_key = {1: 'release_year',
                2: 'genre_new',
                3: 'subject_new',
                4: 'starring',
                5: 'director',
                6: 'musicComposer'}

layer_questions = {2: 'Is <tag> the genre of your movie?',
                   3: 'Is <tag> the subject of your movie?',
                   4: 'Is <tag> an actor of your movie?',
                   5: 'Is <tag> the director of your movie?',
                   6: 'Is <tag> the music composer of your movie?', }


# @title Layer Question Generator
def question_generator(layer, movie_probability,
                       file, play_count,
                       total_movie_count, alpha,
                       beta, questions_asked, answers_given, eliminated_index):
    # read all the keys from given layer
    # eg. read all genres from the genre layer
    # and store in a list
    key = layer_to_key[layer]
    layer_list = list(file[key].keys())

    file_name = 'layer' + str(layer) + '_prob.json'

    # read the file which stores the probability scores of each key of given layer
    with open(file_name, 'r') as fp:
        layer_prob = json.load(fp)

    # calculate score of each key
    # the score depends on
    # 1. how many times the key has been selected
    # 2. Probability of the key in the data - the number of movies associated with that key
    layer_score = {}
    for i in layer_list:
        layer_score[i] = alpha * (len(file[key][i]) / total_movie_count) + (layer_prob[i] / play_count) * (1 - alpha)
        layer_sum = 0
        for j in file[key][i]:
            index = int(j)
            layer_sum += movie_probability[index]
        layer_score[i] += (beta * layer_sum)

    # sort the layer keys in descending order of their scores
    sorted_score = dict(sorted(layer_score.items(), key=lambda kv: kv[1], reverse=True))
    sorted_key = sorted_score.keys()

    # boolean flag to check if any question can be asked
    # It returns False in case all the questions
    # have been asked from the specified layer
    question_left = False

    # generate the question by replacing <tag> with actual value
    for i in sorted_key:
        # get the question from the specified layer
        question = layer_questions[layer]
        question = question.replace('<tag>', str(i))
        if question not in questions_asked:
            question_left = True
            break

    # if no questions can be asked, return
    if not question_left:
        return

    questions_asked.append(question)

    # take user input
    choice = input(question)

    # append user answer to the list
    # used for keeping track to shown at the end
    answers_given.append(choice.lower())

    # the list of movies which belong to the question asked
    filtered_movies = list((set(file[key][i])))
    Norm_factor = 0

    # modify the movie probabilities if the answer is yes
    if choice.lower() == 'y':

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(1) * movie_probability[j]
            elif str(j) not in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(-1) * movie_probability[j]

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(1) * movie_probability[j]) / Norm_factor
            elif str(j) not in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(-1) * movie_probability[j]) / Norm_factor

    # modify the movie probabilities if the answer is no
    elif choice.lower() == 'n':

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(-1) * movie_probability[j]
            elif str(j) not in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(1) * movie_probability[j]

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(-1) * movie_probability[j]) / Norm_factor
            elif str(j) not in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(1) * movie_probability[j]) / Norm_factor


# @title
# title Era Question Generator
def era_question(layer, movie_probability,
                 file, play_count,
                 total_movie_count, alpha,
                 beta, questions_asked,
                 answers_given, birth_year, eliminated_index):
    # read all the eras from data_to_movie
    key = layer_to_key[layer]

    eras_dict = file['release_year']
    years = list(map(int, eras_dict.keys()))

    # find the range of years
    era_min = min(years) - (min(years) % 10)
    era_max = max(years) - (max(years) % 10)

    probability_scores_eras = []
    eras = []
    i = era_min
    era_wise_movies = []
    final_movies = set()

    file_name = 'layer' + str(layer) + '_prob.json'

    # read the file which stores the probability scores of each key of given layer
    with open(file_name, 'r') as fp:
        layer_prob = json.load(fp)

    while i < era_max + 10:
        temp_score = 0
        count_movies = 0
        limit = i + 10
        eras.append(i)

        score = alpha * (len(file[key][str(i)]) / total_movie_count) + (layer_prob[str(i)] / play_count) * (1 - alpha)
        movies_set = set()

        while i < limit:
            temp_score += scipy.stats.norm(birth_year + 20, 10).pdf(i)
            if i in years:
                movies = list(eras_dict[str(i)])
                movies_set.update(movies)
                final_movies.update(movies)
                count_movies += len(movies)
            i += 1

        era_wise_movies.append(movies_set)
        probability_scores_eras.append(temp_score + score)

    sorted_eras = [eras for _, eras in sorted(zip(probability_scores_eras, eras))]
    sorted_era_wise_movies = [eras for _, eras in sorted(zip(probability_scores_eras, era_wise_movies))]

    probability_scores_eras.sort()
    probability_scores_eras.reverse()
    sorted_eras.reverse()
    sorted_era_wise_movies.reverse()

    Question = "Is the movie from " + str(sorted_eras[0]) + "s era ? Y/N/M :"
    questions_asked.append(Question)
    choice = input(Question)
    answers_given.append(choice.lower())

    filtered_movies = list((set(file[key][str(sorted_eras[0])])))
    Norm_factor = 0

    # initialize the norm factor

    # modify the movie probabilities if the answer is yes
    if choice.lower() == 'y':

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(1) * movie_probability[j]
            elif str(j) not in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(-1) * movie_probability[j]

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(1) * movie_probability[j]) / Norm_factor
            elif str(j) not in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(-1) * movie_probability[j]) / Norm_factor

    # modify the movie probabilities if the answer is no
    elif choice.lower() == 'n':

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(-1) * movie_probability[j]
            elif str(j) not in filtered_movies and j not in eliminated_index:
                Norm_factor += math.exp(1) * movie_probability[j]

        for j in range(len(movie_probability)):
            if str(j) in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(-1) * movie_probability[j]) / Norm_factor
            elif str(j) not in filtered_movies and j not in eliminated_index:
                movie_probability[j] = (math.exp(1) * movie_probability[j]) / Norm_factor


# @title Update Play Count
def update_play_count():
    with open('count.json', 'r') as json_file:
        file1 = json.load(json_file)

    count = file1["count"]
    file1["count"] += 1

    with open('count.json', 'w') as fp:
        json.dump(file1, fp, sort_keys=True, indent=4)

    return count + 1


# @title Plot Graph
def plot_g(movie_probability):
    temp = movie_probability.copy()
    temp.sort()
    plt.plot(temp)
    plt.show()


# @title Pairwise Sort
def pair_sort(movies_id, movie_probability):
    temp1 = movie_probability.copy()
    temp2 = movies_id.copy()
    Z = [x for _, x in sorted(zip(temp1, temp2))]
    Z.reverse()
    return Z
    # print(Z)


# @title Main
def main():
    with open('filtered_data_to_movie.json', 'r') as json_file:
        data_to_movie = json.load(json_file)
    with open('filtered_movie_to_data.json', 'r') as json_file:
        movie_to_data = json.load(json_file)
    total_movie_count = len(movie_to_data)

    # TODO
    # primary_keys = list(data_to_movie.keys())

    while (True):

        # choice = input("Do you want to play 20Q-Game ? Y/N :")
        choice = 'Y'
        questions_asked = []
        answers_given = []
        eliminated_index = []
        play_count = update_play_count()

        noq = {1: 0,
               2: 0,
               3: 0,
               4: 0,
               5: 0,
               6: 0}

        if choice.lower() != 'y':
            break
        else:

            # birth_year = int(input("Please enter your Birthyear in YYYY format :"))
            birth_year = 1994
            movie_id = 35
            prob = []
            alpha = 0.2
            beta = 0.4

            movies_id = []
            for i in range(89):
                movies_id.append(i)

            movie_probability = [1 / total_movie_count] * total_movie_count
            era_question(1, movie_probability, data_to_movie, play_count, total_movie_count, alpha, beta,
                         questions_asked, answers_given, birth_year, eliminated_index)
            # plot_g(movie_probability)
            pair_sort(movies_id, movie_probability)
            flag = 'n'
            question_set = [[2, 3, 4, 4], [5, 6], [2, 3, 3, 4, 4], [5, 6], [2, 3, 4, 4], [5, 6]]
            for q_set in question_set:
                flag = ask_question(q_set, movie_probability, data_to_movie, play_count, total_movie_count, alpha, beta,
                                    questions_asked, answers_given, movies_id, prob, eliminated_index, movie_to_data)
                if flag == 'y':
                    flag = 'y'
                    break
            if flag == 'n':
                movie_val = int(input('Enter the index of the correct movie :'))
                update_probability(movie_to_data, movie_val)
        break


main()


# @title Ask Question Set
def ask_question(question_set, movie_probability,
                 data_to_movie, play_count,
                 total_movie_count, alpha,
                 beta, questions_asked,
                 answers_given, movies_id,
                 prob, eliminated_index,
                 movie_to_data):
    length = len(question_set)
    for i in range(length):
        max_index = len(question_set) - 1
        rand_int = randint(0, max_index)
        val = question_set[rand_int]
        del question_set[rand_int]
        question_generator(val, movie_probability, data_to_movie, play_count, total_movie_count, alpha, beta,
                           questions_asked, answers_given, eliminated_index)
        # plot_g(movie_probability)
        pair_sort(movies_id, movie_probability)
        flag = check_kneepoint(movie_probability, eliminated_index, movie_to_data, movies_id, questions_asked)
        if flag == 'y':
            break
    return flag


# @title Update Layer Probabilties
def update_probability(file, movie_val):
    for i in range(1, 7):
        key = layer_to_key[i]

        layer = file[str(movie_val)][key]

        file_name = 'layer' + str(i) + '_prob.json'

        with open(file_name, 'r') as json_file:
            layer_file = json.load(json_file)

        for j in layer:
            layer_file[str(j)] += 1

            with open(file_name, 'w') as fp:
                json.dump(layer_file, fp, sort_keys=True, indent=4)


# @title Check Kneepoint
def check_kneepoint(movie_probability, eliminated_index, movie_to_data, movies_id, questions_asked):
    movie_prob = movie_probability.copy()
    movie_prob.sort()
    movie_prob.reverse()
    count = min(5, len(movie_probability) - len(eliminated_index))
    top_movies = pair_sort(movies_id, movie_probability)
    flag = 'n'

    # if length of probability set is more than 1, then the prediction is made
    if (sum(movie_prob[0:count]) > 0.5 and len(questions_asked) > 6):
        for i in range(count):
            print(top_movies[i], movie_prob[i])

        final_choice = input("Is your movie in the given list ? Y/N :")
        if final_choice.lower() == 'y':
            flag = 'y'
            update_choice = int(input("Enter the index of the correct movie :"))
            movie_val = top_movies[update_choice - 1]
            update_probability(movie_to_data, movie_val)
        elif final_choice.lower() == 'n':
            flag = 'n'
            eliminated_index.extend(top_movies[0:count])
            print(eliminated_index)
            prob_sum = sum(movie_prob[0:count])
            for i in range(len(movie_probability)):
                if i not in eliminated_index:
                    movie_probability[i] += prob_sum / (len(movie_probability) - len(eliminated_index))
                else:
                    movie_probability[i] = 0.0
            # plot_g(movie_probability)
    return flag


# @title Initializer
def count():
    c_dict = {}
    c_dict['count'] = 0
    with open('count.json', 'w') as fp:  # write_in_layer2
        json.dump(c_dict, fp, sort_keys=True, indent=4)


def all_Layer_prob_dump():
    with open('filtered_data_to_movie.json', 'r') as json_file:
        file = json.load(json_file)

    all_layer = ['release_year', 'genre_new', 'subject_new', 'starring', 'director', 'musicComposer']
    json_filename = ['layer1_prob', 'layer2_prob', 'layer3_prob', 'layer4_prob', 'layer5_prob', 'layer6_prob']

    for a in range(len(all_layer)):
        genre_list = list(file[all_layer[a]])
        layer_prob = {}
        for i in genre_list:
            current_keys = list(layer_prob.keys())
            if i not in current_keys:
                layer_prob[str(i)] = 0.0

        json_name = json_filename[a] + ".json"
        with open(json_name, 'w') as fp:
            json.dump(layer_prob, fp, sort_keys=True, indent=4)


def initializer():
    count()
    all_Layer_prob_dump()


initializer()
