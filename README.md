# Simulator: vcfogsim

## Introduction
This software is a simulation tool designed to model and analyze volunteer fog computing environments. It allows researchers and developers to simulate various scenarios in fog computing, including resource allocation, task scheduling, and network performance. The main goal of this simulator is to deploy task allocation algorithms in a volunteer fog computing enviroment and check the performance of the algorithms in terms of energy consumption, task completion time, and other relevant metrics.

## Folders
- `input`: Contains input file templates for the simulation.
- `output`: Contains output files provided by simulation.
- `tests`: Contains test file cases for configuring simulation.
- `models`: Contains the ML models used for baseline placement algorithm PNP.
- 'notebooks': Contains Jupyter notebooks for data analysis and visualization.


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





