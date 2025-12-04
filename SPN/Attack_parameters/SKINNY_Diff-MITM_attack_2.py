attack_parameters = {
    "Cipher": "SKINNY",
    "Key_schedule": "SKINNY",
    "attack_type": "Diff-MITM",
    "structure_rounds": 3,
    "upper_rounds": 5,
    "lower_rounds": 5,
    "distinguisher_probability" : 52,
    "distinguisher_rounds" : 13, 
    "distinguisher_inputs" : [[0, 3], [3, 0]],
    "distinguisher_outputs": [[0, 2], [2, 1], [2, 2], [3, 2]],
    "optimal_complexity": False,
    "truncated_differential" : False
}