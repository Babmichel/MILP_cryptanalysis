# This file contains all the parameters for the MILP model and the display function
# fill it with your own parameters

attack_parameters = {
    "block_size" : , #int
    "key_size" : , #int

    "distinguisher_size" : , #int
    "distinguisher_probability" : , #float
    "distinguisher_active_input_bits" : [], #list left bit is considered 0
    "distinguisher_active_output_bits" : [], #list left bit is considered 0

    "structure_size" : , #int
    "upper_part_size" : , #int
    "lower_part_size" : , #int

    "first_branch_shift" : , #int
    "second_branch_shift" : , #int
    "third_branch_shift" : , #int

    "key_schedule_linearity" : , #boolean, 1 for a linear key schedule, 0 otherwise
    "state_test" : , #boolean, 1 to enable state test, 0 to block them
    "probabilistic_key_recovery" : , #boolean, 1 to enable probabilisitc key recovery, 0 to block them

    "pdf_display" : , #boolean, 1 to generate a pdf picture, 0 otherwise
    "pdf_name" : "" #str
}