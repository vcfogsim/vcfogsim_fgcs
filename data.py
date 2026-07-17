import pymongo

# Create a MongoDB database and two collections
class Data:

    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")

        if "EUA_db" in self.client.list_database_names():
            self.client.drop_database("EUA_db")
        self.db = self.client["EUA_db"]

        # Create two collections (tables)
        self.server_data = self.db["servers_data"]
        self.user_data = self.db["users_data"]
        self.event_data = self.db["events_data"]

     # Insert data into the "server_data" collection
    def insert(self,data,table):
        if table == "server":
            self.server_data.insert_one(data)
        elif table == "user":
            self.user_data.insert_one(data)
        elif table == "event":
            self.event_data.insert_one(data)

    # Query data from the "server_data" collection
    def query_trace(self,table):
        if table == "server":
            return self.server_data.find()
        elif table == "user":
            return self.user_data.find()
        elif table == "event":
            return self.event_data.find()


    # Close the MongoDB connection
    def close(self):
        self.client.close()