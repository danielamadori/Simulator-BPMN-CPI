from random import random
from model.time_spin import DataSPIN


class Defaults:

    @staticmethod
    def choiceChild(net: DataSPIN, p_id: str):
        prop = net.get_props(p_id)
        for p, c in prop.distribution:
            if p == 1:
                return c

    @staticmethod
    def natureChild(net: DataSPIN, p_id: str):
        choice = random()
        sum_p = 0
        prop = net.get_props(p_id)
        last = None

        for p, c in prop.distribution:
            sum_p += p
            if sum_p >= choice:
                return c
            last = c

        return last
