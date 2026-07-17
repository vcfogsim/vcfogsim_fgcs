import os
import math
import enum
import folium
import random
import simpy as sim
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.colors as mcolors
import scipy.interpolate as interpolate

class Event:
    def __init__(self,monitoring,origin,destination,time_event,type_event,message):
        self.monitoring = monitoring
        self.origin = origin
        self.destination = destination
        self.time_event = time_event
        self.type_event = type_event
        self.message = message

    def __str__(self):
        return f"{self.origin} {self.destination} {self.time_event} {self.type_event} {self.message}"

class TypeEvent(enum.Enum):

    user_arrival = 0
    user_expired = 8
    user_completed = 1
    user_interrupted = 6
    server_switched_on = 5
    server_switched_off = 4
    server_information = 10
    user_server_assigned = 3
    server_change_inventary = 7
    server_going_to_process_user = 2
    user_rejected_all_servers_out = 9
    user_rejected_all_servers_off = 11
    user_rejected_not_enough_time = 12 # job is rejected because time expired during execution
    user_lock_for_resources = 13
    user_unlock_for_resources = 14
    user_rejected_not_enough_resources=15
    user_rejected_server_timeout=16

class Monitoring:

    def __init__(self,env,users,servers,capacity=sim.core.Infinity,db=None):
        self.logs = []
        self.env = env
        self.servers = servers
        self.users = users
        self.capacity = capacity
        self.traces = ""
        self.database = db
        self.total_jobs:int = 0
        self.total_completed:int = 0
        self.total_expired:int = 0
        self.total_scores = {'waiting':0, 'assigned':0, 'processing':0}
        self.total_servers_on_by_job_call = 0.0

    def __str__(self):
        s=""
        self.db.query_trace()
        for log in self.logs:
            s+= f"{log.origin} {log.destination} {log.time_event} {log.status} {log.message}\n" #{log.message} \n"
        return s

class Solution:

    def __init__(self,monitor,input):
        self.test = input.test
        self.input = input
        self.monitor = monitor

        self.weigth_user_cost = 2  # Variable Cost
        self.weigth_server_cost = 10
        self.weigth_jobs_completed = 10  # Fixed Cost

        self.total_cost = 0
        self.user_cost = {}

        self.user_QoS = 0.0
        self.user_QoE = 0.0

        self.nb_machines_on = 0
        self.nb_jobs_completed = 0
        self.server_working_time = {}

        self.user_latency = {}
        self.user_latency_avg = 0
        self.user_cost = defaultdict(int)
        self.user_fails = defaultdict(int)

        self.throughput = 0
        self.completed_job = 0

        self.servers = {}


    def __objective_function__(self):

        self.monitor.logs.sort(key=lambda x: x.time_event)
        for event in self.monitor.logs:
            if event.status == TypeEvent.user_completed:
                self.user_latency[event.origin] = event.time_event - self.user_latency[event.origin]
                self.nb_jobs_completed += 1
                self.servers[event.destination][event.origin] =\
                    self.servers[event.destination][event.origin],event.time_event

            elif event.status == TypeEvent.server_switched_on:
                self.nb_machines_on += 1
                self.server_working_time[event.destination] = event.time_event
                if event.destination.prop == 1.0:
                    self.server_working_time[event.destination] = self.test.time \
                                                                  - self.server_working_time[event.destination]
            elif event.status == TypeEvent.user_arrival:
                self.user_latency[event.origin] = event.time_event

            elif event.status == TypeEvent.user_server_assigned:
                self.user_cost[event.origin] += self.weigth_user_cost
                if event.destination not in self.servers:
                    self.servers[event.destination] = {}
                self.servers[event.destination][event.origin] = event.time_event

            elif event.status == TypeEvent.user_interrupted:
                self.user_fails[event.origin] += 1
                self.user_latency[event.origin] = 0
                del self.servers[event.destination][event.origin]

            elif event.status == TypeEvent.user_rejected_not_enough_time or event.status == TypeEvent.user_rejected_all_servers_out or event.status == TypeEvent.user_rejected_all_servers_off:
                self.user_fails[event.origin] += 1
                self.user_latency[event.origin] = 0
                del self.servers[event.destination][event.origin]

            elif event.status == TypeEvent.server_switched_off:
                self.server_working_time[event.destination] = event.time_event \
                                                              - self.server_working_time[event.destination]
                self.nb_machines_on -= 1

        self.throughput = self.nb_jobs_completed / self.test.time
        self.completed_job = self.nb_jobs_completed/len(self.input.users)
        self.user_latency_avg = sum([self.user_latency[k] for k in self.user_latency])/len(self.user_latency)

        self.total_cost = self.weigth_server_cost * self.nb_machines_on + \
                          self.weigth_user_cost * sum([self.user_cost[k] for k in self.user_cost]) -\
                          self.weigth_jobs_completed*self.nb_jobs_completed/len(self.user_latency)

    def get_trace(self,table):

        with open('outputs'+os.sep+self.test.instance+"_output_.txt",'w') as g:
            g.write("time,server_id,on/off,cpu,mem,hdd,#jobs\n")
            for trace in self.monitor.traces:
                g.write(trace)
        #print(self.monitor.database.query_trace(table))

    def gen_data(self):
        with open('outputs'+os.sep+self.test.instance+"_output_.txt",'w') as g:
            # query_events = self.monitor.database.query_trace("event")
            # for row in query_events:
            #     if row['status'] == "TypeEvent.server_information":
            #         g.write(row['message']+'\n')
            query_events = self.monitor.database.query_trace("users")
            for row in query_events:
                g.write(row['user_id']+'\n')



    def get_users_plot(self,T=1440):

        plt.clf()
        total = 1
        nb_jobs = [(0,0)]
        jobs_completed = [(0,0)]
        jobs_caducated = [(0,0)]
        jobs_assigned = [(0, 0)]
        jobs_waiting = [(0, 0)]

        set_jobs = set()
        set_jobs_assigned = set()
        set_jobs_waiting = set()
        set_jobs_completed = set()
        set_jobs_caducated = set()

        query_events = self.monitor.database.query_trace("event")
        for row in query_events:
            if ((row['status'] == "TypeEvent.user_arrival") or (row['status'] == "TypeEvent.user_server_assigned") or
                    ("TypeEvent.user_rejected" in row['status']) or (row['status'] == "TypeEvent.user_interrupted") or
                    (row['status'] == "TypeEvent.user_expired") or (row['status'] == "TypeEvent.user_completed")):

                tokens = row['origin_id'].split(" ")
                if len(tokens) == 6:
                    origin,idd,posx,posy,comp,due = tokens
                else:
                    try:
                        origin, idd, prop = tokens
                    except:
                        print(tokens)

                if ('User' == origin):

                    if (idd not in set_jobs) and (row['status'] == "TypeEvent.user_arrival"):
                        total +=1
                        nb_jobs.append((len(set_jobs)+1,int(float(row['time']))))
                        set_jobs.add(idd)

                    if (idd not in set_jobs_assigned) and (row['status'] == "TypeEvent.user_server_assigned"):

                        jobs_assigned.append((len(set_jobs_assigned)+1,int(float(row['time']))))
                        set_jobs_assigned.add(idd)
                        if idd in set_jobs_waiting:
                            set_jobs_waiting.remove(idd)
                            jobs_waiting.append((len(set_jobs_waiting)-1, int(float(row['time']))))

                    elif (idd not in set_jobs_waiting) and (("TypeEvent.user_rejected" in row['status']) or
                                                            (row['status'] == "TypeEvent.user_arrival") or
                                                            (row['status'] == "TypeEvent.user_interrupted")):

                        jobs_waiting.append((len(set_jobs_waiting) + 1, int(float(row['time']))))
                        set_jobs_waiting.add(idd)

                        if idd in set_jobs_assigned:
                            set_jobs_assigned.remove(idd)
                            jobs_assigned.append((len(set_jobs_assigned)-1, int(float(row['time']))))

                    elif (idd not in set_jobs_completed) and (row['status'] == "TypeEvent.user_completed"):

                        jobs_completed.append(((len(set_jobs_completed)+1),int(float(row['time']))))
                        set_jobs_completed.add(idd)
                        nb_jobs.append((len(set_jobs) - 1, int(float(row['time']))))
                        set_jobs.remove(idd)

                        if idd in set_jobs_assigned:
                            set_jobs_assigned.remove(idd)
                            jobs_assigned.append((len(set_jobs_assigned)-1, int(float(row['time']))))

                        if idd in set_jobs_waiting:
                            set_jobs_waiting.remove(idd)
                            jobs_waiting.append((len(set_jobs_waiting)-1, int(float(row['time']))))

                    elif (idd not in set_jobs_caducated) and (row['status'] == "TypeEvent.user_expired"):

                        #jobs_caducated.append((100*((len(set_jobs_caducated)+1)/total),int(float(row['time']))))
                        jobs_caducated.append(((len(set_jobs_caducated) + 1), int(float(row['time']))))
                        set_jobs_caducated.add(idd)

                        nb_jobs.append((len(set_jobs)-1, int(float(row['time']))))
                        set_jobs.remove(idd)

                        if idd in set_jobs_assigned:
                            set_jobs_assigned.remove(idd)
                            jobs_assigned.append((len(set_jobs_assigned)-1, int(float(row['time']))))

                        if idd in set_jobs_waiting:
                            set_jobs_waiting.remove(idd)
                            jobs_waiting.append((len(set_jobs_waiting)-1, int(float(row['time']))))

                if (len(set_jobs)) != (len(set_jobs_assigned) + len(set_jobs_waiting)):
                    print("Error")

        #T = 1440
        plt.xlim([0, T+math.ceil(T/10)])
        y_limit = max(len(set_jobs), len(set_jobs_assigned), len(set_jobs_waiting), len(set_jobs_completed),
            len(set_jobs_caducated))
        plt.ylim([0,total+total*0.1])
        #plt.ylim([0, 100])

        print("Total users",total)

        labels = ['In system','Assigned','Waiting','Completed (%)','Expired (%)']
        colors = ['orange','red','green','blue','black']

        ax = plt.twinx()
        ax.set_ylim([0,100])

        plots = [nb_jobs,jobs_assigned,jobs_waiting,jobs_completed,jobs_caducated]
        lines = []
        for i,plot in enumerate(plots):
            y, x = zip(*plot)
            x,y = self.interpotale(x,y,T)
            #x, y = self.__normalise_plots(x, y, T)
            #x,y = self.__normalise_plots_v3(x,y,T)
            if i in (0,1,2):
                line, = plt.plot(x, y, color=colors[i], label=labels[i])
            else:
                y = [100*(i/total) for i in y]
                line, = ax.plot(x, y, color=colors[i], label=labels[i])
            lines.append(line)

        #plt.vlines(x=540, ymin=0, ymax=len(set_jobs_completed), colors='black', ls=':', lw=2, label='off_peak')
        #plt.vlines(x=720, ymin=0, ymax=len(set_jobs_completed), colors='black', ls=':', lw=2, label='peak')
        #plt.vlines(x=960, ymin=0, ymax=len(set_jobs_completed), colors='black', ls=':', lw=2, label='low_peak')
        #plt.vlines(x=1320, ymin=0, ymax=len(set_jobs_completed), colors='black', ls=':', lw=2, label='peak')
        for t in range(T):
            if t % 1440 == 0:
                plt.vlines(x=t, ymin=0, ymax=len(set_jobs_completed), colors='blue', lw=2, label='peak')

        #plt.xlabel('Time (minutes)')
        plt.ylabel('% of jobs')
        plt.legend(handles=lines)
        #plt.show()
        plt.savefig('outputs' + os.sep + self.test.instance + "_jobs_.png")

    def __normalise_plots(self,X, Y, T):

        T = T + 1
        px = 0
        nX, nY = [], []

        for x, y in zip(X[1:], Y[1:]):
            nX.extend(list(range(px, x)))
            nY.extend([y] * (x - px))
            px = x

        nX.extend(list(range(px, T)))
        nY.extend([Y[-1]] * (T - px))

        return nX, nY

    #def _get_state_times(self):

        # query_events = self.monitor.database.query_trace("event")
        #
        # nb_servers_on = 0
        # aggregated_time_jobs = {}
        # previous_time_jobs = {}
        # state_jobs = {}
        # for row in query_events:
        #
        #     if row['status'] in ("TypeEvent.user_arrival",
        #                          "TypeEvent.server_switched_on",
        #                          "TypeEvent.server_switched_off",
        #                          "TypeEvent.user_server_assigned",
        #                          "TypeEvent.user_expired",
        #                          "TypeEvent.user_completed",
        #                          "TypeEvent.user_not_enough_resources",
        #                          "TypeEvent.user_rejected_all_servers_out",
        #                          "TypeEvent.user_rejected_not_enough_time",
        #                          "TypeEvent.user_interrupted"):
        #
        #         if row['status'] not in ("TypeEvent.server_switched_on","TypeEvent.server_switched_off"):
        #             'User 0 2.2084301824920085 41.41055669436789 6 17'
        #
        #             job_id = int(row['origin_id'].split(" ")[1])
        #             time = int(float(row["time"]))
        #
        #             if row['status'] == "TypeEvent.user_arrival":
        #                 aggregated_time_jobs[job_id] = {"waiting":0, "assigned":0, "processing":0}
        #                 previous_time_jobs[job_id] = time
        #                 if nb_servers_on == 0:
        #                     state_jobs[job_id] = "waiting"
        #                 else:
        #                     state_jobs[job_id] = "assigned"
        #
        #             elif row['status'] == "TypeEvent.user_server_assigned":
        #
        #                 if state_jobs[job_id] == "waiting" and nb_servers_on!=0:
        #                     aggregated_time_jobs[job_id]["waiting"] += time - previous_time_jobs[job_id]
        #                     state_jobs[job_id] = "assigned"
        #                 # TODO: check if the job is assigned to a server
        #
        #             elif row['status'] == "TypeEvent.user_expired":
        #
        #                 if state_jobs[job_id] == "assigned":
        #                     aggregated_time_jobs[job_id]["assigned"] += time - previous_time_jobs[job_id]
        #                 elif state_jobs[job_id] == "waiting":
        #                     aggregated_time_jobs[job_id]["waiting"] += time - previous_time_jobs[job_id]
        #                 state_jobs[job_id] = "expired"
        #
        #             elif row['status'] == "TypeEvent.user_not_enough_resources":
        #                 if state_jobs[job_id] == "assigned":
        #                     aggregated_time_jobs[job_id]["assigned"] += time - previous_time_jobs[job_id]
        #                     state_jobs[job_id] = "waiting"
        #                 elif state_jobs[job_id] == "waiting":
        #                     aggregated_time_jobs[job_id]["waiting"] += time - previous_time_jobs[job_id]
        #                     state_jobs[job_id] = "waiting"
        #
        #             elif row['status'] == "TypeEvent.user_completed":
        #
        #                 aggregated_time_jobs[job_id]["processing"] += time - previous_time_jobs[job_id]
        #                 state_jobs[job_id] = "completed"
        #
        #             elif row['status'] == "TypeEvent.user_rejected_all_servers_out":
        #
        #                 if state_jobs[job_id] == "waiting":
        #                     aggregated_time_jobs[job_id]["waiting"] += time - previous_time_jobs[job_id]
        #                     state_jobs[job_id] = "waiting"
        #
        #             elif row['status'] == "TypeEvent.user_rejected_not_enough_time":
        #
        #                 if state_jobs[job_id] == "assigned":
        #                     aggregated_time_jobs[job_id]["assigned"] += time - previous_time_jobs[job_id]
        #                     state_jobs[job_id] = "waiting"
        #
        #             elif row['status']== "TypeEvent.user_interrupted":
        #                 if nb_servers_on == 0:
        #                     state_jobs[job_id] = "waiting"
        #                 else:
        #                     state_jobs[job_id] = "assigned"
        #                 aggregated_time_jobs[job_id]["processing"] += time - previous_time_jobs[job_id]
        #
        #             previous_time_jobs[job_id] = time
        #         else:
        #             if row['status'] == "TypeEvent.server_switched_on":
        #                 nb_servers_on += 1
        #             else:
        #                 nb_servers_on -= 1
        #
        # total_scores = {'waiting':0, 'assigned':0, 'processing':0}
        # for job in aggregated_time_jobs:
        #     for r in total_scores:
        #         total_scores[r] += aggregated_time_jobs[job][r]
        #print(self.monitor.total_scores)


    def __normalise_plots_v2(self,X, Y,T):
        nX = []
        nY = []

        i = 0
        for x, y in zip(X, Y):
            if i == 0:
                nY = [y] * len(range(x + 1))
                nX = list(range(x + 1))
            else:
                nY = nY + [nY[-1]] * len(range(nX[-1] + 1, x)) + [y]
                nX = nX + list(range(nX[-1] + 1, x)) + [x]
            i += 1
        x_end = list(range(nX[-1],T+1))
        y_end = [nY[-1]] * len(x_end)
        return nX+x_end, nY+y_end


    def __normalise_plots_v3(self,X,T):

        v,p0 =0,0
        nX,nY = [],[]
        for p in X:
            nX = nX+list(range(p0,p))
            nY = nY+[v]*(p-p0)
            v = 0 if v==1 else 1
            p0 = p
        return nX+list(range(p0,T)), nY+[0]*(T-p0)

    def get_plots(self,T=1440):
        self.get_users_plot(T)
        # self.get_plots_v2()
        self.get_servers_plot(T)

    def get_servers_plots_v2(self,T=1440):
        for server in self.input.servers:
            self.get_servers_plot_ind(server.id,T)

    def get_servers_plot_ind(self,T = 1440):

        def generate_random_colors(n):
            return [(random.random(), random.random(), random.random()) for _ in range(n)]

        n = 10  # Number of colors to generate
        random_colors = generate_random_colors(n)

        servers_on_time = {}
        query_events = self.monitor.database.query_trace("event")
        for row in query_events:

            tokens = row['origin_id'].split(" ")
            if len(tokens) == 4:
                origin, idd, posx, posy = tokens
            else:
                origin, idd, prop = tokens

            if 'Server' == origin:

                if row['status'] == "TypeEvent.server_switched_on":
                    # counting prop servers
                    if idd not in servers_on_time:
                        servers_on_time[idd] = [int(float(row['time']))]
                    else:
                        servers_on_time[idd].append(int(float(row['time'])))

                elif row['status'] == "TypeEvent.server_switched_off":
                    # counting prop servers
                    servers_on_time[idd].append(int(float(row['time'])))

        # T = 1440
        ylim = 1 + 5

        plt.xlim([0, T + 100])
        plt.ylim([0, ylim])

        lines = []
        #get 32 randoms colors
        colors = generate_random_colors(len(servers_on_time))
        #colors = ['red', 'green', 'blue', 'orange']

        k = 0
        for idd in servers_on_time:

            x = servers_on_time[idd]
            nx, ny = self.__normalise_plots_v3(x, T)
            line, = plt.plot(nx, ny, color=colors[k])
            lines.append(line)
            k += 1


        plt.xlabel("Time (minutes)")
        plt.ylabel("#Servers ON")

        #plt.legend(handles=lines)
        plt.show()

    def get_servers_plot(self,T = 1440):

        plt.clf()
        all_set_servers_on = set()
        all_nb_servers_on = [(0,0)]
        nb_servers_on = {'L':[(0,0)],'M':[(0,0)],'H':[(0,0)]}
        set_servers_on = {'L':set(),'M':set(),'H':set()}

        query_events = self.monitor.database.query_trace("event")
        for row in query_events:
            if ((row['status'] == "TypeEvent.server_switched_on") or (row['status'] == "TypeEvent.server_switched_off")):
                tokens = row['origin_id'].split(" ")
                if len(tokens) == 4:
                    origin, idd, posx, posy = tokens
                else:
                    origin, idd, prop = tokens

                if 'Server' == origin:

                    if (idd not in set_servers_on[prop]) and (row['status'] == "TypeEvent.server_switched_on"):
                        # counting prop servers
                        nb_servers_on[prop].append((len(set_servers_on[prop]) + 1, int(float(row['time']))))
                        set_servers_on[prop].add(idd)
                        # counting all servers
                        all_set_servers_on.add(idd)
                        all_nb_servers_on.append((len(all_set_servers_on), int(float(row['time']))))

                    elif (idd in set_servers_on[prop]) and (row['status'] == "TypeEvent.server_switched_off"):
                        # counting prop servers
                        nb_servers_on[prop].append((len(set_servers_on[prop]) - 1, int(float(row['time']))))
                        set_servers_on[prop].remove(idd)
                        # counting all servers
                        all_set_servers_on.remove(idd)
                        all_nb_servers_on.append((len(all_set_servers_on), int(float(row['time']))))

        #T = 1440
        ylim = len(self.input.servers) + 5

        plt.xlim([0, T + 100])
        plt.ylim([0,ylim])

        lines = []
        colors = ['red','green','blue','orange']
        symbol = ['o','x','+','*']
        for k,prop in enumerate(nb_servers_on):
            y, x = zip(*nb_servers_on[prop])
            x, y = self.interpotale(x, y, T)
            line, = plt.plot(x, y, color=colors[k], label='Servers '+prop, marker=symbol[k])
            lines.append(line)

        y, x = zip(*all_nb_servers_on)
        x, y = self.__normalise_plots_v2(x, y, T)
        line, = plt.plot(x, y, color=colors[k+1], label='All Servers')
        lines.append(line)

        #plt.vlines(x=540, ymin=0, ymax=len(self.servers), colors='black', ls=':', lw=2, label='off_peak')

        plt.yticks(list(range(0, ylim,5)))
        for i in range(0, T, 1440):
            plt.vlines(x=i, ymin=0, ymax=ylim, colors='black', ls=':', lw=1)

        plt.xlabel("Time (minutes)")
        plt.ylabel("#Servers ON")
        plt.legend(handles=lines)

        plt.savefig('outputs'+os.sep+self.test.instance+"_servers_on.png")

    def plot_servers_users(self):

        plt.clf()

        # Crear un grafo vacío
        G = nx.Graph()

        for server in self.input.servers:
            G.add_node(server.id, pos=(server.x, server.y))

        # Obtener las posiciones de los nodos
        pos = nx.get_node_attributes(G, 'pos')

        # Dibujar el grafo
        nx.draw(G, pos, with_labels=False, node_color='skyblue', node_size=2000, edge_color='gray', font_size=20,
                font_color='black', font_weight='bold')

        for idx,user in enumerate(self.monitor.database.query_trace("user")):
            G.add_node(idx, pos=(float(user['x']), float(user['y'])))

        # Obtener las posiciones de los nodos
        pos = nx.get_node_attributes(G, 'pos')

        # Dibujar el grafo
        nx.draw(G, pos, with_labels=False, node_color='red', node_size=20, edge_color='gray', font_size=20,
                font_color='black', font_weight='bold')

        # Mostrar el grafo
        plt.show()

    def interpotale(self,x,y,T):

        newx = list(range(0,T+1))
        f = interpolate.interp1d(x,y,kind="previous",fill_value="0",bounds_error=False)
        #newy = np.interp(newx,x,y)
        return newx,f(newx)

    def get_server_levels_plot(self, T=1440):

        plt.clf()
        capacities_total = [0,0,0]
        for server in self.input.servers:
            for i,m in enumerate(('cpu', 'mem', 'hdd')):
                capacities_total[i] += server.__getattribute__(m).capacity

        aggregated = {'cpu':[], 'mem':[], 'hdd':[]}
        for i,m in enumerate(('cpu', 'mem', 'hdd')):
            aggregated[m] =[(0,0)]

        query_events = self.monitor.database.query_trace("event")

        history = {}
        previous = {}
        for row in query_events:
            # check if event of level
            if row['status'] == "TypeEvent.server_change_inventary":

                tokens,msg = row['destination_id'].split(" "),row['message'].split(" ")
                server,idd,_ = tokens

                #cpu,hdd,bwd = msg
                levels = [float(x) for x in msg]
                #print(idd, levels, row['time'])

                print("-------------------------------------------------------------")
                if idd not in previous:
                    for i, m in enumerate(('cpu', 'mem', 'hdd')):
                        previous[idd] = []
                        total = aggregated[m][-1][0] + levels[i]
                        aggregated[m].append((total,float(row['time'])))
                    history[idd] = [levels]
                elif idd in previous:
                    for i,m in enumerate(('cpu','mem','hdd')):
                        # variation of server idd in feature m from previous event
                        dx = previous[idd][i]-levels[i]
                        # total accumalted till this previous event of ferature m
                        total = aggregated[m][-1][0] - dx
                        aggregated[m].append((total,float(row['time'])))
                    history[idd].append(levels)
                previous[idd] = levels

                print(('cpu',aggregated['cpu'][-1]),('mem',aggregated['mem'][-1]),('hdd',aggregated['hdd'][-1]),sep='\n')

        ylim = 100
        plt.xlim([0, T + 100])
        plt.ylim([0, ylim])

        lines = []
        features = ['Cpu','Mem','Hdd']
        colors = ['red', 'green', 'blue']
        symbol = ['o', 'x', '+']
        for k, feature in enumerate(aggregated.keys()):
            y, x = zip(*aggregated[feature])
            y = [100*(c/capacities_total[k]) for c in y]
            x, y = self.interpotale(x,y,T)
            line, = plt.plot(x, y, color=colors[k], label=features[k], marker=symbol[k])
            lines.append(line)
        for i in range(0, T, 1440):
            plt.vlines(x=i, ymin=0, ymax=ylim, colors='black', ls=':', lw=1)

        plt.xlabel("Time (minutes)")
        plt.ylabel("% of resources available")

        plt.legend(handles=lines)
        #plt.show()

        plt.savefig('outputs' + os.sep + self.test.instance + "_servers_levels.png")


    def get_users_levels_plot(self, T=1440):

        capacities_total = [0,0,0]
        aggregated = {'cpu':[], 'mem':[], 'hdd':[]}
        for i,m in enumerate(('cpu', 'mem', 'hdd')):
            aggregated[m] =[(0,0)]

        query_events = self.monitor.database.query_trace("event")

        previous = set()
        maximum_quantities = {'cpu':0,'mem':0,'hdd':0}
        for row in query_events:
            # check if event of level
            if row['status'] == "TypeEvent.user_arrival" or row['status'] == "TypeEvent.user_expired":

                _,idd,_,_ = row['origin_id'].split(" ")
                resources = (row['message'].split(";")[1]).split(" ")

                levels = [float(x) for x in resources]

                print("-------------------------------------------------------------")
                if idd not in previous:
                    for i, m in enumerate(('cpu', 'mem', 'hdd')):
                        total = aggregated[m][-1][0] + levels[i]
                        aggregated[m].append((total,float(row['time'])))
                        if total > maximum_quantities[m]:
                            maximum_quantities[m] = total
                    previous.add(idd)
                elif idd in previous:
                    for i,m in enumerate(('cpu','mem','hdd')):
                        # total accumalted till this previous event of ferature m
                        total = aggregated[m][-1][0] - levels[i]
                        aggregated[m].append((total,float(row['time'])))
                    previous.remove(idd)

                print(('cpu',aggregated['cpu'][-1]),('mem',aggregated['mem'][-1]),('hdd',aggregated['hdd'][-1]),sep='\n')

        ylim = 100
        plt.xlim([0, T + 100])
        plt.ylim([0, ylim])

        lines = []
        colors = ['red', 'green', 'blue']
        symbol = ['o', 'x', '+']
        features = ['Cpu','Mem','Hdd']
        for k, feature in enumerate(aggregated.keys()):
            y, x = zip(*aggregated[feature])
            y = [100*(c/maximum_quantities[feature]) for c in y]
            x, y = self.interpotale(x,y,T)
            line, = plt.plot(x, y, color=colors[k], label=features[k], marker=symbol[k])
            lines.append(line)
        for i in range(0, T, 1440):
            plt.vlines(x=i, ymin=0, ymax=ylim, colors='black', ls=':', lw=1)

        plt.xlabel("Time (minutes)")
        plt.ylabel("% of resources available")

        plt.legend(handles=lines)
        plt.show()

    def gantt_chart(self):

        fig, ax = plt.subplots()
        for i,server in enumerate(self.servers):
            data = []
            for user in self.servers[server]:
                    data.append((self.servers[server][user],user.arrival_time))
            pos=(10*(i+1),9)
            ax.broken_barh(data,pos,facecolors='tab:blue')

        # ax.broken_barh([(110, 30), (150, 10), (10, 5)], (10, 9), facecolors='tab:blue')
        # ax.broken_barh([(10, 50), (100, 20), (130, 10)], (20, 9),
        #                facecolors=('tab:orange', 'tab:green', 'tab:red'))
        #
        # ax.broken_barh([(110, 30), (150, 10), (10, 5)], (10, 9), facecolors='tab:blue')
        ticks = [(15 + 10*i) for i in range(len(self.servers))]
        labels = ['S' + str(i + 1) for i in range(len(self.servers))]
        ax.set_yticks(ticks=ticks,labels=labels)
        ax.set_ylim(0, 10*len(self.servers)+10)
        ax.set_xlim(0, self.input.nPeriods)
        ax.set_xlabel('seconds since start')

        ax.grid(True)

        plt.show()

    def report(self):

        print("Throughput:",self.throughput)
        print(f"Ratio Job Completation: {100*self.completed_job}")
        print("Avg Latency:",self.user_latency_avg)
        print("Total Cost:",self.total_cost)

    def print_statistic(self):
        text = (f'total jobs;total completed;total expired\n{self.monitor.total_jobs};{self.monitor.total_completed};'
                f'{self.monitor.total_expired}')

        with open('outputs'+os.sep+self.test.instance+'_statistics_.txt','w') as f:
            f.write(text)
        print(self.monitor.total_scores)
        print(self.monitor.total_servers_on_by_job_call/self.monitor.total_jobs)
        print(text)


# def n_message_generator(user_id, arrival_time, final_time,server_id, out_pipe,status,reason):
def n_message_generator(event):

    origin = event.origin if event.origin != None else "None"
    destination = event.destination if event.destination != None else "None"
    trace = map(str,[origin,destination,event.time_event,event.type_event,event.message])
    lab = ["origin_id","destination_id","time","status","message"]
    e = dict(zip(lab,trace))

    # mongodb
    event.monitoring.database.insert(e,"event")

def put_trace_servers(env, monitor):
    while True:
        for server in monitor.servers:
            trace = [str(env.now),str(server.id)]
            if server.on:
                trace += [str(1),str(server.cpu.level),str(server.mem.level),str(server.hdd.level),
                          str(len(server.process_swith_off_list)),str(server.x),str(server.y)]
            else:
                trace += [str(0),str(0),str(0),str(0),str(0),
                          str(server.x),str(server.y)]
            trace = ','.join(trace)
            monitor.traces+=trace+"\n"

            #mongodb
            lab = ["time","server_id","on/off","cpu","mem","hdd","#jobs","x","y"]
            server_data = dict(zip(lab,trace.split(',')))
            monitor.database.insert(server_data,"server")

        ### TODO: improve this funcion because now we are not storing all data
        yield env.timeout(100)
        #yield env.timeout(1)

def put_trace_users(user):

    monitor = user.monitoring
    # now,user_id,arrival time, due time, computation time, cpu, hd, bw,
    trace = [str(monitor.env.now),str(user.id),str(user.arrival_time),str(user.due_time),str(user.comp),str(user.cpu),
             str(user.mem),str(user.hdd),str(user.x),str(user.y)]

    #mongodb
    lab = ["now","user_id","arrival","processing","expire","cpu","mem","hdd","x","y"]
    user_data = dict(zip(lab,trace))
    monitor.database.insert(user_data,'user')

def run_monitoring(env,monitor):
    env.process(put_trace_servers(env, monitor))

def get_map(monitor,base_images):
    # url = "https://leafletjs.com/examples/custom-icons/{}".format
    # icon_image = url("leaf-red.png")
    # shadow_image = url("leaf-shadow.png")

    icon = folium.CustomIcon(
        icon_image=base_images+os.sep+'laptop.png',
        icon_size=(100, 100),
        # icon_anchor=(22, 94),
        # shadow_size=(50, 64),
        # shadow_anchor=(4, 62),
        # popup_anchor=(-3, -76),
    )

    used = set()
    positions = []
    pos_user = []
    users = monitor.database.query_trace("user")
    for user in users:
        id = user['user_id']
        if id not in used:
            used.add(id)
            positions.append((float(user['y']),float(user['x'])))
            pos_user.append((float(user['y']),float(user['x'])))

    used = set()
    servers = monitor.database.query_trace("server")
    pos_server = []
    for server in servers:
        id = server["server_id"]
        if id not in used:
            used.add(id)
            positions.append((float(server['y']),float(server['x'])))
            pos_server.append((float(server['y']), float(server['x'])))

    lower_left = positions[0][0], positions[0][1]
    upper_right = positions[0][0], positions[0][1]
    for position in positions:

        if (position[0],position[1]) < lower_left:
            lower_left = position[0],position[1]

        if (position[0],position[1]) > upper_right:
            upper_right = position[0],position[1]

    m = folium.Map(location=[(lower_left[0] + upper_right[0]) / 2,
                             (lower_left[1] + upper_right[1]) / 2], zoom_start=13)

    # for position in pos_user:
    #     folium.Circle(location=[position[0], position[1]], icon=folium.Icon(color="red"), radius=1).add_to(m)

    for position in pos_server:
        folium.Marker(location=[position[0], position[1]], icon=icon, radius=8).add_to(m)

    # https: // matplotlib.org / 3.1.0 / gallery / color / named_colors.html
    colors = list(mcolors.CSS4_COLORS)

    m.save('outputs'+os.sep+'map.html')
    return m

def createHTMLRoutes(self, path, name, solution):
    routes_geo = []
    for aRoute in self.routes:
        route = []
        for edge in aRoute.edges:
            leg_geo = self.get_route(edge.origin.x, edge.origin.y, edge.end.x, edge.end.y)
            route.append(leg_geo)

        routes_geo.append(route)

    m = self.get_map(routes_geo)
    m.save(path + os.sep + name + '_routes.html')