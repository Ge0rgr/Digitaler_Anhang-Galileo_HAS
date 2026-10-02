import plotly.graph_objects as gr_obj
import pandas as pd
import numpy as np
import os #Zum erstellen von Ordnern
import glob #Zum Suchen von Dateipfaden, die best. Mustern entspr. 
import tools


#
#
# Zur Erstellung der skripte wurde KI unterstützend verwendet
#
#

# Bearbeitung der autotopo Messdaten. ERstellung von Boxplots, Differenzplots, Höhenplots, Perzentilplots und einer Tabelle
def autotopo_heightGraphs_HAS_DGM(input_data, save_location):
    
    autotopo_search_path = os.path.join(input_data,"*_autotopo_*.csv")
    autotopo_files = glob.glob(autotopo_search_path) 

    table_diff_rows = []



############################################################# Bearbeitung Autotopo files ########################################################################
    for file in autotopo_files:

        autotopo_filename = os.path.splitext(os.path.basename(file))[0]
        #print(autotopo_filename)
        #print("Fehler hiernach\n\n")

        autotopo_table = pd.read_csv(file, sep =";", decimal=",")

        #Farben der Punkte anpassen: Float oder convergence?
        # Wenn nur ein Graph erzeugt wird
        #for val in autotopo_table["Avail_Code"]:
        #    if val == 1:
         #       marker_colors.append("blue")

        #    if val == 0:
        #        marker_colors.append("orange")


        float_points = autotopo_table["Avail_Code"] == 1
        convergence_points = autotopo_table["Avail_Code"] == 0

        marker_sym_ok= autotopo_table["GalileoSats"] != 0
        marker_sym_prob = autotopo_table["GalileoSats"] == 0


        

######### HAS Angegebene Ungenauigkeiten ############

        #HAS_uncert = 0.40




        fig1 = gr_obj.Figure()


########### HAS Linie der absoluten höhe ############

        #Generell verbindende Linie der Punkte
        fig1.add_trace(
            gr_obj.Scatter(
                x = autotopo_table["Punkt"],
                y = autotopo_table["HAS"],
                mode ="lines",
                name = "HAS, absolute Höhe",
                hoverinfo = "skip",
                line= dict(color = "blue"),
            )
        )


######### HAS Punkte float ############

        #HAS Höhen für float + Galileo vorhanden
        fig1.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[float_points & marker_sym_ok, "Punkt"],
                y = autotopo_table.loc[float_points & marker_sym_ok,"HAS"],
                mode ="markers",
                name = "Float mit Satellitenempfang",
                hoveron="points",
                text=[f"VDop: {value:.2f}"for value in autotopo_table.loc[float_points & marker_sym_ok, "VDop"] ],
                line= dict(color = "blue"),
                marker = dict( color = "blue", symbol = "circle"),
                #error_y=dict(
                    #type="constant",
                    #value=HAS_uncert,
                    #color="rgba(30, 144, 255, 0)",
                    #visible=True 
                #)
            )
        )



        #HAS Höhen für float + Galileo nicht vorhanden
        fig1.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[float_points & marker_sym_prob, "Punkt"],
                y = autotopo_table.loc[float_points & marker_sym_prob,"HAS"],
                mode ="markers",
                name = "Float ohne Satellitenempfang",
                hoveron="points",
                text=[f"VDop: {value:.2f}" for value in autotopo_table.loc[float_points & marker_sym_prob, "VDop"]],
                marker = dict(color = "blue", symbol = "x"),
                #error_y=dict(
                    #type="constant",
                    #value=HAS_uncert,
                    #color="rgba(30, 144, 255, 0)",
                    #visible=True 
                #)
            )
        )
        

######### HAS Punkte Convergence ############

        #HAS Höhen für convergence + Galileo vorhanden
        fig1.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[convergence_points  & marker_sym_ok, "Punkt"],
                y = autotopo_table.loc[convergence_points  & marker_sym_ok,"HAS"],
                mode ="markers",
                name = "Konvergierend mit Satellitenempfang",
                text=[f"VDop: {value:.2f}" for value in autotopo_table.loc[convergence_points  & marker_sym_ok, "VDop"] ],
                marker = dict(color = "orange", symbol = "circle"),
                #error_y=dict(
                    #type="constant",
                    #value=HAS_uncert,
                    #color="rgba(30, 144, 255, 0)",
                    #visible=True 
                #)
            )
        )

        #HAS Höhen für convergence + Galileo vorhanden
        fig1.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[convergence_points  & marker_sym_prob, "Punkt"],
                y = autotopo_table.loc[convergence_points  & marker_sym_prob,"HAS"],
                mode ="markers",
                name = "Konvergierend ohne Satellitenempfang",
                text=[f"VDop: {value:.2f}" for value in autotopo_table.loc[convergence_points  & marker_sym_prob, "VDop"] ],
                marker = dict(color = "orange", symbol = "x"),
                #error_y=dict(
                    #type="constant",
                    #value=HAS_uncert,
                    #color="rgba(30, 144, 255, 0)",
                    #visible=True 
                #)
            )
        )




######### DGM Linie ############

        #DGM Höhen
        fig1.add_trace(
            gr_obj.Scatter(
                x = autotopo_table["Punkt"],
                y = autotopo_table["DGM"],
                mode ="lines",
                name = "DGM",
                line= dict(color = "black"),
            )
        )
        

######### Linienplots Beschriften ############

        if("forst" in autotopo_filename):
                autotopo_title="Höhen im Forst"
        elif("weinberg" in autotopo_filename):
                autotopo_title="Höhen auf dem Weinberg"

        fig1.update_layout(
            title=autotopo_title,
            xaxis_title="Punkt",
            yaxis_title="Höhe [m]",
            hovermode="x unified",
            template="plotly_white",
            hoverdistance = 1
            )

        fig1.update_yaxes(hoverformat=".2f")

######### Linienplots speichern ############

        save_path = os.path.join(save_location, autotopo_filename + "_Linienplot_Höhen_HAS_DGM")

        fig1.write_html(save_path + ".html")
        fig1.write_image(save_path + ".png", width=1400, height=700)



################################################################# Linienplots der Differenzen #####################################################################

        autotopo_table["Diff"] = (autotopo_table["HAS"] - autotopo_table["DGM"]) *100

        autotopo_table["absol_Diff"] = (np.abs(autotopo_table["HAS"] - autotopo_table["DGM"])) *100

        fig_diff = gr_obj.Figure()



###### Linie der Differenz erstellen #########
        fig_diff.add_trace(
            gr_obj.Scatter(
                x = autotopo_table["Punkt"],
                y = autotopo_table["Diff"],
                mode = "lines",
                name ="Differenz: HAS - DGM",
                line_color = "blue",
                hoverinfo = "skip",
            )
        )


############ Differenzpunkte float ############

        #HAS Differenz für float + Galileo vorhanden
        fig_diff.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[float_points & marker_sym_ok, "Punkt"],
                y = autotopo_table.loc[float_points & marker_sym_ok,"Diff"],
                mode ="markers",
                name = "Float mit Satellitenempfang",
                hoveron="points",
                marker = dict(color = "blue",symbol = "circle")
            )
        )


        #HAS Differenz für float + Galileo nicht vorhanden
        fig_diff.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[float_points & marker_sym_prob, "Punkt"],
                y = autotopo_table.loc[float_points & marker_sym_prob,"Diff"],
                mode ="markers",
                name = "Float ohne Satellitenempfang",
                hoveron="points",
                marker = dict(color = "blue",symbol = "x")
            )
        )


######### Differenzpunkte Convergence ############

        #HAS Differenz für Convergence + Galileo vorhanden
        fig_diff.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[convergence_points & marker_sym_ok, "Punkt"],
                y = autotopo_table.loc[convergence_points & marker_sym_ok,"Diff"],
                mode ="markers",
                name = "Konvergierend mit Satellitenempfang",
                hoveron="points",
                marker = dict(color = "orange",symbol = "circle")
            )
        )


        #HAS Differenz für convergence + Galileo nicht vorhanden
        fig_diff.add_trace(
            gr_obj.Scatter(
                x = autotopo_table.loc[convergence_points & marker_sym_prob, "Punkt"],
                y = autotopo_table.loc[convergence_points & marker_sym_prob,"Diff"],
                mode ="markers",
                name = "Konvergierend ohne Satellitenempfang",
                hoveron="points",
                marker = dict(color = "orange", symbol = "x")
            )
        )

######## weitere Kennwerte für den Differenzplot############

        fig_diff.add_hline(
            y = 0,
            line_dash = "dash",
            annotation_text = "Differenz = 0"
        )

    #Mittlere Differenz
        fig_diff.add_hline(
               y = np.mean(autotopo_table["Diff"]),
               line_dash = "dot",
               line_width=0.5,
               line_color = "grey",
               annotation_text = f"Mittlere Differenz = {np.mean(autotopo_table["Diff"]):.2f}cm",
               annotation_bgcolor="rgba(255,255,255,0.4)",
               annotation_borderpad=4,
        )

    #MEdian Differenz
        fig_diff.add_hline(
               y = np.median(autotopo_table["Diff"]),
               line_dash = "dash",
               line_color = "grey",
               line_width=0.5,
               annotation_text = f"Mediane Differenz = {np.median(autotopo_table["Diff"]):.2f}cm",
               annotation_position="top left",
               annotation_bgcolor="rgba(255,255,255,0.4)",
               annotation_borderpad=4
        )



###### Differenzplot beschriften #########
        if("forst" in autotopo_filename):
                autotopo_diff_title="Höhendifferenz im Forst"
        elif("weinberg" in autotopo_filename):
                autotopo_diff_title="Höhendifferenz auf dem Weinberg"

        fig_diff.update_layout(
            title =autotopo_diff_title,
            xaxis_title= "Punkt",
            yaxis_title = "Differenz: HAS - DGM [cm]",
            hovermode = "x unified",
            template = "plotly_white",
            hoverdistance = 1)
        
        fig_diff.update_yaxes(hoverformat=".2f")

###### Differenzplot speichern #########

        save_path = os.path.join(save_location, autotopo_filename + "_Linienplot_Differenz_HAS_DGM")

        fig_diff.write_html(save_path + ".html")
        fig_diff.write_image(save_path + ".png", width=1400, height=700)       



############################################################ Absolute Differenzlinienplots mit 68 und 95 Perzentilen ####################################################################

        if "forst" in autotopo_filename:
                percentil_line_title="Empirische kumulative Verteilung der absoluten Höhendifferenzen (HAS - DGM), Forst"

        elif "weinberg" in autotopo_filename:
                percentil_line_title="Empirische kumulative Verteilung der absoluten Höhendifferenzen (HAS - DGM), Weinberg"


        sorted_diff = np.sort(autotopo_table["absol_Diff"].to_numpy())

        cumulative_percentage = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff) * 100


        count_val = len(sorted_diff)

        empir_68 = int(np.ceil(0.68 * count_val)) - 1
        empir_95 = int(np.ceil(0.95 * count_val)) - 1

        p68 = sorted_diff[empir_68]
        p95 = sorted_diff[empir_95]

        prop_p68 = (np.count_nonzero(sorted_diff <= p68)/ count_val* 100)
        prop_p95 = (np.count_nonzero(sorted_diff <= p95)/ count_val* 100)


        fig_diff_percentiles = gr_obj.Figure()


###### Linie der Differenz erstellen #########

        fig_diff_percentiles.add_trace(
            gr_obj.Scatter(
                x=sorted_diff,
                y=cumulative_percentage,
                mode="lines",
                name="Kumulative Verteilung",
                line=dict(color="blue"),
                hovertemplate=("Abs. Differenz: %{x:.2f} cm<br>Kumulativer Anteil: %{y:.2f}%<extra></extra>"),
            )
        )


        fig_diff_percentiles.add_trace(
            gr_obj.Scatter(
                x=[p68, p95],
                y=[prop_p68, prop_p95],
                mode = "markers",
                name = "Empirisches P68 / P95",
                marker=dict(color="red", size=10),
                text = ["P68", "P95"],
                hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
            )
        )
###### Linien der Perzentile hinzufügen #########

        fig_diff_percentiles.add_hline(
            y=68,
            line_dash="dash",
            line_color="grey",
            annotation_text="68%",
            annotation_position="bottom right"
        )

        fig_diff_percentiles.add_hline(
            y=95,
            line_dash="dot",
            line_color="grey",
            annotation_text="95%",
            annotation_position="bottom right"
        )
        
        '''
        fig_diff_percentiles.add_vline(
            x=p68,
            line_dash="dash",
            line_color="grey",
            annotation_text=f"68 Perzentil: {p68:.2f} cm",
            annotation_position="top left"
        )

        fig_diff_percentiles.add_vline(
            x=p95,
            line_dash="dot",
            line_color="grey",
            annotation_text=f"95 Perzentil: {p95:.2f} cm",
            annotation_position="top left" 
        )
        '''


###### Differenzplot der Perzentile beschriften #########

        fig_diff_percentiles.update_layout(
            title=percentil_line_title,
            xaxis_title="Absolute Differenz: HAS - DGM [cm]",
            yaxis_title="Kumulativer Anteil [%]",
            template="plotly_white",
            hovermode="closest",
            showlegend=True,
        )

        fig_diff_percentiles.update_yaxes(
               range=[0, 101],
               showgrid=True,
               dtick=10,
        )

        fig_diff_percentiles.update_xaxes(
               showgrid=True,
               rangemode="tozero",
        )

###### Differenzplot der Perzentile speichern #########

        save_path = os.path.join(save_location, autotopo_filename + "_Linienplot_Perzentile_Differenz_HAS_DGM")

        fig_diff_percentiles.write_html(save_path + ".html")
        fig_diff_percentiles.write_image(save_path + ".png", width=1400, height=700)


################################################################ BOxplots #######################################################################

##### Segmente einteilen ########
        if "forst" in autotopo_filename:
                seg_size = 110
                autotopo_box_title="Höhendifferenzen nach Steckenabschnitt im Forst"

        elif "weinberg" in autotopo_filename:
                seg_size = 50
                autotopo_box_title="Höhendifferenzen nach Steckenabschnitt auf dem Weinberg"

        autotopo_table["Seg_start"] = (((autotopo_table["Punkt"]-1) // seg_size) * seg_size +1)

        max_point = autotopo_table["Punkt"].max()

        autotopo_table["Seg_end"] = np.minimum(autotopo_table["Seg_start"] + seg_size - 1, max_point)

        fig_box = gr_obj.Figure()

        section_labels = []

        np.random.seed(1)

###### boxplots erstellen #########

        for i, (section_start, section) in enumerate(autotopo_table.groupby("Seg_start",sort=True)):

            section = section.sort_values("Punkt")
            section_end = int(section["Seg_end"].iloc[0])
            section_count = len(section)

            section_label = (f"{int(section_start)}-{section_end} <br> (n={section_count})")
            section_labels.append(section_label)

            float_points_section = section["Avail_Code"] == 1
            convergence_points_section = section["Avail_Code"] == 0

            marker_sym_ok_section = section["GalileoSats"] != 0
            marker_sym_prob_section = section["GalileoSats"] == 0

            legend_group = f"section_{int(section_start)}"

            median_vdop = section["VDop"].median()



########## Fake Punkte im Boxplot #########
            fig_box.add_trace(
                gr_obj.Box(
                    x = np.full(len(section), i),
                    y = section["Diff"],
                    name = section_label,
                    boxpoints = "all",
                    marker = dict(opacity=0),
                    boxmean = True,
                    legendgroup=legend_group,
                    showlegend = True
                )
            )


######## VDOP MEdian ########
            fig_box.add_trace(
                gr_obj.Scatter(
                    x = [i],
                    y = [section["Diff"].max()],
                    mode = "text",
                    text = [f"Median VDOP: {median_vdop:.2f}"],
                    textposition = "top center",
                    showlegend = False,
                    legendgroup = legend_group,
                    hoverinfo = "skip"
                )
            )
   
############ Echte Punkte, aber versteckt; Nur Hover #########

            #HAS float + Galileo vorhanden
            points = section.loc[float_points_section & marker_sym_ok_section].copy()
            jitter = np.random.uniform(-0.12, 0.12, len(points))

            custom_data = np.column_stack([points["Punkt"], points["VDop"]])

            fig_box.add_trace(
                gr_obj.Scatter(
                    x = i + jitter,
                    y = points["Diff"],
                    mode = "markers",
                    name = "Float mit Satellitenempfang",
                    hoveron = "points",
                    marker = dict(color="blue", symbol="circle"),
                    showlegend = False,
                    customdata = custom_data,
                    legendgroup=legend_group,
                    hovertemplate=("Punkt: %{customdata[0]:.0f} <br> HAS - DGM: %{y:.2f} cm <br> VDOP: %{customdata[1]:.2f} <extra></extra>")
                )
            )


            #HAS float + Galileo nicht vorhanden
            points = section.loc[float_points_section & marker_sym_prob_section].copy()
            jitter = np.random.uniform(-0.12, 0.12, len(points))

            custom_data = np.column_stack([points["Punkt"], points["VDop"]])

            fig_box.add_trace(
                gr_obj.Scatter(
                    x = i + jitter,
                    y = points["Diff"],
                    mode = "markers",
                    name = "Float ohne Satellitenempfang",
                    hoveron = "points",
                    marker = dict(color="blue", symbol="x"),
                    showlegend = False,
                    customdata = custom_data,
                    legendgroup=legend_group,
                    hovertemplate = ("Punkt: %{customdata[0]:.0f} <br> HAS - DGM: %{y:.2f} cm <br> VDOP: %{customdata[1]:.2f} <extra></extra>")
                )
            )


            #HAS convergence + Galileo vorhanden
            points = section.loc[convergence_points_section & marker_sym_ok_section].copy()
            jitter = np.random.uniform(-0.12, 0.12, len(points))

            custom_data = np.column_stack([points["Punkt"], points["VDop"]])

            fig_box.add_trace(
                gr_obj.Scatter(
                    x = i + jitter,
                    y = points["Diff"],
                    mode = "markers",
                    name = "Konvergierend mit Satellitenempfang",
                    hoveron = "points",
                    marker = dict(color="orange", symbol="circle"),
                    showlegend = False,
                    customdata = custom_data,
                    legendgroup=legend_group,
                    hovertemplate = ("Punkt: %{customdata[0]:.0f}<br> HAS - DGM: %{y:.2f} cm<br> VDOP: %{customdata[1]:.2f} <extra></extra>")
                )
            )


            #HAS convergence + Galileo nicht vorhanden
            points = section.loc[convergence_points_section & marker_sym_prob_section].copy()
            jitter = np.random.uniform(-0.12, 0.12, len(points))

            custom_data = np.column_stack([points["Punkt"], points["VDop"]])

            fig_box.add_trace(
                gr_obj.Scatter(
                    x = i + jitter,
                    y = points["Diff"],
                    mode = "markers",
                    name = "Konvergierend ohne Satellitenempfang",
                    hoveron = "points",
                    marker = dict(color="orange", symbol="x"),
                    showlegend = False,
                    customdata = custom_data,
                    legendgroup=legend_group,
                    hovertemplate = ("Punkt: %{customdata[0]:.0f}<br> HAS - DGM: %{y:.2f} cm<br> VDOP: %{customdata[1]:.2f} <extra></extra>")
                )
            )


  ########## Fake Punkte, nur für Legende ###########

        #HAS float + Galileo vorhanden
        fig_box.add_trace(
            gr_obj.Scatter(
                x = [None],
                y = [None],
                mode = "markers",
                name = "Float mit Satellitenempfang",
                marker = dict(color="blue", symbol="circle")
            )
        )

        #HAS float + Galileo nicht vorhanden
        fig_box.add_trace(
            gr_obj.Scatter(
                x = [None],
                y = [None],
                mode = "markers",
                name = "Float ohne Satellitenempfang",
                marker = dict(color="blue", symbol="x")
            )
        )

        #HAS convergence + Galileo vorhanden
        fig_box.add_trace(
            gr_obj.Scatter(
                x = [None],
                y = [None],
                mode = "markers",
                name = "Konvergierend mit Satellitenempfang",
                marker = dict(color="orange", symbol="circle")
            )
        )

        #HAS convergence + Galileo nicht vorhanden
        fig_box.add_trace(
            gr_obj.Scatter(
                x = [None],
                y = [None],
                mode = "markers",
                name = "Konvergierend ohne Satellitenempfang",
                marker = dict(color="orange", symbol="x")
            )
        )


        ###### Boxplot beschriften #########

        fig_box.update_layout(
            title = autotopo_box_title,
            xaxis_title = "Punktabschnitt",
            yaxis_title = "Höhendifferenz HAS - DGM [cm]",
            template = "plotly_white",
            showlegend = True,
            hovermode = "closest"
        )
        
        fig_box.update_yaxes(
            hoverformat = ".2f",
            zeroline = False,
            showgrid = True
        )
        
        fig_box.update_xaxes(
            tickmode = "array",
            tickvals = np.arange(len(section_labels)),
            ticktext = section_labels,
            showgrid = False
        )


        ##### Boxplot speichern #########

        save_path = os.path.join(save_location, autotopo_filename + "_Boxplot_Differenz_HAS_DGM")

        fig_box.write_html(save_path + ".html")
        fig_box.write_image(save_path + ".png", width=1400, height=700)




################################################################### Tabelle ###################################################################################

        if "forst" in autotopo_filename:
            szenario_tabelle = "Forst"

        elif "weinberg" in autotopo_filename:
            szenario_tabelle = "Weinberg"


        diff_val = autotopo_table["Diff"].to_numpy()
        abs_diff_val = np.sort(autotopo_table["absol_Diff"].to_numpy())


##### Tabelle für gesamtes Szenario
        count_table = len(abs_diff_val)
        mittel_diff = np.mean(diff_val)
        median_diff = np.median(diff_val)
        mittel_vdop = np.mean(autotopo_table["VDop"].to_numpy())
        median_vdop = np.median(autotopo_table["VDop"].to_numpy())
        mittel_galileo = np.mean(autotopo_table["GalileoSats"].to_numpy())
        median_galileo = np.median(autotopo_table["GalileoSats"].to_numpy())
        mittel_gps = np.mean(autotopo_table["GPSSats"].to_numpy())
        median_gps = np.median(autotopo_table["GPSSats"].to_numpy())
        p68_calc = np.percentile(abs_diff_val, 68)
        p95_calc = np.percentile(abs_diff_val, 95)
        empir_68_table = int(np.ceil(0.68 * count_table)) - 1
        empir_95_table = int(np.ceil(0.95 * count_table)) - 1
        p68_emp = abs_diff_val[empir_68_table]
        p95_emp = abs_diff_val[empir_95_table]



        table_diff_rows.append({
            "Szenario": szenario_tabelle,
            "Lösungsstatus": "Gesamt",
            "Anzahl Messungen": count_table,
            "Mittelwert Differenz [cm]": mittel_diff,
            "Median Differenz [cm]": median_diff,
            "Mittelwert VDOP": mittel_vdop,
            "Median VDOP": median_vdop,
            "Mittelwert Galileo Satelliten": mittel_galileo,
            "Median Galileo Satelliten": median_galileo,
            "Mittelwert GPS Satelliten": mittel_gps,
            "Median GPS Satelliten": median_gps,
            "P68 interpoliert (Absolut) [cm]": p68_calc,
            "P68 empirisch (Absolut) [cm]": p68_emp,
            "P95 interpoliert (Absolut) [cm]": p95_calc,
            "P95 empirisch (Absolut) [cm]": p95_emp
        })


###### Tabelle nach Lösungsstatus getrennt

        autotopo_table["Lösungsstatus"] = np.where(autotopo_table["Avail_Code"] == 1, "Float", "Konvergierend")
        sol_stat = ["Float", "Konvergierend"]

        for status in sol_stat:

            status_table = autotopo_table.loc[autotopo_table["Lösungsstatus"] == status].copy()

            if len(status_table) == 0:
                continue

            diff_val = status_table["Diff"].to_numpy()
            abs_diff_val = np.sort(status_table["absol_Diff"].to_numpy())

            count_table = len(abs_diff_val)
            mittel_diff = np.mean(diff_val)
            median_diff = np.median(diff_val)
            mittel_vdop = np.mean(status_table["VDop"].to_numpy())
            median_vdop = np.median(status_table["VDop"].to_numpy())
            mittel_galileo = np.mean(status_table["GalileoSats"].to_numpy())
            median_galileo = np.median(status_table["GalileoSats"].to_numpy())
            mittel_gps = np.mean(status_table["GPSSats"].to_numpy())
            median_gps = np.median(status_table["GPSSats"].to_numpy())
            p68_calc = np.percentile(abs_diff_val, 68)
            p95_calc = np.percentile(abs_diff_val, 95)
            empir_68_table = int(np.ceil(0.68 * count_table)) - 1
            empir_95_table = int(np.ceil(0.95 * count_table)) - 1
            p68_emp = abs_diff_val[empir_68_table]
            p95_emp = abs_diff_val[empir_95_table]



            table_diff_rows.append({
                "Szenario": szenario_tabelle,
                "Lösungsstatus": status,
                "Anzahl Messungen": count_table,
                "Mittelwert Differenz [cm]": mittel_diff,
                "Median Differenz [cm]": median_diff,
                "Mittelwert VDOP": mittel_vdop,
                "Median VDOP": median_vdop,
                "Mittelwert Galileo Satelliten": mittel_galileo,
                "Median Galileo Satelliten": median_galileo,
                "Mittelwert GPS Satelliten": mittel_gps,
                "Median GPS Satelliten": median_gps,
                "P68 interpoliert (Absolut) [cm]": p68_calc,
                "P68 empirisch (Absolut) [cm]": p68_emp,
                "P95 interpoliert (Absolut) [cm]": p95_calc,
                "P95 empirisch (Absolut) [cm]": p95_emp
            })


######### Speichern #################

    table_diff = pd.DataFrame(table_diff_rows)

    table_diff = table_diff.round(2)

    table_diff = table_diff[[
        "Szenario",
        "Lösungsstatus",
        "Anzahl Messungen",
        "Mittelwert Differenz [cm]",
        "Median Differenz [cm]",
        "Mittelwert VDOP",
        "Median VDOP",
        "Mittelwert Galileo Satelliten",
        "Median Galileo Satelliten",
        "Mittelwert GPS Satelliten",
        "Median GPS Satelliten",
        "P68 interpoliert (Absolut) [cm]",
        "P68 empirisch (Absolut) [cm]",
        "P95 interpoliert (Absolut) [cm]",
        "P95 empirisch (Absolut) [cm]"
    ]]

    save_path = os.path.join(save_location, "Tabelle_Autotopo_HAS_DGM_Höhendifferenzen.csv")
    table_diff.to_csv(save_path, sep=";", decimal=",", index=False, encoding="utf-8-sig")


    print("\nAlles gespeichert!")
    tools.threedots()  