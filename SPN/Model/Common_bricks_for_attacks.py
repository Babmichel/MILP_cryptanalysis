import gurobipy as gp
from sage.all import Matrix, GF
from itertools import combinations
import numpy as np

class MILP_bricks():   
    def __init__(self, cipher_parameters, licence_parameters, model):  
        
        #Cipher name
        self.cipher_name = cipher_parameters.get('Cipher_name', 'SKINNY')
        
        #Block parameters
        self.block_size = cipher_parameters.get('block_size', 64)
        self.block_column_size = cipher_parameters.get('block_column_size', 4)
        self.block_row_size = cipher_parameters.get('block_row_size', 4)
        self.word_size = int(self.block_size/(self.block_column_size*self.block_row_size))

        #Operations parameters
        self.operation_order = cipher_parameters.get('operation_order', ['AK', 'SR', 'MC', 'SB'])
        self.shift_rows = cipher_parameters.get('shift_rows', [0, 1, 2, 3])
        matrixes = cipher_parameters.get('matrixes', [])
        self.sbox_sizes = cipher_parameters.get('sbox_sizes', [1, 1])   
        
        #Extension of the given parameters
        self.state_number = len(self.operation_order)+1
        self.shift_rows_inverse = [(self.block_column_size - shift) % self.block_column_size for shift in self.shift_rows]
        matrixes_inverses = []
        matrixes_transposes = []
        matrixes_transposes_inverses = []
        for element in matrixes : #Computing the inverse of the matrixes
            M = Matrix(GF(2), element)
            M_inv = M.inverse()
            M_transpose = M.transpose()
            M_transpose_inv = M_inv.transpose()
            matrixes_inverses.append([[int(M_inv[j][i])for i in range(M_inv.ncols())] for j in range(M_inv.nrows())])
            matrixes_transposes.append([[int(M_transpose[j][i])for i in range(M_transpose.ncols())] for j in range(M_transpose.nrows())])
            matrixes_transposes_inverses.append([[int(M_transpose_inv[j][i])for i in range(M_transpose_inv.ncols())] for j in range(M_transpose_inv.nrows())])
        self.matrixes = [matrixes, matrixes_inverses]
        self.matrixes_transposes = [matrixes_transposes, matrixes_transposes_inverses]
        
        self.matrixes_sets = {s: [set(map(tuple, round_mc)) for round_mc in self.matrixes[s]]for s in (0,1)}
        self.matrixes_index_map = {s: [{tuple(v): idx for idx, v in enumerate(round_mc)}for round_mc in self.matrixes[s]]for s in (0,1)}
        self.matrixes_transposes_sets =  {s: [set(map(tuple, round_mc)) for round_mc in self.matrixes_transposes[s]]for s in (0,1)}
        self.matrixes_transposes_index_map = {s: [{tuple(v): idx for idx, v in enumerate(round_mc)}for round_mc in self.matrixes_transposes[s]]for s in (0,1)}

        #MC objects
        self.column_range = [[set() for _ in range(len(self.matrixes[0]))], [set() for _ in range(len(self.matrixes[1]))]]
        self.possible_XORs_MC = [[],[]]
        for m in self.matrixes[0]:
            self.possible_XORs_MC[0].append(self.unpack_possible_XORs_M(m))
        for m in self.matrixes[1]:
            self.possible_XORs_MC[1].append(self.unpack_possible_XORs_M(m))
        for i in range(2):
            for m_index, m in enumerate(self.possible_XORs_MC[i]):
                for row in m:
                    for vector_combination in row:
                        for vector in vector_combination:
                            self.column_range[i][m_index].add(tuple(vector))
                            self.column_range[not(i)][m_index].add(tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[not(i)][m_index]), axis=0))))

        self.row_range = [[set() for _ in range(len(self.matrixes[0]))], [set() for _ in range(len(self.matrixes[1]))]]
        self.possible_XORs_MR = [[],[]]
        for m in self.matrixes[0]:
            self.possible_XORs_MR[0].append(self.unpack_possible_XORs_M(m))
        for m in self.matrixes[1]:
            self.possible_XORs_MR[1].append(self.unpack_possible_XORs_M(m))    
        for i in range(2):
            for m_index, m in enumerate(self.possible_XORs_MR[i]):
                for row in m:
                    for vector_combination in row:
                        for vector in vector_combination:
                            self.row_range[i][m_index].add(tuple(vector))
                            self.row_range[not(i)][m_index].add(tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[not(i)][m_index]), axis=0))))

        #Model Creation
        self.model=model
        if self.model==None:
            self.model = gp.Model(env=gp.Env(params={'WLSACCESSID': licence_parameters.get('WLSACCESSID'), 'WLSSECRET': licence_parameters.get('WLSSECRET'), 'LICENSEID': licence_parameters.get('LICENSEID')}))

            # Parameters of the Gurobi model
            self.model.params.FeasibilityTol = 1e-9
            self.model.params.OptimalityTol = 1e-9
            self.model.setParam("IntFeasTol", 1e-9)
            self.model.setParam("Presolve", 1) #keep the logical structure without doing agressiv presolve
            self.model.setParam("Cuts", 2) #Aggressive cuts for logic models
            self.model.setParam("Heuristics", 0.05) #Less heuristics to focus on proving optimality
            self.model.setParam("VarBranch", 1) #Robust branching for logic models
            self.model.setParam("PreSparsify", 1) #AND and OR constraints sparsification
            self.model.setParam("Aggregate", 0) #AND and OR constraints aggregation
            self.model.setParam("MIPFocus", 1) #balances search between feasible solutions and optimality proof
            self.model.setParam("Threads", 12) 
            self.model.setParam("ConcurrentMIP", 1) #exploration paralléle

        # Double Check of cipher model
        self.everything_all_right = True
        self.optimized=False

    #Tool functions
    def unpack_possible_XORs_vector(self, vector):# a refaire car fait avec le chat GPT
        """
        Version optimisée :
        - représentation des vecteurs comme entiers (bitmasks)
        - XOR logique
        - pas de chevauchement de bits entre vecteurs
        - suppression automatique des redondances
        """
        n = len(vector)
        # conversion du vecteur cible en entier (bitmask)
        target_mask = sum((1 << i) for i, v in enumerate(reversed(vector)) if v == 1)
        if target_mask == 0:
            return []

        # positions actives
        ones_positions = [i for i, v in enumerate(vector) if v == 1]
        k = len(ones_positions)

        # --- Génération de tous les sous-vecteurs valides ---
        valid_masks = []
        for mask in range(1, 1 << k):
            # reconstruire la position réelle du bitmask dans la taille totale n
            full_mask = 0
            for bit_index in range(k):
                if (mask >> bit_index) & 1:
                    full_mask |= 1 << (n - 1 - ones_positions[bit_index])
            valid_masks.append(full_mask)

        results = set()
        # --- Tester toutes les combinaisons sans chevauchement ---
        for r in range(1, k + 1):
            for combo in combinations(valid_masks, r):
                # Vérifier qu’ils ne se chevauchent pas
                union_mask = 0
                valid = True
                for m in combo:
                    if union_mask & m:
                        valid = False
                        break
                    union_mask |= m
                if not valid:
                    continue
                # Vérifier que le XOR donne la cible
                xor_sum = 0
                for m in combo:
                    xor_sum ^= m
                if xor_sum == target_mask:
                    results.add(tuple(sorted(combo)))

        # --- Conversion inverse en listes de 0/1 ---
        final_results = []
        for combo in results:
            combo_list = []
            for m in combo:
                bits = [(m >> i) & 1 for i in reversed(range(n))]
                combo_list.append(bits)
            final_results.append(combo_list)

        return final_results

    def unpack_possible_XORs_M(self, matrixe):
        possible_XOR_list = [[] for _ in range(len(matrixe))]
        for row in range(len(matrixe)):
                possible_XOR_list[row]=self.unpack_possible_XORs_vector(matrixe[row])
        return possible_XOR_list
            
    #Propagation of VALUES through ORPERATIONS
    def propagation_SR_values(self, part, attack_side_index, round_index, input_state_index, output_state_index, shift_rows):
        #an unknow value cannot turn to a value that can be computed.
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                                + part[attack_side_index, sens, round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size, 1] <= 1
                                for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                name = "value_propagation_:_SR_0_not_to_1")
   
    def propagation_MC_values(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index):
        sens = int(input_state_index > output_state_index)
        mc_index = round_index % len(self.matrixes[sens])

        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in self.column_range[sens][mc_index]:
                    if c_vector_element[row] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, column) + c_vector_element + (1,)]
                        #If propagation is forward in the upper part of bacward for the lower part : we can use the opposite propagation
                        if attack_side_index == sens:
                            # if the considered vector is in MC than we check if it is known form the opposite propagation
                            if c_vector_element in self.matrixes_sets[sens][mc_index]:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, output_state_index, self.matrixes_index_map[sens][mc_index][c_vector_element], column, 0]]
                            else:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0]]

                            and_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"and_var_MC_side{attack_side_index}_r{round_index}_row{row}_col{column}")

                            # AND constraint with only linear constraints
                            for element in AND_elements:
                                self.model.addConstr(and_var <= element)
                            self.model.addConstr(and_var >= gp.quicksum(AND_elements) - (len(AND_elements) - 1))

                            # XOR is not known only if all the AND elements are unknown
                            self.model.addConstr(XOR_var <= 1 - and_var, name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

                        # in the other setup : forward/lower and backward/upper, we are not using the opposite propagation
                        else:
                            input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                            self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

        #An output value in known if one of the possible XOR combinations leading to it is known

        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MC[sens][round_index%(len(self.matrixes[0]))][row]:
                        or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"or_var_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        if len(combination) >= 1:
                            #Model the OR with linear constraint for efficiency
                            for element in combination :
                                self.model.addConstr(or_var >= XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(element)+(0,)])
                            self.model.addConstr(or_var <= gp.quicksum(XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(element)+(0,)] for element in combination), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        else :
                            self.model.addConstr(or_var == XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(combination[0])+(0,)])
                        or_vars.append(1-or_var)  
                #linear mode for the OR constraint
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] >= elements, name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1]<= gp.quicksum(or_vars), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
    
    def propagation_MR_values(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index):
        sens = int(input_state_index > output_state_index)
        m_index = round_index % len(self.matrixes[sens])

        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in self.row_range[sens][m_index]:
                    if c_vector_element[column] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, row) + c_vector_element + (1,)]
                        #If propagation is forward in the upper part of bacward for the lower part : we can use the opposite propagation
                        if attack_side_index == sens:
                            # if the considered vector is in MC than we check if it is known form the opposite propagation
                            if c_vector_element in self.matrixes_sets[sens][m_index]:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, output_state_index, row, self.matrixes_index_map[sens][m_index][c_vector_element], 0]]
                            else:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0]]

                            and_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"and_var_MR_side{attack_side_index}_r{round_index}_row{row}_col{column}")

                            # AND constraint with only linear constraints
                            for element in AND_elements:
                                self.model.addConstr(and_var <= element)
                            self.model.addConstr(and_var >= gp.quicksum(AND_elements) - (len(AND_elements) - 1))

                            # XOR is not known only if all the AND elements are unknown
                            self.model.addConstr(XOR_var <= 1 - and_var, name=f"MR_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

                        # in the other setup : forward/lower and backward/upper, we are not using the opposite propagation
                        else:
                            input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                            self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MR_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

        #An output value in known if one of the possible XOR combinations leading to it is known
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MR[sens][round_index%(len(self.matrixes[0]))][column]:
                        or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"or_var_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        not_or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"not_or_var_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        if len(combination) >= 1:
                            self.model.addGenConstrOr(or_var, [XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(index)+(0,)] for index in combination], name = f"OR_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        else :
                            self.model.addConstr(or_var == XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(combination[0])+(0,)])
                        self.model.addConstr(not_or_var == 1-or_var)
                        or_vars.append(not_or_var)  
                #linear mode for the OR constraint
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] >= elements, name = f"OR_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1]<= gp.quicksum(or_vars), name = f"OR_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
    
    def propagation_AK(self, part, attack_side_index, subkey_part, round_index, input_state_index, output_state_index):
        #if the state if not known before the AK it cannot be computed after
        sens = int(input_state_index > output_state_index)

        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 0] +
                                part[attack_side_index, sens,round_index, output_state_index, row, column, 1] <= 1
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_state_not_to_1')
        
        #if the key is not known, the state after AK cannot be computed
        self.model.addConstrs(( part[attack_side_index, sens, round_index, output_state_index, row, column, 1] <= subkey_part[round_index, row, column]
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_key_not_to_1')
        
    def propagation_SB_values(self, part, attack_side_index, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        sens = int(input_state_index > output_state_index)

        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row_input, column_input, 0]
                                 + part[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1] <= 1
                                 for row_output in range(self.block_row_size//sbox_sizes[0])
                                 for column_output in range(self.block_column_size//sbox_sizes[1])
                                 for sbox_row in range(sbox_sizes[0])
                                 for sbox_column in range(sbox_sizes[1])
                                 for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                 for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                 name='value_propagation_SB_:_0_not_to_1')

    def propagation_values_NR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        if input_round_index < output_round_index:
            self.model.addConstrs((part[attack_side_index, 0, input_round_index, self.state_number-1, row, column, 0]
                                    + part[attack_side_index, 0, output_round_index, 0, row, column, 1] <= 1
                                      for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                    name='value_propagation_NR_:_0_not_to_1')
        else :
            self.everything_all_right = False
            print("Error in value_propagation_NR: input_round_index should be inferior from output_round_index")

    def propagation_values_PR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs((part[attack_side_index, 1, input_round_index, 0, row, column, 0]
                                + part[attack_side_index, 1, output_round_index, self.state_number-1, row, column, 1] <= 1
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='value_propagation_PR_:_0_not_to_1')

    #Propagation of DIFFERENCES through OPERATIONS
    def propagation_SR_differences(self, part, attack_side_index, round_index, input_state_index, output_state_index, shift_rows):
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                                == part[attack_side_index, sens, round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size, 1] 
                                for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                name = "differential propagation :_SR_1_not_to_1")
    
    def propagation_MC_differences(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index):
        sens = int(input_state_index > output_state_index)
        mc_index = round_index % len(self.matrixes[sens])
        
        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in self.column_range[sens][mc_index]:
                    if c_vector_element[column] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, column) + c_vector_element + (0,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_1_not_to_0")
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, column) + c_vector_element + (2,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_2")
                        
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MC[sens][round_index%(len(self.matrixes[0]))][column]:
                        or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"or_var_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        if len(combination) >= 1:
                            #Model the OR with linear constraint for efficiency
                            for element in combination :
                                self.model.addConstr(or_var >= XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(element)+(1,)])
                            self.model.addConstr(or_var <= gp.quicksum(XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(element)+(1,)] for element in combination), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        else :
                            self.model.addConstr(or_var == XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(combination[0])+(1,)])
                        or_vars.append(1-or_var)  
                #linear mode for the OR constraint
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 0] >= elements, name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 0]<= gp.quicksum(or_vars), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
    
    def propagation_MR_differences(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index):
        sens = int(input_state_index > output_state_index)
        mr_index = round_index % len(self.matrixes[sens])
        
        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in self.row_range[sens][mr_index]:
                    if c_vector_element[row] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, row) + c_vector_element + (0,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_1_not_to_0")
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, row) + c_vector_element + (2,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_2")

        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MR[sens][round_index%(len(self.matrixes[0]))][row]:
                        or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"or_var_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        if len(combination) >= 1:
                            #Model the OR with linear constraint for efficiency
                            for element in combination :
                                self.model.addConstr(or_var >= XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(element)+(1,)])
                            self.model.addConstr(or_var <= gp.quicksum(XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(element)+(1,)] for element in combination), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        else :
                            self.model.addConstr(or_var == XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(combination[0])+(1,)])
                        or_vars.append(1-or_var)  
                #linear mode for the OR constraint
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, row, 0] >= elements, name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, row, 0]<= gp.quicksum(or_vars), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
             
        
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MR[sens][round_index%(len(self.matrixes[0]))][column]:
                        or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"or_var_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        if len(combination) >= 1:
                            #Model the OR with linear constraint for efficiency
                            for element in combination :
                                self.model.addConstr(or_var >= XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(element)+(1,)])
                            self.model.addConstr(or_var <= gp.quicksum(XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(element)+(1,)] for element in combination), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        else :
                            self.model.addConstr(or_var == XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(combination[0])+(1,)])
                        or_vars.append(1-or_var)  
                #linear mode for the OR constraint
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 0] >= elements, name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 0]<= gp.quicksum(or_vars), name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

    def propagation_SB_differences(self, part, attack_side_index, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        sens = int(input_state_index > output_state_index)
        if round_index >= self.upper_part_first_round and round_index <= self.lower_part_last_round :
            self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row_input, column_input, 1]
                                    <= part[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1]
                                    for row_output in range(self.block_row_size//sbox_sizes[0])
                                    for column_output in range(self.block_column_size//sbox_sizes[1])
                                    for sbox_row in range(sbox_sizes[0])
                                    for sbox_column in range(sbox_sizes[1])
                                    for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                    for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                    name='value_propagation_SB_:_0_not_to_1')

        if (self.trunc_diff and (round_index == self.upper_part_last_round or round_index == self.lower_part_first_round)):
            pass
        else :
            self.model.addConstrs((part[attack_side_index, sens, round_index, output_state_index, row_input, column_input, 1] <=
                                    self.values[attack_side_index, not(sens), round_index, input_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1] + self.values[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 2]
                                    for row_output in range(self.block_row_size//sbox_sizes[0])
                                    for column_output in range(self.block_column_size//sbox_sizes[1])
                                    for sbox_row in range(sbox_sizes[0])
                                    for sbox_column in range(sbox_sizes[1])
                                    for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                    for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                    name='value_propagation_SB_:_0_not_to_1')
    
    def propagation_SB_differences_structure(self, part, attack_side_index, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        sens = int(input_state_index > output_state_index)
    
        self.model.addConstrs((part[attack_side_index, sens, round_index, output_state_index, row_input, column_input, 0]
                                >= part[attack_side_index, sens, round_index, input_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 0]
                                for row_output in range(self.block_row_size//sbox_sizes[0])
                                for column_output in range(self.block_column_size//sbox_sizes[1])
                                for sbox_row in range(sbox_sizes[0])
                                for sbox_column in range(sbox_sizes[1])
                                for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                name='value_propagation_SB_:_0_not_to_1')


        self.model.addConstrs((part[attack_side_index, sens, round_index, output_state_index, row_input, column_input, 1] <=
                                    self.values[attack_side_index, not(sens), round_index, input_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1] + self.values[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 2]
                                    for row_output in range(self.block_row_size//sbox_sizes[0])
                                    for column_output in range(self.block_column_size//sbox_sizes[1])
                                    for sbox_row in range(sbox_sizes[0])
                                    for sbox_column in range(sbox_sizes[1])
                                    for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                    for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                    name='value_propagation_SB_:_0_not_to_1')
        
    def propagation_differences_NR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        if input_round_index < output_round_index:
            self.model.addConstrs((part[attack_side_index, 0, input_round_index, self.state_number-1, row, column, 1]
                                    == part[attack_side_index, 0, output_round_index, 0, row, column, 1] 
                                      for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                    name='value_propagation_NR_:_0_not_to_1')
        else :
            self.everything_all_right = False
            print("Error in value_propagation_NR: input_round_index should be inferior from output_round_index")
        
    def propagation_differences_PR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs((part[attack_side_index, 1, input_round_index, 0, row, column, 1]
                                == part[attack_side_index, 1, output_round_index, self.state_number-1, row, column, 1]
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='value_propagation_PR_:_0_not_to_1')

    def free_propagation(self, part, attack_side_index, round_index, input_state_index, output_state_index):
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, output_state_index, row, column, 0] 
                               == part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), name="propagation_simple")
         
    #Propagation of values in rounds
    def forward_values_propagation(self, attack_side_index, first_round_index, last_round_index, subkey):
        condition = False
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR' and condition:
                    self.propagation_SR_values(self.values, attack_side_index, forward_round, state_index, state_index + 1, self.shift_rows)
                elif self.operation_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.values, self.XOR_in_mc_values, attack_side_index, forward_round, state_index, state_index + 1)
                elif self.operation_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.values, self.XOR_in_mr_values, attack_side_index, forward_round, state_index, state_index + 1)
                elif self.operation_order[state_index] == 'SB' and condition:
                    self.propagation_SB_values(self.values, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    if forward_round == first_round_index :
                        condition = True
                    if forward_round == last_round_index :
                        condition = False
                    self.propagation_AK(self.values, attack_side_index, subkey, forward_round, state_index, state_index + 1)
               #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.propagation_values_NR(self.values, attack_side_index, forward_round, forward_round+1)

    def backward_values_propagation(self, attack_side_index, first_round_index, last_round_index, subkey):
        condition = False
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR' and condition:
                    self.propagation_SR_values(self.values, attack_side_index, backward_round, state_index + 1, state_index, self.shift_rows_inverse)
                elif self.operation_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.values, self.XOR_in_mc_values, attack_side_index, backward_round, state_index + 1, state_index)
                elif self.operation_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.values, self.XOR_in_mr_values, attack_side_index, backward_round, state_index + 1, state_index)
                elif self.operation_order[state_index] == 'SB' and condition:
                    self.propagation_SB_values(self.values, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    if backward_round == first_round_index :
                        condition = True
                    if backward_round == last_round_index :
                        condition = False
                    self.propagation_AK(self.values, attack_side_index, subkey, backward_round, state_index + 1, state_index)
                #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.propagation_values_PR(self.values, attack_side_index, backward_round+1, backward_round)
    
    #Propagation of differences in upper and lower parts
    def forward_differences_propagation(self, attack_side_index, first_round_index, last_round_index):
        condition = False
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, forward_round, state_index, state_index + 1, self.shift_rows)
                elif self.operation_order[state_index] == 'MC' and condition:
                    self.propagation_MC_differences(self.differences, self.XOR_in_mc_differences, attack_side_index, forward_round, state_index, state_index + 1)
                elif self.operation_order[state_index] == 'MR' and condition:
                    self.propagation_MR_differences(self.differences, self.XOR_in_mr_differences, attack_side_index, forward_round, state_index, state_index + 1)
                elif self.operation_order[state_index] == 'SB':
                    if forward_round == first_round_index :
                        condition = True
                    if forward_round == last_round_index :
                        condition = False
                    self.propagation_SB_differences(self.differences, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK' and condition:
                    self.free_propagation(self.differences, attack_side_index, forward_round, state_index, state_index + 1)
               #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.propagation_differences_NR(self.differences, attack_side_index, forward_round, forward_round+1)
    
    def backward_differences_propagation(self, attack_side_index, first_round_index, last_round_index):
        condition = False
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, backward_round, state_index + 1, state_index, self.shift_rows_inverse)
                elif self.operation_order[state_index] == 'MC' and condition:
                    self.propagation_MC_differences(self.differences, self.XOR_in_mc_differences, attack_side_index, backward_round, state_index + 1, state_index)
                elif self.operation_order[state_index] == 'MR' and condition:
                    self.propagation_MR_differences(self.differences, self.XOR_in_mr_differences, attack_side_index, backward_round, state_index + 1, state_index)
                elif self.operation_order[state_index] == 'SB' :
                    if backward_round == first_round_index :
                        condition = True
                    if backward_round == last_round_index :
                        condition = False
                    self.propagation_SB_differences(self.differences, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK' and condition:
                    self.free_propagation(self.differences, attack_side_index, backward_round, state_index + 1, state_index)
                #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.propagation_differences_PR(self.differences, attack_side_index, backward_round+1, backward_round)
    
    #Propagation of differences in structure :
    def forward_differences_propagation_in_structure(self, attack_side_index, first_round_index, last_round_index):
        condition = False
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, forward_round, state_index, state_index + 1, self.shift_rows)
                elif self.operation_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.differences, self.XOR_in_mc_differences, attack_side_index, forward_round, state_index, state_index + 1)
                elif self.operation_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.differences, self.XOR_in_mr_differences, attack_side_index, forward_round, state_index, state_index + 1)
                elif self.operation_order[state_index] == 'SB' and condition:
                    self.propagation_SB_differences_structure(self.differences, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    if forward_round == first_round_index :
                        condition = True
                    if forward_round == last_round_index :
                        condition = False
                    self.free_propagation(self.differences, attack_side_index, forward_round, state_index, state_index + 1)
               #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.propagation_differences_NR(self.differences, attack_side_index, forward_round, forward_round+1)
    
    def backward_differences_propagation_in_structure(self, attack_side_index, first_round_index, last_round_index):
        condition = False
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, backward_round, state_index + 1, state_index, self.shift_rows_inverse)
                elif self.operation_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.differences, self.XOR_in_mc_differences, attack_side_index, backward_round, state_index + 1, state_index)
                elif self.operation_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.differences, self.XOR_in_mr_differences, attack_side_index, backward_round, state_index + 1, state_index)
                elif self.operation_order[state_index] == 'SB' and condition:
                    
                    self.propagation_SB_differences_structure(self.differences, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    if backward_round == first_round_index :
                        condition = True
                    if backward_round == last_round_index :
                        condition = False
                    self.free_propagation(self.differences, attack_side_index, backward_round, state_index + 1, state_index)
                #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.propagation_differences_PR(self.differences, attack_side_index, backward_round+1, backward_round)

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



