import math
import random
import numpy as np

class Behavour:

    ID = 0
    # def __init__(self,seed_servers,seed_users):
    #
    #     self.seed_users = seed_users
    #     self.seed_servers = seed_servers
    #
    #     self.users_random = random.Random(seed_users)
    #     self.users_n_random = np.random.default_rng(seed_users)
    #
    #     self.servers_random = random.Random(seed_servers)
    #     self.servers_n_random = np.random.default_rng(seed_servers)
    @classmethod
    def reset(cls):
        cls.ID = 0

    def __init__(self,seed_users,seed_servers):

        self.seed_users = seed_users
        self.seed_servers = seed_servers
        self.random_gen = {}
        self.random_gen_n = {}

        self.create_random(self,use_seed_users=True)

    def create_random(self,object,use_seed_users):

        seed = self.seed_users
        if not use_seed_users:
            seed = self.seed_servers
        self.random_gen[object] = random.Random(seed+Behavour.ID)
        self.random_gen_n[object] = np.random.default_rng(seed+Behavour.ID)
        Behavour.ID += 1

    def get_random(self,obj):
        try:
            return self.random_gen[obj]
        except:
            # self.create_random(obj)
            # return self.random_gen[obj]
            raise Exception

    def get_random_n(self,obj):
        try:
            return self.random_gen_n[obj]
        except:
            # self.create_random(obj)
            # return self.random_gen_n[obj]
            raise Exception

    def p(self,t, L, p_e, t_e):
        # k es el tiempo a partir del cual la función de probabilidad (sigmoide) está entre p y 1
        k = -math.log(1 / p_e - 1)
        # alpha es el factor que modifica la funcion de probabilidad (sigmoide) para configurar el tiempo de encendido t_e
        alpha = k / t_e
        return 1 / (1 + math.exp(-alpha * (2 * t - 2 * L - t_e)))

        # Función de probabilidad de encendido (transición) diaria:
        #      t es el tiempo (variable indep.)
        #      L1 minuto del día que comienza el proceso de encendido
        #      L2 minutos del día que quedan finalizar el dia
        #      p_e define la probabilidad de estar encendido (~1 teoricamente)
        #      t_e es el tiempo de encendido (tiempo en min en que la probabilidad de estar encendido pasa de 0 a p)
        #      P periodo en minutos (1440)
        # NOTA: Se está suponiendo que el tiempo de encendio y apagado son los mismos.


    # def T(t, L1, L2, p_e, t_e, P):
    #     if t <= (L1 + L2) / 2:
    #         return p(t, L1, p_e, t_e)
    #     else:
    #         return p(P - t, L1, p_e, t_e)

    def T(self,t, L1a, L2a, p_e, t_e):
        S = lambda x: 1 / (1 + math.exp(-x))
        k = -math.log(1 / p_e - 1)
        alpha = k / t_e

        if t < (L1a + L2a) / 2:
            return S(alpha * (2*t - 2*L1a + t_e))
        else:
            return S(alpha * (2*L2a - 2*t + t_e))


        # Función que genera el tiempo de disponibilidad del servidor y el minuto del día "alrededor del cual" se encenderá. Los parámetros
        # necesarios son:
        #     WT tiempo minimo de funcionamiento del servidor en minutos
        #     sigma variación en el tiempo minimo de funcionamiento (sigma) en minutos
        #     n fiabilidad en tiempo minimo de funcionamiento del servidor (1, 2 o 3) 68%, 95%, 99.7% (1-sigma, 2-sigma, 3-sigma)


    def AT(self,obj,WT,sigma, n, t_e, T=None):
        if T is None:
            T = int(self.get_random_n(obj).normal(WT + n * sigma, sigma, 1)[0])
            while T < 0 or T > 1440:
                T = int(self.get_random_n(obj).normal(WT + n * sigma, sigma, 1)[0])

        mu = self.get_random_n(obj).integers(0, 1440 - T-2*t_e,size=1,endpoint=True)[0]
        return T, mu  # this T must the same for the H servers

        # Función que genera los momentos L1 (minuto en que comienza el proceso de encendido) y el momento L2 (minuto en que acaba
        # el proceso de apagado). Los parámetros necesarios son:
        #      AT tiempo de disponibilidad del sevidor (Availability time) generado por la función AT(WT, sigma, n)
        #      mu minuto del día "alrededor del cual" se encenderá el servidor, generado por la función AT(WT, sigma, n)


    def L1L2(self,obj,AT,mu,t_e,type_server):

        if type_server == "L":
            #TODO: revisar si es correcto
            # sigma = min(mu, 1440 - AT - mu - 2*t_e)
            sigma = min(max(mu,1), 1440 - AT - mu - 2*t_e)
        elif type_server == "M":
            sigma = 2*t_e
        else:
            sigma = t_e/2

        # L1 is CT    print(mu,sigma)
        L1 = int(self.get_random_n(obj).normal(mu, sigma, 1)[0])
        # ensure L1 is in the range (0, 1440 - AT)
        while L1 <= 0 or L1 > (1440 - AT - 2*t_e):
            L1 = int(self.get_random_n(obj).normal(mu, sigma, 1)[0])
            print(mu,sigma,1440 - AT - 2*t_e,"recalculating L1",L1)
        L1a = L1 + t_e
        L2a = AT + L1a
        return L1a, L2a # 1440-L2-L1