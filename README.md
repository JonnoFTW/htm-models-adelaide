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
    "readings" : [ 
        {"vehicle_count" : 60, "sensor" : "8"}, 
        { "vehicle_count" : 32,"sensor" : "16"}, 
        {"vehicle_count" : 37,"sensor" : "24"}, 
        {"vehicle_count" : 25,"sensor" : "32" }, 
        {"vehicle_count" : 11,"sensor" : "40"}, 
        { "vehicle_count" : 7,"sensor" : "48"}, 
        {"vehicle_count" : 8,"sensor" : "56"}, 
        {"vehicle_count" : 6,"sensor" : "64"}
    ],
    "site_no" : "46",
    "datetime" : ISODate("2010-01-29T09:15:00.000Z")
}
````

Usage
-----

1. Import the SCATS data
2. Use `create_swam_config.py` to generate a swarm configuration for the target intersection
3. Run the swarm using `index.py` to generate the model parameters.
4. Run the model using `index.py` and evaluate anomaly results

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