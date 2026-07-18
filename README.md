# Simulator: vcfogsim

## Introduction
This software is a simulation tool designed to model and analyze volunteer fog computing environments. It allows researchers and developers to simulate various scenarios in fog computing, including resource allocation, task scheduling, and network performance. The main goal of this simulator is to deploy task allocation algorithms in a volunteer fog computing enviroment and check the performance of the algorithms in terms of energy consumption, task completion time, and other relevant metrics.

## Folders
- `input`: Contains input file templates for the simulation.
- `output`: Contains output files provided by simulation.
- `tests`: Contains test file cases for configuring simulation.
- `models`: Contains the ML models used for baseline placement algorithm PNP.

## Installation
### Requirements
 - mongoDB
 - Python 3.6+

To install the simulator, follow these steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/vcfogsim/vcfogsim.git
   ```
2. Navigate to the project directory:
   ```bash
   cd vcfogsim
   ```
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   
5. Start the MongoDB service:
   ```bash
   mongod
   ```
6. Run the simulator:
   ```bash
   python test_manager.py
   ```
## Usage

### Scenarios
In input file contain templates how to define scenario p.e 'input/test_exp_1_short_input.txt'

```text
# periods servers,(A: automatic coordenates) users, number of intervals band, number of type of users, number of disruptions
1440	1	0	5	4	0
#map-file and district or string None
map_bcn.json	Eixample
# servers
# cpu hd bd type_server:
# type_server is the average time of working time/day
# If type server is dedicated is running all day => 1440 minutes.
# Capacities: CPU Mem Hdd type server: dedicated = D, good = H, medium = M, bad = L
30000	4000	128	L
# users
None
# period compu_time req_period server cpu mem hdd x y
# daily (0-1440) band thresholds
# from to lambda (jobs/minute)
0	200	0.0166666666666667
200	420	2
420	720	5
720	1100	2
1100	1440	0.0166666666666667
# for random users according to type
# cpu mem hdd probability
30000	4000	128	0.1
3000	800	1.28	0.3
7500	200	1.28	0.3
1500	200	32	0.3
```

To configure a simulation is required to edit file 'tests/tests2Run.txt' p.e

```text
# instance time(minuts) seed_users seed_servers type_exec:(simulation 0 heuristic 1) type_placement (0 random 1 nearest_server 2 k_nearest_server 3 predictive) radio_servers (meters) seed_for_models
test_exp_1	100	123456789	123456789	0	10	map_bcn.json	Gracia	0	250	123456789
```