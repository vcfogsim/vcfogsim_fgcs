import simpy as sim
from enum import Enum
from nodes import Node
from nodes import generate_random_location
from monitoring import Event, put_trace_users, n_message_generator,TypeEvent


# class User_State(Enum):
#     USER_WAITING = 1
#     USER_ASSIGNED = 2
#     USER_PROCESSING = 3
#     USER_CREATED = 4
#     USER_EXPIRED = 5
#     USER_COMPLETED = 6

class User(Node):
    ID = 0

    # class dummy
    def __init__(self):
        pass
        # self.waiting_time:float = 0
        # self.assigned_time:float = 0
        # self.processing_time:float = 0
        # self.last_type_event:TypeEvent = TypeEvent.user_arrival
        # self.last_event_time:int = 0
        #self.state:User_State = User_State.USER_CREATED


    def print(self):
        return self.__str__()

    def run_user(self,env,servers):
        self.env = env
        env.process(self.laugh_user(env,servers))


    def __processing_event__(self,event):

        # only these events are interesting, user_completed, user_arrival, user_expired, user_server_assigned
        # - user_rejected_not_enough_resources
        # - user_rejected_not_enough_time
        # - user_rejected_all_servers_out
        # - user_interrupted

        '''
         1) Cada job se procesa en orden, el trabajo j+1 - j. Las reglas para calcular los tiempos son:

         # a) Para Waiting:
         # - user server_assigned - user_rejected_not_enough_resources
         # - user server_assigned - user_rejected_not_enoug_time
         # - user server_assigned - user_rejected_all_servers_out
         # - user server_assigned - user_interrupted

         # b) Assigned:
         # - user rejected_not enough resources - user_server_assigned
         # - user rejected_not enough time - user_server_assigned
         # - user interrupted - user_server_assigned (user_interrupted - user_lock_for_resources)

         # c) Processing:
         # - user_completed - user_server_assigned
         # - user_interrupted - user_server_assigned (user_interrputed - user_unlock_for_resources)

         2) user_arrival y user_expired son de control, no se utilizan en las reglas.
         '''


        if event.type_event in [TypeEvent.user_completed,
                                TypeEvent.user_arrival,
                                TypeEvent.user_expired,
                                TypeEvent.user_server_assigned,
                                TypeEvent.user_rejected_not_enough_resources,
                                TypeEvent.user_rejected_not_enough_time,
                                TypeEvent.user_rejected_all_servers_out,
                                TypeEvent.user_interrupted,
                                TypeEvent.user_unlock_for_resources,
                                TypeEvent.user_lock_for_resources,
                                TypeEvent.user_rejected_server_timeout]:


            # Para waiting:
            # - user server_assigned - user_rejected_not_enough_resources
            # - user server_assigned - user_rejected_not_enoug_time
            # - user server_assigned - user_rejected_all_servers_out
            # - user server_assigned - user_interrupted
            if event.type_event == TypeEvent.user_rejected_server_timeout:

                if self.last_type_event in [TypeEvent.user_arrival,TypeEvent.user_rejected_server_timeout]:
                    self.waiting_time += event.time_event - self.last_event_time

            elif event.type_event == TypeEvent.user_expired:

                if self.last_type_event == TypeEvent.user_rejected_server_timeout:
                    self.waiting_time += event.time_event - self.last_event_time

            elif event.type_event == TypeEvent.user_server_assigned:

                if self.last_type_event in [TypeEvent.user_rejected_not_enough_time,
                                            TypeEvent.user_rejected_not_enough_resources,
                                            TypeEvent.user_rejected_all_servers_out,
                                            TypeEvent.user_interrupted]:

                    self.waiting_time += event.time_event - self.last_event_time

            # b) Assigned:
            # - user rejected_not enough resources - user_server_assigned
            # - user rejected_not enough time - user_server_assigned
            # - user interrupted - user_lock_for_resources
            elif event.type_event in [TypeEvent.user_rejected_not_enough_time,
                                     TypeEvent.user_rejected_not_enough_resources,
                                     TypeEvent.user_interrupted]:

                if ((event.type_event == TypeEvent.user_rejected_not_enough_resources and self.last_type_event ==TypeEvent.user_server_assigned)\
                        or (event.type_event == TypeEvent.user_rejected_not_enough_time and self.last_type_event == TypeEvent.user_server_assigned)
                        or (event.type_event == TypeEvent.user_interrupted and self.last_type_event == TypeEvent.user_lock_for_resources)):
                    self.assigned_time += event.time_event - self.last_event_time

            # c) Processing:
            # - user_completed - user_server_assigned
            # - user_interrupted - user_unlock_for
            elif event.type_event in [TypeEvent.user_interrupted,TypeEvent.user_completed]:
                    if (event.type_event == TypeEvent.user_completed and self.last_type_event == TypeEvent.user_server_assigned) or \
                            (event.type_event == TypeEvent.user_interrupted and self.last_type_event == TypeEvent.user_unlock_for_resources):
                        self.processing_time += event.time_event - self.last_event_time


            if event.type_event == TypeEvent.user_completed or event.type_event == TypeEvent.user_expired:
                self.monitoring.total_scores["waiting"] += self.waiting_time
                self.monitoring.total_scores["assigned"] += self.assigned_time
                self.monitoring.total_scores["processing"] += self.processing_time

            self.last_event_time = event.time_event
            self.last_type_event = event.type_event


    def laugh_user(self,env,servers):

        yield env.timeout(self.arrival_time-env.now)

        msg =(f"User {self.id}, arrive at {env.now}, but arrival time was {self.arrival_time}, computation time "
            f"{self.comp}, and due time {self.due_time} {self.cpu} {self.mem} {self.hdd}")
        if self.id==2:
            print(msg)
        evnt = Event(self.monitoring, self, None, env.now, TypeEvent.user_arrival,msg)

        # mongoDB
        n_message_generator(evnt)

        while True:

            info,server = self.input.placement.get_server(self,self.input.test.place_type)
            self.number_calls_to_placement += 1
            self.number_servers_on_ratio += self.input.placement.number_servers_on
            #print(self.number_calls_to_placement,self.number_servers_on_ratio)
            '''
            info = 0 if ok, 1 if no server in coverage, 2 if no server on, if info == 1, 2 server is None
            '''

            if server is not None:

                try:
                    task = env.process(server.complete_task(self))
                    server.process_swith_off_list.append(task)
                    yield task
                    if task in server.process_swith_off_list:
                        del server.process_swith_off_list[server.process_swith_off_list.index(task)]

                except sim.exceptions.Interrupt:
                    msg = f"User {self.id} interrupted in server {server.id} at time {env.now}"
                    evnt = Event(self.monitoring,self, server,env.now, TypeEvent.user_interrupted, msg)
                    # mongoDB
                    self.__processing_event__(evnt)
                    n_message_generator(evnt)

            else:
                match info:

                    case 1:
                        msg = f"User {self.id} rejected at time {env.now} by all servers out of area coverage"
                        evnt = Event(self.monitoring, self, None, env.now, TypeEvent.user_rejected_all_servers_out, msg)
                    case 2:
                        msg = f"User {self.id} rejected at time {env.now} by all servers off"
                        evnt = Event(self.monitoring, self, None, env.now, TypeEvent.user_rejected_all_servers_off, msg)

                # mongoDB
                n_message_generator(evnt)
                self.__processing_event__(evnt)

            if self.done or self.due_time <= env.now:

                if self.done:
                    # print("User completed")
                    #mongoDB
                    event = Event(self.monitoring, self, server, env.now, TypeEvent.user_completed,
                          f"User {self.id} completed in server {server.id} at {env.now}")
                    n_message_generator(event)
                    self.monitoring.total_completed += 1
                else:
                    # print("User expired")
                    #mongoDB
                    event = Event(self.monitoring, self, None, env.now, TypeEvent.user_expired,
                          f"User {self.id} expired at {env.now};{self.cpu} {self.mem} {self.hdd}")
                    n_message_generator(event)
                    self.monitoring.total_expired += 1
                self.__processing_event__(event)
                self.monitoring.total_servers_on_by_job_call += self.number_servers_on_ratio/self.number_calls_to_placement
                # print(self.monitoring.total_servers_on_by_job_call,self.number_servers_on_ratio,self.number

                del self.monitoring.users[self.monitoring.users.index(self)]

                return
            else:
                yield env.timeout(1)

    def __str__(self):
        return f"User {self.id} {self.x} {self.y} {self.comp} {self.due_time}"

    def __del__(self):
         with open(self.input.test.instance+"_users.txt", "a") as f:
             f.write(f"id:{self.id} proc {self.processing_time} wait {self.waiting_time} assign {self.assigned_time}\n")
    #     self.monitoring.total_scores["assigned"] += self.assigned_time
    #     self.monitoring.total_scores["waiting"] += self.waiting_time
    #     self.monitoring.total_scores["processing"] += self.processing_time
    #     self.monitoring.total_servers_on_by_job_call += self.number_servers_on_ratio/self.number_calls_to_placement
    #     #print(self.monitoring.total_servers_on_by_job_call,self.number_servers_on_ratio,self.number_calls_to_placement)
    #     #print(f"id {self.id} Proc {self.processing_time} Wait {self.waiting_time} Assigned {self.assigned_time}")

    def add_data_user(self, time_arrival, due_time, cpu, mem, hdd, comp, x=0, y=0, input=None, placement=None):

        self.id = User.ID
        self.env = None
        self.cpu = cpu
        self.mem = mem
        self.hdd = hdd
        self.comp = comp
        self.arrival_time = time_arrival
        self.due_time = due_time
        self.monitoring = None
        self.done = False
        # self.nearby_servers=[]
        self.placement = placement
        self.resources = {"cpu":self.cpu,"mem":self.mem,"hdd":self.hdd}

        self.waiting_time:float = 0
        self.assigned_time:float = 0
        self.processing_time:float = 0
        self.last_type_event:TypeEvent = TypeEvent.user_arrival
        self.last_event_time:int = self.arrival_time
        self.number_calls_to_placement:int = 0
        self.number_servers_on_ratio:float = 0.0

        self.input = input

        #if self.ID <= 5:
        #    print("User",self.ID,x,y,"arrival",self.arrival_time,"due_time",self.due_time,)
        super().__init__(x, y)

        User.ID += 1


def gen_users(model,max_duration,l_users,district,input):

    # print("gen_users")
    def set_lamda(t):
        t = t % 1440
        for indx,interval in enumerate(input.band_intervals):
            if t in interval:
                return input.users_lambdas[indx]
        return input.users_lambdas[-1]

    while True:

        #create new empty user
        user = User()
        input.test.behavour.create_random(user,use_seed_users=True)

        lambda_value = set_lamda(int(model.env.now + 1))

        arrival = int(model.env.now+1)
        # due_time = random.randint(arrival+max_duration,arrival+max_duration*2)
        # duration = random.randint(1,max_duration)
        due_time = input.test.behavour.get_random(user).randint(arrival+max_duration,arrival+max_duration*2)
        duration = int(input.test.behavour.get_random(user).randint(1,max_duration))
        res = []

        t_users = list(range(len(input.users_prob)))
        t_user = input.test.behavour.get_random(user).choices(t_users,input.users_prob)[0]

        resources = input.users_resources[t_user]

        for r in resources:
            res.append(r)

        x,y = generate_random_location(district,input.test.behavour.get_random_n(user))
        user.add_data_user(arrival,due_time,*res,duration,x,y,input=input)
        #print("Time", model.env.now, "users", user.id, "arrival", arrival, "due_time", due_time, "comput", duration, "resources",res)
        user.monitoring = model.monitoring
        user.monitoring.total_jobs += 1

        #mongoDB
        put_trace_users(user)
        user.run_user(model.env,model.servers)

        #Placement
        l_users.append(user)

        #exp = random.expovariate(lambda_value)
        exp = input.test.behavour.get_random(user).expovariate(lambda_value)
        yield model.env.timeout(exp)