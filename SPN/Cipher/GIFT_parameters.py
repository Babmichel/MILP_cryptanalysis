cipher_parameters = {
    #cipher parameters
    "Cipher_name": 'GIFT',

    #block parameters
    "block_size": 64,
    "column_size": 64,
    "row_size": 1,

    #key parameters
    "key_size": 128,
    "key_column_size": 64,
    "key_row_size": 1,

    #Round function parameters
    "operation_order": ['AK', 'SB', 'PB'],
    "permutations": [[48, 1, 18, 35, 32, 49, 2, 19, 16, 33, 50, 3, 0, 17, 34, 51, 52, 5, 22, 39, 36, 53, 6, 23, 20, 37, 54, 7, 4, 21, 38, 55, 56, 9, 26, 43, 40, 57, 10, 27, 24, 41, 58, 11, 8, 25, 42, 59, 60, 13, 30, 47, 44, 61, 14, 31, 28, 45, 62, 15, 12, 29, 46, 63]],
    "sbox_sizes": [1,4]
}    