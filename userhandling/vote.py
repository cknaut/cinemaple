import numpy as np

from scipy.stats import rankdata


def get_pref_ordering(user_attendence):
    '''
    Return list of movie ids, ordered by preference rating, equal rating being grouped

    e.g.

    [[111], [123, 124]] Rates 111 first and 123 and 124 second
    '''
    votes = user_attendence.get_votes()

    movie_ids = np.asarray(list(votes.values_list('movie'))).flatten()
    ratings = np.asarray(list(votes.values_list('preference'))).flatten()

    ranks = rankdata(ratings, method='min')-1
    num_ranks = len(set(ranks))

    ordered_lists = []
    for i in range(num_ranks):
        ith_rankset = []
        for j, rank_val in enumerate(ranks):
            if i==rank_val:
                ith_rankset.append((movie_ids[j]))
        if not ith_rankset == []:
         ordered_lists.append(ith_rankset)

    # flip to get decreasing preference order
    ordered_lists = np.flip(ordered_lists, 0).tolist()

    return ordered_lists



def get_pref_lists(user_attendences):

    pref_orderings = []
    for user_attendence in user_attendences:
        pref_ordering = get_pref_ordering(user_attendence)
        pref_orderings.append(pref_ordering)

    return pref_orderings

# returns list with only unique values for axis
def get_uniques(input_list):
    output_list = []

    for entry in input_list:
        if not entry in output_list:
            output_list.append(entry)

    return output_list


def prepare_voting_dict(pref_orderings):

    # find unique preferences sets
    unique_prefs = get_uniques(pref_orderings)

    # count unique preference sets

    unique_prefs_counts = []
    for unique_pref in unique_prefs:
        unique_prefs_counts.append(pref_orderings.count(unique_pref))

    assert np.sum(np.asarray(unique_prefs_counts)) == len(pref_orderings), "Sum of counted unique preference orderings not equal to total # of preference orderings."

    # build dictionary
    voting_input_dict_list = []
    for unique_pref, count in zip(unique_prefs, unique_prefs_counts):
        dictionary = {
            "count"     : count,
            "ballot"    : unique_pref
        }
        voting_input_dict_list.append(dictionary)

    return voting_input_dict_list
