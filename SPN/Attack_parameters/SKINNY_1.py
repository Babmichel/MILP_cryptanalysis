attack_parameters = {
    "Cipher": "SKINNY",
    "Key_schedule": "SKINNY",
    "attack_type": "Diff-MITM",
    "structure_rounds": 3,
    "upper_rounds": 6,
    "lower_rounds": 6,
    "distinguisher_probability" : 52,
    "distinguisher_rounds" : 9, 
    "key_space_size": 192,
    "distinguisher_inputs" : [[3, 3]],
    "distinguisher_outputs": [[0, 1], [1, 0]],
    "optimal_complexity": False,
    "truncated_differential" : True,
    "filter_state_test": True
}