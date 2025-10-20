from Model import model_MILP_attack
import gurobipy as gp
import random as rd

class MITM(model_MILP_attack.Model_MILP_attack):
    def __init__(self, cipher_parameters, licence_parameters, attack_parameters,):
        super().__init__(cipher_parameters, licence_parameters)
        #Attack parameters
        self.structure_rounds = attack_parameters.get('structure_rounds', 4)
        self.corps_rounds = attack_parameters.get('corps_rounds', 2)
        self.total_rounds = self.structure_rounds + self.corps_rounds

    def getdetails(self):
        print(self.cipher_name, self.block_size, '-', self.key_size)
        #Structure 

    def structure(self):
        ###Upper values 
        #Variable initialisation
        self.fix_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "fix_up")
        self.active_start_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "active_start_up")
        self.upper_structure_values = self.model.addVars(range(self.structure_rounds),
                                                         range(self.state_number), 
                                                         range(self.block_row_size), 
                                                         range(self.block_column_size), 
                                                         range(3), #{0=unknown, 1=can be computed, 2=Fix}
                                                         vtype=gp.GRB.BINARY, 
                                                         name='upper_state_values')
        self.model.addConstrs((gp.quicksum(self.upper_structure_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.structure_rounds)
                              for state_index in range(self.state_number) 
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), 
                              name='unique_value_in_upper_state_value_constraints')

        #Constraints
        self.bacward_value_propagation(self.upper_structure_values, self.structure_rounds, self.upper_subkey, 0)
        
        self.model.addConstr(self.fix_down == gp.quicksum(self.upper_structure_values[round_index, state_index, row, column, 2]
                                                        for round_index in range(self.structure_rounds)
                                                        for state_index in range(self.state_number)
                                                        for row in range(self.block_row_size)
                                                        for column in range(self.block_column_size)),
                            name='fix_up_count')
        
        self.model.addConstrs(self.active_start_up == self.block_column_size*self.block_row_size 
                                                    - gp.quicksum(self.upper_structure_values[self.structure_rounds-1, self.state_number-1, row, column , 0]
                                                                  for row in range(self.block_row_size) 
                                                                  for column in range(self.block_column_size)), 
                            name='active_last_state_structure')
        
        self.model.addConstr(self.active_start_up==self.fix_up, name='each_up_fix_leads_to_a_known_value_in_last_state')
        
        ###Lower values
        #Variable initialisation
        self.fix_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "fix_down")
        self.active_start_down =  self.model.addVar(vtype= gp.GRB.INTEGER, name = "active_start_down")
        self.lower_structure_values = self.model.addVars(range(self.structure_rounds), 
                                                         range(self.state_number), 
                                                         range(self.block_row_size), 
                                                         range(self.block_column_size), 
                                                         range(3), #{0=unknown, 1=can be computed, 2=Fix}
                                                         vtype=gp.GRB.BINARY, 
                                                         name='upper_state_values')
        self.model.addConstrs((gp.quicksum(self.lower_structure_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.structure_rounds) 
                              for state_index in range(self.state_number) 
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), 
                              'unique_value_in_upper_state_value_constraints')
        
        #Constraints
        self.forward_value_propagation(self.lower_structure_values, self.structure_rounds, self.lower_part_values, 0)
        self.model.addConstr(self.fix_down == gp.quicksum(self.lower_structure_values[round_index, state_index, row, column, 2]
                                                        for round_index in range(self.structure_rounds) 
                                                        for state_index in range(self.state_number) 
                                                        for row in range(self.block_row_size) 
                                                        for column in range(self.block_column_size)),
                            name='fix_down_count')
        
        self.model.addConstrs(self.active_start_down == self.block_column_size*self.block_row_size
                                                     - gp.quicksum(self.lower_structure_values[0, 0, row, column , 0]
                                                                  for row in range(self.block_row_size) 
                                                                  for column in range(self.block_column_size)), 
                            name='active_last_state_structure')
        
        self.model.addConstr(self.active_start_down==self.fix_down, name='each_down_fix_leads_to_a_known_value_in_first_state')

        #Common fix
        self.common_fix = self.model.addVar(vtype= gp.GRB.INTEGER, name = "fix_common")
        self.fix_state = self.model.addVars(range(self.structure_rounds), 
                                                         range(self.state_number), 
                                                         range(self.block_row_size), 
                                                         range(self.block_column_size),
                                                         vtype=gp.GRB.BINARY, 
                                                         name='upper_state_values')
        self.model.addConstrs((self.fix_state[round_index, state_index, row, column] == gp.and_(self.lower_structure_values[round_index, state_index, row, column, 2], self.upper_structure_values[round_index, state_index, row, column, 2])
                             for round_index in range(self.structure_rounds) 
                             for state_index in range(self.state_number) 
                             for row in range(self.block_row_size) 
                             for column in range(self.block_column_size)),
                             name='fix_are_known_upper_and_lower')
        
        
        self.model.addConstr(self.common_fix == (gp.quicksum(self.fix_state[round_index, state_index, row, column]) 
                             for round_index in range(self.structure_rounds) 
                             for state_index in range(self.state_number) 
                             for row in range(self.block_row_size) 
                             for column in range(self.block_column_size)),
                             name='fix_common_count')

    def forward_value_propagation_upper_part(self):
        #Variable initialisation 
        self.state_test_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "state_test_up")
        self.upper_part_values = self.model.addVars(range(self.corps_rounds), #
                                                    range(self.state_number), 
                                                    range(self.block_row_size), 
                                                    range(self.block_column_size), 
                                                    range(3), #valeur{0=unknown, 1=can be computed, 2=state_tested}
                                                    vtype=gp.GRB.BINARY, 
                                                    name='upper_state_values')                        
        self.model.addConstrs((gp.quicksum(self.upper_part_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.corps_rounds)
                              for state_index in range(self.state_number)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)),
                              name='unique_value_in_upper_state_value_constraints')

        #Constraints :
        self.forward_value_propagation(self.upper_part_values, self.corps_rounds, self.upper_subkey, self.structure_rounds)
        self.model.addConstr(self.state_test_up == gp.quicksum(self.upper_part_values[round_index, state_index, row, column, 2]
                                                               for round_index in range(self.corps_rounds)
                                                               for state_index in range(self.state_number)
                                                               for row in range(self.block_row_size)
                                                               for column in range(self.block_column_size)),
                                                               name='state_test_up_count')
    
    def bacward_value_propagation_lower_part(self):
        #Variable initialisation
        self.state_test_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "state_test_down")
        self.lower_part_values = self.model.addVars(range(self.corps_rounds), 
                                                    range(self.state_number), 
                                                    range(self.block_row_size), 
                                                    range(self.block_column_size), 
                                                    range(3), #{0=unknown, 1=can be computed, 2=state_tested}
                                                    vtype=gp.GRB.BINARY, 
                                                    name='lower_state_values')
        self.model.addConstrs((gp.quicksum(self.lower_part_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.corps_rounds) 
                              for state_index in range(self.state_number) 
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), 
                              'unique_value_in_lower_state_value_constraints')
        
        #Constraints
        self.bacward_value_propagation(self.lower_part_values, self.corps_rounds, self.lower_subkey, self.structure_rounds)
        self.model.addConstr(self.state_test_down == gp.quicksum(self.lower_part_values[round_index, state_index, row, column, 2]
                                                               for round_index in range(self.corps_rounds)
                                                               for state_index in range(self.state_number)
                                                               for row in range(self.block_row_size)
                                                               for column in range(self.block_column_size)),
                                                               name='state_test_down_count')

    def match(self):
        self.match_state_index = self.operation_order.index('MC0')
        self.match_quantity = self.model.addVar(vtype= gp.GRB.INTEGER, name = "match_quantity")
        self.match_state = self.model.addVars(range(self.corps_rounds),
                                              range(self.block_row_size), 
                                              range(self.block_column_size), 
                                              vtype = gp.GRB.BINARY, 
                                              name='match_state')
        self.model_addConstrs((self.match_state[round_index, row, column] 
                              == gp.and_(self.upper_part_values[round_index, self.match_state, row, column, 1], self.lower_part_values[round_index, self.match_state, row, column, 1])
                              for round_index in range(self.corps_rounds)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'match_state_around_MC_value_known_by_upper_and_lower')
        
        self.model.addConstr(self.match_quantity == gp.quicksum(self.match_state[round_index, row, column]
                                                                for round_index in range(self.corps_rounds)
                                                                for row in range(self.block_row_size)
                                                                for column in range(self.block_column_size)), 
                                                                name='mathc_only_around_MC')

        self.model.addConstr(self.match_quantity >= 1)

    def attack(self):
        self.master_key()
        self.subkey()
        self.structure()
        self.forward_value_propagation_upper_part()
        self.bacward_value_propagation_lower_part()
        self.match()
        self.objective_function()
        self.optimize()
        self.get_results()
    
    def objective_for_display(self):
        self.for_display = self.model.addVar(vtype= gp.GRB.INTEGER, name = "for_display")

        self.model.addConstr(self.for_display == gp.quicksum(self.upper_part_values[round_index, state_index, row, column, 1] for round_index in range(self.corps_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))
                                     + gp.quicksum(self.lower_part_values[round_index, state_index, row, column, 1] for round_index in range(self.corps_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))
                                     + gp.quicksum(self.lower_structure_values[round_index, state_index, row, column, 1] for round_index in range(self.structure_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))
                                     + gp.quicksum(self.upper_structure_values[round_index, state_index, row, column, 1] for round_index in range(self.structure_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)))
        self.model.setObjectiveN((-1)*self.for_display, index=10, priority=0)
    
    def objective_function(self):
        self.objective_for_display()
        self.complexities()

        self.time_complexity_up = self.state_test_up + self.key_up
        self.time_compleity_down =  
        self.model.setObjectiveN(self.time_complexity, index=0, priority=10)
 
    def get_results(self):
        if self.optimize:
            print(self.state_test_up)
        else :
            print('The Model at no been optimize yet')

    def display_console(self):
        # Upper part display
        for round_index in range(self.corps_rounds):
            print("ROUND ", round_index)
            key_line = ""
            for row in range(self.block_row_size):
                key_line += "        |"
                for column in range(self.block_column_size):
                    if self.upper_subkey[round_index, row, column, 0].X == 1:
                        key_line += "\033[90m ■ \033[0m"
                    elif self.upper_subkey[round_index, row, column, 1].X == 1:
                        key_line += "\033[91m ■ \033[0m"
                    else :
                        key_line += " ? "
                key_line += "|\n"

            print(key_line)
            for row in range(self.block_row_size):
                line = ""
                for state_index in range(self.state_number):
                    line += "|"
                    for column in range(self.block_column_size):
                        if self.upper_values[round_index, state_index, row, column, 0].X == 1:
                            line += "\033[90m ■ \033[0m"
                        elif self.upper_values[round_index, state_index, row, column, 1].X == 1:
                            line += "\033[91m ■ \033[0m"
                        elif self.upper_values[round_index, state_index, row, column, 2].X == 1:
                            line += "\033[92m ■ \033[0m"
                        else :
                            print(self.upper_values[round_index, state_index, row, column, 0].X)
                            print(self.upper_values[round_index, state_index, row, column, 1].X)
                            print(self.upper_values[round_index, state_index, row, column, 2].X)
                            line += " ? "
                    line += "|"
                    if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                        line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                    elif row == self.block_row_size//2 and state_index != self.state_number -1:
                        line += "->"
                    else :
                        line += "  "
                print(line)
            print("\n")
    
        # Lower part display
        for round_index in range(self.corps_rounds):
            print("ROUND ", round_index)
            key_line = ""
            for row in range(self.block_row_size):
                key_line += "        |"
                for column in range(self.block_column_size):
                    if self.lower_subkey[round_index, row, column, 0].X == 1:
                        key_line += "\033[90m ■ \033[0m"
                    elif self.lower_subkey[round_index, row, column, 1].X == 1:
                        key_line += "\033[94m ■ \033[0m"
                    else :
                        key_line += " ? "
                key_line += "|\n"

            print(key_line)
            for row in range(self.block_row_size):
                line = ""
                for state_index in range(self.state_number):
                    line += "|"
                    for column in range(self.block_column_size):
                        if self.lower_values[round_index, state_index, row, column, 0].X == 1:
                            line += "\033[90m ■ \033[0m"
                        elif self.lower_values[round_index, state_index, row, column, 1].X == 1:
                            line += "\033[94m ■ \033[0m"
                        elif self.lower_values[round_index, state_index, row, column, 2].X == 1:
                            line += "\033[92m ■ \033[0m"
                        else :
                            line += " ? "
                    line += "|"
                    if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                        line += f"{self.operation_order[state_index][0]}{self.operation_order[state_index][1]}"
                    elif row == self.block_row_size//2 and state_index != self.state_number -1:
                        line += "<-"
                    else :
                        line += "  "
                print(line)
            print("\n")
        
    
