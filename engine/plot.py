from __future__ import print_function

font = {'size': 30}
import matplotlib

matplotlib.rc('font', **font)
from matplotlib.dates import DateFormatter, DayLocator
import matplotlib.pyplot as plt
from datetime import timedelta
from collections import OrderedDict
import numpy as np
import os
import glob
import tabulate
from metrics import geh, mape, rmse

metrics = []
figs = []
# for i in [
#     # ('pred_data/3002-batch.npz', 'LSTM-Batch'),
#     # ('pred_data/lane_data_3002_3001.csv-htm-pred-data.npz', 'HTM'),
#     # ('pred_data/3002-all-sensor-test-seq-50.npz', 'LSTM-Online'),
#     ('pred_data/3002-all-sensor-test-seq-1.npz', 'LSTM-Online 1')
# ]:

for i in [('pred_data/3002-all-sensor-test-seq-35.npz', 'LSTM-Online')]: # glob.glob('pred_data/3002-all-sensor-test*'):

    fname = i[0]
    title = i[1]
    # fname = i
    # title = i.split('-')[-1].split('.')[0]

    if not os.path.exists(fname):
        print(fname, "not found")
        continue
    print(fname)
    data = np.load(fname)

    # make xy range the same as true_x

    start = data['true_x'][0]
    end = data['true_x'][-1]
    #
    # print('GEH',   geh(data['true_y'], data['pred_y']))
    # print('RMSE', rmse(data['true_y'], data['pred_y']))
    # print('MAPE', mape(data['true_y'], data['pred_y']))

    true_xy_dict = dict(zip(data['true_x'], data['true_y']))
    pred_xy_dict = dict(
        zip(data['pred_x'].reshape(data['pred_x'].shape[0]), data['pred_y'].reshape(data['pred_y'].shape[0])))
    current = start
    full_true = OrderedDict()
    full_pred = OrderedDict()
    while current <= end:
        full_true[current] = true_xy_dict.get(current, np.nan)
        full_pred[current] = pred_xy_dict.get(current, np.nan)
        current += timedelta(minutes=5)

    start = 16 * 288
    end = start + (7 * 288)
    true_x = full_true.keys()[start:end]
    true_y = full_true.values()[start:end]
    pred_x = full_true.keys()[start:end]
    pred_y = full_pred.values()[start:end]
    invalids = true_y == -1
    true_y[invalids] = np.nan
    pred_y[invalids] = np.nan

    fig, ax = plt.subplots()
    figs.append(fig)

    plt.plot(true_x, true_y, 'b-', label='Readings')
    plt.plot(pred_x, pred_y, 'r-', label=title + ' Predictions')

    plt.legend(prop={'size': 23})
    plt.grid(b=True, which='major', color='black', linestyle='-')
    plt.grid(b=True, which='minor', color='black', linestyle='dotted')

    xmajor_fmt = DateFormatter('%-d %b')
    xmajor_locator = DayLocator(interval=1)
    ax.xaxis.set_major_formatter(xmajor_fmt)
    ax.xaxis.set_major_locator(xmajor_locator)
    fig.subplots_adjust(bottom=0.13)
    df = "%A %d %B, %Y"
    plt.title("3002: Traffic Flow from {} to {}".format(true_x[0].strftime(df), true_x[-1].strftime(df)), y=1.03)
    plt.legend()

    plt.ylabel("Vehicles/ 5 min")
    plt.xlabel("Time")
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(26)
        tick.label.set_rotation('vertical')

fig, ax = plt.subplots()
figs.append(fig)
plt.ylabel("RMSE")
plt.xlabel("Sequence Length")
plt.title("Training Loss vs. Sequence Length")
# plt.legend()
plt.grid()

sequence_length_loss = OrderedDict([
    (1, {'tr': 254.522460938, 'GEH': 1.51763, 'MAPE': 38.3661270142, 'RMSE': 14.4501}),
    (10, {'tr': 223.741363525, 'GEH': 1.23649, 'MAPE': 37.5469952822, 'RMSE': 11.1748}),
    (15, {'tr': 224.10887146, 'GEH': 1.17485, 'MAPE': 35.30575037, 'RMSE': 10.6847}),
    (20, {'tr': 221.206619263, 'GEH': 1.27021, 'MAPE': 43.7787085772, 'RMSE': 11.1519}),
    (30, {'tr': 216.162612915, 'GEH': 1.19739, 'MAPE': 35.1223677397, 'RMSE': 10.87}),
    (35, {'tr': 213.992523193, 'GEH': 1.18092, 'MAPE': 33.6014658213, 'RMSE': 10.8066}),
    (40, {'tr': 223.617706299, 'GEH': 1.21856, 'MAPE': 37.7866715193, 'RMSE': 11.092}),
    (45, {'tr': 219.831680298, 'GEH': 1.19703, 'MAPE': 35.5253368616, 'RMSE': 10.9573}),
    (50, {'tr': 207.128631592, 'GEH': 1.21174, 'MAPE': 37.9185050726, 'RMSE': 10.9295}),
    (75, {'tr': 227.562530518, 'GEH': 1.19555, 'MAPE': 32.2056859732, 'RMSE': 10.8755}),
    (100, {'tr': 223.074127197, 'GEH': 1.24105, 'MAPE': 41.0141944885, 'RMSE': 11.0371}),
    (150, {'tr': 229.053405762, 'GEH': 1.2154, 'MAPE': 38.0239486694, 'RMSE': 11.0532}),
    (200, {'tr': 229.743774414, 'GEH': 1.20288, 'MAPE': 36.0716491938, 'RMSE': 10.9351}),
    (500, {'tr': 254.269760132, 'GEH': 1.19896, 'MAPE': 36.5965992212, 'RMSE': 10.9263}),
    (np.inf, {'tr': 1339.01171875, 'GEH': 4.49669, 'MAPE': 343.527007103, 'RMSE': 32.2684})
])
from pluck import pluck

for key in ['tr', 'GEH', 'MAPE', 'RMSE']:
    plt.plot(sequence_length_loss.keys(), map(lambda x: x ** 0.5, pluck(sequence_length_loss.values(),key)),label=key)

plt.show()
