#!/usr/bin/env python
from nupic.swarming import permutations_runner
import os
import json
import logging

logging.basicConfig()
if __name__ == "__main__":
    with open('swarm_config.json', 'r') as conf:
        swarm_config = json.load(conf)

    model_params = permutations_runner.runWithConfig(swarm_config, {'maxWorkers': 1, 'overwrite': True},  verbosity=3)
    exit()
    model_params = permutations_runner.runWithPermutationsScript('permutations.py',
                                                                 {'maxWorkers': 1, 'overwrite': True,
                                                                  # 'expDescConfig': 'description.py',
                                                                  'verbosityCount': 0},
                                                                 'output', './model_0')
    print(json.dumps(model_params))
