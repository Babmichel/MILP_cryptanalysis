attack_parameters = {
    #Cipher parameters
    "Cipher": "GIFT",
    "Key_schedule": "GIFT",
    "attack_type": "Diff-MITM",

    #Attack sizes
    "structure_rounds": 5,
    "upper_rounds": 3,
    "lower_rounds": 2,

    #Distinguisher parameters
    "distinguisher_probability" : 53.82,
    "distinguisher_rounds" : 13, 
    "key_space_size": 124,
    "distinguisher_inputs" : [[0, 54], [0, 62]],
    "distinguisher_outputs": [[0, 31], [0, 29], [0, 63], [0, 61]],

    #Use exponential complexity(can turn the search to impossible)
    "optimal_complexity": False,

    #Attack parameters
    "truncated_differential" : False,
    "state_test_use": False,

    #Upper bound parameters
    "use_upper_bound" : False,
    "known_upper_bound" : 64,

    #Specific Solution search
    "specific_solution_search" : True,
    "solution_value" : 64
}