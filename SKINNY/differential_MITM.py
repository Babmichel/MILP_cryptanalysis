import gurobipy as gp
import numpy as np

class Differential_MITM():
    def __init__(self, parameters, licence):
        self.block_size = parameters.get('block_size', 64)
        self.key_size = parameters.get('key_size', 192)

        self.structure_rounds = parameters.get('structure_rounds', 4)
        self.upper_rounds = parameters.get('upper_rounds', 2)
        self.lower_rounds = parameters.get('lower_rounds', 2)
        self.distinguisher_rounds = parameters.get('distinguisher_rounds', 4)
        self.total_rounds = self.structure_rounds + self.upper_rounds + self.lower_rounds + self.distinguisher_rounds
        
        self.WLSACCESSID = licence['WLSACCESSID']
        self.WLSSECRET = licence['WLSSECRET']
        self.LICENCEID = licence['LICENCEID']

        self.model = gp.Model(env=gp.Env(params={'WLSACCESSID': self.WLSACCESSID, 'WLSSECRET': self.WLSSECRET, 'LICENCEID': self.LICENCEID}))

