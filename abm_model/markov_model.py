import numpy as np
import random


class MarkovModel:
    """
    | Class that represents a Markov model.
    """
    def __init__(self, starting_prob, transition_matrix, states):
        """
        | Constructor method of the MarkovModel class. It initializes a MarkovModel object with the
        specified parameters.

        :param starting_prob: List of probabilities representing the starting probabilities for each state.
        :param transition_matrix: Square matrix representing the transition probabilities between states.
        :param states: A dictionary mapping state indices to state names.
        """
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
        """
        | Updates the current state of the Markov model to the next state based on the transition probabilities.
        It randomly selects the next state using random.choices() based on the transition probabilities associated
        with the current state. The selection is weighted according to the probabilities in the transition matrix.
        """
        self.current_state = random.choices(population=list(self.states.keys()),
                                            weights=self.transition_matrix[self.current_state])[0]