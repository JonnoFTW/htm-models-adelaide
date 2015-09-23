SWARM_DESCRIPTION = {
  "includedFields": [
    {
      "fieldName": "timestamp",
      "fieldType": "datetime"
    },
    {
      "fieldName": "6",
      "fieldType": "int",
      "maxValue": 192,
      "minValue": 0
    }
  ],
  "streamDef": {
    "info": "traffic_flow",
    "version": 1,
    "streams": [
      {
        "info": "Rec Center",
        "source": "file://rec-center-hourly.csv",
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
    "predictedField": "kw_energy_consumption"
  },
  "iterationCount": -1,
  "swarmSize": "medium"
}