#!/usr/bin/env python

"""
Evaluates LSTM on the SM dataset using the best params from
VS dataset
"""
from __future__ import print_function
import itertools
from time import time

from hyperas import optim
from hyperopt import Trials, STATUS_OK, tpe, mongoexp, STATUS_FAIL
from keras import Sequential
from keras.layers import LSTM, LeakyReLU, Dense, Activation, Dropout, Embedding
from keras.regularizers import L1L2
import json
import base64
# from hyperas import optim
from hyperas.distributions import choice, uniform, quniform
from sklearn.preprocessing import MinMaxScaler
import pickle
from keras import backend as K
from datetime import datetime, timedelta, date
import numpy as np
import logging
from keras.callbacks import Callback
import os
from io import BytesIO
from tqdm import tqdm

logging.basicConfig(level=logging.DEBUG)

np.seterr(over='raise')

import subprocess
import matplotlib
import gzip
# matplotlib.use('Agg')
import matplotlib.pyplot as plt


def data():
    pkl_name = '115_2_sm.pkl'
    tmp_name = '/tmp/' + pkl_name
    if os.path.exists(tmp_name):
        print("Loading", tmp_name)
        with open(tmp_name, 'rb') as tmp_file:
            rows = pickle.load(tmp_file)
    else:
        cdir = os.path.dirname(os.path.realpath(__file__))
        pkl_fname = (cdir + '/swarm_data/{}.gz'.format(pkl_name))
        print("Loading", pkl_fname)
        p = subprocess.Popen(['zcat', pkl_fname], stdout=subprocess.PIPE)
        rows = [{k.decode('ascii'): v for k, v in row.items()} for row in pickle.load(p.stdout, encoding='bytes')]
        rows.sort(key=lambda x: x['sequence'])
        with open(tmp_name, 'wb') as tmp_file:
            print("Caching unzipped in", tmp_name)
            pickle.dump(rows, tmp_file)
    limit = None
    data = rows[:limit]

    return data


def create_model(rows):
    use_weekday = {{choice([True, False])}}
    use_minute_of_day = {{choice([True, False])}}
    use_month = {{choice([True, False])}}
    use_weekend = {{choice([True, False])}}
    use_holidays = {{choice([True, False])}}
    use_week_number = {{choice([True, False])}}

    parsed_rows = []
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
    for row in rows:
        flow = row['flow']
        dt = row['datetime']
        if flow > 2046:
            continue
        vals = [flow]
        if use_weekday:
            vals.append(dt.isoweekday())
        if use_minute_of_day:
            vals.append(dt.hour * 60 + dt.minute)
        if use_month:
            vals.append(dt.month)
        if use_week_number:
            vals.append(dt.isocalendar()[1])
        if use_weekend:
            vals.append(int(dt.isoweekday() in [6, 7]))
        if use_holidays:
            vals.append(int(dt.date() in holidays))
        parsed_rows.append(vals)

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

    class ResetStates(Callback):
        def __init__(self):
            super(ResetStates, self).__init__()

        def on_epoch_begin(self, epoch, logs=None):
            self.model.reset_states()

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
        isHoliday
    ]
    for `lookback` records
    """
    lookback = 1  # int({{quniform(1, 40, 1)}})
    scaler = MinMaxScaler((0, 1))
    # rows = scaler.fit_transform(_rows)
    # dataX, dataY, fields = create_dataset(rows, lookback)
    # scaled = scaler.fit_transform(list(data_dict.values()))
    # scaled_data_dict = dict(zip(data_dict.keys(), scaled))

    parsed_rows = scaler.fit_transform(parsed_rows)
    # dataX, dataY, fields = create_dataset_from_dict(data_dict, lookback)

    dataX = np.array(parsed_rows[:-1])
    x_shape = dataX.shape
    dataX = dataX.reshape(x_shape[0], 1, x_shape[1])
    dataY = np.array(parsed_rows[1:])[:, 0]
    fields = x_shape[-1]

    test_train_split = 0.60  # 60% training 40% test
    split_idx = int(len(dataX) * test_train_split)
    train_x = dataX[:split_idx]
    train_y = dataY[:split_idx]
    test_x = dataX[split_idx:]
    test_y = dataY[split_idx:]
    batch_size = 1  # int({{quniform(1, 5, 1)}})

    train_x = fit_to_batch(train_x, batch_size)
    train_y = fit_to_batch(train_y, batch_size)
    test_x = fit_to_batch(test_x, batch_size)
    test_y = fit_to_batch(test_y, batch_size)

    lstm_size_1 = {{quniform(96, 300, 4)}}
    lstm_size_2 = {{quniform(96, 300, 4)}}
    lstm_size_3 = {{quniform(69, 300, 4)}}
    optimizer = {{choice(['adam', 'rmsprop'])}}  # 'nadam', 'adamax', 'adadelta', 'adagrad'])}}
    l1_dropout = {{uniform(0.001, 0.7)}}
    l2_dropout = {{uniform(0.001, 0.7)}}
    l3_dropout = {{uniform(0.001, 0.7)}}
    layer_count = {{choice([1, 2, 3])}}
    l1_l1_reg = {{uniform(0.00001, 0.1)}}
    l1_l2_reg = {{uniform(0.00001, 0.1)}}
    l2_l1_reg = {{uniform(0.00001, 0.1)}}
    l2_l2_reg = {{uniform(0.00001, 0.1)}}
    l3_l1_reg = {{uniform(0.00001, 0.1)}}
    l3_l2_reg = {{uniform(0.00001, 0.1)}}
    params = {
        'batch_size': batch_size,
        'lookback': lookback,
        'lstm_size_1': lstm_size_1,
        'lstm_size_2': lstm_size_2,
        'lstm_size_3': lstm_size_3,
        'l1_dropout': l1_dropout,
        'l2_dropout': l2_dropout,
        'l3_dropout': l3_dropout,
        'l1_reg': (l1_l2_reg, l1_l2_reg),
        'l2_reg': (l2_l2_reg, l2_l2_reg),
        'l3_reg': (l3_l2_reg, l3_l2_reg),
        'optimizer': optimizer,
        'layer_count': layer_count,
        'use_weekday': use_weekday,
        'use_minute_of_day': use_minute_of_day,
        'use_month': use_month,
        'use_weekend': use_weekend,
        'use_holidays': use_holidays,
        'use_week_number': use_week_number

    }
    print("PARAMS=", json.dumps(params, indent=4))

    def krmse(y_true, y_pred):
        return K.sqrt(K.mean(K.square(y_pred - y_true), axis=-1))

    def geh(y_true, y_pred):
        return K.sqrt(2 * K.pow(y_pred - y_true, 2) / (y_pred + y_true)).mean(axis=-1)

    start = datetime.now()
    model = Sequential()

    model.add(LSTM(int(lstm_size_1),
                   batch_input_shape=(1, 1, fields),
                   return_sequences=layer_count in (2, 3),
                   stateful=True,
                   dropout=l1_dropout,
                   activity_regularizer=L1L2(l1_l1_reg, l1_l2_reg),
                   ))
    if layer_count in (2, 3):
        model.add(LSTM(int(lstm_size_2),
                       return_sequences=layer_count == 3,
                       dropout=l2_dropout,
                       activity_regularizer=L1L2(l2_l1_reg, l2_l2_reg),
                       stateful=True,
                       ))
    if layer_count == 3:
        model.add(LSTM(int(lstm_size_3),
                       dropout=l3_dropout,
                       stateful=True,
                       activity_regularizer=L1L2(l3_l1_reg, l3_l2_reg)
                       ))

    model.add(Dense(1, activation='linear'))
    terminate_cb = TerminateOnNaN()
    model.compile(loss='mse', optimizer=optimizer)
    try:
        model.fit(train_x, train_y,
                  epochs=1,
                  verbose=1,
                  batch_size=batch_size,
                  shuffle=False,
                  callbacks=[terminate_cb, ResetStates()],
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
    prog = tqdm(range(len(test_y / batch_size)), desc='Train ')
    for batch in group(test_x, batch_size):
        batch = np.array(batch)
        test_y_batch = np.array(next(test_y_it))
        batch_preds = model.predict_on_batch(batch)[:, 0]
        model.train_on_batch(batch, test_y_batch)
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
    unscaled_pred = scaler.inverse_transform(preds_pad)[:, 0]
    unscaled_test_y = scaler.inverse_transform(test_y_pad)[:, 0]
    rmse_result = rmse(unscaled_pred, unscaled_test_y)
    # rmse_result = rmse(preds, test_y)

    plot_x = np.arange(test_x.shape[0])
    dpi = 80
    width = 1920 / dpi
    height = 1080 / dpi
    last = 100000
    plt.figure(figsize=(width, height), dpi=dpi)
    plt.plot(plot_x[-last:], unscaled_test_y[-last:], color='b', label='Actual')
    plt.plot(plot_x[-last:], unscaled_pred[-last:], color='r', label='Predictions')
    plt.legend()

    plt.title("LSTM SM Predictions at 115, SI 2\nRMSE:{}".format(round(rmse_result, 3)))
    plt.xlabel('Time')
    plt.ylabel('Flow')
    fig_name = 'model_{}_{}.png'.format(time(), rmse_result)
    plt.savefig(fig_name)
    print("Save image to", fig_name)
    bytes_out = BytesIO()
    plt.savefig(bytes_out, format='png')
    plt.show()

    res = {
        'loss': rmse_result,
        'status': STATUS_OK,
        'model': model._updated_config(),
        'metrics': {
            'rmse': rmse_result,
            'duration': (finish - start).total_seconds()
        },
        'figure': bytes_out.getvalue(),
        'params': params
    }
    return res


if __name__ == '__main__':
    import sys

    trials = mongoexp.MongoTrials(sys.argv[1], exp_key='lstm_sm_115_final')
    # just run LSTM with the same params that worked for sm
    # result = create_model(data())
    # print(json.dumps(result, indent=4))
    best_run, best_model = optim.minimize(model=create_model,
                                          data=data,
                                          algo=tpe.suggest,
                                          max_evals=125,
                                          trials=trials,
                                          keep_temp=True)
    print("Best performing model chosen hyper-parameters:")

    print(best_run)
    print(json.dumps(best_model, indent=4))
