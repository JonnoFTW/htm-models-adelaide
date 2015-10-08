import os
import pprint
from nupic.swarming import permutations_runner
import yaml
import importlib

def getEngineDir():
    return os.path.dirname(os.path.realpath(__file__))

try:
    path = os.path.join(os.path.dirname(getEngineDir()), 'connection.yaml')
    with open(path, 'r') as f:
        conf = yaml.load(f)
        MODEL_PARAMS_DIR = conf['MODEL_PARAMS_DIR']
        MODEL_CACHE_DIR = conf['MODEL_CACHE_DIR']
        SWARM_CONFIGS_DIR = conf['SWARM_CONFIGS_DIR']
except:
    raise Exception('No connection.yaml with mongo_uri defined! please make one with a mongo_uri variable')


def writeModelParams(params, intersection):
    paramsName = "model_params_%s.py" % intersection
    outPath = os.path.join(getEngineDir(), MODEL_PARAMS_DIR, paramsName)
    with open(outPath, 'wb') as outfile:
        outfile.write("MODEL_PARAMS = \\\n%s" % pprint.pformat(params, indent=2))
    return outPath


def getSwarmConfig(intersection):
    importName = "%s.swarm_config_%s" % (SWARM_CONFIGS_DIR, intersection)
    print "Importing swarm config from %s" % importName
    try:
        importedSwarmConfig = importlib.import_module(importName)
    except ImportError:
        sys.exit("No swarm config exist for '{0}'. Please run create_swarm_config.py {0}".format(intersection))
    return importedSwarmConfig.SWARM_DESCRIPTION



def swarmParams(swarmConfig, intersection):
    outputLabel = intersection
    permWorkDir = os.path.abspath('swarm')
    if not os.path.exists(permWorkDir):
        os.mkdir(permWorkDir)
    import multiprocessing as mp
    # use 3/4 of your CPUs
    maxWorkers = 3 * mp.cpu_count() / 2
    print "Running swarm!"
    modelParams = permutations_runner.runWithConfig(
        swarmConfig,
        {"maxWorkers": maxWorkers, "overwrite": True},
        outputLabel=outputLabel,
        outDir=permWorkDir,
        permWorkDir=permWorkDir,
        verbosity=2
    )
    modelParamsFile = writeModelParams(modelParams, intersection)
    return modelParamsFile

