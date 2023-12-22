import secretflow as sf
import ray


class Util:
    @staticmethod
    def is_continuous_subsequence(data, length):
        for i in range(len(data) - length + 1):
            subsequence = data[i:i + length]
            if subsequence == list(range(subsequence[0], subsequence[-1] + 1)):
                return True
        return False

    @staticmethod
    def secretflow_reveal(data):
        if data is None:
            return data
        elif isinstance(data, sf.PYUObject):
            if isinstance(data.data, ray.ObjectRef):
                return sf.reveal(data)
            else:
                return data.data
        elif isinstance(data, sf.SPUObject):
            return sf.reveal(data)
        else:
            return data
