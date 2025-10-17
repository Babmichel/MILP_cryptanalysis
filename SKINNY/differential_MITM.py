import gurobipy as gp
import numpy as np
import random as rd

class Model_MILP_Differential_MITM():   
    def __init__(self, cipher_parameters, attack_parameters, licence_parameters):  
        
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
        self.state_number = len(self.shift_rows)+1
        self.mix_columns = cipher_parameters.get('mix_columns', [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]])
        self.sbox_sizes = cipher_parameters.get('sbox_sizes', [1, 1])   
        
        #Model Creation
        self.model = gp.Model(env=gp.Env(params={'WLSACCESSID': licence_parameters.get('WLSACCESSID'), 'WLSSECRET': licence_parameters.get('WLSSECRET'), 'LICENSEID': licence_parameters.get('LICENSEID')}))

        #Attack parameters
        self.structure_rounds = attack_parameters.get('structure_rounds', 4)
        self.upper_rounds = attack_parameters.get('upper_rounds', 2)
        self.lower_rounds = attack_parameters.get('lower_rounds', 2)
        self.distinguisher_rounds = attack_parameters.get('distinguisher_rounds', 4)
        self.total_rounds = self.structure_rounds + self.upper_rounds + self.lower_rounds + self.distinguisher_rounds

        self.everything_all_right = True
        self.optimized=False
    
    def getdetails(self):
        print(self.cipher_name, self.block_size, '-', self.key_size)

    #Attack parts initialisation
    def part_initalisation(self):
        self.upper_subkey=self.model.addVars(range(self.upper_rounds), range(self.block_row_size), range(self.block_column_size), range(2), vtype=gp.GRB.BINARY, name='upper_key')
        #upper_values[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed, 2=state_tested}
        self.upper_values = self.model.addVars(range(self.upper_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='upper_state_values')
        self.model.addConstrs((gp.quicksum(self.upper_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.upper_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_upper_state_value_constraints')

        #lower_values[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed, 2=state_tested}
        self.lower_values = self.model.addVars(range(self.lower_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='lower_state_values')
        self.model.addConstrs((gp.quicksum(self.lower_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.lower_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_lower_state_value_constraints')

        #upper_differences[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed}
        self.upper_differences = self.model.addVars(range(self.upper_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='upper_state_differences')
        self.model.addConstrs((gp.quicksum(self.upper_differences[round_index, state_index, row, column, value] for value in range(2)) == 1 
                              for round_index in range(self.upper_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_upper_difference_value_constraints')

        #lower_differences[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed}
        self.lower_differences = self.model.addVars(range(self.lower_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='lower_state_differences')
        self.model.addConstrs((gp.quicksum(self.lower_differences[round_index, state_index, row, column, value] for value in range(2)) == 1 
                              for round_index in range(self.lower_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_lower_difference_value_constraints')

    #Propagation of values operators
    def value_propagation_SR(self, round_index, input_state_index, output_state_index, shift_rows):
        ''' Generate the SR constraints for the value propagation between two states
        Parameters 
        ----------
        round_index : int 
                The index of the considered round

        input_state_index : int 
                The index of the state to which the SR transformation is applied 

        output_state_index : int 
                The index of the state resulting form the SR transformation

        shift_rows : list 
                The SR transformation 1-dimensional matrix 
        '''
        #an unknow value cannot turn to a value that can be computed.
        self.model.addConstrs(((self.upper_values[round_index, input_state_index, row, column, 0] == 1)
                                >> (self.upper_values[round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size, 1] == 0)
                                for row in range(4) for column in range(4)),
                                name = "value_propagation_SR_0_not_to_1")
        
    def value_propagation_MC(self, round_index, input_state_index, output_state_index, mix_columns):
        ''' Generate the MC constraints for the value propagation between two states
        Parameters 
        ----------
        round_index : int 
                The index of the considered round

        input_state_index : int 
                The index of the state to which the SR transformation is applied 

        output_state_index : int 
                The index of the state resulting form the SR transformati

        mix_columns : list of list 
                The SR transformation 1-dimensional matrix 
        '''
        #if you have an unknow value in the active bits before MC, the ouput of MC cannot be computed
        self.model.addConstrs(((self.upper_values[round_index, input_state_index, row_input, column, 0]==1)
                                >> (self.upper_values[round_index, output_state_index, row_output, column, 1]==0)
                               for row_output in range(self.block_row_size)  for column in range(self.block_column_size) for row_input in [i for i, n in enumerate(mix_columns[column]) if n==1]), 
                               name = "value_propagation_MC_0_not_to_1")
    
    def value_propagation_SB(self, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        self.model.addConstrs(((self.upper_values[round_index, input_state_index, row_input, column_input, 0]==1)
                                 >> (self.upper_values[round_index, output_state_index, row_output, column_output, 1]==0)
                                 for row_output in range(self.block_row_size)
                                 for column_output in range(self.block_column_size)
                                 for row_input in range(row_output, row_output + sbox_sizes[0])
                                 for column_input in range(column_output, column_output+sbox_sizes[1])), 
                                 name='value_propagation_SB_0_not_to_1')

    def value_propagation_AK(self, round_index, input_state_index, output_state_index, subkey_part):
        #if the state if not known before the AK it cannot be computed after
        self.model.addConstrs((((self.upper_values[round_index, input_state_index, row, column, 0]==1)
                                >> (self.upper_values[round_index, output_state_index, row, column, 1]==0))
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_0_in_state_not_to_1')
        
        if subkey_part == 'upper_subkey':
            #if the key is not known, the state after AK cannot be computed
            self.model.addConstrs((((self.upper_subkey[round_index, row, column, 0]==1)
                                   >> (self.upper_values[round_index, output_state_index, row, column, 1]==0))
                                   for row in range(self.block_row_size) for column in range(self.block_column_size))
                                   ,name = 'value_propagation_SK_0_in_upper_subkey_not_to_1')
        
        elif subkey_part == 'lower_subkey':
            #if the key is not known, the state after AK cannot be computed
            self.model.addConstrs((((self.lower_subkey[round_index, row, column, 0]==1)
                                   >> (self.upper_values[round_index, output_state_index, row, column, 1]==0))
                                   for row in range(self.block_row_size) for column in range(self.block_column_size))
                                   ,name = 'value_propagation_SK_0_in_lower_subkey_not_to_1')
        
        else :
            self.everything_all_right = False
            print(f'KEY ERROR :  Subkey name given for the key at round {round_index} is not usable')

    def value_propagation_NR(self, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs(((self.upper_values[input_round_index, self.state_number-1, row, column, 0]==1)
                                >> (self.upper_values[output_round_index, 0, row, column, 1]==0) for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                name='value_propagation_NR_0_not_to_1')

    #Propagation of differences operatos
    #def difference_propagation_SR(self, round_inedx, input_state_index, output_state_index, shift_rows):
        #self.model.addConstrs()

    def upper_part_value_propagation(self):
        self.model.addConstrs(self.upper_values[0, 0, row, column, 1]==1 for row in range(self.block_row_size) for column in range(self.block_column_size))
        self.model.addConstrs(self.upper_subkey[round_index, row, column, 1]==rd.randint(0,1) for round_index in range(self.upper_rounds) for row in range(self.block_row_size) for column in range(self.block_column_size))

        for upper_round in range(self.upper_rounds):
            for state_index in range(len(self.operation_order)):
                if self.operation_order[state_index] == 'SR':
                    self.value_propagation_SR(upper_round, state_index, state_index+1, self.shift_rows)
                elif self.operation_order[state_index] == 'MC':
                    self.value_propagation_MC(upper_round, state_index, state_index+1, self.mix_columns)
                elif self.operation_order[state_index] == 'SB':
                    self.value_propagation_SB(upper_round, state_index, state_index+1, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    self.value_propagation_AK(upper_round, state_index, state_index + 1, 'upper_subkey')
                else :
                    self.everything_all_right = False
                    print("One of the round operator name is not recognized")
            if upper_round != self.upper_rounds-1:
                self.value_propagation_NR(upper_round, upper_round+1)

    def objective_function(self):
        self.state_test_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "state_test_up")
        self.active_fin = self.model.addVar(vtype= gp.GRB.INTEGER, name = "active_fin")

        self.model.addConstr(self.state_test_up == (gp.quicksum(self.upper_values[round_index, state_index, row, column, 2] for round_index in range(self.upper_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))))
        self.model.addConstr(self.active_fin == (gp.quicksum(self.upper_values[self.upper_rounds-1, self.state_number-1, row, column, 1] for row in range(self.block_row_size) for column in range(self.block_column_size))))
        
        
        self.model.setObjective(self.state_test_up - self.active_fin)

    def optimize(self):
        if self.everything_all_right:
            self.model.optimize()
            self.optimize=True
        else : 
            print("Some error occured in assembling the model, please check the error(s) above.")

    def getresults(self):
        if self.optimize:
            print(self.state_test_up)
            print(self.active_fin)
        else :
            print('The Model at no been optimize yet')

