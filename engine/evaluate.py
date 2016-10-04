from __future__ import print_function
from index import create_upstream_model
from metrics import geh, rmse, mape
from collections import OrderedDict

import csv
import tabulate
from datetime import datetime
from pluck import pluck
import numpy as np
import pyprind

steps = [1, 3, 6, 9, 12]
eps = 1e-6

def run_data(model):
    data = []
    # load up the data
    print("Loading Data")
    data_rows = 0
    with open('lane_data.csv', 'rb') as infile:
        reader = csv.DictReader(infile)
        fields = reader.fieldnames
        for row in reader:
            dt = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
            counts = [int(row[x]) for x in fields[1:]]
            if any(map(lambda c: c > 300, counts)):
                # don't list those values that are extremely high
                continue
            data.append({
                'timestamp': dt,
                'downstream': max(1, sum(counts))
            })
            data_rows += 1
            # if data_rows > 100:
            #     break
    print("Data length", data_rows)
    print("Done\nAnalysing Data")
    # process the data

    step_predictions = {
        i: [] for i in steps
        }
    row_count = 0
    progress = pyprind.ProgBar(data_rows, width=100, stream=1)
    for row in data:
        row_count += 1
        progress.update()
        result = model.run(row)
        for i in steps:
            step_predictions[i].append(result.inferences["multiStepBestPredictions"][i])
    return step_predictions, data


if __name__ == "__main__":
    model = create_upstream_model()
    predictions, data = run_data(model)
    # turn the data into numpy arrays
    split_idx = int(len(data) * 0.4)
    flow_values = np.array(pluck(data[split_idx:], 'downstream'))
    print()
    # print (predictions)

    predictions = {
        k: np.array(v[split_idx:]) for k, v in predictions.items()
        }
    print()

    table = []
    print(' & '.join(['step', 'geh', 'mape', 'rmse'])+' \\\\')
    for step in steps:
        # true values
        stepped_vals = flow_values[step:]
        # predicted  values
        pred_vals = predictions[step][:-step] + eps
        table.append(OrderedDict([
            ('steps', step),
            ('geh',  geh(stepped_vals, pred_vals)),
            ('mape', mape(stepped_vals, pred_vals)),
            ('rmse', rmse(stepped_vals, pred_vals))
        ]))
    print(tabulate.tabulate(table, 'keys', 'latex'))

