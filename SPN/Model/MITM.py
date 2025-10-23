from Model import model_MILP_attack
import gurobipy as gp

class MITM(model_MILP_attack.Model_MILP_attack):
    def __init__(self, cipher_parameters, licence_parameters, attack_parameters, model):
        super().__init__(cipher_parameters, licence_parameters, model)
        #Attack parameters
        self.structure_rounds = attack_parameters.get('structure_rounds', 4)
        self.corps_rounds = attack_parameters.get('corps_rounds', 2)
        self.total_rounds = self.structure_rounds + self.corps_rounds
        self.optimal_complexity = attack_parameters.get('optimal_complexity', False)

    def getdetails(self):
        print(self.cipher_name, self.block_size)
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
                                                         name='upper_structure_values')
        self.model.addConstrs((gp.quicksum(self.upper_structure_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.structure_rounds)
                              for state_index in range(self.state_number) 
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), 
                              name='unique_value_in_upper_state_value_constraints')

        #Constraints
        self.forward_value_propagation(self.upper_structure_values, self.structure_rounds, self.upper_subkey, 0)
        
        self.model.addConstr(self.fix_up == gp.quicksum(self.upper_structure_values[round_index, state_index, row, column, 2]
                                                        for round_index in range(self.structure_rounds)
                                                        for state_index in range(self.state_number)
                                                        for row in range(self.block_row_size)
                                                        for column in range(self.block_column_size)),
                            name='fix_up_count')
        
        self.model.addConstr(self.active_start_up == (self.block_size//self.word_size
                                                    - gp.quicksum(self.upper_structure_values[self.structure_rounds-1, self.state_number-1, row, column , 0]
                                                                  for row in range(self.block_row_size) 
                                                                  for column in range(self.block_column_size))), 
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
                                                         name='lower_structure_values')
        self.model.addConstrs((gp.quicksum(self.lower_structure_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.structure_rounds) 
                              for state_index in range(self.state_number) 
                              for row in range(self.block_row_size) 
                              for column in range(self.block_column_size)), 
                              'unique_value_in_upper_state_value_constraints')
        
        #Constraints
        self.backward_value_propagation(self.lower_structure_values, self.structure_rounds, self.lower_subkey, 0)
        
        self.model.addConstr(self.fix_down == gp.quicksum(self.lower_structure_values[round_index, state_index, row, column, 2]
                                                        for round_index in range(self.structure_rounds) 
                                                        for state_index in range(self.state_number) 
                                                        for row in range(self.block_row_size) 
                                                        for column in range(self.block_column_size)),
                            name='fix_down_count')
        
        self.model.addConstr(self.active_start_down == self.block_column_size*self.block_row_size
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
                                                         name='fix_state')
        self.model.addConstrs((self.fix_state[round_index, state_index, row, column] == gp.and_(self.lower_structure_values[round_index, state_index, row, column, 2], self.upper_structure_values[round_index, state_index, row, column, 2])
                             for round_index in range(self.structure_rounds) 
                             for state_index in range(self.state_number) 
                             for row in range(self.block_row_size) 
                             for column in range(self.block_column_size)),
                             name='fix_are_known_upper_and_lower')
        
        
        self.model.addConstr(self.common_fix == (gp.quicksum(self.fix_state[round_index, state_index, row, column] 
                             for round_index in range(self.structure_rounds) 
                             for state_index in range(self.state_number) 
                             for row in range(self.block_row_size) 
                             for column in range(self.block_column_size))),
                             name='fix_common_count')
        
        self.model.addConstr(self.fix_down+self.fix_up-self.common_fix<=self.block_size//self.word_size, name='cannot_fix_more_than_the_block')

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
    
    def backward_value_propagation_lower_part(self):
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
        self.backward_value_propagation(self.lower_part_values, self.corps_rounds, self.lower_subkey, self.structure_rounds)
        self.model.addConstr(self.state_test_down == gp.quicksum(self.lower_part_values[round_index, state_index, row, column, 2]
                                                               for round_index in range(self.corps_rounds)
                                                               for state_index in range(self.state_number)
                                                               for row in range(self.block_row_size)
                                                               for column in range(self.block_column_size)),
                                                               name='state_test_down_count')

    def match(self):
        self.match_state_index = self.operation_order.index('MC0')
        self.match_quantity = self.model.addVars(range(self.corps_rounds), vtype= gp.GRB.INTEGER, name = "match_quantity")
        self.match_state = self.model.addVars(range(self.corps_rounds),
                                              range(2),
                                              range(self.block_row_size), 
                                              range(self.block_column_size), 
                                              vtype = gp.GRB.BINARY, 
                                              name='match_state')

        self.model.addConstrs((self.match_state[round_index, state_index, row, column] 
                              == gp.and_(self.upper_part_values[round_index, self.match_state_index + state_index, row, column, 1], self.lower_part_values[round_index, self.match_state_index + state_index, row, column, 1])
                              for round_index in range(self.corps_rounds)
                              for state_index in range(2)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'match_state_around_MC_value_known_by_upper_and_lower')
        
        self.model.addConstrs((self.match_quantity[round_index] <= gp.quicksum(self.match_state[round_index, state_index, row, column]
                                                                for row in range(self.block_row_size)
                                                                for column in range(self.block_column_size)) for round_index in range(self.corps_rounds) for state_index in range(2)) , 
                                                                name='mathc_only_around_MC')

        self.model.addConstr(gp.quicksum(self.match_quantity[round_index] for round_index in range(self.corps_rounds)) >= 1, name='at_least_one_match')

    def attack(self):
        
        self.structure()
        self.model.addConstr(self.common_fix == 16)
        self.forward_value_propagation_upper_part()
        self.backward_value_propagation_lower_part()
        self.match()
        self.model.addConstr(self.state_test_up==0)
        self.model.addConstr(self.state_test_down==0)
        self.objective_function()
        self.optimize_the_model()
    
    def objective_for_display(self):
        self.for_display = self.model.addVar(vtype= gp.GRB.INTEGER, name = "for_display")

        self.model.addConstr(self.for_display == gp.quicksum(self.upper_part_values[round_index, state_index, row, column, 1] for round_index in range(self.corps_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))
                                     + gp.quicksum(self.lower_part_values[round_index, state_index, row, column, 1] for round_index in range(self.corps_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))
                                     + gp.quicksum(self.lower_structure_values[round_index, state_index, row, column, 1] for round_index in range(self.structure_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))
                                     + gp.quicksum(self.upper_structure_values[round_index, state_index, row, column, 1] for round_index in range(self.structure_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)))
        self.model.setObjectiveN(self.for_display, index=10, priority=0)
    
    def complexities(self):
        self.time_complexity = self.model.addVar(vtype= gp.GRB.CONTINUOUS, name = "time_complexity")
        self.memory_complexity = self.model.addVar(vtype= gp.GRB.CONTINUOUS, name = "memory_complexity")
        self.data_complexity = self.model.addVar(vtype= gp.GRB.CONTINUOUS, name = "data_complexity")
        if self.optimal_complexity :
            self.search_domain = range(120)
            self.time_complexity_up = self.model.addVar(lb = 0, ub = 128,vtype= gp.GRB.INTEGER, name = "time_complexity_up")
            self.time_complexity_down = self.model.addVar(lb = 0, ub = 128,vtype= gp.GRB.INTEGER, name = "time_complexity_down")
            self.time_complexity_match = self.model.addVar(lb = 0, ub = 128,vtype= gp.GRB.INTEGER, name = "time_complexity_match")
        
            self.binary_time_complexity_up = {i: self.model.addVar(vtype=gp.GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in self.search_domain}
            self.binary_time_complexity_down = {i: self.model.addVar(vtype=gp.GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in self.search_domain}
            self.binary_time_complexity_match = {i: self.model.addVar(vtype=gp.GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in self.search_domain}
        
            self.model.addConstr(self.time_complexity_up == gp.quicksum(i * self.binary_time_complexity_up[i] for i in self.search_domain), name="link between binary and integer complexity up")
            self.model.addConstr(self.time_complexity_down == gp.quicksum(i * self.binary_time_complexity_down[i] for i in self.search_domain), name="link between binary and integer complexity down")
            self.model.addConstr(self.time_complexity_match == gp.quicksum(i * self.binary_time_complexity_match[i] for i in self.search_domain), name="link between binary and integer complexity match")

            self.model.addConstr(gp.quicksum(self.binary_time_complexity_up[i] for i in self.search_domain)==1, name="unique binary complexity up")
            self.model.addConstr(gp.quicksum(self.binary_time_complexity_down[i] for i in self.search_domain)==1, name="unique binary complexity down")
            self.model.addConstr(gp.quicksum(self.binary_time_complexity_match[i] for i in self.search_domain)==1, name="unique binary complexity match")

            self.model.addConstr(self.time_complexity == gp.quicksum((2**i)*(self.binary_time_complexity_up[i] + self.binary_time_complexity_down[i] + self.binary_time_complexity_match[i]) for i in self.search_domain), name="time complexity")
        
        else :
            self.time_complexity_up = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_up")
            self.time_complexity_down = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_down")
            self.time_complexity_match = self.model.addVar(lb = 0,vtype= gp.GRB.INTEGER, name = "time_complexity_match")

            self.model.addConstr(self.time_complexity_down <= self.time_complexity, name="suboptimal time complexity down")
            self.model.addConstr(self.time_complexity_up <= self.time_complexity, name="suboptimal time complexity up")
            self.model.addConstr(self.time_complexity_match <= self.time_complexity, name="suboptimal time complexity match")
        
    def objective_function(self):
        #self.objective_for_display()
        self.complexities()

        self.model.addConstr(self.time_complexity_up == self.state_test_up + self.upper_key_guess + (self.block_size//self.word_size - self.fix_up), name='time_complexity_up_definition')
        self.model.addConstr(self.time_complexity_down == self.state_test_down + self.lower_key_guess + (self.block_size//self.word_size - self.fix_down), name='time_complexity_down_definition')
        self.model.addConstr(self.time_complexity_match == self.time_complexity_up + self.time_complexity_down - self.common_key_guess - gp.quicksum(self.match_quantity[round_index] for round_index in range(self.corps_rounds)), name='time_complexity_match_definition')
        
        self.model.addConstr(self.memory_complexity >= self.upper_key_guess + self.state_test_up - self.common_fix + (self.block_size//self.word_size - self.fix_up), name='memory_complexity_up_definition')
        self.model.addConstr(self.memory_complexity >= self.lower_key_guess + self.state_test_down - self.common_fix + (self.block_size//self.word_size - self.fix_down), name='memory_complexity_down_definition')
        
        self.model.addConstr(self.data_complexity >= self.block_size//self.word_size - gp.quicksum(self.lower_structure_values[0, 0, row, column, 2] for row in range(self.block_row_size) for column in range(self.block_column_size)), name='data_definition')
        
        self.model.setObjectiveN(self.time_complexity, index=0, priority=10)
        self.model.setObjectiveN(self.data_complexity, index=0, priority=8)
        self.model.setObjectiveN(self.memory_complexity, index=0, priority=5)
 
    def get_results(self):
        if self.optimized:
            print("----- RESULTS -----")
            print('number of rounds :', self.total_rounds)
            print('\n')
            print("UPPER PART :")
            print("Fix up :", self.fix_up.X)
            print("State tested up :", self.state_test_up.X)
            print("Key bits guessed up :", self.upper_key_guess.X)
            print("Complexity up :", self.time_complexity_up.X)
            print("\n")
            print("LOWER PART :")
            print("Fix down :", self.fix_down.X)
            print("State tested down :", self.state_test_down.X)
            print("Key bits guessed down :", self.lower_key_guess.X)
            print("Complexity down :", self.time_complexity_down.X)
            print("\n")
            print("MATHC PART :")
            print("Common fix :", self.common_fix.X)
            print("Common key bits guessed :", self.common_key_guess.X)
            print("Match quantity :", sum(self.match_quantity[round_index].X for round_index in range(self.corps_rounds)))
            print("Complexity match :", self.time_complexity_match.X)
            print("\n")
            print("OVERALL :")
            print("Time complexity :", self.word_size*self.time_complexity.X)
            print("Memory complexity :", self.word_size*self.memory_complexity.X)
            print("Data complexity :", self.word_size*self.data_complexity.X)
            print("\n")

        else :
            print('The Model at no been optimize yet')

    def display_console(self):
        for global_round_index in range(self.total_rounds):
            
            print("ROUND ", global_round_index)
            key_line = ""
            for row in range(self.block_row_size):
                key_line += "        |"
                for column in range(self.block_column_size):
                    if self.upper_subkey[global_round_index, row, column].X == 0 and self.lower_subkey[global_round_index, row, column].X == 0:
                        key_line += "\033[90m ■ \033[0m"
                    elif self.upper_subkey[global_round_index, row, column].X == 1 and self.lower_subkey[global_round_index, row, column].X == 0:
                        key_line += "\033[91m ■ \033[0m"
                    elif self.upper_subkey[global_round_index, row, column].X == 0 and self.lower_subkey[global_round_index, row, column].X == 1:
                        key_line += "\033[94m ■ \033[0m"
                    elif self.upper_subkey[global_round_index, row, column].X == 1 and self.lower_subkey[global_round_index, row, column].X == 1:
                        key_line += "\033[95m ■ \033[0m"
                    else :
                        key_line += " ? "
                key_line += "|\n"
            print(key_line)
            
            if global_round_index < self.structure_rounds :
                round_index = global_round_index
                for row in range(self.block_row_size):
                    line = ""
                    for state_index in range(self.state_number):
                        line += "|"
                        for column in range(self.block_column_size):
                            if self.upper_structure_values[round_index, state_index, row, column, 0].X == 1 and self.lower_structure_values[round_index, state_index, row, column, 0].X == 1:
                                line += "\033[90m ■ \033[0m"
                            elif self.upper_structure_values[round_index, state_index, row, column, 1].X == 1 and self.lower_structure_values[round_index, state_index, row, column, 0].X == 1:
                                line += "\033[91m ■ \033[0m"
                            elif self.upper_structure_values[round_index, state_index, row, column, 2].X == 1 and self.lower_structure_values[round_index, state_index, row, column, 0].X == 1:
                                line += "\033[91m F \033[0m"
                            elif self.upper_structure_values[round_index, state_index, row, column, 0].X == 1 and self.lower_structure_values[round_index, state_index, row, column, 1].X == 1:
                                line += "\033[94m ■ \033[0m"
                            elif self.upper_structure_values[round_index, state_index, row, column, 0].X == 1 and self.lower_structure_values[round_index, state_index, row, column, 2].X == 1:
                                line += "\033[94m F \033[0m"
                            elif self.upper_structure_values[round_index, state_index, row, column, 1].X == 1 and self.lower_structure_values[round_index, state_index, row, column, 1].X == 1:
                                line += "\033[95m ■ \033[0m"
                            elif self.upper_structure_values[round_index, state_index, row, column, 2].X == 1 and self.lower_structure_values[round_index, state_index, row, column, 2].X == 1:
                                line += "\033[95m F \033[0m"
                            else :
                                print(self.upper_structure_values[round_index, state_index, row, column, 0])
                                print(self.upper_structure_values[round_index, state_index, row, column, 1])
                                print(self.upper_structure_values[round_index, state_index, row, column, 2])
                                print(self.lower_structure_values[round_index, state_index, row, column, 0])
                                print(self.lower_structure_values[round_index, state_index, row, column, 1])
                                print(self.lower_structure_values[round_index, state_index, row, column, 2])
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
            
            else : 
                round_index = global_round_index - self.structure_rounds
                for row in range(self.block_row_size):
                    line = ""
                    for state_index in range(self.state_number):
                        line += "|"
                        for column in range(self.block_column_size):
                            if self.upper_part_values[round_index, state_index, row, column, 0].X == 1 and self.lower_part_values[round_index, state_index, row, column, 0].X == 1:
                                line += "\033[90m ■ \033[0m"
                            elif self.upper_part_values[round_index, state_index, row, column, 1].X == 1 and self.lower_part_values[round_index, state_index, row, column, 0].X == 1:
                                line += "\033[91m ■ \033[0m"
                            elif self.upper_part_values[round_index, state_index, row, column, 2].X == 1 and self.lower_part_values[round_index, state_index, row, column, 0].X == 1:
                                line += "\033[92m ■ \033[0m"
                            elif self.upper_part_values[round_index, state_index, row, column, 0].X == 1 and self.lower_part_values[round_index, state_index, row, column, 1].X == 1:
                                line += "\033[94m ■ \033[0m"
                            elif self.upper_part_values[round_index, state_index, row, column, 0].X == 1 and self.lower_part_values[round_index, state_index, row, column, 2].X == 1:
                                line += "\033[92m ■ \033[0m"
                            elif self.upper_part_values[round_index, state_index, row, column, 1].X == 1 and self.lower_part_values[round_index, state_index, row, column, 1].X == 1:
                                line += "\033[95m ■ \033[0m"
                            else :
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
    
        
    
