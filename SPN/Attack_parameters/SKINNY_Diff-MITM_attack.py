attack_parameters = {
    "Cipher": "SKINNY",
    "Key_schedule": "SKINNY",
    "attack_type": "Diff-MITM",
    "structure_rounds": 2,
    "upper_rounds": 5,
    "lower_rounds": 5,
    "distinguisher_probability" : 52,
    "distinguisher_rounds" : 11, 
    "distinguisher_inputs" : [[1, 2], [2, 1], [3, 0]],
    "distinguisher_outputs": [[0, 1], [1, 1], [2, 1], [3, 1]],
    "optimal_complexity": False
}