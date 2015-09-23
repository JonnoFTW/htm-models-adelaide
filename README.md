Traffic Anomaly Detection in Adelaide using HTM
===============================================

![Adelaide from the air](https://i.imgur.com/5STpTTNh.jpg "Adelaide in all its glory")


Introduction
------------
Adelaide uses SCATS for collecting traffic data (along with signal control) using induction loops beneath the road
to record the number of vehicles that go though a particular lane at an intersection. This data is provided in 5
minute intervals. Our goal is to use this flow data to determine the presence of an incident on a section of road
within a reasonable amount of time. Incidents are not restricted to accidents, they can also include:

* Breakdowns
* Spilled loads
* Natural disasters such as flooding and landslides
* Unscheduled maintenance
* Burst pipes 

It's imperative that the presence of these events is detected and responded to in a timely and appropriate manner 
by those working in a transport management center. The accuracy of these warnings is highly important as high 
false-positive rates result in fatigue and officers eventually ignoring alarms.

In the field of automated incident detection (AID), the problem of detecting incidents in an arterial road networks
is still an open problem. Current research is limited to supervised techniques that are typically run on
data collected in small scale traffic simulations that allow the researcher to easily optimise for 1 or 2 
intersections and ignore the actual issue of scalability and the real-world application of their results.
Additionally, these simulations often provide a more fine grained levelof data (eg. data is provided in 1 second
intervals) than that of the real world data which m. These simulations also allow for ease of training since the simulation 
also provides the time, location and duration of any incident.

The use of HTM for this project was inspired by a [tutorial provided here]
(https://github.com/nupic-community/htmengine-traffic-tutorial). This project was limited to single input models 
using [htmengine](https://github.com/numenta/numenta-apps/tree/master/htmengine), but I wanted to see how multi-input
models would work for my dataset. So I based my code of that in the 
[hot gym anomaly tutorial](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/anomaly).

Usage
-----

1. Import the SCATS data
2. Use `create_swam_config.py` to generate a swarm configuration for the target intersection
3. Run the swarm using `index.py` to generate the model parameters.
4. Run the model using `index.py` and evaluate anomaly results

TODO
----

* Create a web service similar to the tutorial one to show a map of intersections and their anamaly states
* Create a warning system that sends an alarm when anomalous traffic is observed that may indicate an incident
* Possibly link neighbouring models together, so that upstream and downstream flows are taken into account, although
the inputs of upstream/ downstream intersections can just be fed into the model.
* Allow different prediction frameworks to be use and cross evaluated with HTM. Candidate algorithms based on my
initial literature review of outlier predictors are:
  * BIRCH 
  * CluStream 
  * D-Stream
  * DenStream