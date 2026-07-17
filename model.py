import simpy as sim
from user import gen_users
from monitoring import Monitoring, run_monitoring

class Model:

    def __init__(self,users,servers=[],total_periods=0,max_duration=0,users_rate=0,input=None,district=None,
                 placement=None,data=None,ml=None):

        self.users = users
        self.servers = servers
        self.district = district
        self.placement = placement
        self.users_rate = users_rate
        self.max_duration = max_duration
        self.total_periods = total_periods
        self.db = data
        self.ml = ml
        self.input = input

    def run(self):

        self.env = sim.Environment()

        self.monitoring = Monitoring(self.env, self.users, self.servers,db=self.db)
        #self.monitoring = Monitoring(self.env,self.users,self.servers,db=Data())
        run_monitoring(self.env,self.monitoring)

        for server in self.servers:
            server.env = self.env
            server.monitoring = self.monitoring
            server.cpu = sim.Container(self.env,capacity=server.cpu,init=server.cpu)
            server.hdd = sim.Container(self.env, capacity=server.hdd, init=server.hdd)
            server.mem = sim.Container(self.env, capacity=server.mem, init=server.mem)
            server.run_server()

        if self.users==[]:

            self.env.process(gen_users(self, self.max_duration,self.users,self.district,self.input))
        else:
            for user in self.users:
                user.monitoring = self.monitoring

                user.run_user(self.env,self.servers)

        # Starting data, ML and placement
        self.ml.run(self.env)

        #TODO: To decide how to set the time of simulation
        #From test or from instance
        self.env.run(until=self.total_periods)

        # close database
        #mongoDB
        #self.db.close()
        print("END SIMULATION")
        return self.monitoring