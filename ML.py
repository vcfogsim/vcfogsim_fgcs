import os
import math
import random
import pickle
import numpy as np
import pandas as pd
from ngboost import NGBRegressor
from ngboost.distns import Normal
from ngboost.scores import LogScore
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import SMOTE
from imblearn.over_sampling import ADASYN
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor as RandomForrest

class Predictions:

    def __init__(self,data,test,behavior,periods=1440):

        self.data = data
        self.test = test
        self.P = 1440
        self.days = periods//self.P
        self.pred_onoff = {}
        self.pred_level = {}
        self.env = None
        self.behaviour = behavior
        #TODO: Introduce performance metrics of the models

    def run(self,env):
        self.env = env
        #while True:
            #yield self.env.timeout(self.P*self.days)
        if self.test.place_type == 3:
            self.__create_models__()

    def __transformation_vec__(self,length):
        # On/off prediction
        # Prepare data for periodic logistic regression
        # Create apply transformations to time taking account periods
        C = lambda t: math.cos(t * 2 * math.pi / self.P)
        S = lambda t: math.sin(t * 2 * math.pi / self.P)
        time = np.array([[C(t), S(t)] for t in range(length)])
        return time

    def __transformation__(self,t):
        # On/off prediction
        # Prepare data for periodic logistic regression
        # Create apply transformations to time taking account periods
        C = lambda t: math.cos(t * 2 * math.pi / self.P)
        S = lambda t: math.sin(t * 2 * math.pi / self.P)
        return [[C(t), S(t)]]

    # Create models for each server
    def __create_models__(self):

        # check if each server has two models: on/off and level
        for server in self.test.input.servers:

            # TODO: introduce new parameter to choose the seed for the models
            file_path_on_off = 'models'+os.sep+self.test.instance+os.sep+'server_'+str(server.id)+f'_{self.test.seed_for_models}'+'_on_off_.pkl'
            file_path_level = 'models'+os.sep+self.test.instance+os.sep+'server_'+str(server.id)+f'_{self.test.seed_for_models}'+'_level_'
            #file_path_on_off = 'models' + os.sep + 'server_' + str(
            #    server.id) + '_123456789' + '_on_off_.pkl'
            #file_path_level = 'models' + os.sep + 'server_' + str(server.id) + '_123456789' + '_level_'

            if os.path.exists(file_path_on_off) and all([os.path.exists(f'{file_path_level}{res}_.pkl') for res in ["cpu","hdd","mem"]]):
                # Load models from file
                self.pred_onoff[server.id] = pickle.load(open(file_path_on_off,'rb'))

                self.pred_level[server.id] = {}
                res_files = [(res,f'{file_path_level}{res}_.pkl') for res in ["cpu", "hdd", "mem"]]
                for res,file in res_files:
                    self.pred_level[server.id][res] = pickle.load(open(file,'rb'))
            else:
                # Recopile data from last 30 days
                data_server = self.recopile_data(server,self.test.seed_for_models)
                data_server['time'] = data_server['time'] % self.P
                # On/off prediction
                # Prepare data for periodic logistic regression
                # Create apply transformations to time taking account periods
                time = self.__transformation_vec__(data_server.shape[0])

                # Server on/off model creation
                server_status = data_server['on/off']
                pred = LogisticRegression(solver='liblinear', random_state=0)
                pred.fit(time,server_status)
                self.pred_onoff[server.id] = pred

                # if not exists create the folder for the models
                if not os.path.exists(f'models{os.sep+self.test.instance+os.sep}'):
                    os.makedirs(f'models{os.sep+self.test.instance+os.sep}')

                pickle.dump(pred, open(f'models{os.sep+self.test.instance+os.sep}server_{server.id}_{self.test.seed_for_models}_on_off_.pkl', 'wb'))

                # Preparing data for server level prediction
                # Server level prediction

                self.pred_level[server.id] = {}
                for resource in ["cpu","hdd","mem"]:
                #for resource in range(len(self.test.input.servers[server.id].resources)):
                    x_train, x_test, y_train, y_test = train_test_split(
                                                        data_server.drop(columns = ["cpu","hdd","mem"]),
                                                        data_server[resource],
                                                        train_size = 0.9,
                                                        random_state = self.test.seed_servers)
                    ngb_model = NGBRegressor(Dist=Normal, Score=LogScore)
                    #ngb_model.set_params(n_estimators=2000, max_depth=3, learning_rate=0.01)
                    #ngb_model = RandomForrest(n_estimators=100, max_depth=10, min_samples_split=2,
                    #                          min_samples_leaf=1, random_state=self.test.seed_servers )

                    numeric_features = x_train.columns
                    preprocessor = ColumnTransformer(
                        transformers=[
                        ('num', RobustScaler(), numeric_features)])

                    preprocessor = Pipeline(steps=[('preprocessor', preprocessor)])

                    pipeline = Pipeline(steps=[('scaler', preprocessor), ("NGBRegressor", ngb_model)])
                    pipeline.fit(x_train, y_train)
                    print(f"Server {server.id} resource {resource} prediction score: {pipeline.score(x_test, y_test)}")
                    self.pred_level[server.id][resource] = pipeline

                    if not os.path.exists(f'models{os.sep + self.test.instance + os.sep}'):
                        os.makedirs(f'models{os.sep + self.test.instance + os.sep}')

                    pickle.dump(pipeline, open(f'models{os.sep+self.test.instance+os.sep}server_{server.id}_{self.test.seed_for_models}_level_{resource}_.pkl', 'wb'))

    # Recopile last 30 days of data
    def recopile_data(self,server,seed):
        df = pd.read_json('data'+os.sep+f'{self.test.instance}_{seed}_.json')
        df = df.drop(columns=['x', 'y', '_id','#jobs'])
        # df =pd.DataFrame(SimpleImputer(strategy='most_frequent').fit_transform(df),columns=df.columns)
        df = df[df['server_id']==server.id]
        return df.drop(columns=["server_id"])

    def get_prediction_on_off(self,server_id,t):
        t = t % self.P
        return self.pred_onoff[server_id].predict(self.__transformation__(t))[0]

    def get_prediction_level(self,server_id,resource,t):
        t = t % self.P
        df = pd.DataFrame(data={'on/off':[1],'time':[t]})
        return self.pred_level[server_id][resource].predict(df)
