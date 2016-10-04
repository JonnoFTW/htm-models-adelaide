# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

MODEL_PARAMS = {'aggregationInfo': {'days': 0,
                                    'fields': [],
                                    'hours': 0,
                                    'microseconds': 0,
                                    'milliseconds': 0,
                                    'minutes': 0,
                                    'months': 0,
                                    'seconds': 0,
                                    'weeks': 0,
                                    'years': 0},
                'model': 'CLA',
                'modelParams': {'anomalyParams': {u'anomalyCacheRecords': None,
                                                  u'autoDetectThreshold': None,
                                                  u'autoDetectWaitRecords': 5030},
                                'clEnable': True,
                                'clParams': {'alpha': 0.035828933612158,
                                             # 'verbosity': 0,
                                             # 'regionName': 'SDRClassifierRegion',
                                             'clVerbosity': 0,
                                             'regionName': 'CLAClassifierRegion',
                                             'steps': '1'},
                                
                                'inferenceType': 'TemporalAnomaly',
                                
                                'sensorParams': {'encoders': {},
                                                 'sensorAutoReset': None,
                                                 'verbosity': 0},
                                
                                'spEnable': True,

                                'spParams': {
                                  'spVerbosity': 0,
                                  'spatialImp': 'cpp',
                                  'globalInhibition': 1,
                                  'columnCount': 2048,
                                  'inputWidth': 0,
                                  'numActiveColumnsPerInhArea': 40,
                                  'seed': 1956,
                                  'potentialPct': 0.8,
                                  'synPermConnected': 0.2,
                                  'synPermActiveInc': 0.003,
                                  'synPermInactiveDec': 0.0005,
                                  'maxBoost': 1.0,
                                },

                                'tpEnable': True,
                                'tpParams': {
                                  'verbosity': 0,
                                  'columnCount': 2048,
                                  'cellsPerColumn': 32,
                                  'inputWidth': 2048,
                                  'seed': 1960,
                                  'temporalImp': 'cpp',
                                  'newSynapseCount': 20,
                                  'maxSynapsesPerSegment': 32,
                                  'maxSegmentsPerCell': 128,
                                  'initialPerm': 0.21,
                                  'permanenceInc': 0.1,
                                  'permanenceDec': 0.1,
                                  'globalDecay': 0.0,
                                  'maxAge': 0,
                                  'minThreshold': 10,
                                  'activationThreshold': 13,
                                  'outputType': 'normal',
                                  'pamLength': 3,
                                },
                                'trainSPNetOnlyIfRequested': False},
                'predictAheadTime': None,
                'version': 1}
                
