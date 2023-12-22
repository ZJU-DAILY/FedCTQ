import os
from constant import Constant
import copy

Constant.THRESHOLD['d2'] = Constant.THRESHOLD['distance'] ** 2


class Node:
    def __init__(self, height, shareIndex, values, isLeaf=True):
        self.left = None
        self.right = None
        self.height = height
        self.shareIndex = shareIndex
        self.pre = None
        self.next = None
        self.dataSize = 0
        self.isLeaf = isLeaf
        self.values = values
        self.index = None
        if isLeaf:
            self.index = dict()

    def insert(self, uid, id, index, binary):
        if self.index.get(uid) is None:
            self.index[uid] = dict()
        self.index[uid][id] = (index, binary)
        self.dataSize += 1

    def find_close_data_indices(self, treeKey, patientUid, patientId):
        res = dict()
        patientIndex, patientBinary = self.index[patientUid][patientId]
        patientValue = int(self.shareIndex + patientBinary, 2)
        if treeKey == 'time':
            threshold = (patientValue - Constant.THRESHOLD['time'], patientValue + Constant.THRESHOLD['time'])
        else:
            threshold = (patientValue - Constant.THRESHOLD['distance'], patientValue + Constant.THRESHOLD['distance'])

        if threshold[0] <= self.values[0] and self.values[1] <= threshold[1]:
            for userUid, userIndices in self.index.items():
                for userId, (userIndex, userBinary) in userIndices.items():
                    if res.get(userUid) is None:
                        res[userUid] = dict()
                    res[userUid][userId] = (userIndex, patientValue - int(self.shareIndex + userBinary, 2))
        else:
            for userUid, userIndices in self.index.items():
                for userId, (userIndex, userBinary) in userIndices.items():
                    userValue = int(self.shareIndex + userBinary, 2)
                    if threshold[0] <= userValue <= threshold[1]:
                        if res.get(userUid) is None:
                            res[userUid] = dict()
                        res[userUid][userId] = (userIndex, patientValue - userValue)
        if self.values[0] <= threshold[0] and threshold[1] <= self.values[1]:
            return patientIndex, res
        preNode = self.pre
        while preNode is not None and threshold[0] <= preNode.values[1]:
            if threshold[0] <= preNode.values[0] and preNode.values[1] <= threshold[1]:
                for userUid, userIndices in preNode.index.items():
                    for userId, (userIndex, userBinary) in userIndices.items():
                        if res.get(userUid) is None:
                            res[userUid] = dict()
                        res[userUid][userId] = (userIndex, 0)
            else:
                for userUid, userIndices in preNode.index.items():
                    for userId, (userIndex, userBinary) in userIndices.items():
                        userValue = int(preNode.shareIndex + userBinary, 2)
                        if threshold[0] <= userValue <= threshold[1]:
                            if res.get(userUid) is None:
                                res[userUid] = dict()
                            res[userUid][userId] = (userIndex, patientValue - userValue)
            preNode = preNode.pre
        nextNode = self.next
        while nextNode is not None and threshold[1] >= nextNode.values[0]:
            if threshold[0] <= nextNode.values[0] and nextNode.values[1] <= threshold[1]:
                for userUid, userIndices in nextNode.index.items():
                    for userId, (userIndex, userBinary) in userIndices.items():
                        if res.get(userUid) is None:
                            res[userUid] = dict()
                        res[userUid][userId] = (userIndex, 0)
            else:
                for userUid, userIndices in nextNode.index.items():
                    for userId, (userIndex, userBinary) in userIndices.items():
                        userValue = int(nextNode.shareIndex + userBinary, 2)
                        if threshold[0] <= userValue <= threshold[1]:
                            if res.get(userUid) is None:
                                res[userUid] = dict()
                            res[userUid][userId] = (userIndex, patientValue - userValue)
            nextNode = nextNode.next
        return patientIndex, res


class Tree:
    # SPLIT_RATIO = 0.0001
    SPLIT_RATIO = 0.00001

    # SPLIT_RATIO = 0.000001
    # SPLIT_RATIO = 0.0000001

    def __init__(self, height, key):
        self.usersNodes = dict()
        self.root = Node(height=0, values=[0, (2 << (height - 1)) - 1], shareIndex="")
        self.dataSize = 0
        self.maxHeight = height
        self.key = key

    def split(self, node):
        shareIndex = ''
        for uid, data in node.index.items():
            for id, (index, binary) in data.items():
                if shareIndex == '':
                    shareIndex = binary
                    continue
                shareIndex = os.path.commonprefix([shareIndex, binary])
                if shareIndex == '':
                    break
            if shareIndex == '':
                break
        if len(node.shareIndex + shareIndex) == self.maxHeight:
            return
        node.shareIndex += shareIndex
        values = copy.deepcopy(node.values)
        for i in shareIndex:
            if i == '0':
                values[1] = (values[0] + values[1]) // 2
            else:
                values[0] = (values[0] + values[1] + 1) // 2
        node.left = Node(height=len(node.shareIndex) + 1, values=[values[0], (values[0] + values[1]) // 2],
                         shareIndex=node.shareIndex + '0')
        node.right = Node(height=len(node.shareIndex) + 1, values=[(values[0] + values[1] + 1) // 2, values[1]],
                          shareIndex=node.shareIndex + '1')
        node.left.pre = node.pre
        node.pre = None
        if node.left.pre is not None:
            node.left.pre.next = node.left
        node.left.next = node.right
        node.right.pre = node.left
        node.right.next = node.next
        node.next = None
        if node.right.next is not None:
            node.right.next.pre = node.right
        for uid, indices in node.index.items():
            for id, (index, binary) in indices.items():
                if binary[len(shareIndex)] == '0':
                    node.left.insert(uid=uid, id=id, index=index, binary=binary[len(shareIndex) + 1:])
                    self.usersNodes[uid][id] = node.left
                else:
                    node.right.insert(uid=uid, id=id, index=index, binary=binary[len(shareIndex) + 1:])
                    self.usersNodes[uid][id] = node.right
        if node.left.dataSize > self.dataSize * Tree.SPLIT_RATIO and node.left.dataSize > 1 \
                and node.left.height < self.maxHeight:
            self.split(node.left)
        if node.right.dataSize > self.dataSize * Tree.SPLIT_RATIO and node.right.dataSize > 1 and \
                node.right.height < self.maxHeight:
            self.split(node.right)
        node.isLeaf = False
        node.index = None

    def insert(self, index, data):
        node = self.root
        i = 0
        while i <= self.maxHeight:
            if len(node.shareIndex) != i:
                shareIndex = os.path.commonprefix([node.shareIndex, data[self.key]])
                if shareIndex != node.shareIndex:
                    values = copy.deepcopy(node.values)
                    for j in range(node.height, len(shareIndex)):
                        if shareIndex[j] == '0':
                            values[1] = (values[0] + values[1]) // 2
                        else:
                            values[0] = (values[0] + values[1] + 1) // 2
                    newNode = Node(height=len(shareIndex) + 1, values=None,
                                   shareIndex=node.shareIndex, isLeaf=False)
                    newNode.left = node.left
                    newNode.right = node.right
                    node.shareIndex = shareIndex
                    i += len(node.shareIndex) - node.height
                    if data[self.key][len(node.shareIndex)] == '0':
                        node.right = newNode
                        newNode.values = [(values[0] + values[1] + 1) // 2, values[1]]
                        node.left = Node(height=len(node.shareIndex) + 1,
                                         values=[values[0], (values[0] + values[1]) // 2],
                                         shareIndex=node.shareIndex + '0')
                        tmp = newNode
                        while not tmp.isLeaf:
                            tmp = tmp.left
                        if tmp.pre is not None:
                            node.left.pre = tmp.pre
                            tmp.pre.next = node.left
                        tmp.pre = node.left
                        node.left.next = tmp
                        node = node.left
                        i += 1
                    else:
                        node.left = newNode
                        newNode.values = [values[0], (values[0] + values[1]) // 2]
                        node.right = Node(height=len(node.shareIndex) + 1,
                                          values=[(values[0] + values[1] + 1) // 2, values[1]],
                                          shareIndex=node.shareIndex + '1')
                        tmp = newNode
                        while not tmp.isLeaf:
                            tmp = tmp.right
                        if tmp.next is not None:
                            node.right.next = tmp.next
                            tmp.next.pre = node.right
                        tmp.next = node.right
                        node.right.pre = tmp
                        node = node.right
                        i += 1
                else:
                    i += len(node.shareIndex) - node.height
            if node.isLeaf:
                uid = data['uid']
                id = data['id']
                node.insert(uid=uid, id=id, index=index, binary=data[self.key][i:])
                if self.usersNodes.get(uid) is None:
                    self.usersNodes[uid] = dict()
                self.usersNodes[uid][id] = node
                self.dataSize += 1
                if node.dataSize > self.dataSize * Tree.SPLIT_RATIO and node.dataSize > 1 and \
                        node.height < self.maxHeight:
                    self.split(node)
                break
            if data[self.key][i] == '0':
                node = node.left
            else:
                node = node.right
            i += 1

    def get_patients_data_indices(self, patientsUid):
        return {uid: self.usersNodes[uid] for uid in patientsUid}
