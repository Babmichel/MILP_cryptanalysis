# Main function
# This function retrieve the different parameters of the attack, launch the MILP model then display the results

import gurobi_licence
import MILP_model_diff_MITM_Simonlike
import display
import pandas as pd

from parameters_folder import your_parameters as user_parameters

def main(parameters):
    """ Generate and solve model then display the result
    Parameters
    ----------
    parameters : file.
        The file that contains the parameters of your attack
    
    Return
    ------
    Display in terminal the optimal parameters and complexity of found by the model
    Generate a figure of the image in the folder "figures_folder" if ask in parameters file
    If the model is infeasible, generate a file 'model_infeasible.ilp' with the constraints generating the infeasibility
    """

    # This function run the MILP model with given parameters, the function write a file 'solution.csv' 
    # that contains the value of each MILP variable and its corresponding name
    feasibility = MILP_model_diff_MITM_Simonlike.differential_Meet_in_the_middle(parameters.attack_parameters, gurobi_licence.gurobi_licence)
    
    if feasibility :
        #Here we turn the csv file to a dictionnary that can be use in the display functions
        solution = pd.read_csv("solution.csv")
        solution = dict(zip(solution["Variable"], solution["Value"]))
        
        #display the complexity and parameters of the optimal solution
        display.parameters_display(parameters.attack_parameters, solution)

        if parameters.attack_parameters["pdf_display"] : #generate a pdf figure of the attack 
            display.pdf_display(parameters.attack_parameters, solution)

    else :
        print("The model is infeasible, please check you parameters file and the .ilp generate file")

main(user_parameters)
