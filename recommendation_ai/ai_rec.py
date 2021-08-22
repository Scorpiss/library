import numpy as np
import json
from elasticConnector import es_matrix

books_index = json.load(open("recommendation_ai\\save_indxs_books.json", "r", encoding="utf8"))["books"]
sim_matrix_ = np.array(es_matrix.get(id_=0)["_source"]["matrix"])


def get_similarity(author=None, title=None, count=10, cosine=None):
    if cosine == None:
        matrix = es_matrix.multi_search([{"author": author}, {"title": title}], ["matrix"])["hits"]["hits"][0]["_source"]["matrix"]
        sim_scores = list(enumerate(matrix))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        top_10_indicies = sim_scores[1:count + 1]

        top_10_indicies = [x[0] for x in top_10_indicies]
        top_10 = [books_index[x] for x in top_10_indicies]
    else:
        new_matrix = [x for x in sim_matrix_]
        new_matrix.append(cosine)
        new_matrix.sort(reverse=True)
        indx = np.where(np.array(new_matrix) == cosine)[0][0]
        count += 1
        if count % 2 != 0:
            count += 1
            result_cosines = [new_matrix[index] for index in range(indx - int(count/2), indx + int(count/2))][:1]
        else:
            result_cosines = [new_matrix[index] for index in range(indx - int(count/2), indx + int(count/2))]
        result_cosines.remove(cosine)
        result_indices = [np.where(sim_matrix_ == x)[0][0] for x in result_cosines]
        top_10 = [books_index[x] for x in result_indices]

    return top_10


def get_cosine_book(author, title):
    return es_matrix.multi_search([{"author": author}, {"title": title}], ["matrix"])["hits"]["hits"][0]["_source"]["matrix"][0]
