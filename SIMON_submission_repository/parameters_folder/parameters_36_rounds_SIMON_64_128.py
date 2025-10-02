# This file contains all the parameters for the MILP model and the display function
# that are used to find the attack against 36 rounds of SIMON 64-128

attack_parameters = {
    "block_size" :64,
    "key_size" : 128, 

    "distinguisher_size" : 23,
    "distinguisher_probability" : 61.5, 
    "distinguisher_active_input_bits" : [0, 4, 38],
    "distinguisher_active_output_bits" : [6, 32, 36],

    "structure_size" : 3,
    "upper_part_size" : 5,
    "lower_part_size" : 5,
    
    "first_branch_shift" : 8,
    "second_branch_shift" : 1, 
    "third_branch_shift" : 2,

    "key_schedule_linearity" : 1,
    "state_test" : 1,
    "probabilistic_key_recovery" : 1,

    "pdf_display" : 1,
    "pdf_name" : "36_rounds_SIMON_64-128"
}
