import os
import simulation
from sys import platform
from behavour import Behavour
from inputs import readInputs
from monitoring import Solution, get_map

class Test():

    def __init__(self,name,seed_users,seed_servers,seed_for_models,time,type_exec,placement_type,radio_servers=250):
        self.instance = name
        #TODO: What is this time? The simulation time is from is relative to test or to instance
        self.time = time
        self.seed_users = seed_users
        self.seed_servers = seed_servers
        self.seed_for_models = seed_for_models

        self.type_exec = type_exec
        self.input = None
        if platform == "linux":
            os.system('export PATH=$PATH:"/opt/ibm/ILOG/CPLEX_Studio_Community129/cplex/bin/x86-64_linux/"')
        # self.behavour = Behavour(seed_servers, seed_users)
        # Necessary for random number generator
        Behavour.reset()
        self.behavour = Behavour(seed_users,seed_servers)
        self.place_type = placement_type
        self.radio_servers = radio_servers


class TestManager():

    def __init__(self):
        pass

    def run(self):

        baseModels = 'models'
        baseInput = 'inputs'
        baseTest = 'tests'
        baseOuput = 'outputs'
        baseImages = 'images'
        suffix_input = '_input.txt'
        suffix_output = '_output.txt'
        tests_file = 'tests2Run.txt'
        tests_file_path = baseTest + os.sep + tests_file

        tests = self.readTests(tests_file_path)

        for test in tests:

            input_file = baseInput + os.sep + test.instance + suffix_input
            input = readInputs(input_file,test)
            test.input = input

            if test.type_exec == 0:

                monitoring = simulation.run(input)
                #print(monitoring)
                solution = Solution(monitoring,input)
                # solution.report()
                # solution.gantt_chart()
                solution.get_trace('events')
                #solution.gen_data()
                #solution.get_servers_plot_ind(input.nPeriods)
                solution.get_plots(input.nPeriods)
                solution.get_server_levels_plot(input.nPeriods)
                solution.plot_servers_users()
                solution.print_statistic()
                #get_map(monitoring,baseImages)
                # solution.get_users_levels_plot(input.nPeriods)


    def readTests(self,test_file):

        tests = []
        with open(test_file) as file:
            for line in file:
                if line[0] != '#' and line[0] != '\n':
                    if '\n' in line:
                        line = line[:-1]
                    tokens = line.split('\t')
                    instance = tokens[0]
                    time = int(tokens[1])
                    seed_users = int(tokens[2])
                    seed_servers = int(tokens[3])
                    type_exec = int(tokens[4])
                    placement_type = int(tokens[8])
                    radio_server = int(tokens[9])
                    seed_for_models = int(tokens[10])
                    tests.append(Test(instance,seed_users,seed_servers,seed_for_models,time,type_exec,placement_type,radio_server))
        return tests


if __name__=='__main__':
    tm = TestManager()
    tm.run()