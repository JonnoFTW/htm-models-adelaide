from nupic.swarming import permutations_runner

SWARM_DESCRIPTION = {
    "includedFields": [
        {
            "fieldName": "timestamp",
            "fieldType": "datetime"
        },
        {
            "fieldName": "downstream",
            "fieldType": "float",
            "maxValue": 260.0,
            "minValue": 0.0
        }
    ],
    "streamDef": {
        "info": "downstream",
        "version": 1,
        "streams": [
            {
                "info": "3044-3104 readings",
                "source": "file://readings.csv",
                "columns": [
                    "*"
                ]
            }
        ]
    },

    "inferenceType": "TemporalMultiStep",
    "inferenceArgs": {
        "predictionSteps": [
            1
        ],
        "predictedField": "downstream"
    },
    "iterationCount": -1,
    "swarmSize": "small"
}
import os
import pprint


def modelParamsToString(modelParams):
    pp = pprint.PrettyPrinter(indent=4)
    return pp.pformat(modelParams)


def writeModelParamsToFile(modelParams, name):
    cleanName = name.replace(" ", "_").replace("-", "_")
    paramsName = "%s_model_params.py" % cleanName
    outDir = os.path.join(os.getcwd(), 'model_params')
    if not os.path.isdir(outDir):
        os.mkdir(outDir)
    outPath = os.path.join(os.getcwd(), 'model_params', paramsName)
    with open(outPath, "wb") as outFile:
        modelParamsString = modelParamsToString(modelParams)
        outFile.write("MODEL_PARAMS = \\\n%s" % modelParamsString)


def swarmForBestModelParams(swarmConfig, name, maxWorkers=4):
    outputLabel = name
    permWorkDir = os.path.abspath('swarm')
    if not os.path.exists(permWorkDir):
        os.mkdir(permWorkDir)
    modelParams = permutations_runner.runWithConfig(
        swarmConfig,
        {"maxWorkers": maxWorkers, "overwrite": True},
        outputLabel=outputLabel,
        outDir=permWorkDir,
        permWorkDir=permWorkDir,
        verbosity=0
    )
    modelParamsFile = writeModelParamsToFile(modelParams, name)
    return modelParamsFile


if __name__ == "__main__":
    swarmForBestModelParams(SWARM_DESCRIPTION, '3104-3044')
