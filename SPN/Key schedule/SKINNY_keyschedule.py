from SPN.model_MILP_attack import Model_MILP_attack
import gurobipy as gp


class Model_MILP_SKINNY_key_schedule(Model_MILP_attack):
    def __init__(self, cipher_parameters, key_schedule_specification, total_round):
        #Key parameters
        self.tweakey_number = cipher_parameters.get('tweakey_number', 3)
        self.key_size = self.block_size*self.tweakey
        self.key_schedule_permutation = key_schedule_specification.get('permutation')
        self.total_round = total_round

    def one_permutation(self, input_list):
        return([[input_list[self.key_schedule_permutation[i]] for i in range(len(input_list))]])
    
    def x_permutation(self, input_list, x):
        output_permutation = self.one_permutation(input_list)
        for i in range(x):
            output_permutation = self.one_permutation(output_permutation)
        return(output_permutation)

    def master_key_initialisation(self):
        self.master_key = self.model.addVars(range(self.key_size//self.block_size), 
                                             range(self.block_row_size), 
                                             range(self.block_column_size), range(3),
                                             vtype = gp.GRB.BINARY, 
                                             name  = 'master_key')

        self.model.addConstrs((self.master_key[tweakey, row, column, 0]==1) >> (self.master_key[tweakey, row, column, value] == 0)
                              for tweakey in range(self.tweakey_number) 
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)
                              for value in [1,2])

    def subkey_initialisation(self):
        self.subkey_upper_part = self.model.addVars(range(self.total_round), 
                                                    range(self.block_row_size), 
                                                    range(self.block_column_size), 
                                                    vtype = gp.GRB.BINARY, 
                                                    name = 'subkey_upper_part')
        
        self.subkey_lower_part = self.model.addVars(range(self.total_round), 
                                                    range(self.block_row_size), 
                                                    range(self.block_column_size), 
                                                    vtype = gp.GRB.BINARY, 
                                                    name = 'subkey_lower_part')

    def keyschedule(self):
        self.master_key_initialisation()
        self.subkey_initialisation()

        #only half of the state is added
        self.model.addConstrs((self.subkey_upper_part[round_index, row, column]==1
                              for round_index in range(self.total_round)
                              for row in range(self.block_row_size//2, self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'half_upper_subkey_addition_')

        self.model.addConstrs((self.subkey_lower_part[round_index, row, column]==1
                              for round_index in range(self.total_round)
                              for row in range(self.block_row_size//2, self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'half_lower_subkey_addition_')
        
        #If a Master key word is known, the corresponding key word is know in each subkey
        self.model.addConstrs(((self.master_key[tweakey, row, column, 1]==1) >> (self.subkey[round_index, row, column, 1]==1)
                              for tweakey in range(self.tweakey_number)
                              for round_index in range(tweakey, self.total_round, 3)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'master_key_active_induce_subkey_activity')
                              
        
                              

        

        