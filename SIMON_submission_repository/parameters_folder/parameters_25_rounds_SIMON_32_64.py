# This file contains all the parameters for the MILP model and the display function
# that are used to find the attack against 25 rounds of SIMON 32-64

attack_parameters = {
    "block_size" :32,
    "key_size" : 64, 

    "distinguisher_size" : 14,
    "distinguisher_probability" : 30.81, 
    "distinguisher_active_input_bits" : [28],
    "distinguisher_active_output_bits" : [4],

    "structure_size" : 3,
    "upper_part_size" : 4,
    "lower_part_size" : 4,
    
    "first_branch_shift" : 8,
    "second_branch_shift" : 1, 
    "third_branch_shift" : 2,

    "key_schedule_linearity" : 1,
    "state_test" : 1,
    "probabilistic_key_recovery" : 1,

    "pdf_display" : 0,
    "pdf_name" : "25_rounds_SIMON_32-64"
}
