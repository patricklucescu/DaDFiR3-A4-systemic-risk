import numpy as np
import random


class MarkovModel:
    def __init__(self, starting_prob, transition_matrix, states):

        assert (np.shape(transition_matrix)[0] ==
                np.shape(transition_matrix)[1]), f"Please give a square transition matrix"
        assert (len(starting_prob) ==
                len(transition_matrix)), "Please give same length for transition matrix and starting probabilities"
        assert (len(states.keys()) ==
                len(transition_matrix)), "Please give same length for transition matrix and states"

        self.starting_prob = starting_prob
        self.transition_matrix = np.array(transition_matrix)
        self.states = states
        # generate initial state
        self.current_state = random.choices(population=list(self.states.keys()),
                                            weights=self.starting_prob)[0]

    def get_next_state(self):
        self.current_state = random.choices(population=list(self.states.keys()),
                                            weights=self.transition_matrix[self.current_state])[0]
        #return self.states[self.current_state]