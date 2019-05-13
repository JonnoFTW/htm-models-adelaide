#!/usr/bin/env python
import os
import numpy as np
import click
import csv
import yaml
import pymongo
from datetime import datetime
from nupic.frameworks.opf.model_factory import ModelFactory
from tqdm import tqdm
import pickle

with open('../../connection.yaml') as input_file:
    conf = yaml.load(input_file)

mongo_uri = conf['mongo_uri']


class StrategicInputHTMPredictor:
    def __init__(self, intersection, strategic_input, data_folder, model_folder, show_prog=False,
                 conf='model_0/model_params.py'):
        self.intersection = intersection
        self.strategic_input = strategic_input
        self.data_folder = data_folder
        self.model_folder = model_folder
        self.show_prog = show_prog
        self.conf = conf

        client = pymongo.MongoClient(mongo_uri, w=0)
        # load in the data via cursor into csv
        db = client[conf['mongo_database']]
        self.scats_sm = db['scats_sm']
        self.locations = db['locations']
        self.scats_sm_predictions = db['scats_sm_predictions']

        location = self.locations.find_one({'site_no': intersection})
        if location is None:
            exit('Invalid intersection')
        if 'strategic_inputs' not in location:
            exit('No strategic inputs listed for this intersection, please run lx_parser.py')
        if strategic_input not in location['strategic_inputs']:
            exit('{} has no strategic_input: {}'.format(intersection, strategic_input))

    def load_data_to_csv(self, use_swarm_fmt=False):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        fname = '{}/{}_{}.csv'.format(self.data_folder, self.intersection, self.strategic_input)
        if not os.path.exists(fname):
            with open(fname, 'w') as output_file:
                fields = ['datetime', 'flow', 'cycle_time', 'sequence']
                writer = csv.DictWriter(output_file, fieldnames=fields)
                writer.writeheader()
                if use_swarm_fmt:
                    writer.writerow(dict(zip(fields, ["datetime", 'int', 'int', 'int'])))
                    writer.writerow(dict(zip(fields, ["T", "", "", ""])))
                cursor = self.scats_sm.find({
                    'site_no': self.intersection,
                    'strategic_input': int(self.strategic_input)}).sort('sequence', pymongo.ASCENDING)
                count = cursor.count()
                print("Saving data to {} {}".format(fname, count))
                prog = tqdm(total=count)
                for row in cursor:
                    writer.writerow({
                        'datetime': row['datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                        'flow': row['measured_flow'],
                        'cycle_time': row['actual_cycle_time'],
                        'sequence': row['sequence']
                    })
                    prog.update()
                prog.close()
        return fname

    def swarm(self):
        pass

    def save_model(self):
        print("Saving to {}".format(self.model_folder))
        self.model.save(self.model_folder)

    def create_model(self):
        with open(self.conf, 'r') as conf:
            model = ModelFactory.create(conf)
            self.steps = conf['model_params']['clParams']['steps'].split(',')
        self.model = model

    def save_predictions(self, predictions):
        """
        A List of predictions to be upserted into the db
        They look like:
        {datetime: dt,
         sequence: 1,
         site_no: '3043',
         strategic_input: 148,
         htm: {
            1:{ # 1 step prediction
              prediction:5,
              anomalyScore: 0.5,
              anomalyLikelihood: 0.9,
            }
        }
        :param predictions:
        :return:
        """
        self.scats_sm_predictions.insert_many(predictions, ordered=False)

    def run_model(self, limit=None):
        """

        :param limit:
        :return:
        """
        outputs = []
        rows = []
        fname = self.load_data_to_csv()
        pkl_fname = fname + '.pkl'
        if not os.path.exists(pkl_fname):
            with open(fname, 'r') as incsv:
                """
                Read the data into memory,
                because small reads are bad
                """
                reader = csv.reader(incsv)
                row1 = reader.next()
                row2 = reader.next()
                row3 = reader.next()
                # this file was used not used to swarm
                if row1['datetime'] != 'datetime':
                    incsv.seek(0)
                    reader.next()
                for row in reader:
                    dt = row[0]
                    date = datetime.date(int(dt[1:5]), int(dt[6:8]), int(dt[9:11])),
                    time = datetime.time(int(dt[1:3]), int(dt[4:6]), 0)
                    rows.append({
                        'datetime': datetime.combine(date, time),
                        'flow': int(row[1]),
                        'cycle_time': int(row[2]),
                        'sequence': int(row[3])
                    })
            pickle.dump(rows, pkl_fname)
        else:
            rows = pickle.load(pkl_fname)
        prog = None
        if self.show_prog:
            prog = tqdm(total=len(rows), unit_scale=True, desc=fname)

        for row in rows[limit]:
            result = self.model.run(row)
            pred_row = {k: row[k] for k in ['datetime', 'sequence']}
            pred_row['site_no'] = self.intersection
            pred_row['strategic_input'] = self.strategic_input
            pred_row['htm'] = {i: result.inferences['multiStepBestPredictions'][i] for i in self.steps}
            if len(outputs) > 1000:
                self.save_predictions(outputs)
                outputs = []
            if self.show_prog:
                prog.update()


if __name__ == "__main__":
    # Input should be --intersection <intersection> --si <si> --data-folder <folder>
    import argparse

    parser = argparse.ArgumentParser(description="Make predictions about phased traffic data")
    parser.add_argument('--intersection', '-i', help='Intersection number', type=str)
    parser.add_argument('--strategic-input', '-s', help='Strategic Input', type=str)
    parser.add_argument('--data-folder', '-d', help='Data storage folder', type=str)
    parser.add_argument('--model-folder', '-m', help='Model storage folder', type=str)
    parser.add_argument('--show-prog', '-p', action='store_true')
    args = parser.parse_args()
    predictor = StrategicInputHTMPredictor(args.intersection, args.strategic_input, args.data_folder, args.model_folder,
                                           args.show_prog)
    # predictor.load_data_to_csv(True)
  #  predictor.run_model()
  #  predictor.save_model()
