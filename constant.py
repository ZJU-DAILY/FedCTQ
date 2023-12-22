class Constant:
    THRESHOLD = {'distance': 800, 'time': 600, 'k': 10}
    USER_DATA_COLUMNS_TYPE = {'uid': 'uint32', 'id': 'uint32', 'x': 'uint32', 'y': 'uint32', 'time': 'uint32'}
    USER_DATA_COLUMNS = list(USER_DATA_COLUMNS_TYPE.keys())
    R = 6371000
    CLIENTS_NUM = 4
    DATASET: str
    PATIENTS_NUM: int
    PATH: str
    RATIO: float
    ADDRESS: str
