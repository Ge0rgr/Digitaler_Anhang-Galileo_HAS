from matplotlib.table import table
import plotly.graph_objects as gr_obj
import pandas as pd
import numpy as np
import os #Zum erstellen von Ordnern
import glob
import tools

#
#
# Zur Erstellung der skripte wurde KI unterstützend verwendet
#
#

# Analyse der Präzision der StopGo Messungen (Max. Distanz der Punkte innerhalb einer Messposition). Erstellung von einem Perzentilplot, einem Boxplot und Tabellen
def stopgo_precision_evaluation(input_data, save_location):

    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    stopgo_result = []

    for file in files:

        filename = os.path.splitext(os.path.basename(file))[0]

        if  "bitburg" in filename:
            continue;

        table = pd.read_csv(file, sep =";", decimal=",")


        positions = table.groupby("Messposition")


############################################## StopGo Präzison bzw. Abstände zueinander #################################################################

        for measured_pos, sections in positions:

            sections = sections.sort_values("Durchgang")

            coord = sections[["East","North"]].to_numpy()

            dist_1_2 = np.sqrt((coord[0,0]-coord[1,0]) ** 2 + (coord[0,1]-coord[1,1]) ** 2)

            dist_1_3 = np.sqrt((coord[0,0]-coord[2,0]) ** 2 + (coord[0,1]-coord[2,1]) ** 2)

            dist_2_3 = np.sqrt((coord[1,0]-coord[2,0]) ** 2 + (coord[1,1]-coord[2,1]) ** 2)

            dist_1_2_cm = dist_1_2 *100
            dist_1_3_cm = dist_1_3 *100
            dist_2_3_cm = dist_2_3 *100

            max_dist_cm = max(dist_1_2_cm,dist_1_3_cm,dist_2_3_cm) 

            if filename.startswith("feldweg"):
                szenario = "Feldweg"

            elif filename.startswith("parkplatz"):
                szenario = "Parkplatz"

            elif filename.startswith("gruenflaeche"):
                szenario = "Grünfläche mit Seedpoint"

            elif filename.startswith("forst"):
                szenario = "Forst mit Seedpoint"

            elif filename.startswith("wein_drohne"):
                szenario = "Weinberg"


            if max_dist_cm == dist_1_2_cm:
                max_points = "Durchgang 1 und 2"

            elif max_dist_cm == dist_1_3_cm:
                max_points = "Durchgang 1 und 3"

            else:
                max_points = "Durchgang 2 und 3"

            stopgo_result.append(
                {
                "Szenario": szenario,
                "Messposition": measured_pos,
                "Distanz 1 zu 2 [cm]": dist_1_2_cm,
                "Distanz 1 zu 3 [cm]": dist_1_3_cm,
                "Distanz 2 zu 3 [cm]": dist_2_3_cm,
                "Maximale Distanz [cm]": max_dist_cm,
                "Maximale_Punktkombination": max_points
                }
            )

    
    stopgo_result = pd.DataFrame(stopgo_result)

    save_path = os.path.join(save_location, "StopGo_Punktabstände.csv")

    stopgo_result.to_csv(save_path, sep=";", decimal=",", index=False)



########################################## StopGo Boxplots ######################################################################################################

    szenario_farben = {
        "Parkplatz": "rgba(194,144,15, 1)",
        "Feldweg": "rgba(65,194,15,1)",
        "Weinberg": "rgba(0,90,156,1)",
        "Forst mit Seedpoint": "rgba(0,135,90,1)",
        "Grünfläche mit Seedpoint": "rgba(204,121,167,1)"
    }

    fig_box = gr_obj.Figure()

    for szenario in stopgo_result["Szenario"].unique():

        section = stopgo_result.loc[stopgo_result["Szenario"] == szenario]

        fig_box.add_trace(
            gr_obj.Box(
                y = section["Maximale Distanz [cm]"],
                name= szenario,
                boxpoints="all",
                boxmean = True,
                jitter=0.3,
                pointpos=0,
                marker_color=szenario_farben.get(szenario), 
                customdata = np.column_stack([section["Messposition"],section["Maximale_Punktkombination"]]),
                hovertemplate=("Messposition: %{customdata[0]}<br>Maximale Distanz zwischen: %{customdata[1]}<br>Maximale Punktspanne: %{y:.2f} cm <extra></extra>")
            )
        )

        fig_box.update_layout(
            title= "Maximale horizontale Punktspanne innerhalb der StopGo Messungen",
            xaxis_title = "Messszenario",
            yaxis_title = "Maximale Distanz [cm]",
            template = "plotly_white"
        )

        
    save_path = os.path.join(save_location, "StopGo_Boxplots")

    fig_box.write_html(save_path + ".html")
    fig_box.write_image(save_path + ".png", width=1400, height=700)




    ########################################## StopGo Linienplot + Tabellenwerte, Häufigkeit ###########################################################################################
    

    fig_akkum_stopgo = gr_obj.Figure()

    table_stopgo_rows = []

    for szenario in stopgo_result["Szenario"].unique():

        section = stopgo_result.loc[stopgo_result["Szenario"] == szenario]

        sorted_dist = np.sort(section["Maximale Distanz [cm]"].to_numpy())

        cumulative_percentage = (np.arange(1, len(sorted_dist) + 1)/ len(sorted_dist)* 100)

        count_val = len(sorted_dist)

        empir_95 = int(np.ceil(0.95 * count_val)) - 1

        p95 = sorted_dist[empir_95]

        prop_p95 = (np.count_nonzero(sorted_dist <= p95)/ count_val* 100) 

        mean = np.mean(sorted_dist)
        median = np.median(sorted_dist)
        maxim = np.max(sorted_dist)

        p95_calc = np.percentile(sorted_dist, 95)


        table_stopgo_rows.append({
            "Szenario": szenario,
            "Anzahl Messpositionen": count_val,
            "Mittelwert maximale Distanz [cm]": mean,
            "Median maximale Distanz [cm]": median,
            "Maximum [cm]": maxim,
            "P95 interpoliert [cm]": p95_calc,
            "P95 empirisch [cm]": p95,
        })


        fig_akkum_stopgo.add_trace(
            gr_obj.Scatter(
                x = sorted_dist,
                y = cumulative_percentage,
                mode = "lines",
                name = szenario,
                legendgroup=szenario,
                line = dict(color = szenario_farben.get(szenario)),
                hovertemplate=("Szenario: " + str(szenario) +  "<br>Maximale Distanz: %{x:.2f} cm <br>Kumulativer Anteil: %{y:.2f} % <extra></extra>")
            )
        )

###### Echter Punkt; Versteckt in der Legende ########################
        fig_akkum_stopgo.add_trace(
            gr_obj.Scatter(
                x=[p95],
                y=[prop_p95],
                mode = "markers",
                legendgroup=szenario,
                name = "95 Perzentil von " + str(szenario),
                text = ["P95"],
                marker=dict(color="red", size=10),
                hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
                showlegend = False
            )
        )

######## Fake Punkt; für Legende######################
    fig_akkum_stopgo.add_trace(
        gr_obj.Scatter(
            x=[None],
            y=[None],
            mode = "markers",
            name = "Empirisches P95",
            marker=dict(color="red", size=10),
            showlegend = True
        )
    )

    
    fig_akkum_stopgo.add_hline(
        y=95,
        line_dash="dot",
        line_color="gray",
        annotation_text="95 %",
        annotation_position="bottom right"
    )



    fig_akkum_stopgo.update_layout(
        title= ("Empirische kumulative Verteilung maximaler Distanzen der StopGo Messungen"),
        xaxis_title = "Maximale Distanz [cm]",
        yaxis_title = "Kumulativer Anteil [%]",
        legend=dict(groupclick="togglegroup"),
        hovermode = "closest",
        template = "plotly_white"
    )
    
    fig_akkum_stopgo.update_xaxes(
        showgrid = True,
        rangemode = "tozero"
    )
    
    fig_akkum_stopgo.update_yaxes(
        showgrid = True,
        range=[0,101],
        dtick=10
    )

########### Linienplot speichern ###############

    save_path = os.path.join(save_location, "Linienplot_perzentile_der_maximalen_distanzen")
    fig_akkum_stopgo.write_html(save_path + ".html")
    fig_akkum_stopgo.write_image(save_path + ".png", width=1400, height=700)


################################################################### Tabelle ###################################################################################

    table_stopgo = pd.DataFrame(table_stopgo_rows)

    table_stopgo = table_stopgo.round(2)

    table_stopgo = table_stopgo[[
        "Szenario",
        "Anzahl Messpositionen",
        "Mittelwert maximale Distanz [cm]",
        "Median maximale Distanz [cm]",
        "Maximum [cm]",
        "P95 interpoliert [cm]",
        "P95 empirisch [cm]",
    ]]


    save_path = os.path.join(save_location,"Tabelle_StopGo_Präzision.csv")
    table_stopgo.to_csv(save_path, sep=";", decimal=",", index=False)

    print("\nAlles gespeichert!")
    tools.threedots() 