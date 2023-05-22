import numpy as np


class UncannyTerms:
    """
    Uncanny terms are just for terms "temporally"
    """

    def __init__(self, num_uncanny_terms, time_duration):
        self.num_uncanny_terms = num_uncanny_terms
        self.time_duration = time_duration
        self.terms = []

    def update_uncanny_terms(self, word):
        if len(self.terms) == self.num_uncanny_terms:
            # remove the one with the minimal duration
            self.terms = np.delete(self.terms,
                                   np.where(np.array(self.terms)[:, 1] == min(np.array(self.terms)[:, 1]))[0][0],
                                   axis=0).tolist()
        self.terms.append([word, self.time_duration])

    def step(self):
        tmp = []
        for each in self.terms:
            if each[1] != 0:
                tmp.append([each[0], each[1] - 1])
        self.terms = tmp

    def check(self, word):
        i = False
        c = 0
        for each in self.terms:
            if word == each[0]:
                i = True
                c += 1
        return i, 2 ** c
