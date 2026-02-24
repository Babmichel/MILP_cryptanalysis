from Model import Common_bricks_for_attacks
import gurobipy as gp
import numpy as np

class attack_model(Common_bricks_for_attacks.MILP_bricks):
    def __init__(self, cipher_parameters, licence_parameters, attack_parameters, model):
        super().__init__(cipher_parameters, licence_parameters, model)
        #Attack parameters
        self.structure_rounds = attack_parameters.get('structure_rounds', 4)
        self.structure_first_round_index = 0
        self.structure_last_round_index = self.structure_rounds - 1

        self.upper_rounds = attack_parameters.get('upper_rounds', 2)
        self.upper_part_first_round = self.structure_rounds
        self.upper_part_last_round = self.structure_rounds + self.upper_rounds - 1

        self.distinguisher_probability = attack_parameters.get('distinguisher_probability', 32)
        self.distinguisher_rounds = attack_parameters.get('distinguisher_rounds', 2)
        self.distinguisher_input = attack_parameters.get('distinguisher_inputs', [[2, 1], [3, 2]])
        self.distinguisher_output = attack_parameters.get('distinguisher_outputs', [[2, 1], [3, 2]])
        self.distinguisher_input_quantity = len(self.distinguisher_input)
        self.distinguisher_output_quantity = len(self.distinguisher_output)

        self.lower_rounds = attack_parameters.get('lower_rounds', 2)
        self.lower_part_first_round = self.upper_part_last_round + self.distinguisher_rounds
        self.lower_part_last_round = self.lower_part_first_round + self.lower_rounds

        self.key_size = cipher_parameters.get('key_size', self.block_size*2)
        self.key_space_size = attack_parameters.get('key_space_size', self.key_size)

        self.total_rounds = self.structure_rounds + self.upper_rounds + self.lower_rounds + self.distinguisher_rounds
        self.optimal_complexity = attack_parameters.get('optimal_complexity', False)

        self.trunc_diff = attack_parameters.get('truncated_differential', False)

        self.filter_state_test = attack_parameters.get('filter_state_test', False)

        self.state_test_use = attack_parameters.get('state_test_use', True)
        
    #Variables initialisation
    #values to construct the structure and the upper and lower parts
    def value_variables_initialisation(self):
        self.values = self.model.addVars(range(2), range(2),
                                            range(self.total_rounds),
                                            range(self.state_number),
                                            range(self.block_row_size),
                                            range(self.block_column_size),
                                            range(3), #valeur{0=unknown, 1=can be computed, 2=fixed}
                                            vtype=gp.GRB.BINARY,
                                            name='state')
        
        self.model.addConstrs((gp.quicksum(self.values[part, sens, round_index, state_index, row, column, value] for value in range(3)) == 1 
                                for part in range(2)
                                for sens in range(2)
                                for round_index in range(self.total_rounds)
                                for state_index in range(self.state_number) 
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='unique_value_in_state_constraints')

        self.model.addConstrs((self.values[part, 0, round_index, state_index, row, column, 2] == self.values[part, 1, round_index, state_index, row, column, 2]
                             for part in range(2)
                             for round_index in range(self.total_rounds)
                             for state_index in range(self.state_number) 
                             for row in range(self.block_row_size) 
                             for column in range(self.block_column_size)), 
                             name='same fix elements in both propagation')
        
        #value in the structure for the matching differences
        self.value_in_structure=self.model.addVars(range(2), range(2),
                                            range(self.structure_first_round_index, self.structure_last_round_index+1),
                                            range(self.state_number),
                                            range(self.block_row_size),
                                            range(self.block_column_size),
                                            range(3),
                                            vtype=gp.GRB.BINARY,
                                            name='value_in_structure')

        self.model.addConstrs((gp.quicksum(self.value_in_structure[part, sens, round_index, state_index, row, column, value] for value in range(3)) == 1 
                                for part in range(2)
                                for sens in range(2)
                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                for state_index in range(self.state_number) 
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='unique_value_in_state_constraints')
        
        self.model.addConstrs((self.value_in_structure[part, sens, round_index, state_index, row, column, 2] == 0
                             for part in range(2)
                             for sens in range(2)
                             for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                             for state_index in range(self.state_number) 
                             for row in range(self.block_row_size) 
                             for column in range(self.block_column_size)), 
                             name='no fix for value propagation')
        
        #MC fix values
        for element in self.operation_order:
            if element == 'MC':
                self.XOR_in_mc_values = self.model.addVars((((part, sens, round_index, column) + (xor_combination) + (value,)) 
                                                            for part in range(2)
                                                            for sens in range(2)
                                                            for round_index in range(self.total_rounds)
                                                            for column in range(self.block_column_size)
                                                            for xor_combination in self.column_range[sens][round_index%len(self.matrixes[sens])]   
                                                            for value in range(3)), vtype=gp.GRB.INTEGER, name="fix_in_mc")
                
                self.model.addConstrs((gp.quicksum(self.XOR_in_mc_values[(part, sens, round_index, column) + xor_combination + (value,)] for value in range(3)) == 1 
                                        for part in range(2)
                                        for sens in range(2)
                                        for round_index in range(self.total_rounds)
                                        for column in range(self.block_column_size)
                                        for xor_combination in self.column_range[sens][round_index%len(self.matrixes[sens])]),
                                        name='unique_value_in_mc_fix_constraints')

                self.model.addConstrs((self.XOR_in_mc_values[(part, 0, round_index, column) + xor_combination + (2,)] == self.XOR_in_mc_values[(part, 1, round_index, column) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)]
                                        for part in range(2)
                                        for round_index in range(self.total_rounds)
                                        for column in range(self.block_column_size)
                                        for xor_combination in self.column_range[0][round_index%len(self.matrixes[0])]),
                                        name='same fix for backward and forward propagation')
            
            if element == 'MR':
                self.XOR_in_mr_values = self.model.addVars((((part, sens, round_index, row) + (xor_combination) + (value,)) 
                                                            for part in range(2)
                                                            for sens in range(2)
                                                            for round_index in range(self.total_rounds)
                                                            for row in range(self.block_row_size)
                                                            for xor_combination in self.row_range[sens][round_index%len(self.matrixes[sens])]   
                                                            for value in range(3)), vtype=gp.GRB.INTEGER, name="fix_in_mc")
                
                self.model.addConstrs((gp.quicksum(self.XOR_in_mr_values[(part, sens, round_index, row) + xor_combination + (value,)] for value in range(3)) == 1 
                                        for part in range(2)
                                        for sens in range(2)
                                        for round_index in range(self.total_rounds)
                                        for row in range(self.block_row_size)
                                        for xor_combination in self.row_range[sens][round_index%len(self.matrixes[sens])]),
                                        name='unique_value_in_mc_fix_constraints')

                self.model.addConstrs((self.XOR_in_mr_values[(part, 0, round_index, row) + xor_combination + (2,)] == self.XOR_in_mr_values[(part, 1, round_index, row) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)]
                                        for part in range(2)
                                        for round_index in range(self.total_rounds)
                                        for row in range(self.block_row_size)
                                        for xor_combination in self.row_range[0][round_index%len(self.matrixes[0])]),
                                        name='same fix for backward and forward propagation')
                

        #state_test
        if not self.state_test_use :
            self.model.addConstr((gp.quicksum(self.values[part, sens, round_index, state_index, row, column, 2]
                                for part in range(2)
                                for sens in range(2)
                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                for state_index in range(self.state_number)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)) == 0), 
                                name='no_state_test_constraints')

    
    def difference_variables_initialisation(self):
        #Difference propagation
        self.differences = self.model.addVars(range(2), range(2),
                                            range(self.total_rounds),
                                            range(self.state_number),
                                            range(self.block_row_size),
                                            range(self.block_column_size),
                                            range(2), #valeur{0=active, 1=unactive}
                                            vtype=gp.GRB.BINARY,
                                            name='state')
        
        #unique possible value
        self.model.addConstrs((gp.quicksum(self.differences[part, sens, round_index, state_index, row, column, value] for value in range(2)) == 1 
                                for part in range(2)
                                for sens in range(2)
                                for round_index in range(self.total_rounds)
                                for state_index in range(self.state_number) 
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='unique_value_in_difference_constraints')
        
        #MC and MR possible XOR
        for element in self.operation_order:
            if element == 'MC':
                self.XOR_in_mc_differences = self.model.addVars((((part, sens, round_index, column) + (xor_combination) + (value,)) 
                                                            for part in range(2)
                                                            for sens in range(2)
                                                            for round_index in range(self.total_rounds)
                                                            for column in range(self.block_column_size)
                                                            for xor_combination in self.column_range[sens][round_index%len(self.matrixes[sens])]   
                                                            for value in range(3)), vtype=gp.GRB.INTEGER, name="fix_in_mc_diff")
                
                self.model.addConstrs((gp.quicksum(self.XOR_in_mc_differences[(part, sens, round_index, column) + xor_combination + (value,)] for value in range(3)) == 1 
                                        for part in range(2)
                                        for sens in range(2)
                                        for round_index in range(self.total_rounds)
                                        for column in range(self.block_column_size)
                                        for xor_combination in self.column_range[sens][round_index%len(self.matrixes[sens])]),
                                        name='unique_value_in_mc_fix_constraints')

                self.model.addConstrs((self.XOR_in_mc_differences[(part, 0, round_index, column) + xor_combination + (2,)] == self.XOR_in_mc_differences[(part, 1, round_index, column) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)]
                                        for part in range(2)
                                        for round_index in range(self.total_rounds)
                                        for column in range(self.block_column_size)
                                        for xor_combination in self.column_range[0][round_index%len(self.matrixes[0])]),
                                        name='same fix for backward and forward propagation')     

                for round_index in range(self.total_rounds):
                    for vector in self.column_range[0][round_index%len(self.matrixes[0])]:
                        if sum(vector)==1:
                            self.model.addConstrs((self.XOR_in_mc_differences[(part, 0, round_index, column) + vector + (2,)] == 0
                                                  for part in range(2)
                                                  for column in range(self.block_column_size)), name="cannot cancel a single difference")
                    for vector in self.column_range[1][round_index%len(self.matrixes[1])]:
                        if sum(vector)==1:
                            self.model.addConstrs((self.XOR_in_mc_differences[(part, 1, round_index, column) + vector + (2,)] == 0
                                                  for part in range(2)
                                                  for column in range(self.block_column_size)), name="cannot cancel a single difference")
            
            if element == 'MR':
                self.XOR_in_mr_differences = self.model.addVars((((part, sens, round_index, row) + (xor_combination) + (value,)) 
                                                            for part in range(2)
                                                            for sens in range(2)
                                                            for round_index in range(self.total_rounds)
                                                            for row in range(self.block_row_size)
                                                            for xor_combination in self.row_range[sens][round_index%len(self.matrixes[sens])]   
                                                            for value in range(3)), vtype=gp.GRB.INTEGER, name="fix_in_mc_diff")
                
                self.model.addConstrs((gp.quicksum(self.XOR_in_mr_differences[(part, sens, round_index, row) + xor_combination + (value,)] for value in range(3)) == 1 
                                        for part in range(2)
                                        for sens in range(2)
                                        for round_index in range(self.total_rounds)
                                        for row in range(self.block_row_size)
                                        for xor_combination in self.row_range[sens][round_index%len(self.matrixes[sens])]),
                                        name='unique_value_in_mc_fix_constraints')

                self.model.addConstrs((self.XOR_in_mr_differences[(part, 0, round_index, row) + xor_combination + (2,)] == self.XOR_in_mr_differences[(part, 1, round_index, row) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)]
                                        for part in range(2)
                                        for round_index in range(self.total_rounds)
                                        for row in range(self.block_row_size)
                                        for xor_combination in self.row_range[0][round_index%len(self.matrixes[0])]),
                                        name='same fix for backward and forward propagation')
                
                for round_index in range(self.total_rounds):
                    for vector in self.row_range[0][round_index%len(self.matrixes[0])]:
                        if sum(vector)==1:
                            self.model.addConstrs((self.XOR_in_mr_differences[(part, 0, round_index, row) + vector + (2,)] == 0
                                                  for part in range(2)
                                                  for row in range(self.block_row_size)), name="cannot cancel a single difference")
                            
                for round_index in range(self.total_rounds):
                    for vector in self.row_range[1][round_index%len(self.matrixes[1])]:
                        if sum(vector)==1:
                            self.model.addConstrs((self.XOR_in_mr_differences[(part, 1, round_index, row) + vector + (2,)] == 0
                                                  for part in range(2)
                                                  for row in range(self.block_row_size)), name="cannot cancel a single difference")
                
    #Part constraints
    def structure(self):
        ###VALUES
        ###Upper values 
        #Variable initialisation
        self.fix_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "fix_up")
        
        self.active_start_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "active_start_up")

        #Constraints
        self.forward_values_propagation(0, self.structure_first_round_index, self.structure_last_round_index, self.upper_subkey)
        self.backward_values_propagation(0, self.structure_first_round_index, self.structure_last_round_index, self.upper_subkey)
        
        fix_elements = gp.quicksum(self.values[0, 0, round_index, state_index, row, column, 2]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for state_index in range(self.state_number)
                                                            for row in range(self.block_row_size)
                                                            for column in range(self.block_column_size))
        if 'MC' in self.operation_order:
            fix_elements += gp.quicksum(self.XOR_in_mc_values[(0, 0, round_index, column)+(column_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for column in range(self.block_column_size)
                                                            for column_xor in self.column_range[0][round_index%len(self.matrixes[0])])
        if 'MR' in self.operation_order:
            fix_elements += gp.quicksum(self.XOR_in_mr_values[(0, 0, round_index, row)+(row_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for row in range(self.block_row_size)
                                                            for row_xor in self.row_range[0][round_index%len(self.matrixes[0])]) 
        
        self.model.addConstr(self.fix_up == fix_elements, name='fix_up_count')
        
        self.model.addConstr(self.active_start_up == (self.block_size//self.word_size
                                                    - gp.quicksum(self.values[0, 0, self.structure_last_round_index, self.operation_order.index('AK')+1, row, column , 0]
                                                                  for row in range(self.block_row_size) 
                                                                  for column in range(self.block_column_size))), 
                            name='active_last_state_structure')
        
        self.model.addConstr(self.active_start_up==self.fix_up, name='each_up_fix_leads_to_a_known_value_in_last_state')
        
        ###Lower values
        #Variable initialisation
        self.fix_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "fix_down")
        
        self.active_start_down =  self.model.addVar(vtype= gp.GRB.INTEGER, name = "active_start_down")
        
        #Constraints
        self.backward_values_propagation(1, self.structure_first_round_index, self.structure_last_round_index, self.lower_subkey)
        self.forward_values_propagation(1, self.structure_first_round_index, self.structure_last_round_index, self.lower_subkey)
        
        fix_elements = gp.quicksum(self.values[1, 1, round_index, state_index, row, column, 2]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for state_index in range(self.state_number)
                                                            for row in range(self.block_row_size)
                                                            for column in range(self.block_column_size))
        if 'MC' in self.operation_order:
            fix_elements += gp.quicksum(self.XOR_in_mc_values[(1, 1, round_index, column)+(column_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for column in range(self.block_column_size)
                                                            for column_xor in self.column_range[1][round_index%len(self.matrixes[1])])
        if 'MR' in self.operation_order:
            fix_elements += gp.quicksum(self.XOR_in_mr_values[(1, 1, round_index, row)+(row_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for row in range(self.block_row_size)
                                                            for row_xor in self.row_range[1][round_index%len(self.matrixes[1])])
        
        self.model.addConstr(self.fix_down == fix_elements, name='fix_down_count')

        self.model.addConstr(self.active_start_down == self.block_column_size*self.block_row_size
                                                     - gp.quicksum(self.values[1, 1, self.structure_first_round_index, self.operation_order.index('AK'), row, column , 0]
                                                                  for row in range(self.block_row_size) 
                                                                  for column in range(self.block_column_size)), 
                            name='active_last_state_structure')
        
        self.model.addConstr(self.active_start_down==self.fix_down, name='each_down_fix_leads_to_a_known_value_in_first_state')
        
        
        #Propagation initial Contrainst
        self.model.addConstrs((self.values[0, 0, 0, self.operation_order.index('AK'), row, column, 1] == 0
                            for row in range(self.block_row_size)
                            for column in range(self.block_column_size)),
                            name='no_initial_known_value_upper_structure')

        self.model.addConstrs((self.values[1, 0, 0, self.operation_order.index('AK'), row, column, 1] == 0
                            for row in range(self.block_row_size)
                            for column in range(self.block_column_size)),
                            name='no_initial_known_value_lower_structure')
        
        self.model.addConstrs((self.values[1, 1, self.structure_rounds-1, self.operation_order.index('AK')+1, row, column, 1] ==0
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name='no_initial_known_value_lower_structure')
        
        self.model.addConstrs((self.values[0, 1, self.structure_rounds-1, self.operation_order.index('AK')+1, row, column, 1] ==0
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name='no_initial_known_value_upper_structure')
        
        # Common fix constraints          
        self.common_fix = self.model.addVar(vtype= gp.GRB.INTEGER, name = "fix_common")
        
        common_fix_elements = gp.quicksum(self.values[1, 1, round_index, state_index, row, column, 2]*self.values[0, 0, round_index, state_index, row, column, 2]
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                                for state_index in range(self.state_number) 
                                                                for row in range(self.block_row_size) 
                                                                for column in range(self.block_column_size) )
        if 'MC' in self.operation_order:
            common_fix_elements += gp.quicksum(self.XOR_in_mc_values[(0, 0, round_index, column)+xor_combination+(2,)]*self.XOR_in_mc_values[(1, 1, round_index, column) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) +(2,)]
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                                for column in range(self.block_column_size)
                                                                for xor_combination in self.column_range[0][round_index%len(self.matrixes[1])])
        
        if 'MR' in self.operation_order:
            common_fix_elements += gp.quicksum(self.XOR_in_mr_values[(0, 0, round_index, row)+xor_combination+(2,)]*self.XOR_in_mr_values[(1, 1, round_index, row) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) +(2,)]
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                                for row in range(self.block_row_size)
                                                                for xor_combination in self.row_range[0][round_index%len(self.matrixes[1])])
        
        self.model.addConstr(self.common_fix == common_fix_elements, name='common_fix_count')
        
        self.model.addConstr(self.fix_down+self.fix_up-self.common_fix<=self.block_size//self.word_size, name='cannot_fix_more_than_the_block')

        self.max_fix_up_fix_down = self.model.addVar(vtype= gp.GRB.INTEGER, name="max fix upper part")
        self.binary_max_fix_up_fix_down = self.model.addVar(vtype= gp.GRB.INTEGER, name="max fix upper part")
        max_max = self.block_column_size*self.block_row_size
        self.model.addConstr(self.max_fix_up_fix_down >= self.fix_up)
        self.model.addConstr(self.max_fix_up_fix_down >= self.fix_down)
        self.model.addConstr(self.max_fix_up_fix_down <= self.fix_up + max_max*self.binary_max_fix_up_fix_down)
        self.model.addConstr(self.max_fix_up_fix_down <= self.fix_down + max_max*self.binary_max_fix_up_fix_down)



        ### DIFEERENCES
        #Not interest in propagation of forward differences of upper part
        self.model.addConstrs((self.differences[0, 0, round_index, part, row, column, 0] == 1
                               for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                               for part in range(self.state_number)
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="no_forward_upper_differences")
        
        #Not interest in propagation of backward differences of lower part
        self.model.addConstrs((self.differences[1, 1, round_index, part, row, column, 0] == 1
                               for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                               for part in range(self.state_number)
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="no_backaward_lower_differences")
        
        #first state is completly known by the lower part
        self.model.addConstrs((self.differences[1, 0, 0, self.operation_order.index('AK'), row, column, 1] == 1
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="lower part know all the differences at the begining at the structure")
        
        #Last state is completely known by the upper part
        self.model.addConstrs((self.differences[0, 1, self.structure_last_round_index, self.operation_order.index('AK')+1, row, column, 1] == 1
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="upper part know all the differences at the end at the structure")
        
        self.forward_differences_propagation_in_structure(1, self.structure_first_round_index, self.structure_last_round_index)
        self.backward_differences_propagation_in_structure(0, self.structure_first_round_index, self.structure_last_round_index)

        max_max = self.block_column_size*self.block_row_size
        self.matching_differences = self.model.addVars(range(self.structure_rounds-1), vtype= gp.GRB.INTEGER, name = "match_differences per round")
        self.matching_differences_quantity = self.model.addVar(lb=0, ub=max_max, vtype=gp.GRB.INTEGER, name="match quantity")
        self.binary_matching_differences_quantity = self.model.addVars(range(self.structure_rounds-1), vtype=gp.GRB.BINARY, name="match quantity_binary")
        

        self.model.addConstrs((self.matching_differences[round_index] == gp.quicksum(self.differences[0, 1, round_index+self.structure_first_round_index, self.operation_order.index('SB')+i, row, column, 1]*self.differences[1, 0, round_index+self.structure_first_round_index, self.operation_order.index('SB')+i, row, column, 1]
                                                                      for i in range(2)
                                                                      for row in range(self.block_row_size)
                                                                      for column in range(self.block_column_size))
                                                                      - gp.quicksum(self.differences[0, 1, round_index+self.structure_first_round_index, self.operation_order.index('SB'), row, column, 1]*self.differences[1, 0, round_index+self.structure_first_round_index, self.operation_order.index('SB')+1, row, column, 1]
                                                                      for row in range(self.block_row_size)
                                                                      for column in range(self.block_column_size))
                                                                      for round_index in range(self.structure_rounds-1)), name = "counting matching differences")
        
        for round_index in range(self.structure_rounds-1) :
            self.model.addConstr(self.matching_differences_quantity >= self.matching_differences[round_index], name = "difference matching in structure max 1")
            self.model.addConstr(self.matching_differences_quantity <= self.matching_differences[round_index] + max_max*(1-self.binary_matching_differences_quantity[round_index]), name = "difference matching in structure max 2")
        self.model.addConstr(gp.quicksum(self.binary_matching_differences_quantity[round_index] for round_index in range(self.structure_rounds-1) ) == 1, name = "at least one max")
        
        self.model.addConstr(self.matching_differences_quantity >= self.common_fix)
        #No probabilisit propagation in structure :
        if 'MC' in self.operation_order :
            self.model.addConstrs(self.XOR_in_mc_differences[(attack_side_index, sens, round_index, column) + vector + (2,)]==0
                                                                for attack_side_index in range(2)
                                                                for sens in range(2)
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                                for column in range(self.block_column_size)
                                                                for vector in self.column_range[sens][round_index%len(self.matrixes[sens])])
        
        if 'MR' in self.operation_order :
            self.model.addConstrs(self.XOR_in_mr_differences[(attack_side_index, sens, round_index, row) + vector + (2,)]==0
                                                                for attack_side_index in range(2)
                                                                for sens in range(2)
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                                for row in range(self.block_row_size)
                                                                for vector in self.row_range[sens][round_index%len(self.matrixes[sens])]) 

        #Propagation of values for difference matching
        #Not interest in propagation of bacward lower values
        self.model.addConstrs((self.value_in_structure[1, 1, round_index, state, row, column, 0] == 1
                               for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                               for state in range(self.state_number)
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), 
                               name = "no bacward lower values propagation in the structure for matching differences")
        
        #Not interest in propagation of bacward lower values
        self.model.addConstrs((self.value_in_structure[0, 0, round_index, state, row, column, 0] == 1
                               for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                               for state in range(self.state_number)
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), 
                               name = "no bacward lower values propagation in the structure for matching differences")
        
        #first state of the begining of the structure is know by the upper part :
        self.model.addConstrs((self.value_in_structure[1, 0, 0, 0, row, column, 1]==1
                             for row in range(self.block_row_size)
                             for column in range(self.block_column_size)), 
                             name = "first state of structure is know by the lower part")
        
        self.model.addConstrs((self.value_in_structure[0, 1, self.structure_last_round_index, self.state_number-1, row, column, 1]==1
                             for row in range(self.block_row_size)
                             for column in range(self.block_column_size)), 
                             name = "first state of structure is know by the lower part")
        
        self.forward_values_propagation_in_structure(1, self.structure_first_round_index, self.structure_last_round_index, self.lower_subkey)
        self.backward_values_propagation_in_structure(0, self.structure_first_round_index, self.structure_last_round_index, self.upper_subkey)
               
    def upper_part(self):
        ### Values
        #Variable initialisation 
        self.state_test_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "state_test_up")

        #Constraints :
        self.forward_values_propagation(0, self.upper_part_first_round, self.lower_part_last_round, self.upper_subkey)
        
        #not interest in bacward propagation of values 
        self.model.addConstrs((self.values[0, 1, round_index, part, row, column, 1]==0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), name="no backward propagation of upper values in corps")
        
        state_stest_up_elements = gp.quicksum(self.values[0, 0, round_index, state_index, row, column, 2]
                                                               for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                               for state_index in range(self.state_number)
                                                               for row in range(self.block_row_size)
                                                               for column in range(self.block_column_size))
        if 'MC' in self.operation_order:
            state_stest_up_elements += gp.quicksum(self.XOR_in_mc_values[(0, 0, round_index, column)+(column_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for column in range(self.block_column_size)
                                                                for column_xor in self.column_range[0][round_index%len(self.matrixes[0])])

        if 'MR' in self.operation_order:
            state_stest_up_elements += gp.quicksum(self.XOR_in_mr_values[(0, 0, round_index, row)+(row_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for row in range(self.block_row_size)
                                                                for row_xor in self.row_range[0][round_index%len(self.matrixes[0])])

        self.model.addConstr(self.state_test_up == state_stest_up_elements, name='state_test_up_count')
       
        self.model.addConstrs((self.values[0, 1, self.lower_part_last_round, self.operation_order.index('AK')+1, row, column, 0]==1 
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), name="last state of bacward propagation of upper values is 0")
        
        ### Differences
        #Variable initialisation
        self.probabilist_annulation_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "probabilist_annulation_up")

        #Constraints

        #Fix distinguisher input
        for row in range(self.block_row_size) :
            for column in range(self.block_column_size):
                if [row, column] in self.distinguisher_input :
                    self.model.addConstr(self.differences[0, 1, self.upper_part_last_round,self.operation_order.index('SB'), row, column, 1] == 1,
                                name='fix differcences active in the input of the distinguisher')
                else :
                    self.model.addConstr(self.differences[0, 1, self.upper_part_last_round,self.operation_order.index('SB'), row, column, 0] == 1,
                                name='fix differcences active in the input of the distinguisher')
        
        self.backward_differences_propagation(0, self.upper_part_first_round, self.lower_part_last_round)

        #no bacward propagation of differences in the upper part
        self.model.addConstrs((self.differences[0, 0, round_index, part, row, column, 1]==0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = "no backward upper propagation")
        
        #counting probabilist annulation
        probabilist_annulation_up_count = 0
        if 'MC' in self.operation_order:
            probabilist_annulation_up_count += gp.quicksum(self.XOR_in_mc_differences[(0, 1, round_index, column)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for column in range(self.block_column_size)
                                                          for vector in self.column_range[1][round_index%len(self.matrixes[1])])
        if 'MR' in self.operation_order:
            probabilist_annulation_up_count += gp.quicksum(self.XOR_in_mr_differences[(0, 1, round_index, row)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for row in range(self.block_row_size)
                                                          for vector in self.column_range[1][round_index%len(self.matrixes[1])])
        
        self.model.addConstr(self.probabilist_annulation_up == probabilist_annulation_up_count, name="probabilist annulation up count")
     
    def lower_part(self):
        ###VALUE
        #Variable initialisation
        self.state_test_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "state_test_down")
        
        #Constraints
        self.backward_values_propagation(1, self.upper_part_first_round, self.lower_part_last_round, self.lower_subkey)
        
        #not interest in forward propagation of lower values
        self.model.addConstrs((self.values[1, 0, round_index, part, row, column, 1]==0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), name="no backward propagation of upper values in corps")
        
        state_test_down_elements = gp.quicksum(self.values[1, 1, round_index, state_index, row, column, 2]
                                                               for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                               for state_index in range(self.state_number)
                                                               for row in range(self.block_row_size)
                                                               for column in range(self.block_column_size))
        if 'MC' in self.operation_order:
            state_test_down_elements += gp.quicksum(self.XOR_in_mc_values[(1, 0, round_index, column)+(column_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for column in range(self.block_column_size)
                                                                for column_xor in self.column_range[0][round_index%len(self.matrixes[0])])
        if 'MR' in self.operation_order:
            state_test_down_elements += gp.quicksum(self.XOR_in_mr_values[(1, 0, round_index, row)+(row_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for row in range(self.block_row_size)
                                                                for row_xor in self.row_range[0][round_index%len(self.matrixes[0])])
        
        self.model.addConstr(self.state_test_down == state_test_down_elements, name='state_test_down_count')

        self.model.addConstrs((self.values[1, 0, self.upper_part_first_round, self.operation_order.index('AK'), row, column, 0]==1
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), name = " forward propagation of lower values starts with only 0")  

        ### DIFFERENCE
        #Variable initialisation
        self.probabilist_annulation_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "probabilist_annulation_down")

        #Constraints

        #Fix distinguisher input
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                if [row, column] in self.distinguisher_output:
                    self.model.addConstr(self.differences[1, 0, self.lower_part_first_round, self.operation_order.index('SB'), row, column, 1] == 1,
                                    name='fix differences active in the output of the distinguisher')
                    
                else :
                    self.model.addConstr(self.differences[1, 0, self.lower_part_first_round, self.operation_order.index('SB'), row, column, 0] == 1,
                                    name='fix differences active in the output of the distinguisher')
        
        self.forward_differences_propagation(1, self.lower_part_first_round, self.lower_part_last_round)

        #no forward propagation of differences in the lower part
        self.model.addConstrs((self.differences[1, 1, round_index, part, row, column, 1]==0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = "no backward upper propagation")
        
        #counting probabilist annulation
        probabilist_annulation_down_count = 0
        if 'MC' in self.operation_order:
            probabilist_annulation_down_count += gp.quicksum(self.XOR_in_mc_differences[(1, 0, round_index, column)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for column in range(self.block_column_size)
                                                          for vector in self.column_range[0][round_index%len(self.matrixes[0])])
        if 'MR' in self.operation_order:
            probabilist_annulation_down_count += gp.quicksum(self.XOR_in_mr_differences[(1, 0, round_index, row)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for row in range(self.block_row_size)
                                                          for vector in self.row_range[0][round_index%len(self.matrixes[0])])
        
        self.model.addConstr(self.probabilist_annulation_down == probabilist_annulation_down_count, name = "counting probabilist_annulation in the lower part")                      
    
    #Complexities and objectives
    def complexities(self):
        self.time_complexity = self.model.addVar(vtype= gp.GRB.CONTINUOUS, name = "time_complexity")
        self.memory_complexity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "memory_complexity")
        self.data_complexity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "data_complexity")

        self.time_complexity_up = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_up")
        self.time_complexity_down = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_down")
        self.time_complexity_match = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_match")
        self.time_complexity_brute_force = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_brute_force")

        self.data_fixe = self.model.addVar(vtype= gp.GRB.INTEGER, name = "data_fixe")

        self.key_guess_quantity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "time_complexity_up")

        self.attack_repetition = self.model.addVar(vtype= gp.GRB.INTEGER, name = "attack_repetition")

        if (self.structure_rounds <=1 and self.cipher_name == 'SKINNY') or (self.structure_rounds <=2 and self.cipher_name == 'GIFT'):
            self.model.addConstr(self.key_guess_quantity == self.upper_key_guess + self.lower_key_guess - self.common_key_guess + (self.matching_differences_quantity - self.common_fix)/2)
        else :
            self.model.addConstr(self.key_guess_quantity == self.upper_key_guess + self.lower_key_guess - self.common_key_guess + (self.matching_differences_quantity - self.common_fix))
        
        T_complexity_up = self.upper_key_guess + self.state_test_up + self.probabilist_annulation_down + self.max_fix_up_fix_down- self.fix_up
        T_complexity_down = self.lower_key_guess + self.state_test_down + self.probabilist_annulation_up + self.max_fix_up_fix_down- self.fix_down
        T_complexity_match = T_complexity_up + T_complexity_down - self.matching_differences_quantity + self.block_size//self.word_size - self.common_fix*2 - self.common_key_guess
        T_complexit_brute_force = self.key_space_size + (T_complexity_match-self.key_guess_quantity)*(1-self.attack_repetition)
        
        if self.filter_state_test :
            T_complexity_match += -self.state_test_up -self.state_test_down
    
        if self.trunc_diff :
            T_complexity_down += self.distinguisher_output_quantity - self.distinguisher_input_quantity
            T_complexity_match += self.distinguisher_output_quantity

        self.model.addConstr(self.time_complexity_up == T_complexity_up)
        self.model.addConstr(self.time_complexity_down == T_complexity_down)
        self.model.addConstr(self.time_complexity_match == T_complexity_match)
        self.model.addConstr(self.time_complexity_brute_force == T_complexit_brute_force)

        self.model.addConstr(self.time_complexity_down <= self.time_complexity, name="suboptimal time complexity down")
        self.model.addConstr(self.time_complexity_up <= self.time_complexity, name="suboptimal time complexity up")
        self.model.addConstr(self.time_complexity_match <= self.time_complexity, name="suboptimal time complexity match")
        #self.model.addConstr(self.time_complexity_brute_force <= self.time_complexity, name="suboptimal time complexity brute force")

        # self.model.addConstr(self.time_complexity_match + self.time_complexity_down +self.time_complexity_up <= self.time_complexity, name="suboptimal time complexity match")

        self.model.addConstr(self.memory_complexity <= self.upper_key_guess + self.state_test_up - self.common_fix + (self.block_size//self.word_size - self.fix_up),
                              name='memory_complexity_up_definition')
        self.model.addConstr(self.memory_complexity <= self.lower_key_guess + self.state_test_down - self.common_fix + (self.block_size//self.word_size - self.fix_down),
                              name='memory_complexity_down_definition')
        
        self.model.addConstr(self.data_complexity >= self.block_size//self.word_size - gp.quicksum(self.values[1, 1, 0, 0, row, column, 2] for row in range(self.block_row_size) for column in range(self.block_column_size)), name='data_definition')
        
        self.model.addConstr(self.data_complexity >= self.distinguisher_probability//self.word_size, name='data_definition')

    def objective_for_display(self):
        self.for_display = self.model.addVar(vtype= gp.GRB.INTEGER, name = "for_display")

        self.model.addConstr(self.for_display == gp.quicksum(self.values[attack_part, attack_part, round_index, state_index, row, column, 1]
                                                             for attack_part in range(2)
                                                             for round_index in range(self.total_rounds)
                                                             for state_index in range(self.state_number) 
                                                             for row in range(self.block_row_size) 
                                                             for column in range(self.block_column_size)) 
                                                + gp.quicksum(self.differences[attack_part, not(attack_part), round_index, state_index, row, column, 1]
                                                             for attack_part in range(2)
                                                             for round_index in range(self.total_rounds)
                                                             for state_index in range(self.state_number) 
                                                             for row in range(self.block_row_size) 
                                                             for column in range(self.block_column_size)) )

        self.model.setObjectiveN(self.for_display, index=10, priority=0)
    
    def objective(self):
        self.objective_for_display()
        self.complexities()

        self.model.setObjectiveN(self.time_complexity, index=0, priority=10)
        #self.model.setObjectiveN(self.d
        # a_complexity, index=1, priority=8)
        #self.model.setObjectiveN(-self.memory_complexity, index=2, priority=5)
        self.model.setObjectiveN(self.state_test_up+self.state_test_down, index = 3, priority=2)
    
    #Attack build
    def attack(self):
        self.value_variables_initialisation()
        self.difference_variables_initialisation()
        
        self.structure()

        self.upper_part()

        self.lower_part()

        
        #global constraints
        #The total probability of the attack cannot exceed the size of the block
        self.model.addConstr(self.word_size*self.probabilist_annulation_down+self.word_size*self.probabilist_annulation_up+self.distinguisher_probability <= self.block_size)
        
        #Not optimal to repeat the attack more than the number of time needed to verify the probability of the trail
        self.model.addConstr(self.distinguisher_probability + self.word_size*self.common_fix >= self.block_size+1)
        
        #self.model.addConstr(self.state_test_up==0, name="at least one state test up")
        #self.model.addConstr(self.state_test_down==0, name="at least one state test down")
        #self.model.addConstr(self.probabilist_annulation_down==0, name="at least one pb key down")
        #self.model.addConstr(self.probabilist_annulation_up==0, name="at least one pb key up")
        #self.model.addConstr(self.matching_differences_quantity>=2, name="at least 2 matching differences")
        self.objective()

        self.optimize_the_model()
    
    #Display
    def get_results(self):
        if self.optimized:
            print("----- RESULTS -----")
            print('number of rounds :', self.total_rounds)
            print('\n')
            print("UPPER PART :")
            print("Fix up :", self.fix_up.X)
            print("State tested up :", self.state_test_up.X)
            print("Probabilist annulation up :", self.probabilist_annulation_up.X)
            print("Key bits guessed up :", self.upper_key_guess.X)
            print("Complexity up :", self.time_complexity_up.X)
            print("Total complexity up :", self.time_complexity_up.X*self.word_size + self.distinguisher_probability)
            print("\n")
            print("LOWER PART :")
            print("Fix down :", self.fix_down.X)
            print("State tested down :", self.state_test_down.X)
            print("Probabilist annulation down :", self.probabilist_annulation_down.X)
            print("Key bits guessed down :", self.lower_key_guess.X)
            if self.trunc_diff :
                print('delta_in - delta_out :', self.distinguisher_output_quantity - self.distinguisher_input_quantity)
            print("Complexity down :", self.time_complexity_down.X)
            print("Total complexity down :", self.time_complexity_down.X*self.word_size + self.distinguisher_probability)
            print("\n")
            print("MATHC PART :")
            print("Matching differences :", self.matching_differences_quantity.X)
            print("attack_key_space :", self.key_space_size)
            if self.trunc_diff :
                print("truncated end :", self.distinguisher_output_quantity)
            print("Complexity match :", self.time_complexity_match.X)
            print("Total complexity match :", self.time_complexity_match.X*self.word_size + self.distinguisher_probability)
            print("\n")
            print("STRUCTURE Parameters")
            print("Common fix :", self.common_fix.X)
            print("max Fin Fout :", self.max_fix_up_fix_down.X )
            print('\n')
            print('Information on the key :')
            print("total_key_quantity_guess :", self.key_guess_quantity.X)
            print("total_key_quantity_guess :", self.common_key_guess.X)

            print("\n")
            print("OVERALL :")
            print("Time complexity :", self.word_size*self.time_complexity.X+self.distinguisher_probability)
            print("Memory complexity :", self.word_size*self.memory_complexity.X)
            print("Data complexity :", self.word_size*self.data_complexity.X)
            print("Attaque Valide :", self.time_complexity.X*self.word_size + self.distinguisher_probability <= self.key_space_size)
            print("\n")
        else :
            print('The Model at no been optimize yet')
    
    def display_console(self):
        for round_index in range(self.total_rounds):
            if round_index >self.upper_part_last_round and round_index < self.lower_part_first_round :
                pass
            else :
                print("ROUND ", round_index)
                key_line = "KEY : \n"
                for row in range(self.block_row_size):
                    key_line += "|"
                    for column in range(self.block_column_size):
                        if self.upper_subkey[round_index, row, column].X == 0 and self.lower_subkey[round_index, row, column].X == 0:
                            key_line += "\033[90m ■ \033[0m"
                        elif self.upper_subkey[round_index, row, column].X == 1 and self.lower_subkey[round_index, row, column].X == 0:
                            key_line += "\033[91m ■ \033[0m"
                        elif self.upper_subkey[round_index, row, column].X == 0 and self.lower_subkey[round_index, row, column].X == 1:
                            key_line += "\033[94m ■ \033[0m"
                        elif self.upper_subkey[round_index, row, column].X == 1 and self.lower_subkey[round_index, row, column].X == 1:
                            key_line += "\033[95m ■ \033[0m"
                        else :
                            key_line += " ? "
                    key_line += "|\n"
                print(key_line)
                print('\n')

                if self.block_column_size <= 12:
                    for row in range(self.block_row_size):
                        line = ""
                        for state_index in range(self.state_number):
                            line += "|"
                            for column in range(self.block_column_size):
                                if (self.values[0, 0, round_index, state_index, row, column, 1].X == 1 or self.values[0, 1, round_index, state_index, row, column, 1].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 1].X == 1 or self.values[1, 1, round_index, state_index, row, column, 1].X == 1):
                                    line += "\033[95m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 0].X == 1 and self.values[0, 1, round_index, state_index, row, column, 0].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 0].X == 1 and self.values[1, 1, round_index, state_index, row, column, 0].X == 1):
                                    line += "\033[90m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 1].X == 1 or self.values[0, 1, round_index, state_index, row, column, 1].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 0].X == 1 or self.values[1, 1, round_index, state_index, row, column, 0].X == 1):
                                    line += "\033[91m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 2].X == 1 or self.values[0, 1, round_index, state_index, row, column, 2].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 0].X == 1 or self.values[1, 1, round_index, state_index, row, column, 0].X == 1):
                                    line += "\033[91m F \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 0].X == 1 or self.values[0, 1, round_index, state_index, row, column, 0].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 1].X == 1 or self.values[1, 1, round_index, state_index, row, column, 1].X == 1):
                                    line += "\033[94m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 0].X == 1 or self.values[0, 1, round_index, state_index, row, column, 0].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 2].X == 1 or self.values[1, 1, round_index, state_index, row, column, 2].X == 1):
                                    line += "\033[94m F \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 2].X == 1 or self.values[0, 1, round_index, state_index, row, column, 2].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 2].X == 1 or self.values[1, 1, round_index, state_index, row, column, 2].X == 1):
                                    line += "\033[95m F \033[0m"
                                else :
                                    line += " ? "
                                    print(self.values[0, 0, round_index, state_index, row, column, 2])
                                    print(self.values[1, 1, round_index, state_index, row, column, 1])
                            line += "|"
                            if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                                line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                            elif row == self.block_row_size//2:
                                line += "->"
                            elif row == self.block_row_size//2 - 1 and state_index == self.state_number -1:
                                line += "NR"
                            else :
                                line += "  "
                        line += "             "
                        for state_index in range(self.state_number):
                            line += "|"
                            for column in range(self.block_column_size):
                                if self.differences[0, 1, round_index, state_index, row, column, 1].X == 0 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 0:
                                    line+="\033[90m ■ \033[0m"
                                elif self.differences[0, 1, round_index, state_index, row, column, 1].X == 1 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 0:
                                    line+="\033[91m ■ \033[0m"
                                elif self.differences[0, 1, round_index, state_index, row, column, 1].X == 0 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 1:
                                    line+="\033[94m ■ \033[0m"
                                elif self.differences[0, 1, round_index, state_index, row, column, 1].X == 1 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 1:
                                    line+="\033[95m ■ \033[0m"
                            line += "|"
                            if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                                line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                            elif row == self.block_row_size//2:
                                line += "->"
                            elif row == self.block_row_size//2 - 1 and state_index == self.state_number -1:
                                line += "NR"
                            else :
                                line += "  "
                        print(line)
                else :
                    for state_index in range(self.state_number):
                        for row in range(self.block_row_size):
                            line = ""
                            line += "|"
                            for column in range(self.block_column_size):
                                if (self.values[0, 0, round_index, state_index, row, column, 1].X == 1 or self.values[0, 1, round_index, state_index, row, column, 1].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 1].X == 1 or self.values[1, 1, round_index, state_index, row, column, 1].X == 1):
                                    line += "\033[95m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 0].X == 1 and self.values[0, 1, round_index, state_index, row, column, 0].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 0].X == 1 and self.values[1, 1, round_index, state_index, row, column, 0].X == 1):
                                    line += "\033[90m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 1].X == 1 or self.values[0, 1, round_index, state_index, row, column, 1].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 0].X == 1 or self.values[1, 1, round_index, state_index, row, column, 0].X == 1):
                                    line += "\033[91m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 2].X == 1 or self.values[0, 1, round_index, state_index, row, column, 2].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 0].X == 1 or self.values[1, 1, round_index, state_index, row, column, 0].X == 1):
                                    line += "\033[91m F \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 0].X == 1 or self.values[0, 1, round_index, state_index, row, column, 0].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 1].X == 1 or self.values[1, 1, round_index, state_index, row, column, 1].X == 1):
                                    line += "\033[94m ■ \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 0].X == 1 or self.values[0, 1, round_index, state_index, row, column, 0].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 2].X == 1 or self.values[1, 1, round_index, state_index, row, column, 2].X == 1):
                                    line += "\033[94m F \033[0m"
                                elif (self.values[0, 0, round_index, state_index, row, column, 2].X == 1 or self.values[0, 1, round_index, state_index, row, column, 2].X == 1) and (self.values[1, 0, round_index, state_index, row, column, 2].X == 1 or self.values[1, 1, round_index, state_index, row, column, 2].X == 1):
                                    line += "\033[95m F \033[0m"
                                else :
                                    line += " ? "
                                    print(self.values[0, 0, round_index, state_index, row, column, 2])
                                    print(self.values[1, 1, round_index, state_index, row, column, 1])
                            line += "|"
                            if row == self.block_row_size//2 and state_index != self.state_number-1:
                                line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}->"
                            else :
                                line += "    "
                            line += "             "
                            line += "|"
                            for column in range(self.block_column_size):
                                if self.differences[0, 1, round_index, state_index, row, column, 1].X == 0 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 0:
                                    line+="\033[90m ■ \033[0m"
                                elif self.differences[0, 1, round_index, state_index, row, column, 1].X == 1 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 0:
                                    line+="\033[91m ■ \033[0m"
                                elif self.differences[0, 1, round_index, state_index, row, column, 1].X == 0 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 1:
                                    line+="\033[94m ■ \033[0m"
                                elif self.differences[0, 1, round_index, state_index, row, column, 1].X == 1 and self.differences[1, 0, round_index, state_index, row, column, 1].X == 1:
                                    line+="\033[95m ■ \033[0m"
                            line += "|"
                            if row == self.block_row_size//2 and state_index != self.state_number-1:
                                line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}->"
                            else :
                                line += "    "
                            line += ""
                            print(line)
                        print("")

                if round_index == self.structure_last_round_index:
                    print("------------------------------------------------------------- FIN STRUCTURE -------------------------------------------------------------")
                if round_index == self.upper_part_last_round:
                    print(f"------------------------------------------------------------- DISTINGUISHER - {self.distinguisher_rounds} -------------------------------------------------------------")

                # print("\n lower forward propagation")
                # for row in range(self.block_row_size):
                #     line = ""
                #     for state_index in range(self.state_number):
                #         line += "|"
                #         for column in range(self.block_column_size):
                #             if (self.values[1, 0, round_index, state_index, row, column, 0].X == 1):
                #                 line += "\033[90m ■ \033[0m"
                #             elif (self.values[1, 0, round_index, state_index, row, column, 1].X == 1):
                #                 line += "\033[94m ■ \033[0m"
                #             elif (self.values[1, 0, round_index, state_index, row, column, 2].X == 1):
                #                 line += "\033[94m F \033[0m"
                #             else :
                #                 line += " ? "
                #                 print(self.values[0, 0, round_index, state_index, row, column, 2])
                #                 print(self.values[1, 1, round_index, state_index, row, column, 1])
                #         line += "|"
                #         if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #             line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #         elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #             line += "->"
                #         else :
                #             line += "  "
                #     line += "             "
                #     if round_index >= self.structure_first_round_index and round_index <=self.lower_part_last_round:
                #         for state_index in range(self.state_number):
                #             line += "|"
                #             for column in range(self.block_column_size):
                #                 if (self.differences[1, 0, round_index, state_index, row, column, 0].X == 1):
                #                     line += "\033[90m ■ \033[0m"
                #                 elif (self.differences[1, 0, round_index, state_index, row, column, 1].X == 1):
                #                     line += "\033[94m ■ \033[0m"
                #             line += "|"
                #             if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #                 line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #             elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #                 line += "->"
                #             else :
                #                 line += "  "
                    
                #     line += " "
                #     print(line)
                #     line=""
                # print("\n lower backward propagation")
                # for row in range(self.block_row_size):
                #     line = ""
                #     for state_index in range(self.state_number):
                #         line += "|"
                #         for column in range(self.block_column_size):
                #             if (self.values[1, 1, round_index, state_index, row, column, 0].X == 1):
                #                 line += "\033[90m ■ \033[0m"
                #             elif (self.values[1, 1, round_index, state_index, row, column, 1].X == 1):
                #                 line += "\033[94m ■ \033[0m"
                #             elif (self.values[1, 1, round_index, state_index, row, column, 2].X == 1):
                #                 line += "\033[94m F \033[0m"
                #         line += "|"
                #         if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #             line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #         elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #             line += "->"
                #         else :
                #             line += "  "
                #     line += "             "
                #     if round_index >= self.structure_first_round_index and round_index <=self.lower_part_last_round:
                #         for state_index in range(self.state_number):
                #             line += "|"
                #             for column in range(self.block_column_size):
                #                 if (self.differences[1, 1, round_index, state_index, row, column, 0].X == 1):
                #                     line += "\033[90m ■ \033[0m"
                #                 elif (self.differences[1, 1, round_index, state_index, row, column, 1].X == 1):
                #                     line += "\033[94m ■ \033[0m"
                #             line += "|"
                #             if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #                 line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #             elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #                 line += "->"
                #             else :
                #                 line += "  "
                #     line += " "
                #     print(line)
                #     line=""
                # print("\n upper backward propagation")
                # for row in range(self.block_row_size):
                #     line = ""
                #     for state_index in range(self.state_number):
                #         line += "|"
                #         for column in range(self.block_column_size):
                #             if (self.values[0, 1, round_index, state_index, row, column, 0].X == 1):
                #                 line += "\033[90m ■ \033[0m"
                #             elif (self.values[0, 1, round_index, state_index, row, column, 1].X == 1):
                #                 line += "\033[91m ■ \033[0m"
                #             elif (self.values[0, 1, round_index, state_index, row, column, 2].X == 1):
                #                 line += "\033[91m F \033[0m"
                #         line += "|"
                #         if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #             line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #         elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #             line += "->"
                #         else :
                #             line += "  "
                #     line += "             "
                #     if round_index >= self.structure_first_round_index and round_index <=self.lower_part_last_round:
                #         for state_index in range(self.state_number):
                #             line += "|"
                #             for column in range(self.block_column_size):
                #                 if (self.differences[0, 1, round_index, state_index, row, column, 0].X == 1):
                #                     line += "\033[90m ■ \033[0m"
                #                 elif (self.differences[0, 1, round_index, state_index, row, column, 1].X == 1):
                #                     line += "\033[91m ■ \033[0m"
                #             line += "|"
                #             if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #                 line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #             elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #                 line += "->"
                #             else :
                #                 line += "  "
                #     print(line)
                #     line=""
                # print("\n upper direct propagation :")
                # for row in range(self.block_row_size):
                #     line = ""
                #     for state_index in range(self.state_number):
                #         line += "|"
                #         for column in range(self.block_column_size):
                #             if (self.values[0, 0, round_index, state_index, row, column, 0].X == 1):
                #                 line += "\033[90m ■ \033[0m"
                #             elif (self.values[0, 0, round_index, state_index, row, column, 1].X == 1):
                #                 line += "\033[91m ■ \033[0m"
                #             elif (self.values[0, 0, round_index, state_index, row, column, 2].X == 1):
                #                 line += "\033[91m F \033[0m"
                #         line += "|"
                #         if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #             line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #         elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #             line += "->"
                #         else :
                #             line += "  "
                #     line += "             "
                #     if round_index >= self.structure_first_round_index and round_index <=self.lower_part_last_round:
                #         for state_index in range(self.state_number):
                #             line += "|"
                #             for column in range(self.block_column_size):
                #                 if (self.differences[0, 0, round_index, state_index, row, column, 0].X == 1):
                #                     line += "\033[90m ■ \033[0m"
                #                 elif (self.differences[0, 0, round_index, state_index, row, column, 1].X == 1):
                #                     line += "\033[91m ■ \033[0m"
                #             line += "|"
                #             if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                #                 line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                #             elif row == self.block_row_size//2 and state_index != self.state_number -1:
                #                 line += "->"
                #             else :
                #                 line += "  "
                #     print(line)
                #     line=""
                
                if 'MC' in self.operation_order:
                    line=""
                    print('Fix values through MC')
                    for column in range(self.block_column_size):
                        for vector in self.column_range[0][round_index%len(self.matrixes[0])]:
                                vector = tuple(vector)
                                if self.XOR_in_mc_values[(0, 0, round_index, column)+vector+(2,)].X == 1 :
                                    line += f"\033[91m c:{column} / {vector} : F\033[0m \n"
                                if self.XOR_in_mc_values[(1, 0, round_index, column)+vector+(2,)].X == 1 :
                                    line += f"\033[94m c:{column} / {tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0)))} : F\033[0m \n"
                    print(line)
                    line=""
                    print('Fix differences through MC')
                    for column in range(self.block_column_size):
                        for vector in self.column_range[0][round_index%len(self.matrixes[0])]:
                                vector = tuple(vector)
                                if self.XOR_in_mc_differences[(0, 0, round_index, column)+vector+(2,)].X == 1:
                                    line += f"\033[91m c:{column} / {tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0)))} : F\033[0m \n"
                                if self.XOR_in_mc_differences[(1, 0, round_index, column)+vector+(2,)].X == 1 :
                                    line += f"\033[94m c:{column} / {vector} : F\033[0m \n"
                    print(line)
                    line=""
                line=""
                print("\n")
                if 'MR' in self.operation_order:
                    line=""
                    print('Fix values through MC')
                    for row in range(self.block_row_size):
                        for vector in self.row_range[0][round_index%len(self.matrixes[0])]:
                                vector = tuple(vector)
                                if self.XOR_in_mr_values[(0, 0, round_index, row)+vector+(2,)].X == 1 :
                                    line += f"\033[91m c:{column} / {vector} : F\033[0m \n"
                                if self.XOR_in_mr_values[(1, 0, round_index, row)+vector+(2,)].X == 1 :
                                    line += f"\033[94m c:{column} / {tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0)))} : F\033[0m \n"
                    print(line)
                    line=""
                    print('Fix differences through MR')
                    for row in range(self.block_row_size):
                        for vector in self.row_range[0][round_index%len(self.matrixes[0])]:
                                vector = tuple(vector)
                                if self.XOR_in_mr_differences[(0, 0, round_index, row)+vector+(2,)].X == 1:
                                    line += f"\033[91m c:{row} / {tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0)))} : F\033[0m \n"
                                if self.XOR_in_mr_differences[(1, 0, round_index, row)+vector+(2,)].X == 1 :
                                    line += f"\033[94m c:{row} / {vector} : F\033[0m \n"
                    print(line)
                    line=""
                    line+="\n"
                line=""
                print("\n")
        print("END OF THE ATTACK")