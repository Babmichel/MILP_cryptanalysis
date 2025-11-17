from Model.model_MILP_attack import Model_MILP_attack
import gurobipy as gp

class Model_MILP_SKINNY_key_schedule(Model_MILP_attack):
    def __init__(self, cipher_parameters, total_round, model):
        super().__init__(cipher_parameters, None, model)
        #Key parameters
        self.key_size = cipher_parameters.get('key_size', 256)
        self.total_round = total_round
        self.model=model

    def master_key_initialisation(self):
        self.master_key = self.model.addVars(range(8), range(self.key_size//8), range(3),
                           vtype=gp.GRB.BINARY, name="master_key")
        
        self.model.addConstr((gp.quicksum(self.master_key[row, column, value] for value in range(3)) >= 1 
                             for row in range(4) 
                             for column in range(self.key_size//4)),
                             name='master_key_known_or_unknown')
    
    def round_key_initialisation(self):
        #round_keys
        self.upper_key = self.model.addVars(range(self.total_round+1), range(4), range(self.key_size//8),
                           vtype=gp.GRB.BINARY, name="round_key")
        
        self.lower_key = self.model.addVars(range(self.total_round+1), range(4), range(self.key_size//8),
                           vtype=gp.GRB.BINARY, name="round_key")
        
    def keyschedule(self):
        self.master_key_initialisation()
        self.round_key_initialisation()
        
