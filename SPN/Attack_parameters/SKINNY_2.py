attack_parameters = {
    #Cipher parameters
    "Cipher": "SKINNY",
    "Key_schedule": "SKINNY",
    "attack_type": "Diff-MITM",
    "structure_position": "lower",

    #Attack sizes
    "structure_rounds": 7,
    "upper_rounds": 7,
    "lower_rounds": 7,

    #Distinguisher parameters
    "distinguisher_probability" : 1,
    "distinguisher_rounds" : 2,
    "key_space_size": 192,
    "distinguisher_inputs" : [[3, 3]],
    "distinguisher_outputs": [[0, 3], [1, 3], [3, 3]],

    #Use exponential complexity(can turn the search to impossible)
    "optimal_complexity": False,

    #Attack parameters
    "truncated_differential" : True,
    "state_test_use": True,
    "filter_state_test": True,

    #Upper bound parameters
    "use_upper_bound" : False,
    "known_upper_bound" : 64,

    #Specific Solution search
    "specific_solution_search" : False,
    "solution_value" : 64,

    #Filter extra key guess
    "filter_extra_key_guess" : False,

    #specific key filtering
    "specific_key_filtering" : True,
}
