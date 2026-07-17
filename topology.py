class Route_Request_packet:
    def __init__(self ,source ,destination ,sequence_number):
        self.type = 'Route_Request'
        self.source = source
        self.destination = destination
        self.sequence_number = sequence_number

class Route_Reply_packet:
    def __init__(self ,source ,destination ,next_hop ,sequence_number):
        self.type = 'Route_Reply'
        self.source = source
        self.destination = destination
        self.next_hop = next_hop
        self.sequence_number = sequence_number

# On-demand Distance Vector Routing Protocol
class algorithm_OVDV:
    def __init__(self,env,nodes,route_timeout=300):
        # Data Structures
        self.env = env # Simpy environment
        self.nodes = nodes # List of nodes in the network
        self.routing_table = {}  # Node's routing table
        for node in self.nodes:
            self.routing_table[node] = {} # Routing table for each node

        self.sequence_number = 0  # Sequence number for each node

        self.active_routes = {}   # Active routes maintained by nodes
        for node in self.nodes:
            self.active_routes[node] = {} # Active routes for each node

        self.route_timeout = route_timeout # Timeout for inactive routes

    # Broadcast Process
    def broadcast(self,packet):
        for node in self.nodes:
            self.handle_packet(node,packet)

    # Route Request Process
    def route_request(self,origen,destination):
        self.sequence_number += 1
        packet = Route_Request_packet(origen,destination,self.sequence_number)
        self.broadcast(packet)

    def handle_route_request(self,current_node,packet):
        source = packet.source
        destination = packet.destination
        if destination in self.routing_table[current_node]:
            source,next_hop = self.routing_table[current_node][destination]
            # Send Route Reply back to the source
            send(Route_Reply_packet(source, destination, next_hop, packet.sequence_number))

    # Route Reply Process
    def handle_route_reply(self,current_node,packet):
        if packet.destination == current_node:
            # Update routing table with received information
            self.update_routing_table(packet.source, packet.destination, packet.next_hop)

    # Route Maintenance
    def update_routing_table(self,source, destination, next_hop):
        self.routing_table[destination] = (source, next_hop)
        self.active_routes[destination] = self.env.timeout

    def check_routes(self):
        for route in self.active_routes:
            # Check if route has time out
            # TODO: find out if we have to use time simulation
            if (self.env.timeout - self.active_routes[route]) > self.route_timeout:
                # Remove inactive routes from routing table
                del self.routing_table[route]
                del self.active_routes[route]

    # Packet Handling
    def handle_packet(self,current_node,packet):
        if packet.type == 'Route_Request':
            self.handle_route_request(current_node,packet)
        elif packet.type == 'Route_Reply':
            self.handle_route_reply(current_node,packet)

    # Main Loop
    def __run__(self):
        while True:
            yield self.env.timeout(1)
            self.check_routes()

    def run(self):
        self.env.process(self.__run__())
