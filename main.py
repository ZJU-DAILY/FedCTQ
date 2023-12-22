from party import Server, Client, User
from constant import Constant
import pandas as pd
import argparse
import secretflow as sf


def upload():
    data = pd.read_csv(f'{Constant.PATH}/FedCTQ/{Constant.DATASET.lower()}.csv').astype(
        Constant.USER_DATA_COLUMNS_TYPE)
    data = data[:int(len(data) * Constant.RATIO)]
    maxX = data['x'].max()
    maxY = data['y'].max()
    maxTime = data['time'].max()
    data = data.assign(xi='')
    data = data.assign(yi='')
    data = data.assign(ti='')
    user = User(party=sf.PYU(party='user'))
    client = Client(party=sf.PYU(party='client'), xHeight=len(bin(maxX)[2 + Constant.CLIENTS_NUM:]),
                    yHeight=len(bin(maxY)[2 + Constant.CLIENTS_NUM:]),
                    timeHeight=len(bin(maxTime)[2 + Constant.CLIENTS_NUM:]))
    for index, row in data.iterrows():
        x = format(int(row['x']), f'0{len(bin(maxX)[2:])}b')
        y = format(int(row['y']), f'0{len(bin(maxY)[2:])}b')
        t = format(int(row['time']), f'0{len(bin(maxTime)[2:])}b')
        row['x'] = int(x[:Constant.CLIENTS_NUM], 2)
        row['xi'] = str(x[Constant.CLIENTS_NUM:])
        row['y'] = int(y[:Constant.CLIENTS_NUM], 2)
        row['yi'] = str(y[Constant.CLIENTS_NUM:])
        row['time'] = int(t[:Constant.CLIENTS_NUM], 2)
        row['ti'] = str(t[Constant.CLIENTS_NUM:])
        user.upload_data(index=index, data=row, client=client)
    data.drop(labels=['xi', 'yi', 'ti'], axis=1, inplace=True)
    return client, data


def query():
    client, data = upload()
    client.data = data
    server = Server(party=sf.PYU(party='server'))
    uids = data.uid.unique()
    uids.sort()
    patientsUid = uids[:Constant.PATIENTS_NUM]
    return server.fctq(client=client, patientsUid=patientsUid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='Gowalla_Small')
    parser.add_argument('--patients_num', type=int, default=1)
    parser.add_argument('--path', type=str, default='')
    parser.add_argument('--ratio', type=float, default=1.0)
    parser.add_argument('--address', type=str, default='')
    args = parser.parse_args()
    Constant.DATASET = args.dataset
    Constant.PATIENTS_NUM = args.patients_num
    Constant.PATH = args.path
    Constant.RATIO = args.ratio
    Constant.ADDRESS = args.address
    sf.init(parties=['server', 'client', 'user'], address=Constant.ADDRESS)
    contactors = query()
    print(contactors)
