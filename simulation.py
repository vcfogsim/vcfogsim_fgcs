from model import Model


def run(input):
    if input.users != []:
        model = Model(users=input.users,servers=input.servers,input=input)
    else:
        model = Model(users=input.users,servers=input.servers,total_periods=input.nPeriods,max_duration=10,
                      users_rate=5,input=input,district=input.district,placement=input.placement,
                      data=input.db,ml=input.ml)
    return model.run()