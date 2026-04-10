attack_parameters = {
    #Cipher parameters
    "Cipher": "GIFT",
    "Key_schedule": "GIFT",
    "attack_type": "Diff-MITM",
    "structure_position": "upper",

    #Attack sizes
    "structure_rounds": 2,
    "upper_rounds": 3,
    "lower_rounds": 3,

    #Distinguisher parameters
    "distinguisher_probability" : 58,
    "distinguisher_rounds" : 18,
    "key_space_size": 120,
    "distinguisher_inputs" : [[0, 17], [0, 18], [0, 53], [0, 54]],
    "distinguisher_outputs": [[0, 3], [0, 5], [0, 33], [0, 39]],

    #Use exponential complexity(can turn the search to impossible)
    "optimal_complexity": True,

    #Attack parameters
    "truncated_differential" : False,
    "state_test_use": False,
    "filter_state_test": False,

    #Upper bound parameters
    "use_upper_bound" : False,
    "known_upper_bound" : 64,

    #Specific Solution search
    "specific_solution_search" : False,
    "solution_value" : 64,

    #Filter extra key guess
    "filter_extra_key_guess" : False,

    #specific key filtering
    "specific_key_filtering" : False,
}
