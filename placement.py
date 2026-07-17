import math
import enum
import random
import numpy as np
from scipy.spatial import KDTree

class TypeError(enum.Enum):

    error_all_servers_off = 1
    error_all_servers_out_coverage = 2

class Placement:

    def __init__(self,test,points,ml,radio):

        self.ml = ml
        self.test = test
        self.radio = radio
        self.k2dtree = KDTree(points)
        self.number_servers_on:float = 0.0

    def __get_k_nearest_servers__(self,user, k=20):
        '''
        retorn the k nearest servers to the user in the radio coverage
        :param user:
        :param k:
        :return: list of servers can be empty if no server is in the radio coverage
        '''
        point = (user.x,user.y)

        servers = [s for s in self.test.input.servers]
        _,indexes = self.k2dtree.query(point,k)
        if not (type(indexes) is np.ndarray):
            indexes = [indexes]

        servers = [servers[i] for i in indexes]
        self.test.behavour.get_random(user).shuffle(servers)
        return self.__filter_servers__(user,servers)


    def __get_nearest_server__(self,user):
        '''
        get the nearest server to the user in the radio coverage
        :param user:
        :return:
        '''
        return self.__get_k_nearest_servers__(user, k=1)

    def __filter_servers__(self,user,servers):
        '''
        filter the servers by distance to the user
        :param user:
        :param servers:
        :return: list of servers in the radio coverage
        '''
        #TODO: distance matrix in constructor to avoid recomputing it every time


        dist = lambda params: math.acos(math.sin(math.radians(user.y))*math.sin(math.radians(params[1]))+
                                        math.cos(math.radians(user.y))*math.cos(math.radians(params[1]))*
                                        math.cos(math.radians(params[0])-math.radians(user.x)))*6371000

        distances = list(map(dist,[(server.x,server.y) for server in servers]))
        #print(distances)
        nb = len(servers)
        servers = [s for i,s in enumerate(servers) if distances[i]<=self.radio]
        self.number_servers_on = sum(1 for s in servers) #if s.on)

        return servers

    def __get_random_server__(self,user):
        '''
        get a permutation of server from the list of servers
        :param user:
        :return:
        '''

        servers = [server for server in self.test.input.servers]
        servers = self.__filter_servers__(user,servers)
        #servers = servers[:10]
        self.test.behavour.get_random(user).shuffle(servers)
        return servers


    def __check_resources__(self,user,server_id,t):
        for resource in user.resources:
            if user.resources[resource] > self.ml.get_prediction_level(server_id,resource,t):
                return False
        return True

    def __get_ML_server__(self,user):
        '''
        get a list o server that would be on in the radio coverage
        :param user:
        :return: info = 0 if ok, 1 if no server in coverage, 2 if no server on, list of servers or empty if no server found
        '''

        current_time = int(user.env.now)
        #servers = self.__get_k_nearest_servers__(user)
        servers = self.__get_random_server__(user)
        if servers == []:
            return 1,[]

        servers_on = []
        for server in servers:

            on_off,t_u = True, current_time
            while on_off and t_u < (current_time + 1 + user.comp):
                on_off = self.ml.get_prediction_on_off(server.id,t_u)>0.9
                t_u += 1

            if on_off: #and self.__check_resources__(user,server.id,current_time):
                servers_on.append(server)

        if servers_on == 0:
            return 2,[]
        return 0,servers_on

    def get_server(self,user,placement_type):
        '''
        :param user:
        :param placement_type: 0 - random, 1 - nearest, 2 - k nearest, 3 - ML
        :return:  info = 0 if ok, 1 if no server in coverage, 2 if no server on, first server or None if no server found
        '''

        info,servers = 0,None
        if placement_type == 0:
            servers = self.__get_random_server__(user)
        elif placement_type == 1:
            servers = self.__get_nearest_server__(user)
        elif placement_type == 2:
            servers = self.__get_k_nearest_servers__(user)
        elif placement_type == 3:
            try:
                info,servers = self.__get_ML_server__(user)
            except Exception as e:
                print("here",e)
        if servers == []:
            info = 1 if info == 0 else 2
            return info,None

        return info,servers[0]

