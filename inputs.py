import os
from user import User
from data import Data
from sympy import Interval
from ML import Predictions
from behavour import Behavour
from my_placement import ExtendedPlacement as Placement  # swap to add new types
from server import VolunteerServer, RegularServer
from nodes import generate_random_location, get_district

class Input:
    def __init__(self,periods,test):

        self.users = []
        self.servers = []
        self.nPeriods = periods
        self.ml = None
        self.db = None
        self.district = None
        self.placement = None
        self.test = test
        self.band_intervals = []
        self.users_lambdas = []
        self.users_resources = []
        self.users_prob = []
        self.disruptions = []

def __create_kdtree__(test,input):
    points = [(server.x,server.y) for server in input.servers]
    input.placement = Placement(test, points, input.ml, input.test.radio_servers)

def __create_machine_learning__(input):
    # data, test, behavior, days=30
    pred = Predictions(input.db,input.test,input.test.behavour,input.nPeriods)
    input.ml = pred

def __create_data_base__(input):
    input.db = Data()

def readInputs(instance,test):

    input = None
    current_folder = instance[:len(instance) - instance[::-1].find(os.sep)]

    # random number generator lnked to the test
    beh = test.behavour
    Behavour.reset()
    beh.create_random(test, use_seed_users=False)

    with (open(instance) as file):

        nUsers = 0
        nServers = 0
        nIntervals = 0
        n_type_users = 0
        n_disruptions = 0

        stage = 0
        lines = file.readlines()
        for nline,line in enumerate(lines):
            if '\n' in line:
                line = line[:-1]
            if line[0] != '#' and line[0] != '':
                tokens = line.split('\t')
                # print(tokens,stage)
                if stage == 0:
                    nPeriods = int(tokens[0])
                    nServers = int(tokens[1])
                    nUsers = int(tokens[2])
                    nIntervals = int(tokens[3])
                    n_type_users = int(tokens[4])
                    n_disruptions = int(tokens[5])
                    input = Input(nPeriods,test)
                    stage += 1

                elif stage == 1:
                    map, district = None, None
                    if len(tokens) == 2:
                        map,district = tuple(tokens)

                    stage += 1
                elif stage == 2:
                    cpu, hd, bd, prop, x, y = 0,0,0,0,0,0
                    if map != None:
                        cpu,mem,hdd,prop = tuple(tokens)
                        if input.district is None:
                            input.district = get_district(current_folder+os.sep+map,district)
                        x,y = generate_random_location(input.district,beh.get_random_n(test))
                    else:
                        cpu,mem,hdd,prop,x,y = tuple(tokens)

                    if prop == 'D':
                        input.servers.append(
                            RegularServer(int(float(cpu)),int(float(mem)),int(float(hdd)),nPeriods,x,y,input))
                    else:
                        input.servers.append(VolunteerServer(int(float(cpu)),int(float(mem)),int(float(hdd)),
                                                             nPeriods,prop,x,y,input))
                    nServers -= 1
                    if nServers == 0:
                        stage += 1
                elif stage == 3:
                    # TODO:  annulation this option
                    if nUsers > 0:
                        period, compu_time, period_req, servers, cpu, hd, bd = tuple(tokens)
                        input.users.append(User(int(float(period)), int(float(period_req)), int(float(cpu)),
                                                int(float(hd)), int(float(bd)), int(float(compu_time))))
                        input.users[-1].nearby_servers = [int(ser) for ser in servers.split('_')]
                    else:
                        stage += 1
                    nUsers -= 1
                elif stage == 4:
                    start, end, lambda_v = tuple(tokens)
                    input.band_intervals.append(Interval.Ropen(int(start),int(end)))
                    input.users_lambdas.append(float(lambda_v))

                    nIntervals -= 1
                    if nIntervals == 0:
                        stage += 1
                elif stage == 5:
                    cpu, mem, hdd, prob = tuple(tokens)
                    input.users_resources.append((float(cpu),float(mem),float(hdd)))
                    input.users_prob.append(float(prob))
                    if n_type_users-1==0:
                        stage += 1
                    n_type_users -= 1
                elif stage == 6:
                    if n_disruptions == 0:
                        stage += 1
                        continue
                    n_disruptions -= 1
                    severs_to_disr, start, duration = [int(v) for v in tuple(tokens)]
                    input.disruptions[severs_to_disr] = input.disruptions.get(severs_to_disr, []) + [(start, duration)]

        # Create a data structure for the placement
        # Geographic collocation of server such that can get the nearest server
        __create_data_base__(input)
        __create_machine_learning__(input)
        __create_kdtree__(test,input)
        input.users.sort(key=lambda x: x.arrival_time)

    return input