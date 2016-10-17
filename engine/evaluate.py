from __future__ import print_function
from index import create_upstream_model
from metrics import geh, rmse, mape
from collections import OrderedDict

import csv
import tabulate
from datetime import datetime
from nupic.frameworks.opf import model
from pluck import pluck
import numpy as np
import pyprind

steps = [1]#, 3, 6, 9, 12]
eps = 1e-6

def run_data(fname, limit=None, sensors=None):

    data = []
    # load up the data
    print("Loading Data")
    data_rows = 0
    max_input = 0
    last_row = np.inf
    with open(fname, 'rb') as infile:
        reader = csv.DictReader(infile)
        fields = reader.fieldnames
        for row in reader:
            dt = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
            if type(limit) is datetime and limit > dt:
                last_row = data_rows
            if sensors is None:
                counts = [int(row[x]) for x in fields[1:]]
            else:
                counts = [int(row[x]) for x in fields[1:] if int(x) in sensors]
            if any(map(lambda x: x > 300, counts)):
                continue
            downstream = max(1, sum(counts))
            data.append({
                'timestamp': dt,
                'downstream': downstream
            })
            if downstream < 300:
                max_input = max(max_input, downstream)
            data_rows += 1
            # if data_rows > 100:
            #     break
    print("Data length", data_rows, "max_input", max_input)
    print("Done\nAnalysing Data")
    # process the data
    model = create_upstream_model(max_input, steps)
    step_predictions = {
        i: [] for i in steps
    }
    row_count = 0
    progress = pyprind.ProgBar(min(last_row, data_rows), width=50, stream=1)
    it = iter(data)
    for row in it:
        progress.update()

        # result = model.run(row)
        # for i in steps:
        #     step_predictions[i].append(result.inferences["multiStepBestPredictions"][i])
        if type(limit) is datetime and row['timestamp'] >= limit:
            break
        row_count += 1
    return step_predictions, data, model, it, row_count, len(data)


if __name__ == "__main__":
    import sys
    for i in sys.argv[1:]:
        print("Running ", i)
        fname = i.split('/')[-1]
        predictions, data, model, it, row_count, data_len = run_data(i, limit=datetime(2013, 4, 23), sensors=[5])
        model = model.load('/scratch/model_store/3002_model_sensor_5')
        # turn the data into numpy arrays
        # split_idx = int(len(data) * 0.4)
        # flow_values = np.array(pluck(data[split_idx:], 'downstream'))
        # print()
        # # print (predictions)
        #
        # predictions = {
        #     k: np.array(v[split_idx:]) for k, v in predictions.items()
        # }
        # print()
        #
        # table = []
        # print(' & '.join(['step', 'geh', 'mape', 'rmse'])+' \\\\')
        # for step in steps:
        #     # true values
        #     stepped_vals = flow_values[step:len(predictions)]
        #     # predicted  values
        #     pred_vals = predictions[step][:-step] + eps
        #     table.append(OrderedDict([
        #         ('steps', step),
        #         ('geh',  geh(stepped_vals, pred_vals)),
        #         ('mape', mape(stepped_vals, pred_vals)),
        #         ('rmse', rmse(stepped_vals, pred_vals))
        #     ]))
        # print(tabulate.tabulate(table, 'keys', 'latex'))
        #
        print("Loading matplotlib")
        import matplotlib.pyplot as plt

        true_y = []
        true_x = []
        pred_y = []
        print("Predicting data rows: {}".format(data_len - row_count))

        progress = pyprind.ProgBar(data_len - row_count, width=50, stream=1)
        for row in it:
            progress.update()
            preds = model.run(row)
            if row['timestamp'] > datetime(2013, 6, 15):
                break
            true_x.append(row['timestamp'])
            true_y.append(row['downstream'])
            pred_y.append(preds.inferences["multiStepBestPredictions"][1])

        np_ty = np.array(true_y)
        np_py = np.array(pred_y)
        print("GEH: ",  geh(np_ty, np_py))
        print("MAPE: ", mape(np_ty, np_py))
        print("RMSE: ", rmse(np_ty, np_py))


        print()
        print("True x:", len(true_x))
        print("True y:", len(true_x))
        print("Pred y:", len(true_x))
        plt.plot(true_x[1:], true_y[1:], 'b-', label='Readings')
        plt.plot(true_x[1:], pred_y[:-1], 'r-', label='Predictions')
        df = "%A %d %B, %Y"
        plt.title("3002: Traffic Flow from {} to {}".format(true_x[0].strftime(df), true_x[-1].strftime(df)))
        plt.legend()


        plt.ylabel("Vehicles/ 5 min")
        plt.xlabel("Time")
        plt.show()

