Traffic Anomaly Detection in Adelaide using HTM
===============================================

![Adelaide from the air](https://i.imgur.com/5STpTTNh.jpg "Adelaide in all its glory")


Introduction
------------
Adelaide uses SCATS for collecting traffic data (along with signal control) using induction loops beneath the road
to record the number of vehicles that go though a particular lane at an intersection. This data is provided in 5
minute intervals for every sensor at every intersection in the city which works out to 2920 individual sensors across
134 intersections in the CBD alone
 
 Our goal is to use this flow data to determine the presence of an incident on a section of road
within a reasonable amount of time. Incidents are not restricted to vehicle accidents, they may also include:

* Breakdowns
* Spilled loads
* Natural disasters such as flooding and landslides
* Unscheduled maintenance
* Burst pipes 

It's imperative that the presence of these events is detected and responded to in a timely and appropriate manner 
by those working in a transport management center. Research has shown that the accuracy of these warnings is important
as high false-positive rates result in fatigue and staff eventually ignoring alarms.

In the field of automated incident detection (AID), the problem of detecting incidents in an arterial road networks
is still an open problem. Current research is limited to supervised techniques that are typically run on
data collected in small scale traffic simulations that allow the researcher to easily optimise for 1 or 2 
intersections and ignore the actual issue of scalability and the real-world application of their results.
Additionally, these simulations often provide a more fine grained level of data (eg. data is provided in 1 second
intervals) than that of the real world data which typically has longer collection intervals. These simulations
also allow for ease of training since the simulation also provides the time, location and duration of any incident,
something that is not easily obtained (although I have such data for this project and will use it for validation).

Detection
---------

The use of HTM for this project was inspired by the [htmengine-traffic-tutorial]
(https://github.com/nupic-community/htmengine-traffic-tutorial), however, this project was limited to single input models 
using [htmengine](https://github.com/numenta/numenta-apps/tree/master/htmengine), but I wanted to see how multi-input
models would work for my dataset. So I based my code off of that in the 
[hot gym anomaly tutorial](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/anomaly).

This project uses a model per intersection, where each input is a single sensor. Each sensor looks at a particular
lane and does not record turning movements, only vehicles passing a sensor. Intersections have at least 8 and at most 
24 sensors. The large number of model inputs should be easily handled by the use of a purpose built server with 64GB 
RAM and 15TB of RAID5 permanent storage.

Dataset
-------
The data for this project is supplied by the 
[Flinders Transport Systems Centre](http://www.flinders.edu.au/science_engineering/csem/research/centres/tsc/) and is 
thus not available for public use. Currently, I have 7 years of historical data encompassing 3.5TB for the entire city
of Adelaide. The data is stored in *mongodb* in the following format:

````
{
    "readings" : { 
        "8": 60, 
        "16": 32, 
        "24": 37, 
        "32": 25 , 
        "40": 11, 
        "48": 7, 
        "56": 8, 
         "64": 6,
    },
    "site_no" : "46",
    "datetime" : ISODate("2010-01-29T09:15:00.000Z")
}
````

The readings are a dict that maps the sensor's ID to the vehicle count at that time. Sometimes, these sensors output
an error value of 2046 or 2047 indicating physical damage or detector error respectively. In the application, these 
values are ignored and passed to the models as null values. Future work will seek to fill in these error gaps using 
some form of prediction.

Usage
-----
0. Make sure you've got a suitable version of python installed (preferably in a virtualenvironment) with nupic
1. Import the SCATS data into your mongo instance
   * Make sure you've mongodb installed and in your path
   * Use mongoimport to import the data files (contact me if you really want them since they're private):
    Invocation might look like
    ````
    mongoimport --db htm_adelaide --collection readings --file readings.json
    mongoimport --db htm_adelaide --collection crashes --file crashes.json --numInsertionWorkers 3
    mongoimport --db htm_adelaide --collection locations --file locations.json
    ````

   * If your instance is not on your machine, you'll need to provide `--host`, `--port`, `--username` and `-password`
   parameters
   * For additional information refer to the documentation on [mongo import](https://docs.mongodb.org/v3.0/reference/program/mongoimport/)
   * Once imported, make sure everything is indexed properly by running from the mongo client `mongo`:
    ````
    db.crashes.createIndex({datetime: 1})
    db.crashes.createIndex({loc: "2dsphere"})
    db.locations.createIndex({intersection_number: 1})
    db.locations.createIndex({loc: "2dsphere"})
    db.readings.createIndex({datetime: 1})
    db.readings.createIndex({site_no: 1})
    ````
2. Create a `connection.yaml` file in the root directory with:
   * mongo_uri: (`string`) mongo connection URI
   * mongo_database: (`string`) mongo database to use
   * mongo_collection: (`string`) mongo collection to get vehicle flow data from
   * GMAPS_API_KEY: (`string`) google maps api key for use with site
   * MODEL_PARAMS_DIR: (`directory`) folder where model params will be stored
   * MODEL_CACHE_DIR: (`directory`) folder where models are serialised to 
   * SWARM_CONFIGS_DIR: (`directory`) folder where swarm configurations are stored
   * max_vehicles: (`int`) highest number of vehicles allowed per time period (200 is a good value)

3. Run the model using `index.py` and evaluate anomaly results

##### Viewing the results

1. Navigate to `htm-site` folder 
2. Run `python setup.py develop`
3. Run the server with `pserve development.ini`
4. Access the site on http://127.0.0.1:8070
5. I only have data for the CBD area, so click on a marker and follow the link to see it's information
6. To go to a specific intersection, use the url: http://127.0.0.1:8070/intersection/3083
7. You should be able to see anomalies if they've been analysed, along with the raw readings. You can select which sensor
you want to show for by clicking the dropdown above the readings chart or using the link in the info. The anomaly chart
shows green points as actual crashes. The orange points are times when the engine thinks an incident has occurred, each
0.1 increment above zero for the orange points is 1 sensor in an "accident" state.
8. To zoom in on any chart, just click and drag, to zoom out, double click anywhere on the chart.
9. To widen the radius used in the crash search, click the radius button and select your range.

##### Don't feel like downloading 20MB pages?

If you're running nginx, you can use it take the output of the webapp, gzip and send it to you which should make
each page a 1.2MB file. Follow the instructions in [htm-site](https://github.com/JonnoFTW/htm-models-adelaide/tree/master/htm-site) for more.



##### Engine Arguments

* `--write-anomaly` : Write the anomaly score, predictions and anomaly likelihood back into the document
* `--all`: Run all readings through models in parallel (can you specify a comma separated list of intersections with 
`--intersection` with this option, eg. `--all --intersection 3001,3002,3085`)
* `--intersection`:  Name of the intersection(s) to process
* `--incomplete`: Only process those readings without anomaly values
* `--popular`: Show the most popular sensor for an intersection
* `--cache-models`: Attempt to load models from cache and store them to disk
* `--multi-model`: Use one model per sensor for the intersection (as opposed to making a single model that ues each
 sensor as an input). This mode will take longer and runs each model on a separate process.
###### Examples

To run all the data for an intersection against a model do:

`./index.py --intersection 3083 --write-anomaly --multi-model`

To run all models in parallel do:

`./index.py --all --write-anomaly --multi-model`

Results
-------
Results will be stored in mongodb, alongside the readings for a particular intersection
at a particular time, the prediction and anomaly score and anomaly likelihood will be saved.

TODO
----

* Create a web service similar to the tutorial one to show a map of intersections and their anomaly states
* Create a warning system that sends an alarm when anomalous traffic is observed that may indicate an incident
* Have the data streamed in from the SCATS service in real time.
* Possibly link neighbouring models together, so that upstream and downstream flows are taken into account, although
the inputs of upstream/ downstream intersections can just be fed into the model.
* Allow different prediction frameworks to be use and cross evaluated with HTM. Candidate algorithms based on my
initial literature review of outlier predictors are:
  * BIRCH 
  * CluStream 
  * D-Stream
  * DenStream