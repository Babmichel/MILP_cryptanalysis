import gurobipy as gp
import numpy as np
import sage as sg

class Model_MILP_attack():   
    def __init__(self, cipher_parameters, licence_parameters):  
        
        self.cipher_name = cipher_parameters.get('Cipher_name', 'SKINNY')
        #Block parameters
        self.block_size = cipher_parameters.get('block_size', 64)
        self.block_column_size = cipher_parameters.get('block_column_size', 4)
        self.block_row_size = cipher_parameters.get('block_row_size', 4)
        self.word_size = int(self.block_size/(self.block_column_size+self.block_row_size))
        
        #Key parameters
        self.key_size = cipher_parameters.get('key_size', 192)
        self.key_column_size = cipher_parameters.get('key_column_size', 4)
        self.key_row_size = cipher_parameters.get('key_row_size', 2)

        #Operations parameters
        self.operation_order = cipher_parameters.get('operation_order', ['AK', 'SR', 'MC', 'SB'])
        self.shift_rows = cipher_parameters.get('shift_rows', [0, 1, 2, 3])
        self.shift_rows_inverse = [(self.block_column_size - shift) % self.block_column_size for shift in self.shift_rows]
        self.state_number = len(self.shift_rows)+1
        self.mix_columns = cipher_parameters.get('mix_columns', [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]])
        self.mix_columns_inverse = np.invert(np.array(self.mix_columns)).astype(int).tolist()
        self.sbox_sizes = cipher_parameters.get('sbox_sizes', [1, 1])   
        
        #Model Creation
        self.model = gp.Model(env=gp.Env(params={'WLSACCESSID': licence_parameters.get('WLSACCESSID'), 'WLSSECRET': licence_parameters.get('WLSSECRET'), 'LICENSEID': licence_parameters.get('LICENSEID')}))
        # Parameters of the Gurobi model
        self.model.params.FeasibilityTol = 1e-9
        self.model.params.OptimalityTol = 1e-9
        self.model.setParam("OutputFlag", 1) 
        self.model.setParam("LogToConsole", 1)
        self.model.setParam("IntFeasTol", 1e-9)
        self.everything_all_right = True
        self.optimized=False
    
    #Propagation of values operators
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

    def value_propagation_AK(self, part, subkey_part, round_index, input_state_index, output_state_index):
        #if the state if not known before the AK it cannot be computed after
        self.model.addConstrs((((part[round_index, input_state_index, row, column, 0]==1)
                                >> (part[round_index, output_state_index, row, column, 1]==0))
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_state_not_to_1')
        
        #if the key is not known, the state after AK cannot be computed
        self.model.addConstrs((((subkey_part[round_index, row, column, 0]==1)
                                >> (part[round_index, output_state_index, row, column, 1]==0))
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_key_not_to_1')
        
    def value_propagation_NR(self, part, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        if input_round_index < output_round_index:
            self.model.addConstrs(((part[input_round_index, self.state_number-1, row, column, 0]==1)
                                    >> (part[output_round_index, 0, row, column, 1]==0) for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                    name='value_propagation_NR_:_0_not_to_1')
        elif input_round_index > output_round_index:
            self.model.addConstrs(((part[input_round_index, 0, row, column, 0]==1)
                                    >> (part[output_round_index, self.state_number-1, row, column, 1]==0) for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                    name='value_propagation_NR_:_0_not_to_1')
        else :
            self.everything_all_right = False
            print("Error in value_propagation_NR: input_round_index should be different from output_round_index")
        
    def value_propagation_PR(self, part, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs(((part[input_round_index, self.state_number-1, row, column, 0]==1)
                                >> (part[output_round_index, 0, row, column, 1]==0) for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                name='value_propagation_NR_:_0_not_to_1')

    def optimize(self): 
        if self.everything_all_right:
            self.model.optimize()
            self.optimize=True
        else : 
            print("Some error occured in assembling the model, please check the error(s) above.")

    

