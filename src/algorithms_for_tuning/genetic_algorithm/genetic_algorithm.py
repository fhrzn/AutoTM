#!/usr/bin/env python3
import os
import logging
import sys
from logging import config
import warnings
import yaml
from yaml import Loader

import click
import uuid

from ga import GA
from algorithms_for_tuning.utils import make_log_config_dict

warnings.filterwarnings("ignore")

logger = logging.getLogger("GA")

if "FITNESS_CONFIG_PATH" in os.environ:
    filepath = os.environ["FITNESS_CONFIG_PATH"]
else:
    filepath = "../../algorithms_for_tuning/ga_with_surrogate/config.yaml"

with open(filepath, "r") as file:
    config = yaml.load(file, Loader=Loader)

glob_algo_params = config["gaAlgoParams"]
NUM_FITNESS_EVALUATIONS = glob_algo_params['numEvals']

NUM_FITNESS_EVALUATIONS = 150

@click.command(context_settings=dict(allow_extra_args=True))
@click.option('--dataset', required=True, help='dataset name in the config')
@click.option('--num-individuals', default=10, help='number of individuals in generation')
@click.option('--num-iterations', default=400, help='number of iterations to make')
@click.option('--mutation-type', default="combined",
              help='mutation type can have value from (mutation_one_param, combined, psm, positioning_mutation)')
@click.option('--crossover-type', default="blend_crossover",
              help='crossover type can have value from (crossover_pmx, crossover_one_point, blend_crossover)')
@click.option('--selection-type', default="fitness_prop",
              help='selection type can have value from (fitness_prop, rank_based)')
@click.option('--elem-cross-prob', default=None, help='crossover probability')
@click.option('--cross-alpha', default=None, help='alpha for blend crossover')
@click.option('--best-proc', default=0.4, help='number of best parents to propagate')
@click.option('--log-file', default="/var/log/tm-alg.log",
              help='a log file to write logs of the algorithm execution to')
@click.option('--exp-id', required=True, type=int, help='mlflow experiment id')
@click.option('--topic-count', required=False, type=int, help='desired count of MAIN topics')
def run_algorithm(dataset,
                  num_individuals,
                  num_iterations,
                  mutation_type, crossover_type, selection_type,
                  elem_cross_prob, cross_alpha,
                  best_proc, log_file, exp_id, topic_count):
    logger.debug(f"Command line: {sys.argv}")

    run_uid = str(uuid.uuid4())
    logging_config = make_log_config_dict(filename=log_file, uid=run_uid)
    logging.config.dictConfig(logging_config)

    logger.info(f"Starting a new run of algorithm. Args: {sys.argv[1:]}")

    if elem_cross_prob is not None:
        elem_cross_prob = float(elem_cross_prob)

    if cross_alpha is not None:
        cross_alpha = float(cross_alpha)

    g = GA(dataset=dataset,
           num_individuals=num_individuals,
           num_iterations=num_iterations,
           mutation_type=mutation_type,
           crossover_type=crossover_type,
           selection_type=selection_type,
           elem_cross_prob=elem_cross_prob,
           num_fitness_evaluations=NUM_FITNESS_EVALUATIONS,
           best_proc=best_proc,
           alpha=cross_alpha,
           exp_id=exp_id,
           topic_count=topic_count)
    best_value = g.run(verbose=True)
    print(best_value * (-1))


if __name__ == "__main__":
    run_algorithm()
