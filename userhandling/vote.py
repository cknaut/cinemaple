from .models import UserAttendence, VotePreference
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
                ith_rankset.append(movie_ids[j])
        if not ith_rankset == []:
         ordered_lists.append(ith_rankset)

    # flip to get decreasing preference order
    ordered_lists = np.flip(ordered_lists, 0)


    return ordered_lists



def get_pref_lists(movienight):

    user_attendences = movienight.get_registered_userattend()

    for user_attendence in user_attendences:
        pref_ordering = get_pref_ordering(user_attendence)

    return movienight
