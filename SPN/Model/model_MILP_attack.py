import gurobipy as gp
import numpy as np
from sage.all import Matrix, GF

class Model_MILP_attack():   
    def __init__(self, cipher_parameters, licence_parameters, model):  
        
        #Cipher name
        self.cipher_name = cipher_parameters.get('Cipher_name', 'SKINNY')
        
        #Block parameters
        self.block_size = cipher_parameters.get('block_size', 64)
        self.block_column_size = cipher_parameters.get('block_column_size', 4)
        self.block_row_size = cipher_parameters.get('block_row_size', 4)
        self.word_size = int(self.block_size/(self.block_column_size*self.block_row_size))
        
        #Operations parameters
        self.operation_order = cipher_parameters.get('operation_order', ['AK', 'SR', 'MC0', 'SB'])
        self.shift_rows = cipher_parameters.get('shift_rows', [0, 1, 2, 3])
        self.mix_columns = cipher_parameters.get('mix_columns')
        self.sbox_sizes = cipher_parameters.get('sbox_sizes', [1, 1])   
        
        #Extension of the given parameters
        self.state_number = len(self.shift_rows)+1
        self.shift_rows_inverse = [(self.block_column_size - shift) % self.block_column_size for shift in self.shift_rows]
        self.mix_columns_inverse = []
        for element in self.mix_columns : #Computing the inverse of the matrixes
            MC = Matrix(GF(2), element)
            MC_inv = MC.inverse()
            self.mix_columns_inverse.append([[int(MC_inv[i][j])for i in range(MC_inv.ncols())] for j in range(MC_inv.nrows())])
        
        self.model=model
        #Model Creation
        if self.model==None:
            self.model = gp.Model(env=gp.Env(params={'WLSACCESSID': licence_parameters.get('WLSACCESSID'), 'WLSSECRET': licence_parameters.get('WLSSECRET'), 'LICENSEID': licence_parameters.get('LICENSEID')}))

            # Parameters of the Gurobi model
            self.model.params.FeasibilityTol = 1e-9
            self.model.params.OptimalityTol = 1e-9
            self.model.setParam("OutputFlag", 1) 
            self.model.setParam("LogToConsole", 1)
            self.model.setParam("IntFeasTol", 1e-9)
            
        
        # Double Check of cipher model
        self.everything_all_right = True
        self.optimized=False
    
    #Propagation of values OPERATORS
    def value_propagation_SR(self, part, round_index, input_state_index, output_state_index, shift_rows):
        #an unknow value cannot turn to a value that can be computed.
        self.model.addConstrs(((part[round_index, input_state_index, row, column, 0] == 1)
                                >> (part[round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size, 1] == 0)
                                for row in range(4) for column in range(4)),
                                name = "value_propagation_:_SR_0_not_to_1")
        
    def value_propagation_MC(self, part, round_index, input_state_index, output_state_index, mix_columns):
        #if you have an unknow value in the active bits before MC, the ouput of MC cannot be computed
        self.model.addConstrs(((part[round_index, input_state_index, row_input, column, 0]==1)
                                >> (part[round_index, output_state_index, row_output, column, 1]==0)
                               for row_output in range(self.block_row_size) for column in range(self.block_column_size) for row_input in [i for i, n in enumerate(mix_columns[row_output]) if n==1]), 
                               name = "value_propagation_MC_:_0_not_to_1")
    
    def value_propagation_SB(self, part, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        self.model.addConstrs(((part[round_index, input_state_index, row_input, column_input, 0]==1)
                                 >> (part[round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1]==0)
                                 for row_output in range(self.block_row_size//sbox_sizes[0])
                                 for column_output in range(self.block_column_size//sbox_sizes[1])
                                 for sbox_row in range(sbox_sizes[0])
                                 for sbox_column in range(sbox_sizes[1])
                                 for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                 for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                 name='value_propagation_SB_:_0_not_to_1')

    def value_propagation_AK(self, part, subkey_part, subkey_index, round_index, input_state_index, output_state_index):
        #if the state if not known before the AK it cannot be computed after
        self.model.addConstrs((((part[round_index, input_state_index, row, column, 0]==1)
                                >> (part[round_index, output_state_index, row, column, 1]==0))
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_state_not_to_1')
        
        #if the key is not known, the state after AK cannot be computed
        self.model.addConstrs((((subkey_part[round_index+subkey_index, row, column]==0)
                                >> (part[round_index, output_state_index, row, column, 1]==0))
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_key_not_to_1')
        
    def value_propagation_NR(self, part, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        if input_round_index < output_round_index:
            self.model.addConstrs(((part[input_round_index, self.state_number-1, row, column, 0]==1)
                                    >> (part[output_round_index, 0, row, column, 1]==0) for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                    name='value_propagation_NR_:_0_not_to_1')
        else :
            self.everything_all_right = False
            print("Error in value_propagation_NR: input_round_index should be inferior from output_round_index")
        
    def value_propagation_PR(self, part, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs(((part[input_round_index, 0, row, column, 0]==1)
                                >> (part[output_round_index, self.state_number-1, row, column, 1]==0) 
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='value_propagation_NR_:_0_not_to_1')

    #Progation of values X-ROUND
    def forward_value_propagation(self, part, part_size, subkey, subkey_first_round_index):
        for forward_round in range(part_size):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR':
                    self.value_propagation_SR(part, forward_round, state_index, state_index + 1, self.shift_rows)
                elif self.operation_order[state_index][0]+self.operation_order[state_index][1] == 'MC':
                    self.value_propagation_MC(part, forward_round, state_index, state_index + 1, self.mix_columns[int(self.operation_order[state_index][2])])
                elif self.operation_order[state_index] == 'SB':
                    self.value_propagation_SB(part, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    self.value_propagation_AK(part, subkey, subkey_first_round_index, forward_round, state_index, state_index + 1, )
                else :
                    self.everything_all_right = False
                    print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != part_size-1:
                self.value_propagation_NR(part, forward_round, forward_round+1)

    def backward_value_propagation(self, part, part_size, subkey, subkey_first_round_index):
        for backward_round in range(part_size):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR':
                    self.value_propagation_SR(part, backward_round, state_index + 1, state_index, self.shift_rows_inverse)
                elif self.operation_order[state_index][0]+self.operation_order[state_index][1] == 'MC':
                    self.value_propagation_MC(part, backward_round, state_index + 1, state_index, self.mix_columns_inverse[int(self.operation_order[state_index][2])])
                elif self.operation_order[state_index] == 'SB':
                    self.value_propagation_SB(part, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    self.value_propagation_AK(part, subkey, subkey_first_round_index, backward_round, state_index + 1, state_index)
                else :
                    self.everything_all_right = False
                    print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != part_size-1:
                self.value_propagation_PR(part, backward_round+1, backward_round)
   
    def complexities(self):
        self.time_complexity = self.model.addVar(vtype= gp.GRB.CONTINUOUS, name = "time_complexity")
        if self.block_size//self.word_size < 0 :
            self.search_domain = range(128)
            self.time_complexity_up = self.model.addVar(lb = 0, ub = 128,vtype= gp.GRB.INTEGER, name = "time_complexity_up")
            self.time_complexity_down = self.model.addVar(lb = 0, ub = 128,vtype= gp.GRB.INTEGER, name = "time_complexity_down")
            self.time_complexity_match = self.model.addVar(lb = 0, ub = 128,vtype= gp.GRB.INTEGER, name = "time_complexity_match")
        
            self.binary_time_complexity_up = {i: self.model.addVar(vtype=gp.GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in self.search_domain}
            self.binary_time_complexity_down = {i: self.model.addVar(vtype=gp.GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in self.search_domain}
            self.binary_time_complexity_match = {i: self.model.addVar(vtype=gp.GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in self.search_domain}
        
            self.model.addConstr(self.time_complexity_up == gp.quicksum(i * self.binary_time_complexity_up[i] for i in self.search_domain), name="link between binary and integer complexity up")
            self.model.addConstr(self.time_complexity_down == gp.quicksum(i * self.binary_time_complexity_down[i] for i in self.search_domain), name="link between binary and integer complexity down")
            self.model.addConstr(self.time_complexity_match == gp.quicksum(i * self.binary_time_complexity_match[i] for i in self.search_domain), name="link between binary and integer complexity match")

            self.model.addConstr(self.time_complexity == gp.quicksum((2**i)*(self.binary_time_complexity_up[i] + self.binary_time_complexity_down[i] + self.binary_time_complexity_match[i]) for i in self.search_domain), name="time complexity")
        
        else :
            self.time_complexity_up = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_up")
            self.time_complexity_down = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_down")
            self.time_complexity_match = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_match")

            self.model.addConstr(self.time_complexity_down <= self.time_complexity, name="suboptimal time complexity down")
            self.model.addConstr(self.time_complexity_up <= self.time_complexity, name="suboptimal time complexity up")
            self.model.addConstr(self.time_complexity_match <= self.time_complexity, name="suboptimal time complexity match")
        
    def optimize_the_model(self): 
        if self.everything_all_right:
            self.model.optimize()
            if self.model.Status != gp.GRB.INFEASIBLE :
                self.optimized=True
            else :
                self.model.computeIIS()
                self.model.write("model_infeasible.ilp")
        else : 
            print("Some error occured in assembling the model, please check the error(s) above.")



