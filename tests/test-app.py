import pickle

from algorithms_for_tuning import prepare_fitness_estimator, estimate_fitness

with open("test-population.pickle", "rb") as f:
    pop = pickle.load(f)

individual = pop[0]

prepare_fitness_estimator()
estimate_fitness(pop)
