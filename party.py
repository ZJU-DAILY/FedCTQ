import index
from util import Util
from constant import Constant
import secretflow as sf
import pandas as pd
import math


class Party:
    def __init__(self, party):
        self.party = party

    def __str__(self):
        return 'fedctq'


class Server(Party):
    def __init__(self, party: sf.PYU = None):
        super().__init__(party=party)

    def fctq(self, client, patientsUid):
        print(f'Query Start')
        haveContactors = client.fctq(patientsUid=patientsUid)
        contactors = [uid for uid, hasContactors in haveContactors.items() if
                      Util.is_continuous_subsequence(data=hasContactors, length=Constant.THRESHOLD['k'])]
        contactors.sort()
        print(f'Query End')
        return contactors


class Client(Party):
    def __init__(self, party: sf.PYU = None, data=None, xHeight=0, yHeight=0, timeHeight=0):
        super().__init__(party=party)
        self.data = data
        self.index = {'x': index.Tree(xHeight, 'xi'), 'y': index.Tree(yHeight, 'yi'),
                      't': index.Tree(timeHeight, 'ti')}

    def insert_user_data(self, index, data):
        self.index['x'].insert(index=index, data=data)
        self.index['y'].insert(index=index, data=data)
        self.index['t'].insert(index=index, data=data)

    @staticmethod
    def get_patients_data_indices(index, patientsUid):
        return {'x': index['x'].get_patients_data_indices(patientsUid=patientsUid),
                'y': index['y'].get_patients_data_indices(patientsUid=patientsUid),
                't': index['t'].get_patients_data_indices(patientsUid=patientsUid)}

    @staticmethod
    def find_close_data_indices(node: index.Node, treeKey, patientUid, patientId):
        return node.find_close_data_indices(treeKey=treeKey, patientUid=patientUid, patientId=patientId)

    @staticmethod
    def in_condition(patientData, userData, values):
        if patientData['x'] == userData['x'] and patientData['y'] == userData['y'] and \
                patientData['time'] == userData['time'] and \
                math.pow(values[0], 2) + math.pow(values[1], 2) < Constant.THRESHOLD['d2']:
            return True
        return False

    @staticmethod
    def has_contactors(patientData, userIndices, data: pd.DataFrame, contactors):
        res = list()
        for userId, (userIndex, values) in userIndices.items():
            if userId not in contactors:
                if Client.in_condition(patientData=patientData, userData=data.iloc[userIndex], values=values):
                    res.append(userId)
        return res

    def index_query(self, patientsUid):
        patientsIndices = Client.get_patients_data_indices(index=self.index, patientsUid=patientsUid)
        _closeIndices = dict()
        for treeKey, patientsTree in patientsIndices.items():
            for patientUid, nodes in patientsTree.items():
                for patientId, node in nodes.items():
                    patientIndex, usersIndices = Client.find_close_data_indices(
                        node=node, treeKey=treeKey, patientUid=patientUid, patientId=patientId)
                    for userUid, userIndices in usersIndices.items():
                        for userId, (userIndex, value) in userIndices.items():
                            if treeKey == 'x':
                                if _closeIndices.get(patientIndex) is None:
                                    _closeIndices[patientIndex] = dict()
                                if _closeIndices[patientIndex].get(userUid) is None:
                                    _closeIndices[patientIndex][userUid] = dict()
                                _closeIndices[patientIndex][userUid][userId] = (userIndex, [value])
                            elif _closeIndices.get(patientIndex) is not None and _closeIndices[patientIndex].get(
                                    userUid) is not None:
                                if _closeIndices[patientIndex][userUid].get(userId) is not None:
                                    _closeIndices[patientIndex][userUid][userId][1].append(value)
        closeIndices = dict()
        for patientIndex, usersIndices in _closeIndices.items():
            for userUid, userIndices in usersIndices.items():
                for userId, (userIndex, values) in userIndices.items():
                    if len(values) == 3:
                        if closeIndices.get(patientIndex) is None:
                            closeIndices[patientIndex] = dict()
                        if closeIndices[patientIndex].get(userUid) is None:
                            closeIndices[patientIndex][userUid] = dict()
                        closeIndices[patientIndex][userUid][userId] = (userIndex, values[:2])
        return closeIndices

    def fctq(self, patientsUid):
        closeIndices = self.index_query(patientsUid=patientsUid)
        contactors = dict()
        i = 0
        for patientIndex, usersIndices in closeIndices.items():
            patientData = self.data.loc[patientIndex]
            for userUid, userIndices in usersIndices.items():
                haveContactors = Client.has_contactors(patientData=patientData, userIndices=userIndices, data=self.data,
                                                       contactors=contactors[userUid]
                                                       if contactors.get(userUid) is not None else list())
                if len(haveContactors) > 0:
                    if contactors.get(userUid) is None:
                        contactors[userUid] = list()
                    contactors[userUid] += haveContactors
            i += 1
        for key in contactors.keys():
            contactors[key].sort()
        return contactors


class User(Party):
    def __init__(self, party: sf.PYU = None):
        super().__init__(party=party)

    def upload_data(self, index, data, client):
        client.insert_user_data(index=index, data=data)
