from Model import Common_bricks_for_attacks
import gurobipy as gp
import numpy as np
import math

class attack_model(Common_bricks_for_attacks.MILP_bricks):
    def __init__(self, cipher_parameters, licence_parameters, attack_parameters, model):
        super().__init__(cipher_parameters, licence_parameters, model)
        #Attack parameters
        self.structure_rounds = attack_parameters.get('structure_rounds', 4)
        self.structure_position = attack_parameters.get('structure_position', 'upper')

        self.upper_rounds = attack_parameters.get('upper_rounds', 2)

        self.distinguisher_probability = attack_parameters.get('distinguisher_probability', 32)
        self.distinguisher_rounds = attack_parameters.get('distinguisher_rounds', 2)
        self.distinguisher_input = attack_parameters.get('distinguisher_inputs', [[2, 1], [3, 2]])
        self.distinguisher_output = attack_parameters.get('distinguisher_outputs', [[2, 1], [3, 2]])
        self.distinguisher_input_quantity = len(self.distinguisher_input)
        self.distinguisher_output_quantity = len(self.distinguisher_output)

        self.lower_rounds = attack_parameters.get('lower_rounds', 2)

        if self.structure_position == 'upper':
            # Layout: [Structure] → [Upper] → [Distinguisher] → [Lower]
            self.structure_first_round_index = 0
            self.structure_last_round_index = self.structure_rounds - 1
            self.upper_part_first_round = self.structure_rounds
            self.upper_part_last_round = self.structure_rounds + self.upper_rounds - 1
            self.lower_part_first_round = self.upper_part_last_round + self.distinguisher_rounds
            self.lower_part_last_round = self.lower_part_first_round + self.lower_rounds
        else:  # 'lower'
            # Layout: [Upper] → [Distinguisher] → [Lower] → [Structure]
            self.upper_part_first_round = 0
            self.upper_part_last_round = self.upper_rounds - 1
            self.lower_part_first_round = self.upper_part_last_round + self.distinguisher_rounds
            self.lower_part_last_round = self.lower_part_first_round + self.lower_rounds
            self.structure_first_round_index = self.lower_part_last_round + 1
            self.structure_last_round_index = self.lower_part_last_round + self.structure_rounds

        self.key_size = cipher_parameters.get('key_size', self.block_size*2)
        self.key_space_size = attack_parameters.get('key_space_size', self.key_size)

        self.total_rounds = self.structure_rounds + self.upper_rounds + self.lower_rounds + self.distinguisher_rounds
        self.optimal_complexity = attack_parameters.get('optimal_complexity', False)

        self.trunc_diff = attack_parameters.get('truncated_differential', False)

        self.filter_state_test = attack_parameters.get('filter_state_test', False)

        self.state_test_use = attack_parameters.get('state_test_use', True)

        self.use_upper_bound = attack_parameters.get('use_upper_bound', False)
        self.known_upper_bound = attack_parameters.get('known_upper_bound', None)

        self.specific_solution_search = attack_parameters.get('specific_solution_search', False)
        self.solution_value = attack_parameters.get('solution_value', None)

        self.filter_extra_key_guess = attack_parameters.get('filter_extra_key_guess', False)

        self.specific_key_filtering = attack_parameters.get('specific_key_filtering', False)

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
        if 'MC' in self.operation_order_up or 'MC' in self.operation_order_down:
            self.XOR_in_mc_values = self.model.addVars((((part, sens, round_index, column) + (xor_combination) + (value,))
                                                        for part in range(2)
                                                        for sens in range(2)
                                                        for round_index in range(self.total_rounds)
                                                        for column in range(self.block_column_size)
                                                        for xor_combination in self.column_range[sens][round_index%len(self.matrixes[sens])]
                                                        for value in range(3)), vtype=gp.GRB.BINARY, name="fix_in_mc")

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

        if 'MR' in self.operation_order_up or 'MR' in self.operation_order_down:
            self.XOR_in_mr_values = self.model.addVars((((part, sens, round_index, row) + (xor_combination) + (value,))
                                                        for part in range(2)
                                                        for sens in range(2)
                                                        for round_index in range(self.total_rounds)
                                                        for row in range(self.block_row_size)
                                                        for xor_combination in self.row_range[sens][round_index%len(self.matrixes[sens])]
                                                        for value in range(3)), vtype=gp.GRB.BINARY, name="fix_in_mr")

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
        # differences[..., 0] = null (x=0), differences[..., 1] = active (x=1)
        # x=2 (cancelled through MC/MR) is encoded in XOR_in_mc_differences[..., 2]
        self.differences = self.model.addVars(range(2), range(2),
                                            range(self.total_rounds),
                                            range(self.state_number),
                                            range(self.block_row_size),
                                            range(self.block_column_size),
                                            range(2), #valeur{0=null, 1=active}
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

        # diff_known[part, sens, r, s, row, col] = y ∈ {0,1}
        # y=0: value of this difference does not need to be known
        # y=1: value of this difference must be known (value cannot be unknown)
        self.diff_known = self.model.addVars(range(2), range(2),
                                            range(self.total_rounds),
                                            range(self.state_number),
                                            range(self.block_row_size),
                                            range(self.block_column_size),
                                            vtype=gp.GRB.BINARY,
                                            name='diff_known')
        
        #MC and MR possible XOR
        if 'MC' in self.operation_order_up or 'MC' in self.operation_order_down:
            self.XOR_in_mc_differences = self.model.addVars((((part, sens, round_index, column) + (xor_combination) + (value,))
                                                        for part in range(2)
                                                        for sens in range(2)
                                                        for round_index in range(self.total_rounds)
                                                        for column in range(self.block_column_size)
                                                        for xor_combination in self.column_range[sens][round_index%len(self.matrixes[sens])]
                                                        for value in range(3)), vtype=gp.GRB.BINARY, name="fix_in_mc_diff")

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

        if 'MR' in self.operation_order_up or 'MR' in self.operation_order_down:
            self.XOR_in_mr_differences = self.model.addVars((((part, sens, round_index, row) + (xor_combination) + (value,))
                                                        for part in range(2)
                                                        for sens in range(2)
                                                        for round_index in range(self.total_rounds)
                                                        for row in range(self.block_row_size)
                                                        for xor_combination in self.row_range[sens][round_index%len(self.matrixes[sens])]
                                                        for value in range(3)), vtype=gp.GRB.BINARY, name="fix_in_mr_diff")

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
        # With no structure rounds, all structure-derived quantities are 0.
        # The required variables (used in complexities()) are still created but fixed to 0.
        if self.structure_rounds == 0:
            self.fix_up                    = self.model.addVar(lb=0, ub=0, vtype=gp.GRB.INTEGER, name="fix_up")
            self.active_start_up           = self.model.addVar(lb=0, ub=0, vtype=gp.GRB.INTEGER, name="active_start_up")
            self.fix_down                  = self.model.addVar(lb=0, ub=0, vtype=gp.GRB.INTEGER, name="fix_down")
            self.active_start_down         = self.model.addVar(lb=0, ub=0, vtype=gp.GRB.INTEGER, name="active_start_down")
            self.common_fix_count          = self.model.addVar(lb=0, ub=0, vtype=gp.GRB.INTEGER, name="fix_common")
            self.max_fix_up_fix_down       = self.model.addVar(lb=0, ub=0, vtype=gp.GRB.INTEGER, name="max_fix_up_fix_down")
            self.matching_differences_quantity = self.model.addVar(lb=0, ub=0, vtype=gp.GRB.INTEGER, name="match quantity")
            return

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
        if 'MC' in self.operation_order_up:
            fix_elements += gp.quicksum(self.XOR_in_mc_values[(0, 0, round_index, column)+(column_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for column in range(self.block_column_size)
                                                            for column_xor in self.column_range[0][round_index%len(self.matrixes[0])])
        if 'MR' in self.operation_order_up:
            fix_elements += gp.quicksum(self.XOR_in_mr_values[(0, 0, round_index, row)+(row_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for row in range(self.block_row_size)
                                                            for row_xor in self.row_range[0][round_index%len(self.matrixes[0])])

        self.model.addConstr(self.fix_up == fix_elements, name='fix_up_count')

        self.model.addConstr(self.active_start_up == (self.block_size//self.word_size
                                                    - gp.quicksum(self.values[0, 0, self.structure_last_round_index, self.operation_order_up.index('AK')+1, row, column , 0]
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
        if 'MC' in self.operation_order_down:
            fix_elements += gp.quicksum(self.XOR_in_mc_values[(1, 1, round_index, column)+(column_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for column in range(self.block_column_size)
                                                            for column_xor in self.column_range[1][round_index%len(self.matrixes[1])])
        if 'MR' in self.operation_order_down:
            fix_elements += gp.quicksum(self.XOR_in_mr_values[(1, 1, round_index, row)+(row_xor)+(2,)]
                                                            for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                            for row in range(self.block_row_size)
                                                            for row_xor in self.row_range[1][round_index%len(self.matrixes[1])])

        self.model.addConstr(self.fix_down == fix_elements, name='fix_down_count')

        self.model.addConstr(self.active_start_down == self.block_column_size*self.block_row_size
                                                     - gp.quicksum(self.values[1, 1, self.structure_first_round_index, self.operation_order_down.index('AK'), row, column , 0]
                                                                  for row in range(self.block_row_size) 
                                                                  for column in range(self.block_column_size)), 
                            name='active_last_state_structure')
        
        self.model.addConstr(self.active_start_down==self.fix_down, name='each_down_fix_leads_to_a_known_value_in_first_state')
        
        
        #Propagation initial Contrainst
        self.model.addConstrs((self.values[0, 0, self.structure_first_round_index, self.operation_order_up.index('AK'), row, column, 1] == 0
                            for row in range(self.block_row_size)
                            for column in range(self.block_column_size)),
                            name='no_initial_known_value_upper_structure')

        self.model.addConstrs((self.values[1, 0, self.structure_first_round_index, self.operation_order_down.index('AK'), row, column, 1] == 0
                            for row in range(self.block_row_size)
                            for column in range(self.block_column_size)),
                            name='no_initial_known_value_lower_structure')

        self.model.addConstrs((self.values[1, 1, self.structure_last_round_index, self.operation_order_down.index('AK')+1, row, column, 1] ==0
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name='no_initial_known_value_lower_structure')

        self.model.addConstrs((self.values[0, 1, self.structure_last_round_index, self.operation_order_up.index('AK')+1, row, column, 1] ==0
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name='no_initial_known_value_upper_structure')
        
        # Common fix compting constraints constraints     
        # Consider a common fix if the nibble is fix in the upper and lower part
        # Here we use McCormik constraints rather than multiplication to keep a linear model and not MIQCP
        # Counting the fix     
        self.common_fix_count = self.model.addVar(vtype= gp.GRB.INTEGER, name = "fix_common")

        self.common_fix = self.model.addVars(range(self.structure_first_round_index, self.structure_last_round_index+1),
                                            range(self.state_number),
                                            range(self.block_row_size),
                                            range(self.block_column_size),
                                            vtype=gp.GRB.BINARY, name='common_fix')
        
        self.model.addConstrs((self.common_fix[round_index, state_index, row, column] <= self.values[0, 0, round_index, state_index, row, column, 2]
                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                for state_index in range(self.state_number)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name='common_fix_upper_part_McCormik_constraints')
        
        self.model.addConstrs((self.common_fix[round_index, state_index, row, column] <= self.values[1, 1, round_index, state_index, row, column, 2]
                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                for state_index in range(self.state_number)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name='common_fix_lower_part_McCormik_constraints') 
        
        self.model.addConstrs((self.common_fix[round_index, state_index, row, column] >= self.values[0, 0, round_index, state_index, row, column, 2] + self.values[1, 1, round_index, state_index, row, column, 2] - 1
                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                for state_index in range(self.state_number)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name='common_fix_common_part_McCormik_constraints')    
        
        common_fix_count_elements = gp.quicksum(self.common_fix[round_index, state_index, row, column]
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                                for state_index in range(self.state_number) 
                                                                for row in range(self.block_row_size) 
                                                                for column in range(self.block_column_size))
        
    

        if 'MC' in self.operation_order_up or 'MC' in self.operation_order_down:
            self.common_fix_in_MC = self.model.addVars((((round_index, column) + (xor_combination))
                                                        for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                        for column in range(self.block_column_size)
                                                        for xor_combination in self.column_range[0][round_index%len(self.matrixes[0])]), vtype=gp.GRB.BINARY, name="common_fix_in_mc")
            
            self.model.addConstrs((self.common_fix_in_MC[(round_index, column) + xor_combination] <= self.XOR_in_mc_values[(0, 0, round_index, column) + xor_combination + (2,)]
                                    for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                    for column in range(self.block_column_size)
                                    for xor_combination in self.column_range[0][round_index%len(self.matrixes[0])]),
                                    name='common_fix_in_mc_upper_part_constraints')
            
            self.model.addConstrs((self.common_fix_in_MC[(round_index, column) + xor_combination] <= self.XOR_in_mc_values[(1, 1, round_index, column) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)]
                                    for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                    for column in range(self.block_column_size)
                                    for xor_combination in self.column_range[0][round_index%len(self.matrixes[0])]),
                                    name='common_fix_in_mc_lower_part_constraints')
            
            self.model.addConstrs((self.common_fix_in_MC[(round_index, column) + xor_combination] >= self.XOR_in_mc_values[(0, 0, round_index, column) + xor_combination + (2,)] + self.XOR_in_mc_values[(1, 1, round_index, column) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)] - 1
                                    for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                    for column in range(self.block_column_size)
                                    for xor_combination in self.column_range[0][round_index%len(self.matrixes[0])]),
                                    name='common_fix_in_mc_common_part_constraints')
            
            common_fix_count_elements += gp.quicksum(self.common_fix_in_MC[(round_index, column) + xor_combination]
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                                for column in range(self.block_column_size)
                                                                for xor_combination in self.column_range[0][round_index%len(self.matrixes[0])])
        
        if 'MR' in self.operation_order_up or 'MR' in self.operation_order_down:
            self.common_fix_in_MR = self.model.addVars((((round_index, row) + (xor_combination))
                                                        for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                        for row in range(self.block_row_size)
                                                        for xor_combination in self.row_range[0][round_index%len(self.matrixes[0])]), vtype=gp.GRB.BINARY, name="common_fix_in_mr")
            
            self.model.addConstrs((self.common_fix_in_MR[(round_index, row) + xor_combination] <= self.XOR_in_mr_values[(0, 0, round_index, row) + xor_combination + (2,)]
                                    for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                    for row in range(self.block_row_size)
                                    for xor_combination in self.row_range[0][round_index%len(self.matrixes[0])]),
                                    name='common_fix_in_mr_upper_part_constraints')
            
            self.model.addConstrs((self.common_fix_in_MR[(round_index, row) + xor_combination] <= self.XOR_in_mr_values[(1, 1, round_index, row) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)]
                                    for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                    for row in range(self.block_row_size)
                                    for xor_combination in self.row_range[0][round_index%len(self.matrixes[0])]),
                                    name='common_fix_in_mr_lower_part_constraints')
            
            self.model.addConstrs((self.common_fix_in_MR[(round_index, row) + xor_combination] >= self.XOR_in_mr_values[(0, 0, round_index, row) + xor_combination + (2,)] + self.XOR_in_mr_values[(1, 1, round_index, row) + tuple(map(int,np.bitwise_xor.reduce(np.array(xor_combination)[:,None]*np.array(self.matrixes[1][round_index%len(self.matrixes[1])]), axis=0))) + (2,)] - 1
                                    for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                    for row in range(self.block_row_size)
                                    for xor_combination in self.row_range[0][round_index%len(self.matrixes[0])]),
                                    name='common_fix_in_mr_common_part_constraints')    
            
            common_fix_count_elements += gp.quicksum(self.common_fix_in_MR[(round_index, row) + xor_combination]
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1) 
                                                                for row in range(self.block_row_size)
                                                                for xor_combination in self.row_range[0][round_index%len(self.matrixes[0])])
        
        self.model.addConstr(self.common_fix_count == common_fix_count_elements, name='common_fix_count')
        
        self.model.addConstr(self.fix_down+self.fix_up-self.common_fix_count<=self.block_size//self.word_size, name='cannot_fix_more_than_the_block')

        self.max_fix_up_fix_down = self.model.addVar(vtype= gp.GRB.INTEGER, name="max_fix_up_fix_down")
        # Linearisation of max(fix_up, fix_down) with a binary variable z:
        # max >= fix_up, max >= fix_down (lower bounds)
        # max <= fix_up  + M*(1-z), max <= fix_down + M*z (upper bound, tight on the argmax side)
        M_fix = self.block_size // self.word_size
        z_max_fix = self.model.addVar(vtype=gp.GRB.BINARY, name="z_max_fix_up_fix_down")
        self.model.addConstr(self.max_fix_up_fix_down >= self.fix_up,   name="max_fix_lb_up")
        self.model.addConstr(self.max_fix_up_fix_down >= self.fix_down, name="max_fix_lb_down")
        self.model.addConstr(self.max_fix_up_fix_down <= self.fix_up   + M_fix * (1 - z_max_fix), name="max_fix_ub_up")
        self.model.addConstr(self.max_fix_up_fix_down <= self.fix_down + M_fix * z_max_fix,       name="max_fix_ub_down")

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
        # y=0 for unused difference directions
        self.model.addConstrs((self.diff_known[0, 0, round_index, part, row, column] == 0
                               for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                               for part in range(self.state_number)
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="diff_known_zero_upper_forward_structure")
        self.model.addConstrs((self.diff_known[1, 1, round_index, part, row, column] == 0
                               for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                               for part in range(self.state_number)
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="diff_known_zero_lower_backward_structure")

        #first state is completly known by the lower part
        self.model.addConstrs((self.differences[1, 0, self.structure_first_round_index, self.operation_order_down.index('AK'), row, column, 1] == 1
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="lower part know all the differences at the begining at the structure")
        # y=1 at structure boundary: all active differences must be known
        self.model.addConstrs((self.diff_known[1, 0, self.structure_first_round_index, self.operation_order_down.index('AK'), row, column] == 1
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="diff_known_lower_start_structure")

        #Last state is completely known by the upper part
        self.model.addConstrs((self.differences[0, 1, self.structure_last_round_index, self.operation_order_up.index('AK')+1, row, column, 1] == 1
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="upper part know all the differences at the end at the structure")
        # y=1 at structure boundary: all active differences must be known
        self.model.addConstrs((self.diff_known[0, 1, self.structure_last_round_index, self.operation_order_up.index('AK')+1, row, column] == 1
                               for row in range(self.block_row_size)
                               for column in range(self.block_column_size)), name="diff_known_upper_end_structure")

        self.forward_differences_propagation_in_structure(1, self.structure_first_round_index, self.structure_last_round_index)
        self.backward_differences_propagation_in_structure(0, self.structure_first_round_index, self.structure_last_round_index)

        max_max = self.block_column_size*self.block_row_size
        self.matching_differences_count = self.model.addVars(range(self.structure_rounds-1), lb=0, ub=max_max, vtype= gp.GRB.INTEGER, name = "match_differences per round")
        self.matching_differences_quantity = self.model.addVar(lb=0, ub=max_max, vtype=gp.GRB.INTEGER, name="match quantity")
        
        #counting the matching diffrences
        #Here we use McCormik constraints rather than multiplication to keep a linear model and not MIQCP

        #First we count the differences we known in the state before and after the Sbox
        self.matching_differences = self.model.addVars(range(self.structure_rounds-1), range(2), range(self.block_row_size), range(self.block_column_size), vtype= gp.GRB.BINARY, name = "match_differences per round")
        
        self.model.addConstrs((self.matching_differences[round_index, i, row, column] <= self.differences[0, 1, round_index+self.structure_first_round_index, self.operation_order_up.index('SB')+i, row, column, 1]
                                for round_index in range(self.structure_rounds-1)
                                for i in range(2)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name="difference_is_known by_upper_part")

        self.model.addConstrs((self.matching_differences[round_index, i, row, column] <= self.differences[1, 0, round_index+self.structure_first_round_index, self.operation_order_down.index('SB')+i, row, column, 1]
                                for round_index in range(self.structure_rounds-1)
                                for i in range(2)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name="difference_is_known by_lower_part")

        self.model.addConstrs((self.matching_differences[round_index, i, row, column] >= self.differences[0, 1, round_index+self.structure_first_round_index, self.operation_order_up.index('SB')+i, row, column, 1] + self.differences[1, 0, round_index+self.structure_first_round_index, self.operation_order_down.index('SB')+i, row, column, 1] - 1
                                for round_index in range(self.structure_rounds-1)
                                for i in range(2)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name="difference_is_known by_both_parts")
        
        #Then we count words on witch the difference is known before and after the Sbox
        self.matching_differences_not_twice = self.model.addVars(range(self.structure_rounds-1), range(self.block_row_size), range(self.block_column_size), vtype= gp.GRB.BINARY, name = "match_differences per round not twice")
    
        self.model.addConstrs((self.matching_differences_not_twice[round_index, row, column] <= self.differences[0, 1, round_index+self.structure_first_round_index, self.operation_order_up.index('SB'), row, column, 1]
                                for round_index in range(self.structure_rounds-1)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name="difference is known before the sbox")

        self.model.addConstrs((self.matching_differences_not_twice[round_index, row, column] <= self.differences[1, 0, round_index+self.structure_first_round_index, self.operation_order_down.index('SB')+1, row, column, 1]
                                for round_index in range(self.structure_rounds-1)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name="difference is known after the sbox")

        self.model.addConstrs((self.matching_differences_not_twice[round_index, row, column] >= self.differences[0, 1, round_index+self.structure_first_round_index, self.operation_order_up.index('SB'), row, column, 1] + self.differences[1, 0, round_index+self.structure_first_round_index, self.operation_order_down.index('SB')+1, row, column, 1] - 1
                                for round_index in range(self.structure_rounds-1)
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)), name="difference is known before and after the sbox")
        
        #To count the differences we count all the known deferences around the sbox and substract the ones known twice.
        self.model.addConstrs((self.matching_differences_count[round_index] == gp.quicksum(self.matching_differences[round_index, i, row, column]
                                                                                      for i in range(2) for row in range(self.block_row_size)
                                                                                      for column in range(self.block_column_size))
                                                                                    - gp.quicksum(self.matching_differences_not_twice[round_index, row, column]
                                                                                      for row in range(self.block_row_size) 
                                                                                      for column in range(self.block_column_size))
                                                                                    for round_index in range(self.structure_rounds-1)), name="counting matching differences")
        
        # Linearisation of max(matching_differences_count[r]) over r in range(structure_rounds-1)
        # One-hot vector z_match[r]: exactly one r is the argmax.
        # max >= count[r] for all r (lower bounds, always valid)
        # max <= count[r] + M*(1-z[r]) for all r (upper bound tight on the selected r)
        #
        # structure_rounds == 1: no intermediate SB positions inside the structure,
        # so there is nothing to match → matching_differences_quantity = 0.
        if self.structure_rounds >= 2:
            z_match = self.model.addVars(range(self.structure_rounds - 1), vtype=gp.GRB.BINARY, name="z_max_match")
            self.model.addConstr(gp.quicksum(z_match[r] for r in range(self.structure_rounds - 1)) == 1, name="z_max_match_one_hot")
            for r in range(self.structure_rounds - 1):
                self.model.addConstr(self.matching_differences_quantity >= self.matching_differences_count[r], name=f"max_match_lb_{r}")
                self.model.addConstr(self.matching_differences_quantity <= self.matching_differences_count[r] + max_max * (1 - z_match[r]), name=f"max_match_ub_{r}")
        else:
            self.model.addConstr(self.matching_differences_quantity == 0, name="no_match_single_structure_round")
        
        #self.model.addConstr(self.matching_differences_quantity >= self.common_fix_count)
        #No probabilisit propagation in structure :
        if 'MC' in self.operation_order_up or 'MC' in self.operation_order_down:
            self.model.addConstrs(self.XOR_in_mc_differences[(attack_side_index, sens, round_index, column) + vector + (2,)]==0
                                                                for attack_side_index in range(2)
                                                                for sens in range(2)
                                                                for round_index in range(self.structure_first_round_index, self.structure_last_round_index+1)
                                                                for column in range(self.block_column_size)
                                                                for vector in self.column_range[sens][round_index%len(self.matrixes[sens])])
        
        if 'MR' in self.operation_order_up or 'MR' in self.operation_order_down:
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
        
        #first state of the begining of the structure is know by the lower part :
        self.model.addConstrs((self.value_in_structure[1, 0, self.structure_first_round_index, 0, row, column, 1]==1
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
        if 'MC' in self.operation_order_up:
            state_stest_up_elements += gp.quicksum(self.XOR_in_mc_values[(0, 0, round_index, column)+(column_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for column in range(self.block_column_size)
                                                                for column_xor in self.column_range[0][round_index%len(self.matrixes[0])])

        if 'MR' in self.operation_order_up:
            state_stest_up_elements += gp.quicksum(self.XOR_in_mr_values[(0, 0, round_index, row)+(row_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for row in range(self.block_row_size)
                                                                for row_xor in self.row_range[0][round_index%len(self.matrixes[0])])

        self.model.addConstr(self.state_test_up == state_stest_up_elements, name='state_test_up_count')

        self.model.addConstrs((self.values[0, 1, self.lower_part_last_round, self.operation_order_up.index('AK')+1, row, column, 0]==1 
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), name="last state of bacward propagation of upper values is 0")
        
        ### Differences
        #Variable initialisation
        self.probabilist_annulation_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "probabilist_annulation_up")

        #Constraints

        #Fix distinguisher input and set y at distinguisher boundary
        sb_up = self.operation_order_up.index('SB')
        for row in range(self.block_row_size) :
            for column in range(self.block_column_size):
                if [row, column] in self.distinguisher_input :
                    self.model.addConstr(self.differences[0, 1, self.upper_part_last_round, sb_up, row, column, 1] == 1,
                                name='fix differcences active in the input of the distinguisher')
                    # active word at distinguisher boundary: y=1 if non-truncated, y=0 if truncated
                    if not self.trunc_diff:
                        self.model.addConstr(self.diff_known[0, 1, self.upper_part_last_round, sb_up, row, column] == 1,
                                    name='diff_known_active_upper_boundary')
                    else:
                        self.model.addConstr(self.diff_known[0, 1, self.upper_part_last_round, sb_up, row, column] == 0,
                                    name='diff_known_active_upper_boundary_trunc')
                else :
                    self.model.addConstr(self.differences[0, 1, self.upper_part_last_round, sb_up, row, column, 0] == 1,
                                name='fix differcences active in the input of the distinguisher')
                    # null word at distinguisher boundary: y=1 always (must verify it's truly null)
                    self.model.addConstr(self.diff_known[0, 1, self.upper_part_last_round, sb_up, row, column] == 1,
                                name='diff_known_null_upper_boundary')

        self.backward_differences_propagation(0, self.upper_part_first_round, self.lower_part_last_round)

        #no bacward propagation of differences in the upper part
        self.model.addConstrs((self.differences[0, 0, round_index, part, row, column, 1]==0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name = "no backward upper propagation")
        # y=0 for unused direction
        self.model.addConstrs((self.diff_known[0, 0, round_index, part, row, column] == 0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name = "diff_known_zero_upper_forward")
        
        #counting probabilist annulation
        probabilist_annulation_up_count = 0
        if 'MC' in self.operation_order_up:
            probabilist_annulation_up_count += gp.quicksum(self.XOR_in_mc_differences[(0, 1, round_index, column)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for column in range(self.block_column_size)
                                                          for vector in self.column_range[1][round_index%len(self.matrixes[1])])
        if 'MR' in self.operation_order_up:
            probabilist_annulation_up_count += gp.quicksum(self.XOR_in_mr_differences[(0, 1, round_index, row)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for row in range(self.block_row_size)
                                                          for vector in self.row_range[1][round_index%len(self.matrixes[1])])

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
        if 'MC' in self.operation_order_down:
            state_test_down_elements += gp.quicksum(self.XOR_in_mc_values[(1, 0, round_index, column)+(column_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for column in range(self.block_column_size)
                                                                for column_xor in self.column_range[0][round_index%len(self.matrixes[0])])
        if 'MR' in self.operation_order_down:
            state_test_down_elements += gp.quicksum(self.XOR_in_mr_values[(1, 0, round_index, row)+(row_xor)+(2,)]
                                                                for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                                for row in range(self.block_row_size)
                                                                for row_xor in self.row_range[0][round_index%len(self.matrixes[0])])

        self.model.addConstr(self.state_test_down == state_test_down_elements, name='state_test_down_count')

        self.model.addConstrs((self.values[1, 0, self.upper_part_first_round, self.operation_order_down.index('AK'), row, column, 0]==1
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), name = " forward propagation of lower values starts with only 0")  

        ### DIFFERENCE
        #Variable initialisation
        self.probabilist_annulation_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "probabilist_annulation_down")

        #Constraints

        #Fix distinguisher output and set y at distinguisher boundary
        sb_down = self.operation_order_down.index('SB')
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                if [row, column] in self.distinguisher_output:
                    self.model.addConstr(self.differences[1, 0, self.lower_part_first_round, sb_down, row, column, 1] == 1,
                                    name='fix differences active in the output of the distinguisher')
                    # active word at distinguisher boundary: y=1 if non-truncated, y=0 if truncated
                    if not self.trunc_diff:
                        self.model.addConstr(self.diff_known[1, 0, self.lower_part_first_round, sb_down, row, column] == 1,
                                    name='diff_known_active_lower_boundary')
                    else:
                        self.model.addConstr(self.diff_known[1, 0, self.lower_part_first_round, sb_down, row, column] == 0,
                                    name='diff_known_active_lower_boundary_trunc')
                else :
                    self.model.addConstr(self.differences[1, 0, self.lower_part_first_round, sb_down, row, column, 0] == 1,
                                    name='fix differences active in the output of the distinguisher')
                    # null word at distinguisher boundary: y=1 always
                    self.model.addConstr(self.diff_known[1, 0, self.lower_part_first_round, sb_down, row, column] == 1,
                                    name='diff_known_null_lower_boundary')

        self.forward_differences_propagation(1, self.lower_part_first_round, self.lower_part_last_round)

        #no forward propagation of differences in the lower part
        self.model.addConstrs((self.differences[1, 1, round_index, part, row, column, 1]==0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name = "no backward upper propagation")
        # y=0 for unused direction
        self.model.addConstrs((self.diff_known[1, 1, round_index, part, row, column] == 0
                              for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                              for part in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name = "diff_known_zero_lower_backward")
        
        #counting probabilist annulation
        probabilist_annulation_down_count = 0
        if 'MC' in self.operation_order_down:
            probabilist_annulation_down_count += gp.quicksum(self.XOR_in_mc_differences[(1, 0, round_index, column)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for column in range(self.block_column_size)
                                                          for vector in self.column_range[0][round_index%len(self.matrixes[0])])
        if 'MR' in self.operation_order_down:
            probabilist_annulation_down_count += gp.quicksum(self.XOR_in_mr_differences[(1, 0, round_index, row)+vector+(2,)]
                                                          for round_index in range(self.upper_part_first_round, self.lower_part_last_round+1)
                                                          for row in range(self.block_row_size)
                                                          for vector in self.row_range[0][round_index%len(self.matrixes[0])])
        
        self.model.addConstr(self.probabilist_annulation_down == probabilist_annulation_down_count, name = "counting probabilist_annulation in the lower part")                      
    
    #Complexities and objectives
    def complexities(self):
        self.time_complexity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "time_complexity")
        self.memory_complexity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "memory_complexity")
        self.data_complexity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "data_complexity")

        self.time_complexity_up = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_up")
        self.time_complexity_down = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_down")
        self.time_complexity_match = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_match")
        self.time_complexity_brute_force = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_brute_force")

        self.data_fixe = self.model.addVar(vtype= gp.GRB.INTEGER, name = "data_fixe")

        
        T_complexity_up = self.upper_key_guess + self.state_test_up + self.probabilist_annulation_down
        T_complexity_down = self.lower_key_guess + self.state_test_down + self.probabilist_annulation_up 
        
        
        T_complexity_match = self.block_size//self.word_size + self.max_fix_up_fix_down - self.fix_up - self.fix_down + self.upper_key_guess + self.lower_key_guess - self.common_key_guess + self.state_test_up + self.state_test_down - self.matching_differences_quantity #- self.common_fix_count
        
        if self.structure_rounds <= 1 :
            T_complexity_match = self.upper_key_guess + self.lower_key_guess - self.common_key_guess + self.state_test_up + self.state_test_down - self.block_size//self.word_size
        

        if self.filter_state_test :
            T_complexity_match += -self.state_test_up -self.state_test_down
    
        if self.trunc_diff :
            T_complexity_down += self.distinguisher_output_quantity - self.distinguisher_input_quantity
            T_complexity_match += self.distinguisher_output_quantity
        
        if self.specific_key_filtering :
            T_complexity_match -= self.specific_key_filtering_quantity

        #brute force part
        
        self.key_guess_quantity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "key_guess_quantity")

        key_guess = self.upper_key_guess + self.lower_key_guess - self.common_key_guess + (self.matching_differences_quantity - self.common_fix_count)
        
        if self.filter_state_test :
            key_guess +=  self.state_test_up + self.state_test_down

        self.model.addConstr(self.key_guess_quantity == key_guess, name = "key guess quantity definition")
        
        if self.filter_extra_key_guess :
            T_complexity_match -= self.key_space_size - self.key_guess_quantity

        self.attack_repetition = self.model.addVar(vtype= gp.GRB.INTEGER, name = "attack_repetition")
        max_repetetions = 10
        
        #Binary variable to linearize integer
        self.binary_indicator_repetitions = self.model.addVars(range(max_repetetions+1), vtype= gp.GRB.BINARY, name = "binary_indicator_repetitions")

        self.model.addConstr(gp.quicksum(self.binary_indicator_repetitions[repetition] for repetition in range(max_repetetions+1)) == 1, name = "only one repetition value")

        self.model.addConstr(self.attack_repetition == gp.quicksum(repetition*self.binary_indicator_repetitions[repetition] for repetition in range(max_repetetions+1)), name = "attack repetition definition")
        # attack_repetition=r means the attack is run r+1 times total
        # log2 overhead: r=0 → 1 run → log2(1)=0; r=1 → 2 runs → log2(2)=1; etc.
        log2_costs = [0 if r == 0 else math.ceil(math.log2(r + 1)) for r in range(max_repetetions+1)]
        log2_repetitions_expr = gp.quicksum(log2_costs[r] * self.binary_indicator_repetitions[r] for r in range(max_repetetions+1))
        # advantage_per_run = max(0, key_guess_quantity - T_complexity_match)
        # delta_adv=1 iff key_guess_quantity >= T_complexity_match
        advantage_per_run = self.model.addVar(lb=0, ub=self.key_space_size, vtype=gp.GRB.INTEGER, name="advantage_per_run")
        delta_adv = self.model.addVar(vtype=gp.GRB.BINARY, name="delta_advantage_positive")
        self.model.addConstr(advantage_per_run >= self.key_guess_quantity - T_complexity_match - math.ceil(self.distinguisher_probability/self.word_size), name="advantage_per_run_lb")
        self.model.addConstr(advantage_per_run <= self.key_guess_quantity - T_complexity_match - math.ceil(self.distinguisher_probability/self.word_size) + self.key_space_size*(1 - delta_adv), name="advantage_per_run_ub_positive")
        self.model.addConstr(advantage_per_run <= self.key_space_size * delta_adv, name="advantage_per_run_ub_zero")

        # McCormick: possible_advantage[r] = r * advantage_per_run  when binary_indicator[r]=1, else 0
        possible_advantage = self.model.addVars(range(max_repetetions+1), lb=0, ub=max_repetetions*self.key_space_size, vtype=gp.GRB.INTEGER, name="possible_advantage")

        for repetition in range(max_repetetions+1):
            self.model.addConstr(possible_advantage[repetition] <= repetition * advantage_per_run)
            self.model.addConstr(possible_advantage[repetition] <= repetition * self.key_space_size//self.word_size * self.binary_indicator_repetitions[repetition])
            self.model.addConstr(possible_advantage[repetition] >= repetition * advantage_per_run - repetition * self.key_space_size//self.word_size * (1 - self.binary_indicator_repetitions[repetition]))

        self.total_advantage = self.model.addVar(lb=0, ub=max_repetetions*self.key_space_size//self.word_size, vtype=gp.GRB.INTEGER, name="total_advantage")
        self.model.addConstr(self.total_advantage == gp.quicksum(possible_advantage[repetition] for repetition in range(max_repetetions+1)))

        T_complexity_brute_force = T_complexity_match + self.key_space_size//self.word_size - self.key_guess_quantity - self.total_advantage
        

        self.model.addConstr(self.time_complexity_up == T_complexity_up + log2_repetitions_expr)
        self.model.addConstr(self.time_complexity_down == T_complexity_down + log2_repetitions_expr)
        self.model.addConstr(self.time_complexity_match == T_complexity_match + log2_repetitions_expr)
        self.model.addConstr(self.time_complexity_brute_force == T_complexity_brute_force + log2_repetitions_expr)

        self.model.addConstr(self.time_complexity_down <= self.time_complexity, name="suboptimal time complexity down")
        self.model.addConstr(self.time_complexity_up <= self.time_complexity, name="suboptimal time complexity up")
        self.model.addConstr(self.time_complexity_match <= self.time_complexity, name="suboptimal time complexity match")
        #self.model.addConstr(self.time_complexity_brute_force <= self.time_complexity, name="suboptimal time complexity brute force")

        self.model.addConstr(self.memory_complexity <= self.upper_key_guess + self.state_test_up - self.common_fix_count + (self.block_size//self.word_size - self.fix_up),
                              name='memory_complexity_up_definition')
        self.model.addConstr(self.memory_complexity <= self.lower_key_guess + self.state_test_down - self.common_fix_count + (self.block_size//self.word_size - self.fix_down),
                              name='memory_complexity_down_definition')
        
        #Complexite Data
        self.model.addConstr(self.data_fixe <= gp.quicksum(self.values[1, 1, 0, 0, row, column, 2] for row in range(self.block_row_size) for column in range(self.block_column_size)), name='data_fixe')
        
        self.model.addConstr(self.data_complexity >= self.block_size//self.word_size - self.data_fixe, name='data_definition')
        
        self.model.addConstr(self.data_complexity >= self.distinguisher_probability//self.word_size + self.data_fixe, name='data_definition')

        #self.model.addConstr(self.time_complexity_up <= 33)
        #self.model.addConstr(self.time_complexity_down <= 33)

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

        #self.model.setObjectiveN(self.for_display, index=10, priority=0)
    
    def objective(self):
        self.objective_for_display()
        self.complexities()

        # Weighted-sum objective. The coefficient on state_test (0.0001) is small enough
        # that no realistic number of state_test words (block_size/word_size ~ 16-64)
        # can outweigh 1 unit of time_complexity, so the primary objective is effectively
        # time_complexity alone.
        self.model.setObjectiveN(self.time_complexity + 0.1*(self.time_complexity_up+self.time_complexity_down) + 0.01*(self.state_test_up + self.state_test_down) + 0.000001*self.for_display, gp.GRB.MINIMIZE)
        
    #Attack build
    def attack(self):

        #initialization
        self.value_variables_initialisation()

        self.difference_variables_initialisation()
        

        #Constraints of each part
        self.structure()

        self.upper_part()

        self.lower_part()

        #Global constraints
        #The total probability of the attack cannot exceed the size of the block
        self.model.addConstr(self.word_size*self.probabilist_annulation_down+self.word_size*self.probabilist_annulation_up+self.distinguisher_probability <= self.block_size)
        
        #Not optimal to repeat the attack more than the number of time needed to verify the probability of the trail
        #(only meaningful when there is a structure, as max_fix is 0 otherwise)
        if self.structure_rounds > 0:
            self.model.addConstr(self.distinguisher_probability + self.word_size*self.max_fix_up_fix_down >= self.block_size+1)
        
        ###debugging constraints

        #self.model.addConstr(self.state_test_up==1, name="at least one state test up")
        #self.model.addConstr(self.state_test_down==1, name="at least one state test down")
        #self.model.addConstr(self.values[0, 0, 4, 3, 2, 1, 2]==1)
        #self.model.addConstr(self.values[1, 1, 16, 0, 1, 1, 2]==1)
        #self.model.addConstr(self.probabilist_annulation_down==1, name="at least one pb key down")
        #self.model.addConstr(self.probabilist_annulation_up==1, name="at least one pb key up")
        #self.model.addConstr(self.matching_differences_quantity>=2, name="at least 2 matching differences")
        self.model.addConstr(self.common_fix_count==self.fix_up, name="only common fix")
        self.model.addConstr(self.common_fix_count==self.fix_down, name="only common fix")
        #self.model.addConstr(self.upper_key_guess + self.state_test_up <= self.key_size//self.word_size)
        #self.model.addConstr(self.lower_key_guess + self.state_test_down <= self.key_size//self.word_size)
        #self.model.addConstr(self.common_fix_count==6)
        #self.model.addConstr(self.upper_key_guess - self.lower_key_guess <= 5, name="guess_balance_up")
        #self.model.addConstr(self.lower_key_guess - self.upper_key_guess <= 5, name="guess_balance_down")
        
        #Objective functions
        self.objective()

        if self.use_upper_bound :
            self.model.addConstr(self.time_complexity <= self.known_upper_bound - 1, name='upper_bound_cut')
        
        if self.specific_solution_search :
            self.model.setParam("MIPGap",     1.0)   #stop when at least one solution is find
            self.model.setParam("MIPFocus",   1)     #search only for solution not optimality
            self.model.setParam("Heuristics", 0.5)   #Use many heuristics to focus on finding a solution
            self.model.addConstr(self.time_complexity <= self.solution_value,name='target_bound')
        
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


            print("MATCH PART :")
            print("Matching differences :", self.matching_differences_quantity.X)
            print("total_common_key_guess :", self.common_key_guess.X)
            if self.trunc_diff :
                print("truncated end :", self.distinguisher_output_quantity)
            print("Common fix :", self.common_fix_count.X)
            print("max(Fin,Fout) :", self.max_fix_up_fix_down.X )
            print("Complexity match :", self.time_complexity_match.X)
            print("Total complexity match :", self.time_complexity_match.X*self.word_size + self.distinguisher_probability)
            print("\n")

            print("BRUTE FORCE PART :")

            print("attack_key_space :", self.key_space_size)
            print("total_key_quantity_guess :", self.key_guess_quantity.X)
            for r in range(11):
                 if self.binary_indicator_repetitions[r].X == 1:
                     print(f"Repetitions : {r}")
            print("attack_repetition :", self.attack_repetition.X)
            print("total_advantage :", self.total_advantage.X)
            print("Time complexity brute force :", self.time_complexity_brute_force.X*self.word_size + self.distinguisher_probability)  

            print("\n")
            print("OVERALL :")
            print("Time complexity :", self.word_size*self.time_complexity.X+self.distinguisher_probability)
            print("Time complexity :", self.time_complexity.X)
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
                                _op = self.operation_order_down if round_index >= self.lower_part_first_round else self.operation_order_up
                                line += f"{_op[state_index][0]}{_op[state_index][1]}"
                            elif row == self.block_row_size//2:
                                line += "->"
                            elif row == self.block_row_size//2 - 1 and state_index == self.state_number -1:
                                line += "NR"
                            else :
                                line += "  "
                        line += "             "
                        is_structure_round = (self.structure_rounds > 0 and
                                              self.structure_first_round_index <= round_index <= self.structure_last_round_index)
                        for state_index in range(self.state_number):
                            line += "|"
                            for column in range(self.block_column_size):
                                d_up = self.differences[0, 1, round_index, state_index, row, column, 1].X
                                d_dn = self.differences[1, 0, round_index, state_index, row, column, 1].X
                                if is_structure_round:
                                    # In structure, all propagated differences are known by definition
                                    sym_up = sym_dn = " ■ "
                                else:
                                    y_up = self.diff_known[0, 1, round_index, state_index, row, column].X if d_up == 1 else 1
                                    y_dn = self.diff_known[1, 0, round_index, state_index, row, column].X if d_dn == 1 else 1
                                    sym_up = " ■ " if y_up == 1 else " ▲ "
                                    sym_dn = " ■ " if y_dn == 1 else " ▲ "
                                if d_up == 0 and d_dn == 0:
                                    line += "\033[90m ■ \033[0m"
                                elif d_up == 1 and d_dn == 0:
                                    line += f"\033[91m{sym_up}\033[0m"
                                elif d_up == 0 and d_dn == 1:
                                    line += f"\033[94m{sym_dn}\033[0m"
                                elif d_up == 1 and d_dn == 1:
                                    line += f"\033[95m ■ \033[0m"
                            line += "|"
                            if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                                _op = self.operation_order_down if round_index >= self.lower_part_first_round else self.operation_order_up
                                line += f"{_op[state_index][0]}{_op[state_index][1]}"
                            elif row == self.block_row_size//2:
                                line += "->"
                            elif row == self.block_row_size//2 - 1 and state_index == self.state_number -1:
                                line += "NR"
                            else :
                                line += "  "
                        print(line)
                else :
                    is_structure_round = (self.structure_rounds > 0 and
                                          self.structure_first_round_index <= round_index <= self.structure_last_round_index)
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
                                _op = self.operation_order_down if round_index >= self.lower_part_first_round else self.operation_order_up
                                line += f"{_op[state_index][0]}{_op[state_index][1]}->"
                            else :
                                line += "    "
                            line += "             "
                            line += "|"
                            for column in range(self.block_column_size):
                                d_up = self.differences[0, 1, round_index, state_index, row, column, 1].X
                                d_dn = self.differences[1, 0, round_index, state_index, row, column, 1].X
                                if not is_structure_round:
                                    y_up = self.diff_known[0, 1, round_index, state_index, row, column].X if d_up == 1 else 1
                                    y_dn = self.diff_known[1, 0, round_index, state_index, row, column].X if d_dn == 1 else 1
                                    sym_up = " ■ " if y_up == 1 else " ▲ "
                                    sym_dn = " ■ " if y_dn == 1 else " ▲ "
                                else:
                                    sym_up = sym_dn = " ■ "
                                if d_up == 0 and d_dn == 0:
                                    line += "\033[90m ■ \033[0m"
                                elif d_up == 1 and d_dn == 0:
                                    line += f"\033[91m{sym_up}\033[0m"
                                elif d_up == 0 and d_dn == 1:
                                    line += f"\033[94m{sym_dn}\033[0m"
                                elif d_up == 1 and d_dn == 1:
                                    line += f"\033[95m ■ \033[0m"
                            line += "|"
                            if row == self.block_row_size//2 and state_index != self.state_number-1:
                                _op = self.operation_order_down if round_index >= self.lower_part_first_round else self.operation_order_up
                                line += f"{_op[state_index][0]}{_op[state_index][1]}->"
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
                
                if 'MC' in self.operation_order_up or 'MC' in self.operation_order_down:
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
                if 'MR' in self.operation_order_up or 'MR' in self.operation_order_down:
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