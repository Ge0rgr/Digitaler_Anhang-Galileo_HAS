import sys
import tools, graphs_autotopo, graphs_normal_height, stopgo_precision, precision, graphs_normal_horizontal

#
#
# Zur Erstellung der skripte wurde KI unterstützend verwendet
#
#

def main():

    input_base = "G:\\(0)_Bachelorarbeit\\Bachelor_HAS_Skripte\\Inputs\\"
    save_base = "G:\\(0)_Bachelorarbeit\\Bachelor_HAS_Skripte\\Outputs\\"


    while True: 

        print(
            "[1] excelTimePDop,\n" \
            "[2] excelAvailability,\n" \
            "[3] varianceName, \n" \
            "[4] completeAvailability, \n" \
            "[5] autotopo_heightGraphs_HAS_SAPOS_DGM, \n" \
            "[6] normal_heightGraphs_HAS_SAPOS_DGM, \n" \
            "[7] normal_horizontalGraphs_HAS_SAPOS, \n" \
            "[8] precision_evaluation, \n" \
            "[9] stopgo_precision_evaluation"
            #"[998] tableSplit, \n" \
            #"[999] covarianceAnalysis, \n" \
        )

        step = input("Welchen Arbeitsschritt?: ")

        try: 
            test = int(step)

        except: 
            print("\nBeende Programm",end="")
            tools.threedots()
            sys.exit()

        match step:

            case "1":
                input_data = input_base + "1_Input_excelTimePDop"
                save_location = save_base + "1_Output_excelTimePDop" 

                tools.foldercheck(input_data,save_location)

                tools.excelTimePDop(input_data,save_location)

                sys.exit()


            case "2":
                input_data = input_base + "2_Input_excelAvailability"
                save_location = save_base + "2_Output_excelAvailability"

                tools.foldercheck(input_data,save_location)

                tools.excelAvailability(input_data,save_location)

                sys.exit()

            case "3":

                input_data = input_base + "3_Input_varianceName"
                save_location = save_base + "3_Output_varianceName" 

                tools.foldercheck(input_data,save_location)

                tools.varianceName(input_data,save_location)

                sys.exit()

            case "4": # a, weil es ein Endprodukt ist. Diese Daten werden Visualisiert
                input_data = input_base + "a_Input_completeAvailability"
                save_location = save_base + "a_Output_completeAvailability" 

                tools.foldercheck(input_data,save_location)

                tools.completeAvailability(input_data,save_location)

                sys.exit()


            
            case "5":
                input_data = input_base + "b_Input_autotopo_heightGraphs_HAS_DGM"
                save_location = save_base + "b_Output_autotopo_heightGraphs_HAS_DGM"

                tools.foldercheck(input_data,save_location)

                graphs_autotopo.autotopo_heightGraphs_HAS_DGM(input_data,save_location)

                sys.exit()


            case "6":
                input_data = input_base + "c_Input_normal_heightGraphs_HAS_SAPOS_DGM"
                save_location = save_base + "c_Output_normal_heightGraphs_HAS_SAPOS_DGM"

                tools.foldercheck(input_data,save_location)

                graphs_normal_height.normal_heightGraphs_HAS_SAPOS_DGM(input_data,save_location)

                sys.exit()

            case "7":
                input_data = input_base + "d_Input_normal_horizontalGraphs_HAS_SAPOS"
                save_location = save_base + "d_Output_normal_horizontalGraphs_HAS_SAPOS"

                tools.foldercheck(input_data,save_location)
                
                graphs_normal_horizontal.normal_horizontalGraphs_HAS_SAPOS(input_data,save_location)

                sys.exit()

            case "8":
                input_data = input_base + "e_Input_precision_evaluation"
                save_location = save_base + "e_Output_precision_evaluation"

                tools.foldercheck(input_data,save_location)

                precision.precision_evaluation(input_data,save_location)
                
                sys.exit()

            case "9":
                input_data = input_base + "f_Input_stopgo_precision_evaluation"
                save_location = save_base + "f_Output_stopgo_precision_evaluation"

                tools.foldercheck(input_data,save_location)
                
                stopgo_precision.stopgo_precision_evaluation(input_data,save_location)

                sys.exit()



#### Ungenutzte Funktionen
                '''
            case "998":
                input_data = input_base + "998_Input_tableSplit"
                save_location = save_base + "998_Output_tableSplit"

                tools.foldercheck(input_data,save_location)

                tools.tableSplit(input_data,save_location)

            case "999":
                input_data = input_base + "999_Input_covarianceAnalysis"
                save_location = save_base + "999_Output_covarianceAnalysis"

                tools.foldercheck(input_data,save_location)

                tools.covarianceAnalysis(input_data,save_location)
                '''

if __name__ == "__main__":
    main()