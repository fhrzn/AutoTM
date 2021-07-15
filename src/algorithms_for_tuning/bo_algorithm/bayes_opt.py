#!/usr/bin/env python3

import click
from hyperopt import STATUS_OK, fmin, hp, tpe
from typing import List, Optional
from algorithms_for_tuning.utils import make_log_config_dict
from kube_fitness.tasks import IndividualDTO, TqdmToLogger
import warnings
import logging
import os
import yaml
from yaml import Loader
import copy
import random
import uuid
import numpy as np

ALG_ID = "bo"

SPACE = {
    'decor': hp.quniform('decor', 0, 1e5, 0.05),
    'n1': hp.quniform('n1', 0, 8, 1),
    'spb': hp.quniform('spb', 1e-3, 1e2, 0.05),
    'stb': hp.quniform('stb', 1e-3, 1e2, 0.05),
    'n2': hp.quniform('n2', 0, 8, 1),
    'sp1': hp.quniform('sp1', -1e2, -1e-3, 0.05),
    'st1': hp.quniform('st1', -1e2, -1e-3, 0.05),
    'n3': hp.quniform('n3', 0, 8, 1),
    'sp2': hp.quniform('sp2', -1e2, -1e-3, 0.05),
    'st2': hp.quniform('st2', -1e2, -1e-3, 0.05),
    'n4': hp.quniform('n4', 0, 8, 1),
    'B': hp.quniform('B', 0, 8, 1),
    'decor_2': hp.quniform('decor_2', 0, 1e5, 0.05)
}

warnings.filterwarnings("ignore")

logger = logging.getLogger("BO")

# getting config vars
if "FITNESS_CONFIG_PATH" in os.environ:
    filepath = os.environ["FITNESS_CONFIG_PATH"]
else:
    filepath = "../../algorithms_for_tuning/bo_algorithm/config.yaml"

with open(filepath, "r") as file:
    config = yaml.load(file, Loader=Loader)

if not config['testMode']:
    from kube_fitness.tasks import make_celery_app as prepare_fitness_estimator
    from kube_fitness.tasks import parallel_fitness as estimate_fitness
    from kube_fitness.tasks import log_best_solution
else:
    # from kube_fitness.tm import calculate_fitness_of_individual, TopicModelFactory
    from tqdm import tqdm


    def prepare_fitness_estimator():
        pass


    def estimate_fitness(population: List[IndividualDTO],
                         use_tqdm: bool = False,
                         tqdm_check_period: int = 2) -> List[IndividualDTO]:
        results = []

        tqdm_out = TqdmToLogger(logger, level=logging.INFO)
        for p in tqdm(population, file=tqdm_out):
            individual = copy.deepcopy(p)
            individual.fitness_value = random.random()
            results.append(individual)

        return results


    def log_best_solution(individual: IndividualDTO, alg_args: Optional[str]):
        pass

NUM_FITNESS_EVALUATIONS = config['deAlgoParams']['numEvals']


class BigartmFitness:

    def __init__(self, dataset: str, exp_id: Optional[int] = None):
        self.dataset = dataset
        self.exp_id = exp_id
        # self.best_solution: Optional[IndividualDTO] = None

    def make_individ(self, x):
        params = [float(i) for i in x]
        params = params[:-1] + [0.0, 0.0, 0.0] + [params[-1]]
        return IndividualDTO(
            id=str(uuid.uuid4()),
            dataset=self.dataset,
            params=params,
            exp_id=self.exp_id,
            alg_id=ALG_ID
        )

    def __call__(self, x):
        population = [self.make_individ(x)]

        population = estimate_fitness(population)
        individ = population[0]

        # if self.best_solution is None or individ.fitness_value > self.best_solution.fitness_value:
        #     self.best_solution = copy.deepcopy(individ)

        return -1 * individ.fitness_value


def score(params):
    f_alg = BigartmFitness(**params)
    try:
        fitness = f_alg.__call__()
    except:
        fitness = 0
    if np.isnan(fitness):
        fitness = 0
    print()
    print('CURRENT FITNESS: {}'.format(fitness))
    print()
    return {'loss': -fitness, 'status': STATUS_OK}


@click.command(context_settings=dict(allow_extra_args=True))
@click.option('--dataset', required=True, type=str, help='dataset name in the config')
@click.option('--log-file', type=str, default="/var/log/tm-alg.log",
              help='a log file to write logs of the algorithm execution to')
def run_algorithm(dataset, log_file):
    run_uid = uuid.uuid4() if not config['testMode'] else None
    logging_config = make_log_config_dict(filename=log_file, uid=run_uid)
    logging.config.dictConfig(logging_config)
    best = fmin(score, SPACE, algo=tpe.suggest, max_evals=500)


if __name__ == "__main__":
    run_algorithm()
