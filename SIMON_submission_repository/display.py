#This file contains the display functions
import math
import matplotlib.pyplot as plt
from matplotlib.patches import *
from matplotlib.widgets import *

def parameters_display(parameters, solution):
        """Display the parameters of each part of the found attack and the linked complexities. 
        Parameters
        ----------
        parameters: file.
                The file that contains the parameters of your attack

        solution : file.
                The file that contains the dictionnary linking all the model varaibles to their optimal values
        
        Returns
        -------
        Disply is made in the terminal
        """
        print("--- UPPER part parameters ---")
        print("size :", parameters['upper_part_size'])
        print("key :", solution['key_quantity_up'])
        print("state test :", solution['state_test_up_quantity'])
        print("filtered state test :", solution['filtered_state_test_up'])
        print("proba key rec :", solution['probabilistic_key_recovery_up'])
        print('complexity =', solution['time_complexity_up'] + parameters['distinguisher_probability'])
        print("")
        print("--- LOWER part parameters ---")
        print("size :", parameters['lower_part_size'])
        print("key :", solution['key_quantity_down'])
        print("state test :", solution['state_test_down_quantity'])
        print("filtered state test :", solution['filtered_state_test_down'])
        print("proba key rec :", solution['probabilistic_key_recovery_down'])
        print('complexity :', solution['time_complexity_down'] + parameters["distinguisher_probability"])
        print("")
        print("--- MATCH and Structure parameters ---")
        print("structure_size :", parameters['structure_size'])
        print("fix number :", solution['structure_fix'])
        print("fix_on_first_round :", solution['structure_fix_first_round'])
        print("filtered differences :", solution['structure_match_differences'])
        if parameters["key_schedule_linearity"] == 1:
                print("key quantity :", solution['total_key_information'] + parameters['key_size'])
        if parameters["key_schedule_linearity"] == 0:
                print("key quantity :", solution['key_quantity_up'] + solution['key_quantity_down'] + solution['filtered_state_test_down'] + solution['filtered_state_test_up'] + solution['structure_match_differences'])
        print("complexite match :", solution['time_complexity_match'] + parameters["distinguisher_probability"])
        print("")
        print("number of rounds attacked :", parameters['structure_size'] + parameters['upper_part_size'] + parameters['lower_part_size'] + parameters['distinguisher_size'])
        print("Final time complexity :", math.log2(pow(2, solution['time_complexity_up'] + parameters["distinguisher_probability"]) + pow(2, solution['time_complexity_down'] + parameters["distinguisher_probability"]) + pow(2, solution['time_complexity_match'] + parameters["distinguisher_probability"])))
        print("Final memory complexity :", min(solution['key_quantity_up'] + solution['state_test_up_quantity'] + parameters['block_size'] - solution['structure_fix'], solution['key_quantity_down'] + solution['state_test_down_quantity'] + parameters['block_size'] - solution['structure_fix']))
        print("Final data complexity :", solution['data_complexity'])
        print("")


def pdf_display(parameters, solution):
        """Generate a pdf picture of the attack found by the model
        Parameters
        ----------
        parameters: file.
                The file that contains the parameters of your attack

        solution : file.
                The file that contains the dictionnary linking all the model varaibles to their optimal values
        
        Returns
        -------
        The picture is saved in the folder 'figures_folder' with the name given in the parameters file
        """
        mult = 1


        font_decallage = 4
        font_etat = 6
        font_legende = 8
        font_difference = 4
        font_text = 8
        dec_K=0

        state_size = int(parameters['block_size']/2)
        structure_size = parameters['structure_size']
  
        dec_up = parameters['first_branch_shift']
        dec_mid = parameters['second_branch_shift']
        dec_down = parameters['third_branch_shift']

        if 2*state_size == 48 :
                dec_K=0.25
                font_text = 10
        
        if 2*state_size == 64 :
                dec_K=0.5
                font_text = 12

        if 2*state_size == 128 :
                font_decallage = 2
                font_etat = 4
                font_legende = 6
                font_difference = 3
                font_text = 5.5

        plt.rcParams['lines.linewidth'] = 0.1
        plt.rcParams.update({'font.size': font_etat})

        r_up_max = structure_size + parameters['upper_part_size']
        r_up_min = structure_size

        r_down_max = parameters['lower_part_size']
        r_down_min = 0

        taille_distingueur = parameters['distinguisher_size']
        proba_distingueur = parameters['distinguisher_probability']

        if state_size <= 32: 
                state_draw = state_size
        else: 
                state_draw = state_size//2

        n_s = int(state_size//state_draw)
        
        x_min, x_max = -7*mult, (state_draw*2+0.1*(state_draw//4-1)+10+7)*mult
        y_min, y_max = min((r_up_max)*(-6*n_s-11)*mult, ((r_down_max)*(-6*n_s-11)-28)*mult), 1
        
        fig = plt.figure()
        draw = fig.add_subplot()
        draw.set_aspect('equal', adjustable='box')

        #Strucutre : 
        for r in range(0, structure_size):
                dec_r=(-1*r)*(-6*n_s-11)
                for k in range(4):
                        #trait haut gauche 
                        plt.plot([(-6)*mult, (-6)*mult],[(0-n_s/2 - dec_r)*mult,(-(5.75*n_s+5)-n_s/2 - dec_r)*mult], color="black")
                        plt.plot([(-6)*mult,( state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult,( -(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                        plt.plot([(-6)*mult,(-4)*mult], [(0-n_s/2-dec_r)*mult,(0-n_s/2-dec_r)*mult], color="black")
                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5- dec_r)*mult], color="black")
                        
                        #trait haut droit
                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+6)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (-(6.25*n_s+5) - dec_r)*mult], color="black")
                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-6+state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult, (-(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+4)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (0-n_s/2 - dec_r)*mult], color="black")
                        plt.plot([(-6+state_draw/2)*mult,(-6+state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-4-1 - dec_r)*mult], color="black")
                        
                        #text
                        plt.text((-5.5)*mult, (-n_s*2.4 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                        plt.text((-5.5)*mult, (-n_s*3.4-1 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)
                        plt.text((-5.5)*mult, (-n_s*4.4-2 - dec_r)*mult, f"<<< {dec_down}", fontname="serif", fontsize=font_decallage)

                        plt.text((state_draw+0.5-4)*mult, (-n_s/2-0.25 - dec_r)*mult, f"L{r}")
                        plt.text((state_draw+13-1.5)*mult, (-n_s/2-0.25 - dec_r)*mult, f"R{r}", fontname="serif")
                        plt.text((state_draw+7.5)*mult, (-3*n_s/2 - 1.5 - dec_r)*mult, f"K{r}", fontname="serif")


                        #decallage des premiers etats
                        if k==0 :
                                dec_start = 4
                        else : dec_start = 0

                        for j in range(state_size//state_draw):
                        
                                for i in range(state_draw):
                                        dec = 0
                
                                        #trait horizontaux millieu AND et XOR
                                        if j%n_s ==0 and k in [1, 3]:
                                                plt.plot([(state_draw)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                        if j%n_s ==0 and k in [3]:
                                                plt.plot([(state_draw+5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                        
                                        if j%n_s ==0 and k in [2]:
                                                plt.plot([(state_draw)*mult,(state_draw+4.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                plt.plot([(state_draw+5.5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")

                                        #trait verticaux
                                        if j%n_s ==0 and k in [1]:
                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-2*n_s-2+0.5 - dec_r)*mult], color="black")
                                        
                                        if j%n_s ==0 and k in [2]:
                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2-0.5 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1-0.5 - dec_r)*mult], color="black")

                                        #cercle XOR et AND
                                        if j%n_s ==0 and k in [2, 3]:
                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)
                                        
                                        if j%n_s ==0 and k in [2]:
                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.1)*mult, color = "black", linewidth = 0.1)
                                                draw.add_patch(circle)
                                        
                                        if j%n_s ==0 and k in [1, 2, 3]:
                                                #trait horizontaux gauche
                                                plt.plot([(-6)*mult,(0)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                #trait horizontaux droite
                                        if j%n_s ==0 and k in [1, 3]:
                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6+0.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                #cercle Xor droit
                                                circle = plt.Circle(((state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)

                                        #decalage tout les quatres etats
                                        if i%4 == 0 and i!=0:
                                                dec+=0.1
                                        #Couleur Carré 
                                        color_right = "white"
                                        color_left = "white"
                                        color="white"
                                        #Carre état
                                        if k==0:
                                                if solution[f'structure_left1_{r}_{j*state_draw+i}_0_2_1']==1:
                                                        color = "silver"
                                                elif solution[f'structure_left1_{r}_{j*state_draw+i}_1_2_1']==1:
                                                        color = "lightgreen"
                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square) 
                                                color="white"
                                                if solution[f'structure_right1_{r}_{j*state_draw+i}_0_2_1'] ==1:
                                                        color = "silver"
                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square)
                                        if k==1:
                                                if solution[f'structure_left1_{r}_{((j*state_draw+i)+dec_up)%state_size}_0_2_1'] ==1:
                                                        color = "silver"
                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square) 
                                                color="white"
                                                if solution[f'key_structure_{r}_{j*state_draw+i}_1']==1:
                                                        color="dodgerblue"
                                                if solution[f'key_structure_{r}_{j*state_draw+i}_2']==1:
                                                        color="red"
                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square)
                                        if k==2:
                                                if solution[f'structure_left1_{r}_{((j*state_draw+i)+1)%state_size}_0_2_1'] ==1:
                                                        color = "silver"
                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square) 
                                                color="white"
                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square)
                                        if k==3:
                                                if solution[f'structure_left1_{r}_{((j*state_draw+i)+2)%state_size}_0_2_1'] ==1:
                                                        color = "silver"
                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square) 
                                                color="white"
                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square)
                                                
                                

        #UPPER PART
        for r in range(r_up_min,r_up_max):
                dec_r = (-1*r)*(-6*n_s-11)
                for k in range(6):
                        #trait haut gauche 
                        plt.plot([(-6)*mult, (-6)*mult],[(0-n_s/2 - dec_r)*mult,(-(5.75*n_s+5)-n_s/2 - dec_r)*mult], color="black")
                        plt.plot([(-6)*mult,( state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult,( -(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                        plt.plot([(-6)*mult,(-4)*mult], [(0-n_s/2-dec_r)*mult,(0-n_s/2-dec_r)*mult], color="black")
                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5- dec_r)*mult], color="black")
                        
                        #trait haut droit
                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+6)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (-(6.25*n_s+5) - dec_r)*mult], color="black")
                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-6+state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult, (-(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+4)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (0-n_s/2 - dec_r)*mult], color="black")
                        plt.plot([(-6+state_draw/2)*mult,(-6+state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-4-1 - dec_r)*mult], color="black")
                        
                        #text
                        plt.text((-5.5)*mult, (-n_s*2.4-2 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                        plt.text((-5.5)*mult, (-n_s*4.4-4 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)
                        plt.text((-5.5)*mult, (-n_s*5.4-5 - dec_r)*mult, f"<<< {dec_down}", fontname="serif", fontsize=font_decallage)

                        if r!=r_up_min:
                                plt.text((state_draw+0.5)*mult, (-n_s*1.4-1 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                                plt.text((state_draw+0.5)*mult, (-n_s*3.4-3 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)

                        plt.text((state_draw+0.5-4)*mult, (-n_s/2-0.25 - dec_r)*mult, f"L{r}")
                        plt.text((state_draw+13-1)*mult, (-n_s/2-0.25 - dec_r)*mult, f"R{r}", fontname="serif")
                        if r!=r_up_min:
                                plt.text((2*state_draw+10.5+dec_K)*mult, (-5*n_s/2 - 2 -0.25 - dec_r)*mult, f"K'{r}", fontname="serif")


                        #decallage des premiers etats
                        if k==0 :
                                dec_start = 4
                        else : dec_start = 0

                        for j in range(state_size//state_draw):
                        
                                for i in range(state_draw):
                                        dec = 0
                                        #trait clé de gauche
                                        if j%n_s ==0 and k in [1, 3] and r!=r_up_min:
                                                #trait droite
                                                plt.plot([(state_draw)*mult,(state_draw+8)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                        
                                                #traits gauche et XOR
                                                plt.plot([(-2)*mult,0],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                plt.plot([(-2)*mult,(-2)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1.5 - dec_r)*mult], color="black")
                                                circle = plt.Circle(((-2)*mult, (-1*j-(n_s+1)*k-n_s/2-n_s-1 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)

                                        #trait millieu cle de droite
                                        if j%n_s ==0 and k in [2] and r!=r_up_min:
                                                plt.plot([(state_draw+8)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                plt.plot([(state_draw+8)*mult,(state_draw+8)*mult],[(-1*(j-1-n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*(j+1+n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                        
                                        #trait horizontaux millieu AND et XOR
                                        if j%n_s ==0 and k in [2, 5]:
                                                plt.plot([(state_draw)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                        if j%n_s ==0 and k in [5]:
                                                plt.plot([(state_draw+5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                        
                                        if j%n_s ==0 and k in [4]:
                                                plt.plot([(state_draw)*mult,(state_draw+4.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                plt.plot([(state_draw+5.5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")

                                        #trait verticaux
                                        if j%n_s ==0 and k in [2]:
                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-2*n_s-2+0.5 - dec_r)*mult], color="black")
                                        
                                        if j%n_s ==0 and k in [4]:
                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2-0.5 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1-0.5 - dec_r)*mult], color="black")

                                        #cercle XOR et AND
                                        if j%n_s ==0 and k in [4, 5]:
                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)
                                        
                                        if j%n_s ==0 and k in [4]:
                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.1)*mult, color = "black", linewidth = 0.1)
                                                draw.add_patch(circle)
                                        
                                        if j%n_s ==0 and k in [2, 4, 5]:
                                                #trait horizontaux gauche
                                                plt.plot([(-6)*mult,(0)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                #trait horizontaux droite
                                        if j%n_s ==0 and k in [5]:
                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6+0.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                #cercle Xor droit
                                                circle = plt.Circle(((state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)

                                        #decalage tout les quatres etats
                                        if i%4 == 0 and i!=0:
                                                dec+=0.1
                                        #Carre état
                                        color_right="white"
                                        color_left="white"
                                        diff_value="0"
                                        if r==r_up_min:
                                                color_right="lightcoral"
                                                color_left="lightcoral"
                                        else :
                                                if k == 0:
                                                        if r != r_up_min +1 :
                                                                if solution[f'up_left_state_{r-structure_size-2}_{j*state_draw+i}_1'] == 1:
                                                                        color_right="lightcoral"
                                                        else :
                                                                color_right="lightcoral"
                                                        if solution[f'up_left_state_{r-structure_size-1}_{j*state_draw+i}_1'] == 1:
                                                                color_left="lightcoral"

                                                if k == 1:
                                                        if solution[f'key_{r}_{(j*state_draw+i+dec_up)%state_size}_1'] == 1:
                                                                color_left="red"
                                                if k == 2:
                                                        if solution[f'up_left_state_up_{r-structure_size}_{j*state_draw+i}_1'] == 1:
                                                                color_left="lightcoral"
                                                        if solution[f'up_state_test_or_{r-structure_size}_{(j*state_draw+i+dec_up)%state_size}_1'] == 1:
                                                                if solution[f'up_left_equation_{r-structure_size}_{(j*state_draw+i+dec_up)%state_size}_2'] == 1:
                                                                        color_left="orange"
                                                                else :
                                                                        color_left="gold"
                                                        if solution[f'key_{r}_{j*state_draw+i}_1'] == 1:
                                                                color_right="red"
                                                if k == 3:
                                                        if solution[f'key_{r}_{(j*state_draw+i+dec_mid)%state_size}_1'] == 1:
                                                                color_left="red"
                                                if k == 4:
                                                        if solution[f'up_left_state_mid_{r-structure_size}_{j*state_draw+i}_1'] == 1:
                                                                color_left="lightcoral"
                                                        if solution[f'up_state_test_or_{r-structure_size}_{(j*state_draw+i+dec_mid)%state_size}_1'] == 1:
                                                                if solution[f'up_left_equation_{r-structure_size}_{(j*state_draw+i+dec_mid)%state_size}_2'] == 1:
                                                                        color_left="orange"
                                                                else :
                                                                        color_left="gold"
                                                        if solution[f'up_left_state_up_{r-structure_size}_{j*state_draw+i}_0'] == 0 and solution[f'up_left_state_mid_{r-structure_size}_{j*state_draw+i}_0']==0:
                                                                color_right="lightcoral"

                                                if k == 5:
                                                        if solution[f'up_left_state_down_{r-structure_size}_{j*state_draw+i}_1'] == 1:
                                                                color_left="lightcoral"
                                                        if solution[f'up_left_state_up_{r-structure_size}_{j*state_draw+i}_0'] == 0 and solution[f'up_left_state_mid_{r-structure_size}_{j*state_draw+i}_0']==0 and solution[f'up_left_state_down_{r-structure_size}_{j*state_draw+i}_0']==0:
                                                                color_right="lightcoral"
                                        if r!=r_up_min:
                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square)
                                                if k not in [1,3]:  
                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                        draw.add_patch(square)
                                        else :
                                                if k not in [1,3]: 
                                                        square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                        draw.add_patch(square)
                                                if k not in [1,2,3]:  
                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                        draw.add_patch(square)
                                        if k == 0:
                                                if solution[f'up_right_difference_{r-structure_size}_{j*state_draw+i}_1']==1:
                                                        diff_value="1"
                                                elif solution[f'up_right_difference_{r-structure_size}_{j*state_draw+i}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                                if solution[f'up_right_difference_XOR_{r-structure_size}_{j*state_draw+i}_1']==1:
                                                        diff_value="1"
                                                elif solution[f'up_right_difference_XOR_{r-structure_size}_{j*state_draw+i}_2']==1:
                                                        diff_value="?"
                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                        if k == 2:
                                                if solution[f'up_right_difference_{r-structure_size}_{(j*state_draw+i+dec_up)%state_size}_1']==1:
                                                        diff_value="1"
                                                elif solution[f'up_right_difference_{r-structure_size}_{(j*state_draw+i+dec_up)%state_size}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                        if k == 4:
                                                if solution[f'up_right_difference_{r-structure_size}_{(j*state_draw+i+dec_mid)%state_size}_1']==1:
                                                        diff_value="1"
                                                if solution[f'up_right_difference_{r-structure_size}_{(j*state_draw+i+dec_mid)%state_size}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                                if solution[f'up_left_difference_AND_{r-structure_size}_{j*state_draw+i}_1']==1:
                                                        diff_value="?"
                                                if solution[f'up_left_difference_AND_{r-structure_size}_{j*state_draw+i}_2']==1:
                                                        diff_value="P"
                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                        if k == 5:
                                                if solution[f'up_right_difference_{r-structure_size}_{(j*state_draw+i+dec_down)%state_size}_1']==1:
                                                        diff_value="1"
                                                if solution[f'up_right_difference_{r-structure_size}_{(j*state_draw+i+dec_down)%state_size}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                                if solution[f'up_left_difference_XOR_{r-structure_size}_{j*state_draw+i}_1']==1:
                                                        diff_value="1"
                                                if solution[f'up_left_difference_XOR_{r-structure_size}_{j*state_draw+i}_2']==1:
                                                        diff_value="?"
                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"

        #size control                                                      
        fig.set_size_inches(8.27, 11.27)
        #draw.set_aspect('equal')
        plt.axis("off")
        #plt.axis("equal")
        draw.set_xlim(x_min, x_max)
        draw.set_ylim(y_min, y_max)      
        fig.savefig(f'figures_folder/{parameters["pdf_name"]}_up.pdf', format='pdf',  bbox_inches='tight', dpi=300)

        fig = plt.figure()
        draw = fig.add_subplot()
        draw.set_aspect('equal', adjustable='box')

        #LOWER PART AND DISTINGUISHER
        dec_d = 0#10+state_draw*2+12+10
        square = Rectangle(((dec_d)*mult, 0), (state_draw*2+10)*mult, (-4)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)
        plt.text((dec_d+state_draw*0.5)*mult, -2.75*mult, f"{taille_distingueur}-rounds differential distinguisher", fontsize=font_text)
        plt.plot([(4 + dec_d)*mult, (4 + dec_d)*mult],[-4*mult,-6*mult], color="black")
        plt.plot([(4 + dec_d+1.5*state_draw+10+0.4)*mult, (4 + dec_d+1.5*state_draw+10+0.4)*mult],[-4*mult,-6*mult], color="black")
                
        for r in range(r_down_min,r_down_max):
                dec_r = (-1*r)*(-6*n_s-11)+6
                for k in range(6):
                        #trait haut gauche 
                        plt.plot([(-6 + dec_d)*mult, (-6 + dec_d)*mult],[(0-n_s/2 - dec_r)*mult,(-(5.75*n_s+5)-n_s/2 - dec_r)*mult], color="black")
                        plt.plot([(-6 + dec_d)*mult,(-4 + dec_d)*mult], [(0-n_s/2-dec_r)*mult,(0-n_s/2-dec_r)*mult], color="black")    
                        if r!=r_down_max-1:
                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2 + dec_d)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2 + dec_d)*mult], [(-(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5- dec_r)*mult], color="black")
                                plt.plot([(-6 + dec_d)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2 + dec_d)*mult],[(-(6.25*n_s+5) - dec_r)*mult,( -(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                        
                        #trait haut droit
                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+6 + dec_d)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6 + dec_d)*mult],[(0-n_s/2 - dec_r)*mult, (-(6.25*n_s+5) - dec_r)*mult], color="black")
                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+4 + dec_d)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6 + dec_d)*mult],[(0-n_s/2 - dec_r)*mult, (0-n_s/2 - dec_r)*mult], color="black")    
                        if r!=r_down_max-1:
                                plt.plot([(-6+state_draw/2 + dec_d)*mult,(-6+state_draw/2 + dec_d)*mult], [(-(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5 - dec_r)*mult], color="black")
                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6 + dec_d)*mult, (-6+state_draw/2 + dec_d)*mult],[(-(6.25*n_s+5) - dec_r)*mult, (-(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                        
                        #text
                        plt.text((-5.5 + dec_d)*mult, (-n_s*2.4-2 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                        plt.text((-5.5 + dec_d)*mult, (-n_s*4.4-4 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)
                        plt.text((-5.5 + dec_d)*mult, (-n_s*5.4-5 - dec_r)*mult, f"<<< {dec_down}", fontname="serif", fontsize=font_decallage)

                        if r!=r_down_max-1:
                                plt.text((state_draw+0.5 + dec_d)*mult, (-n_s*1.4-1 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                                plt.text((state_draw+0.5 + dec_d)*mult, (-n_s*3.4-3 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)

                        plt.text((state_draw+0.5-4 + dec_d)*mult, (-n_s/2-0.25 - dec_r)*mult, f"L{r+taille_distingueur+r_up_max}")
                        plt.text((state_draw+13-2 + dec_d)*mult, (-n_s/2-0.25 - dec_r)*mult, f"R{r+taille_distingueur+r_up_max}", fontname="serif")
                        if r!=r_down_max-1:
                                plt.text((2*state_draw+10.5 + dec_d+dec_K)*mult, (-5*n_s/2 - 2 -0.25 - dec_r)*mult, f"K'{r+taille_distingueur+r_up_max}", fontname="serif")


                        #decallage des premiers etats
                        if k==0 :
                                dec_start = 4
                        else : dec_start = 0

                        for j in range(state_size//state_draw):
                        
                                for i in range(state_draw):
                                        dec = 0
                                        #trait clé de gauche
                                        if j%n_s ==0 and k in [1, 3] and r!=r_down_max-1:
                                                #trait droite
                                                plt.plot([(state_draw + dec_d)*mult,(state_draw+8 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                
                                                #traits gauche et XOR
                                                plt.plot([(-2 + dec_d)*mult,(0 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                plt.plot([(-2 + dec_d)*mult,(-2 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1.5 - dec_r)*mult], color="black")
                                                circle = plt.Circle(((-2 + dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2-n_s-1 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)

                                        #trait millieu cle de droite
                                        if j%n_s ==0 and k in [2] and r!=r_down_max-1:
                                                plt.plot([(state_draw+8)*mult,(state_draw+10+0.1*(state_draw//4 -1) + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                plt.plot([(state_draw+8 + dec_d)*mult,(state_draw+8 + dec_d)*mult],[(-1*(j-1-n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*(j+1+n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                        
                                        #trait horizontaux millieu AND et XOR
                                        if j%n_s ==0 and k in [2, 5]:
                                                plt.plot([(state_draw + dec_d)*mult,(state_draw+5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                        if j%n_s ==0 and k in [5]:
                                                plt.plot([(state_draw+5 + dec_d)*mult,(state_draw+10+0.1*(state_draw//4 -1) + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                        
                                        if j%n_s ==0 and k in [4]:
                                                plt.plot([(state_draw + dec_d)*mult,(state_draw+4.5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                plt.plot([(state_draw+5.5 + dec_d)*mult,(state_draw+10+0.1*(state_draw//4 -1) + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")

                                        #trait verticaux
                                        if j%n_s ==0 and k in [2]:
                                                plt.plot([(state_draw+5 + dec_d)*mult,(state_draw+5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-2*n_s-2+0.5 - dec_r)*mult], color="black")
                                        
                                        if j%n_s ==0 and k in [4]:
                                                plt.plot([(state_draw+5 + dec_d)*mult,(state_draw+5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2-0.5 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1-0.5 - dec_r)*mult], color="black")

                                        #cercle XOR et AND
                                        if j%n_s ==0 and k in [4, 5]:
                                                circle = plt.Circle(((state_draw+5 + dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)
                                        
                                        if j%n_s ==0 and k in [4]:
                                                circle = plt.Circle(((state_draw+5 + dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.1)*mult, color = "black", linewidth = 0.1)
                                                draw.add_patch(circle)
                                        
                                        if j%n_s ==0 and k in [2, 4, 5]:
                                        #trait horizontaux gauche
                                                plt.plot([(-6 + dec_d)*mult,(0 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                        #trait horizontaux droite
                                        if j%n_s ==0 and k in [5]:
                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10 + dec_d)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6+0.5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                #cercle Xor droit
                                                circle = plt.Circle(((state_draw*2+0.1*(state_draw//4 -1)+10+6+dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                draw.add_patch(circle)
                                        
                                        #decalage tout les quatres etats
                                        if i%4 == 0 and i!=0:
                                                dec+=0.1
                                        #Carre état
                                        color_right="white"
                                        color_left="white"
                                        diff_value="0"
                                        if r==r_down_max-1:
                                                color_right="lightskyblue"
                                                color_left="lightskyblue"
                                        else :
                                                if k == 0 and r!=r_down_max-1:
                                                        if solution[f'down_right_state_{r}_{j*state_draw+i}_1'] == 1:
                                                                color_right="lightskyblue"
                                                        if r!= r_down_max-1:
                                                                if solution[f'down_right_state_{r+1}_{j*state_draw+i}_1'] == 1:
                                                                        color_left="lightskyblue"
                                                        else :
                                                                color_left="lightskyblue"
                                                if k == 1:
                                                        if solution[f'key_{r+taille_distingueur+r_up_max}_{(j*state_draw+i+dec_up)%state_size}_1'] == 1:
                                                                color_left="dodgerblue"
                                                if k == 2:
                                                        if solution[f'down_left_state_up_{r}_{j*state_draw+i}_1'] == 1:
                                                                color_left="lightskyblue"
                                                        if solution[f'down_state_test_or_{r}_{(j*state_draw+i+dec_up)%state_size}_1'] == 1:
                                                                if solution[f'down_right_equation_{r}_{(j*state_draw+i+dec_up)%state_size}_2']==1:
                                                                        color_left="mediumturquoise"
                                                                else :
                                                                        color_left="aquamarine"
                                                        if solution[f'key_{r+taille_distingueur+r_up_max}_{j*state_draw+i}_1'] == 1:
                                                                color_right="dodgerblue"
                                                if k == 3:
                                                        if solution[f'key_{r+taille_distingueur+r_up_max}_{(j*state_draw+i+dec_mid)%state_size}_1'] == 1:
                                                                color_left="dodgerblue"
                                                if k == 4:
                                                        if solution[f'down_left_state_mid_{r}_{j*state_draw+i}_1'] == 1:
                                                                color_left="lightskyblue"
                                                        if solution[f'down_state_test_or_{r}_{(j*state_draw+i+dec_mid)%state_size}_1'] == 1:
                                                                if solution[f'down_right_equation_{r}_{(j*state_draw+i+dec_mid)%state_size}_2']==1:
                                                                        color_left="mediumturquoise"
                                                                else :
                                                                        color_left="aquamarine"
                                                        if solution[f'down_left_state_up_{r}_{j*state_draw+i}_0'] == 0 and solution[f'down_left_state_mid_{r}_{j*state_draw+i}_0']==0:
                                                                color_right="lightskyblue"

                                                if k == 5:
                                                        if solution[f'down_left_state_down_{r}_{j*state_draw+i}_1'] == 1:
                                                                color_left="lightskyblue"
                                                        if solution[f'down_left_state_up_{r}_{j*state_draw+i}_0'] == 0 and solution[f'down_left_state_mid_{r}_{j*state_draw+i}_0']==0 and solution[f'down_left_state_down_{r}_{j*state_draw+i}_0']==0:
                                                                color_right="lightskyblue"
                                        if r!=r_down_max-1:
                                                square = Rectangle(((i+dec-dec_start + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                draw.add_patch(square)
                                                if k not in [1,3]:  
                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                        draw.add_patch(square)
                                        else :
                                                if k not in [1,3]: 
                                                        square = Rectangle(((i+dec-dec_start + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                        draw.add_patch(square)
                                                if k not in [1,2,3]:  
                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                        draw.add_patch(square)
                                        if k == 0:
                                                if solution[f'down_left_difference_{r}_{j*state_draw+i}_1']==1:
                                                        diff_value="1"
                                                if solution[f'down_left_difference_{r}_{j*state_draw+i}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                                if solution[f'down_right_difference_{r}_{j*state_draw+i}_1']==1:
                                                        diff_value="1"
                                                if solution[f'down_right_difference_{r}_{j*state_draw+i}_2']==1:
                                                        diff_value="?"
                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                        if k == 2:
                                                if solution[f'down_left_difference_{r}_{(j*state_draw+i+dec_up)%state_size}_1']==1:
                                                        diff_value="1"
                                                if solution[f'down_left_difference_{r}_{(j*state_draw+i+dec_up)%state_size}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                        if k == 4:
                                                if solution[f'down_left_difference_{r}_{(j*state_draw+i+dec_mid)%state_size}_1']==1:
                                                        diff_value="1"
                                                if solution[f'down_left_difference_{r}_{(j*state_draw+i+dec_mid)%state_size}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                                if solution[f'down_left_difference_AND_{r}_{j*state_draw+i}_1']==1:
                                                        diff_value="?"
                                                if solution[f'down_left_difference_AND_{r}_{j*state_draw+i}_2']==1:
                                                        diff_value="P"
                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                        if k == 5:
                                                if solution[f'down_left_difference_{r}_{(j*state_draw+i+dec_down)%state_size}_1']==1:
                                                        diff_value="1"
                                                if solution[f'down_left_difference_{r}_{(j*state_draw+i+dec_down)%state_size}_2']==1:
                                                        diff_value="?"
                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                diff_value="0"
                                                if solution[f'down_left_difference_XOR_{r}_{j*state_draw+i}_1']==1:
                                                        diff_value="1"
                                                if solution[f'down_left_difference_XOR_{r}_{j*state_draw+i}_2']==1:
                                                        diff_value="?"
                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
        #Légende
        dec_d=dec_d-6
        #upper state
        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-6)*mult), (1)*mult, (1)*mult, facecolor="red", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)               
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-6)*mult, ": This key bit is guessed by the upper part of the attack", fontname="serif", fontsize=font_legende)

        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-8)*mult), (1)*mult, (1)*mult, facecolor="lightcoral", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)               
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-8)*mult, ": This state bit can be computed by the upper part of the attack", fontname="serif", fontsize=font_legende)

        if solution[f'state_test_up_quantity'] != 0:
                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-10)*mult), (1)*mult, (1)*mult, facecolor="gold", edgecolor = "black", linewidth=0.1)
                draw.add_patch(square)               
                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-10)*mult, ": This state bit is guessed by the upper part of the attack,", fontname="serif", fontsize=font_legende)
                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-12)*mult, "  it is used to sieve the candidates during the match", fontname="serif", fontsize=font_legende)
                
                if solution[f'state_test_up_quantity'] != solution[f'filtered_state_test_up'] :
                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-14)*mult), (1)*mult, (1)*mult, facecolor="orange", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-14)*mult, ": This state bit is guessed by the upper part of the attack,", fontname="serif", fontsize=font_legende)
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-16)*mult, "  it cannot be used in the match because of it's non linearity", fontname="serif", fontsize=font_legende)

        #lower state
        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-18)*mult), (1)*mult, (1)*mult, facecolor="dodgerblue", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)               
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-18)*mult, ": This key bit is guessed by the lower part of the attack", fontname="serif", fontsize=font_legende)

        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-20)*mult), (1)*mult, (1)*mult, facecolor="lightskyblue", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)               
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-20)*mult, ": This state bit can be computed by the lower part of the attack", fontname="serif", fontsize=font_legende)

        if solution[f'state_test_down_quantity'] != 0:
                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-22)*mult), (1)*mult, (1)*mult, facecolor="aquamarine", edgecolor = "black", linewidth=0.1)
                draw.add_patch(square)               
                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-22)*mult, ": This state bit is guessed by the lower part of the attack,", fontname="serif", fontsize=font_legende)
                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-24)*mult, "  it is used to sieve the candidates during the match", fontname="serif", fontsize=font_legende)
                
                if solution[f'state_test_down_quantity'] != solution[f'filtered_state_test_down'] :
                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-26)*mult), (1)*mult, (1)*mult, facecolor="deepskyblue", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-26)*mult, ": This state bit is guessed by the lower part of the attack", fontname="serif", fontsize=font_legende)
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-28)*mult, "  it cannot be used in the match because of it's non linearity", fontname="serif", fontsize=font_legende)
                
        #differences
        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-30)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square) 
        plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-30+0.2)*mult, "0", fontname="serif", fontsize=font_difference)              
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-30)*mult, ": The difference on this bit is 0", fontname="serif", fontsize=font_legende)

        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-32)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)               
        plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-32+0.2)*mult, "1", fontname="serif", fontsize=font_difference)              
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-32)*mult, ": The difference on this bit is 1", fontname="serif", fontsize=font_legende)

        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-34)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)               
        plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-34+0.2)*mult, "?", fontname="serif", fontsize=font_difference)              
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-34)*mult, ": The difference on this bit can be 0 or 1", fontname="serif", fontsize=font_legende)
        
        if solution[f'probabilistic_key_recovery_down'] + solution[f'probabilistic_key_recovery_up'] !=0 :
                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-36)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
                draw.add_patch(square)               
                plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-36+0.2)*mult, "P", fontname="serif", fontsize=font_difference)              
                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-36)*mult, ": The difference on this bit is considered 0 by probabilist propagation", fontname="serif", fontsize=font_legende)
        
        #structure
        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-38)*mult), (1)*mult, (1)*mult, facecolor="lightgreen", edgecolor = "black", linewidth=0.1)
        draw.add_patch(square)               
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-38)*mult, ": The difference on this bit can be computed by the upper", fontname="serif", fontsize=font_legende)
        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-40)*mult, "  and lower part of the attack", fontname="serif", fontsize=font_legende)
        
        if solution[f'structure_fix'] != 0:
                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-42)*mult), (1)*mult, (1)*mult, facecolor="silver", edgecolor = "black", linewidth=0.1)
                draw.add_patch(square)               
                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-42)*mult, ": The value of this bit is fix", fontname="serif", fontsize=font_legende)
        

        #size control                                                      
        fig.set_size_inches(8.27, 11.27)
        plt.axis("off")
        #plt.axis("equal")
        draw.set_xlim(x_min, x_max)
        draw.set_ylim(y_min, y_max)
        fig.savefig(f'figures_folder/{parameters["pdf_name"]}_down.pdf', format='pdf',  bbox_inches='tight', dpi=300)
