#!/usr/bin/env python
from __future__ import print_function
import itertools
from time import time
from hyperopt import Trials, STATUS_OK, tpe, mongoexp, STATUS_FAIL
from keras import Sequential
from keras.layers import LSTM, LeakyReLU, Dense, Activation, Dropout, Embedding
from keras.regularizers import L1L2
import json
import base64
from hyperas import optim
from hyperas.distributions import choice, uniform, quniform
from sklearn.preprocessing import MinMaxScaler
import pickle
from keras import backend as K
from datetime import datetime, timedelta, date
import numpy as np
import logging
from keras.callbacks import Callback
import os
from tqdm import tqdm


logging.basicConfig(level=logging.DEBUG)

np.seterr(over='raise')

import subprocess
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

def data():

    cdir = os.path.dirname(os.path.realpath(__file__))
    pkl_fname = cdir + '/swarm_data/115_2_1_2_3_4_swarm.pkl.gz'
    p = subprocess.Popen(['zcat', pkl_fname], stdout=subprocess.PIPE)
    rows = pickle.load(p.stdout)
    limit = None
    data = rows[:limit]
    _rows = np.empty((len(data), 6), np.float32)
    data_dict = {}
    holidays = {date(2015, 1, 1),
                date(2015, 1, 26),
                date(2015, 3, 9),
                date(2015, 4, 3),
                date(2015, 4, 4),
                date(2015, 4, 6),
                date(2015, 4, 25),
                date(2015, 6, 8),
                date(2015, 10, 5),
                date(2015, 12, 24),
                date(2015, 12, 25),
                date(2015, 12, 28),
                date(2015, 12, 31),
                date(2016, 1, 1),
                date(2016, 1, 26),
                date(2016, 3, 14),
                date(2016, 3, 25),
                date(2016, 3, 26),
                date(2016, 3, 28),
                date(2016, 4, 25),
                date(2016, 6, 13),
                date(2016, 10, 3),
                date(2016, 12, 24),
                date(2016, 12, 26),
                date(2016, 12, 27),
                date(2016, 12, 31),
                date(2017, 1, 1),
                date(2017, 1, 2),
                date(2017, 1, 26),
                date(2017, 3, 13),
                date(2017, 4, 14),
                date(2017, 4, 15),
                date(2017, 4, 17),
                date(2017, 4, 25),
                date(2017, 6, 12),
                date(2017, 10, 2),
                date(2017, 12, 24),
                date(2017, 12, 25),
                date(2017, 12, 26),
                date(2017, 12, 31)}
    max_flow = 0
    for idx, row in enumerate(data):
        if row['flow'] > 2046:
            continue
        dt = row['datetime']
        max_flow = max(max_flow, row['flow'])
        data_dict[dt] = [
            row['flow'],
            dt.isoweekday(),
            dt.hour * 60 + dt.minute,
            dt.month,
            dt.isocalendar()[1],
            int(dt.isoweekday() in [6, 7]),
            int(dt.date() in holidays)
        ]

    return _rows, data_dict, max_flow


def create_model(_rows, data_dict, max_flow):
    def rmse(y_true, y_pred, axis=0):
        return np.sqrt(((y_pred - y_true) ** 2).mean(axis=axis))

    def create_dataset_from_dict(ddata, lookback=1, steps=1):
        dataX = []
        dataY = []
        for dt, data in ddata.items():
            timestep = []
            yval = ddata.get(dt + timedelta(minutes=5 * steps))
            # check the future value exists and is not an error
            if yval is not None:
                for j in range(lookback):
                    offset = dt - timedelta(minutes=5 * steps * j)
                    # make sure we have all previous values in the lookback
                    if ddata.get(offset) is not None:
                        timestep.append(ddata[offset])
                if len(timestep) == lookback:
                    dataX.append(timestep)
                    dataY.append(yval[0])
        fields = len(dataX[0][0])
        return np.array(dataX, dtype=np.double), np.array(dataY, dtype=np.double), fields

    def fit_to_batch(arr, b_size):
        lim = len(arr) - (len(arr) % b_size)
        return arr[:lim]

    class TerminateOnNaN(Callback):
        """Callback that terminates training when a NaN loss is encountered.
        """

        def __init__(self):
            super(TerminateOnNaN, self).__init__()
            self.terminated = False

        def on_batch_end(self, batch, logs=None):
            logs = logs or {}
            loss = logs.get('loss')
            if loss is not None:
                if np.isnan(loss) or np.isinf(loss):
                    print('Batch %d: Invalid loss, terminating training' % (batch))
                    self.model.stop_training = True
                    self.terminated = True

    # input fields are:
    """
    Input is: 
    [
        flow
        dayOfWeek
        MinuteOfDay
        month
        week
        isWeekend
    ]
    for `lookback` records
    """
    lookback = int({{quniform(1, 40, 1)}})
    scaler = MinMaxScaler((0, 1))
    # rows = scaler.fit_transform(_rows)
    # dataX, dataY, fields = create_dataset(rows, lookback)
    scaled = scaler.fit_transform(list(data_dict.values()))
    scaled_data_dict = dict(zip(data_dict.keys(), scaled))
    dataX, dataY, fields = create_dataset_from_dict(scaled_data_dict, lookback)

    test_train_split = 0.60  ## 60% training 40% test
    split_idx = int(len(dataX) * test_train_split)
    train_x = dataX[:split_idx]
    train_y = dataY[:split_idx]
    test_x = dataX[split_idx:]
    test_y = dataY[split_idx:]
    batch_size = int({{quniform(1, 5, 1)}})

    train_x = fit_to_batch(train_x, batch_size)
    train_y = fit_to_batch(train_y, batch_size)
    test_x = fit_to_batch(test_x, batch_size)
    test_y = fit_to_batch(test_y, batch_size)

    nb_epoch = 1
    lstm_size_1 = {{quniform(96, 300, 4)}}
    lstm_size_2 = {{quniform(96, 300, 4)}}
    lstm_size_3 = {{quniform(69, 300, 4)}}
    optimizer = {{choice(['adam', 'rmsprop'])}}  #  'nadam', 'adamax', 'adadelta', 'adagrad'])}}
    l1_dropout = {{uniform(0.001, 0.7)}}
    l2_dropout = {{uniform(0.001, 0.7)}}
    l3_dropout = {{uniform(0.001, 0.7)}}
    output_activation = {{choice(['relu', 'tanh', 'linear'])}}
    # reset_interval = int({{quniform(1, 100, 1)}})
    # layer_count = {{choice([1, 2, 3])}}
    l1_reg = {{uniform(0.0001, 0.1)}}
    l2_reg = {{uniform(0.0001, 0.1)}}
    params = {
        'batch_size': batch_size,
        'lookback': lookback,
        'lstm_size_1': lstm_size_1,
        'lstm_size_2': lstm_size_2,
        'lstm_size_3': lstm_size_3,
        'l1_dropout': l1_dropout,
        'l2_dropout': l2_dropout,
        'l3_dropout': l3_dropout,
        'l1_reg': l1_reg,
        'l2_reg': l2_reg,
        'optimizer': optimizer,
        'output_activation': output_activation,
        # 'state_reset': reset_interval,
        # 'layer_count': layer_count,
        # 'use_embedding': use_embedding
    }
    print("PARAMS=", json.dumps(params, indent=4))

    def krmse(y_true, y_pred):
        return K.sqrt(K.mean(K.square(y_pred - y_true), axis=-1))

    def geh(y_true, y_pred):
        return K.sqrt(2 * K.pow(y_pred - y_true, 2) / (y_pred + y_true)).mean(axis=-1)

    reg = L1L2(l1_reg, l2_reg)
    start = datetime.now()
    model = Sequential()
    # if conditional(use_embedding):
    #     model.add(Embedding())
    model.add(LSTM(int(lstm_size_1),
                   batch_input_shape=(batch_size, lookback, fields),
                   return_sequences=True,
                   stateful=True,
                   activity_regularizer=reg,
                   bias_initializer='ones'))
    model.add(Dropout(l1_dropout))
    model.add(Activation('relu'))
    model.add(LSTM(int(lstm_size_2),
                   return_sequences=True,
                   bias_initializer='ones',
                   stateful=True,
                   activity_regularizer=reg))
    model.add(Dropout(l2_dropout))
    model.add(Activation('relu'))
    model.add(LSTM(int(lstm_size_3),
                   bias_initializer='ones',
                   stateful=True,
                   activity_regularizer=reg))
    model.add(Dropout(l3_dropout))
    model.add(Activation('relu'))
    model.add(Dense(1, activation='relu'))

    terminate_cb = TerminateOnNaN()
    model.compile(loss='mse', optimizer=optimizer)
    try:
        model.fit(train_x, train_y,
                  epochs=1,
                  verbose=1,
                  batch_size=batch_size,
                  shuffle=False,
                  callbacks=[terminate_cb],
                  )
    except Exception as e:
        print(e)
        return {
            'status': STATUS_FAIL,
            'msg': e
        }
    if terminate_cb.terminated:
        return {
            'status': STATUS_FAIL,
            'msg': "Invalid loss"
        }
    # have it continue learning during this phase
    # split the test_x,test_y
    preds = []

    def group(iterable, n):
        it = iter(iterable)
        while True:
            chunk = tuple(itertools.islice(it, n))
            if not chunk:
                return
            yield chunk

    test_y_it = iter(group(test_y, batch_size))
    test_batch_idx = 0
    prog = tqdm(range(len(test_y/batch_size)), desc='Train ')
    for batch in group(test_x, batch_size):

        batch = np.array(batch)
        test_y_batch = np.array(next(test_y_it))
        model.train_on_batch(batch, test_y_batch)
        batch_preds = model.predict_on_batch(batch)[:, 0]
        preds.extend(batch_preds)
        test_batch_idx += 1
        prog.update()
        # if test_batch_idx % reset_interval == 0:
        #     model.reset_states()
    preds = np.array(preds)
    finish = datetime.now()
    preds_pad = np.zeros((preds.shape[0], fields))
    preds_pad[:, 0] = preds.flatten()
    test_y_pad = np.zeros((preds.shape[0], fields))
    test_y_pad[:, 0] = test_y.flatten()
    unscaled_pred = scaler.inverse_transform(preds_pad)
    unscaled_test_y = scaler.inverse_transform(test_y_pad)
    rmse_result = rmse(unscaled_pred, unscaled_test_y)[0]

    plot_x = np.arange(test_x.shape[0])
    dpi = 80
    width = 1920 / dpi
    height = 1080 / dpi
    plt.figure(figsize=(width, height), dpi=dpi)
    plt.plot(plot_x, unscaled_test_y[:, 0], color='b', label='Actual')
    plt.plot(plot_x, unscaled_pred[:, 0], color='r', label='Predictions')
    plt.legend()

    plt.title("LSTM Discrete Predictions at 115, SI 2\nRMSE:{}".format(round(rmse_result, 3)))
    plt.xlabel('Time')
    plt.ylabel('Flow')
    fig_name = 'model_{}.png'.format(time())
    plt.savefig(fig_name)
    plt.show()
    with open(fig_name, 'rb') as img_file:
        fig_b64 = base64.b64encode(img_file.read()).decode('ascii')

    return {
        'loss': rmse_result,
        'status': STATUS_OK,
        'model': model._updated_config(),
        'metrics': {
            'rmse': rmse_result,
            # 'geh': geh(unscaled_pred, unscaled_test_y)[0],
            'duration': (finish - start).total_seconds()
        },
        'figure': fig_b64,
        'params': params
    }


if __name__ == '__main__':
    # trials = Trials()
    import sys
    trials = mongoexp.MongoTrials(sys.argv[1],
                                  exp_key='lstm_3_layer_115_2')

    best_run, best_model = optim.minimize(model=create_model,
                                          data=data,
                                          algo=tpe.suggest,
                                          max_evals=300,
                                          trials=trials)
    print("BEST_RUN",
          json.dumps({k: v for k, v in trials.best_trial['result'].items() if k not in ['model', 'figure']}, indent=4))
