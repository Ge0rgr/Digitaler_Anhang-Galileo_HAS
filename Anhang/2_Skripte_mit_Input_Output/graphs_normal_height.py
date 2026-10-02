import plotly.graph_objects as gr_obj
from plotly.subplots import make_subplots
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


# Analyse der Höhengenauigkeit. Erstellung von Boxplots, Differenzplots, Höhenplots, Perzentilplots, Scatterplots und einer Tabelle
def normal_heightGraphs_HAS_SAPOS_DGM(input_data, save_location):

    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    tables_normal = []
    tables_stopgo = []
    table_accuracy_rows = []

    for file in files:

        filename = os.path.splitext(os.path.basename(file))[0]

        table = pd.read_csv(file, sep =";", decimal=",")

        table["Diff_HAS_DGM_cm"] = (table["HAS_höhe_m"] - table["DGM_höhe_m"]) * 100
        table["Diff_HAS_SAPOS_cm"] = (table["HAS_höhe_m"] - table["SAPOS_höhe_m"]) * 100
        table["Diff_DGM_SAPOS_cm"] = (table["DGM_höhe_m"] - table["SAPOS_höhe_m"]) * 100

        table["Diff_HAS_DGM_cm_abs"] = (table["Diff_HAS_DGM_cm"].abs())
        table["Diff_HAS_SAPOS_cm_abs"] = (table["Diff_HAS_SAPOS_cm"].abs())
        table["Diff_DGM_SAPOS_cm_abs"] = (table["Diff_DGM_SAPOS_cm"].abs())
        

########### Ergänzung der Szenarien für die Boxplots ###########
        if filename.startswith("parkplatz"):
            table["Szenario"] = "Parkplatz"

        elif filename.startswith("feldweg"):
            table["Szenario"] = "Feldweg"

        elif filename.startswith("schlosspark"):
            table["Szenario"] = "Schlosspark mit Seedpoint"

        elif filename.startswith("weinberg_HAS"):
            table["Szenario"] = "Weinberg"

        elif filename.startswith("weinberg_nur_drohne"):
            table["Szenario"] = "Drohnenreferenzpunkte"

        elif filename.startswith("weingut_nur_seedpoint"):
            table["Szenario"] = ("Weingut mit Seedpoint")

        elif filename.startswith("weingut_ohne"):
            table["Szenario"] = ("Weingut ohne Seedpoint")

            
        elif filename.startswith("weingut_HAS"):
            table["Szenario"] = ("Weingut")


        elif filename.startswith("forst"):
            table["Szenario"] = ("Forst mit Seedpoint")

        elif filename.startswith("gruenflaeche"):
            table["Szenario"] = ("Grünfläche mit Seedpoint")

            


        tables_normal.append(table.loc[table["Messart"].str.startswith("Normal")].copy())
        tables_stopgo.append(table.loc[table["Messart"].str.startswith("StopGo")].copy())



    big_table_normal = pd.concat(tables_normal, ignore_index=True)
    big_table_stopgo = pd.concat(tables_stopgo, ignore_index=True)


    szenario_farben = {
        "Parkplatz": "rgba(194,144,15, 1)",
        "Feldweg": "rgba(65,194,15,1)",
        "Schlosspark mit Seedpoint": "rgba(213,94,0,1)",
        "Weinberg": "rgba(0,90,156,1)",
        "Drohnenreferenzpunkte": "rgba(86,180,233,1)",
        "Weingut mit Seedpoint": "rgba(112,48,160,1)",
        "Weingut ohne Seedpoint": "rgba(190,120,210,1)",
        "Forst mit Seedpoint": "rgba(0,135,90,1)",
        "Grünfläche mit Seedpoint": "rgba(204,121,167,1)"
    }

    szenarien = big_table_normal["Szenario"].unique()


################################################################### Boxplots ##################################################################################

################ Normale Durchgägne; HAS - SAPOS #################

    fig_box_normal_has_sapos = gr_obj.Figure()

    szenarien_box_normal = big_table_normal["Szenario"].unique()
    szenarien_box_normal = szenarien_box_normal[szenarien_box_normal != "Weingut"]

    np.random.seed(1)

    for i, szenario in enumerate(szenarien_box_normal):


        szenario_table = big_table_normal.loc[big_table_normal["Szenario"] == szenario].copy()

        float_points = szenario_table["Avail_Code"] == 1
        convergence_points = szenario_table["Avail_Code"] == 0

        fig_box_normal_has_sapos.add_trace(
            gr_obj.Box(
                x=np.full(len(szenario_table), i),
                y=szenario_table["Diff_HAS_SAPOS_cm"],
                name=szenario,
                boxmean=True,
                boxpoints = "all",
                marker = dict(opacity=0),
                legendgroup=szenario,
                line_color=szenario_farben.get(szenario),
                marker_color=szenario_farben.get(szenario),
                showlegend=True
            )
        )



############ Echte Punkte, aber versteckt; Nur Hover #########

        #HAS float
        points = szenario_table.loc[float_points].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_normal_has_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_SAPOS_cm"],
                mode ="markers",
                name = "Float",
                hoveron="points",
                marker_color = "blue",
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate=("Messpunkt: %{text} <br> HAS - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup=szenario
            )
        )

        #HAS convergence
        points = szenario_table.loc[convergence_points].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_normal_has_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_SAPOS_cm"],
                mode ="markers",
                name = "Konvergierend",
                hoveron="points",
                marker_color = "orange",
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate = ("Messpunkt: %{text} <br> HAS - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup = szenario,
            )
        )

 ########## Fake Punkte, nur für Legende ###########
        
    #HAS float
    fig_box_normal_has_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float",
            marker_color = "blue"
        )
    )


    #HAS convergence
    fig_box_normal_has_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Konvergierend",
            marker_color = "orange"
        )
    )


    fig_box_normal_has_sapos.update_layout(
        title="Höhendifferenz von HAS gegenüber SAPOS",
        xaxis_title="Messszenario",
        yaxis_title="Höhendifferenz HAS - SAPOS [cm]",
        hovermode="closest",
        template="plotly_white",
    )

    
    fig_box_normal_has_sapos.update_yaxes(
        hoverformat=".2f",
        showgrid=True
    )

    fig_box_normal_has_sapos.update_xaxes(
        tickmode = "array",
        tickvals = np.arange(len(szenarien_box_normal)),
        ticktext = szenarien_box_normal,
        showgrid = False
    )



    save_path = os.path.join(save_location, "Boxplot_Höhenabweichung_HAS_SAPOS_Normal")
    fig_box_normal_has_sapos.write_html(save_path + ".html")
    fig_box_normal_has_sapos.write_image(save_path + ".png",width=1400,height=700)


################ Normale Durchgägne; DGM - SAPOS #################


    fig_box_normal_dgm_sapos = gr_obj.Figure()


    np.random.seed(1)

    for i, szenario in enumerate(szenarien_box_normal):


        szenario_table = big_table_normal.loc[big_table_normal["Szenario"] == szenario].copy()

        float_points = szenario_table["Avail_Code"] == 1
        convergence_points = szenario_table["Avail_Code"] == 0

        fig_box_normal_dgm_sapos.add_trace(
            gr_obj.Box(
                x=np.full(len(szenario_table), i),
                y=szenario_table["Diff_DGM_SAPOS_cm"],
                name=szenario,
                boxmean=True,
                boxpoints = "all",
                marker = dict(opacity=0),
                legendgroup=szenario,
                line_color=szenario_farben.get(szenario),
                marker_color=szenario_farben.get(szenario),
                showlegend=True
            )
        )


############ Echte Punkte, aber versteckt; Nur Hover #########

        #HAS float
        points = szenario_table.loc[float_points].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_normal_dgm_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_DGM_SAPOS_cm"],
                mode ="markers",
                name = "Float",
                hoveron="points",
                marker_color = "blue",
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate=("Messpunkt: %{text} <br> DGM - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup=szenario
            )
        )

        #HAS convergence
        points = szenario_table.loc[convergence_points].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_normal_dgm_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_DGM_SAPOS_cm"],
                mode ="markers",
                name = "Konvergierend",
                hoveron="points",
                marker_color = "orange",
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate = ("Messpunkt: %{text} <br> DGM - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup = szenario,
            )
        )

 ########## Fake Punkte, nur für Legende ###########
        
    #HAS float
    fig_box_normal_dgm_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float",
            marker_color = "blue"
        )
    )


    #HAS convergence
    fig_box_normal_dgm_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Konvergierend",
            marker_color = "orange"
        )
    )


    fig_box_normal_dgm_sapos.update_layout(
        title="Höhendifferenz vom DGM gegenüber SAPOS",
        xaxis_title="Messszenario",
        yaxis_title="Höhendifferenz DGM - SAPOS [cm]",
        hovermode="closest",
        template="plotly_white",
    )

    
    fig_box_normal_dgm_sapos.update_yaxes(
        hoverformat=".2f",
        showgrid=True
    )

    fig_box_normal_dgm_sapos.update_xaxes(
        tickmode = "array",
        tickvals = np.arange(len(szenarien_box_normal)),
        ticktext = szenarien_box_normal,
        showgrid = False
    )



    save_path = os.path.join(save_location, "Boxplot_Höhenabweichung_DGM_SAPOS_Normal")
    fig_box_normal_dgm_sapos.write_html(save_path + ".html")
    fig_box_normal_dgm_sapos.write_image(save_path + ".png",width=1400,height=700)


################ Normale Durchgägne; HAS - DGM #################


    fig_box_normal_has_dgm = gr_obj.Figure()

    np.random.seed(1)

    for i, szenario in enumerate(szenarien_box_normal):

        szenario_table = big_table_normal.loc[big_table_normal["Szenario"] == szenario].copy()

        float_points = szenario_table["Avail_Code"] == 1
        convergence_points = szenario_table["Avail_Code"] == 0

        fig_box_normal_has_dgm.add_trace(
            gr_obj.Box(
                x=np.full(len(szenario_table), i),
                y=szenario_table["Diff_HAS_DGM_cm"],
                name=szenario,
                boxmean=True,
                boxpoints = "all",
                marker = dict(opacity=0),
                legendgroup=szenario,
                line_color=szenario_farben.get(szenario),
                marker_color=szenario_farben.get(szenario),
                showlegend=True
            )
        )


############ Echte Punkte, aber versteckt; Nur Hover #########

        #HAS float
        points = szenario_table.loc[float_points].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_normal_has_dgm.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_DGM_cm"],
                mode ="markers",
                name = "Float",
                hoveron="points",
                marker_color = "blue",
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate=("Messpunkt: %{text} <br> HAS - DGM: %{y:.2f} cm <extra></extra>"),
                legendgroup=szenario
            )
        )

        #HAS convergence
        points = szenario_table.loc[convergence_points].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_normal_has_dgm.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_DGM_cm"],
                mode ="markers",
                name = "Konvergierend",
                hoveron="points",
                marker_color = "orange",
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate = ("Messpunkt: %{text} <br> HAS - DGM: %{y:.2f} cm <extra></extra>"),
                legendgroup = szenario,
            )
        )

 ########## Fake Punkte, nur für Legende ###########
        
    #HAS float
    fig_box_normal_has_dgm.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float",
            marker_color = "blue"
        )
    )


    #HAS convergence
    fig_box_normal_has_dgm.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Konvergierend",
            marker_color = "orange"
        )
    )


    fig_box_normal_has_dgm.update_layout(
        title="Höhendifferenz vom HAS gegenüber DGM",
        xaxis_title="Messszenario",
        yaxis_title="Höhendifferenz HAS - DGM [cm]",
        hovermode="closest",
        template="plotly_white",
    )

    
    fig_box_normal_has_dgm.update_yaxes(
        hoverformat=".2f",
        showgrid=True
    )

    fig_box_normal_has_dgm.update_xaxes(
        tickmode = "array",
        tickvals = np.arange(len(szenarien_box_normal)),
        ticktext = szenarien_box_normal,
        showgrid = False
    )



    save_path = os.path.join(save_location, "Boxplot_Höhenabweichung_HAS_DGM_Normal")
    fig_box_normal_has_dgm.write_html(save_path + ".html")
    fig_box_normal_has_dgm.write_image(save_path + ".png",width=1400,height=700)


################### StopGo HAS - SAPOS ####################

    fig_box_stopgo_has_sapos = gr_obj.Figure()

    szenarien_stopgo = big_table_stopgo["Szenario"].unique()

    np.random.seed(1)

    for i, szenario in enumerate(szenarien_stopgo):

        szenario_table = big_table_stopgo.loc[big_table_stopgo["Szenario"] == szenario].copy()

        float_points = szenario_table["Avail_Code"] == 1
        convergence_points = szenario_table["Avail_Code"] == 0

        marker_sym_ok= szenario_table["Satellitenempfang"] == 1
        marker_sym_prob = szenario_table["Satellitenempfang"] == 0

        fig_box_stopgo_has_sapos.add_trace(
            gr_obj.Box(
                x=np.full(len(szenario_table), i),
                y=szenario_table["Diff_HAS_SAPOS_cm"],
                name=szenario,
                boxmean=True,
                boxpoints = "all",
                marker = dict(opacity=0),
                legendgroup=szenario,
                line_color=szenario_farben.get(szenario),
                marker_color=szenario_farben.get(szenario),
                showlegend=True
            )
        )

############ Echte Punkte, aber versteckt; Nur Hover #########


        #HAS float + Galileo vorhanden
        points = szenario_table.loc[float_points & marker_sym_ok].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_stopgo_has_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_SAPOS_cm"],
                mode ="markers",
                name = "Float mit Satellitenempfang",
                hoveron="points",
                marker = dict( color = "blue", symbol = "circle"),
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate=("Messpunkt: %{text} <br> HAS - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup=szenario
                #legendgroup="has_float"
            )
        )


        #HAS float + Galileo nicht vorhanden
        points = szenario_table.loc[float_points & marker_sym_prob].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_stopgo_has_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_SAPOS_cm"],
                mode ="markers",
                name = "Float ohne Satellitenempfang",
                hoveron="points",
                marker = dict( color = "blue", symbol = "x"),
                showlegend = False,
                text =points["Punktname"].astype(str),
                hovertemplate=("Messpunkt: %{text} <br> HAS - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup=szenario,
                #legendgroup="has_prob"
            )
        )

        #HAS convergence + Galileo vorhanden
        points = szenario_table.loc[convergence_points & marker_sym_ok].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_stopgo_has_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_SAPOS_cm"],
                mode ="markers",
                name = "Konvergierend mit Satellitenempfang",
                hoveron="points",
                marker = dict( color = "orange", symbol = "circle"),
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate = ("Messpunkt: %{text} <br> HAS - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup = szenario,
                #legendgroup="has_convergence"
            )
        )

        #HAS convergence + Galileo nicht vorhanden
        points = szenario_table.loc[convergence_points & marker_sym_prob].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_stopgo_has_sapos.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Diff_HAS_SAPOS_cm"],
                mode ="markers",
                name = "Konvergierend ohne Satellitenempfang",
                hoveron="points",
                marker = dict( color = "orange", symbol = "x"),
                showlegend = False,
                text=points["Punktname"].astype(str),
                hovertemplate = ("Messpunkt: %{text} <br> HAS - SAPOS: %{y:.2f} cm <extra></extra>"),
                legendgroup = szenario,
                #legendgroup="has_convergence_prob"
            )
        )

  ########## Fake Punkte, nur für Legende ###########
        
    #HAS float + Galileo vorhanden
    fig_box_stopgo_has_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float mit Satellitenempfang",
            marker = dict( color = "blue", symbol = "circle"),
            #legendgroup="has_float"
        )
    )

    #HAS float + Galileo nicht vorhanden
    fig_box_stopgo_has_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float ohne Satellitenempfang",
            marker = dict( color = "blue", symbol = "x"),
            #legendgroup="has_prob"
        )
    )

    #HAS convergence + Galileo vorhanden
    fig_box_stopgo_has_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Konvergierend mit Satellitenempfang",
            marker = dict( color = "orange", symbol = "circle"),
            #legendgroup="has_convergence"
        )
    )

    #HAS convergence + Galileo nicht vorhanden
    fig_box_stopgo_has_sapos.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Konvergierend ohne Satellitenempfang",
            marker = dict( color = "orange", symbol = "x"),
            #legendgroup="has_convergence_prob"
        )
    )


    fig_box_stopgo_has_sapos.update_layout(
        title = "Höhendifferenz von HAS (StopGo) gegenüber SAPOS",
        xaxis_title= "Messszenario",
        yaxis_title = "Höhendifferenz HAS - SAPOS [cm]",
        hovermode ="closest",
        template = "plotly_white",
    )

    fig_box_stopgo_has_sapos.update_yaxes(
        hoverformat = ".2f",
        showgrid = True
    )

    fig_box_stopgo_has_sapos.update_xaxes(
        tickmode ="array",
        tickvals = np.arange(len(szenarien_stopgo)),
        ticktext = szenarien_stopgo,
        showgrid = False
    )


    save_path = os.path.join(save_location, "Boxplot_Höhenabweichung_HAS_SAPOS_StopGo")
    fig_box_stopgo_has_sapos.write_html(save_path + ".html")
    fig_box_stopgo_has_sapos.write_image(save_path + ".png",width=1400,height=700)



############################################################# Höhenlinienplots #####################################################################################
   

    for szenario in szenarien:

            
        fig_line = gr_obj.Figure()

        szenario_table = big_table_normal.loc[big_table_normal["Szenario"] == szenario].copy()

        messarten = szenario_table["Messart"].dropna().unique()


        for mess in messarten:

            mess_table = szenario_table.loc[szenario_table["Messart"] == mess].copy()

            dg = mess_table["Messdurchgang"].dropna().unique()

            for durchgang in dg:

                dg_table = mess_table.loc[mess_table["Messdurchgang"] == durchgang].copy()

                if szenario == "Drohnenreferenzpunkte":
                    if int(durchgang) == 1:
                        name = "HAS - 10 Epochen"

                    if int(durchgang) == 2:
                        name = "HAS - 60 Epochen"


                elif mess == "Normal_mit_Seedpoint":
                    name = "HAS - mit Seedpoint"
                    linienstil = "solid"

                elif mess == "Normal_ohne_Seedpoint":
                    name = f"HAS - Messdurchgang {int(durchgang)}"
                    linienstil = "solid"

                else:
                    name = f"HAS - Messdurchgang {int(durchgang)}"
                    linienstil = "solid"


                fig_line.add_trace(gr_obj.Scatter(
                        x=dg_table["Punkt_ID"],
                        y=dg_table["HAS_höhe_m"],
                        mode="lines",
                        name= name,
                        line=dict(dash=linienstil),
                        hovertemplate=("HAS-Höhe: %{y:.2f} m<extra></extra>")
                    )
                )


############# HAS STopGo Höhenlinien ####################

        stopgo_szenario = big_table_stopgo.loc[big_table_stopgo["Szenario"] == szenario].copy()

        rep = stopgo_szenario["Wiederholung"].dropna().unique()

        for wiederholung in rep:

            stopgo_table = stopgo_szenario.loc[stopgo_szenario["Wiederholung"] == wiederholung].copy()

            fig_line.add_trace(gr_obj.Scatter(
                x=stopgo_table["Punkt_ID"],
                y=stopgo_table["HAS_höhe_m"],
                mode="lines",
                name=f"HAS - StopGo {int(wiederholung)}",
                line=dict(dash="dash"),
                hovertemplate=("HAS-StopGo-Höhe: %{y:.2f} m<extra></extra>")
            )
        )


############ SAPOS Höhenlinie ########################

        sapos_table = (szenario_table[["Punkt_ID", "Punktname", "SAPOS_höhe_m"]].drop_duplicates(subset="Punkt_ID"))

        fig_line.add_trace(gr_obj.Scatter(
                x = sapos_table["Punkt_ID"],
                y = sapos_table["SAPOS_höhe_m"],
                mode ="lines",
                name = "SAPOS",
                line_color = "rgba(0, 167, 22, 1)",
                hovertemplate=(f"SAPOS-Höhe: %{{y:.2f}} m <extra></extra>")
            )
        )


############ DGM Höhenlinie ########################

        dgm_table = (szenario_table[["Punkt_ID", "Punktname", "DGM_höhe_m"]].drop_duplicates(subset="Punkt_ID"))

        fig_line.add_trace(gr_obj.Scatter(
                x = dgm_table["Punkt_ID"],
                y = dgm_table["DGM_höhe_m"],
                mode ="lines",
                name = "DGM",
                line_color = "black",
                hovertemplate=(f"DGM-Höhe: %{{y:.2f}} m<extra></extra>")
            )
        )

        fig_line.update_layout(
            title=f"Vergleich der gemessenen Höhen - {szenario}",
            xaxis_title="Messpunkt",
            yaxis_title="Höhe [m]",
            hovermode="x unified",
            legend=dict(groupclick="togglegroup"),
            template="plotly_white"
        )


        save_path = os.path.join(save_location,"Höhenplot_" + str(szenario))
        fig_line.write_html(save_path + ".html")
        fig_line.write_image(save_path + ".png",width=1400,height=700)




############################################################# Differenzplots #####################################################################################


    for szenario in szenarien:

        fig_diff = gr_obj.Figure()

        normal_szenario = big_table_normal.loc[big_table_normal["Szenario"] == szenario].copy()

        messarten = normal_szenario["Messart"].dropna().unique()

        for mess in messarten:

            mess_table = normal_szenario.loc[normal_szenario["Messart"] == mess].copy()

            dg = mess_table["Messdurchgang"].dropna().unique()

            for durchgang in dg:

                dg_table = mess_table.loc[mess_table["Messdurchgang"] == durchgang].copy()


                if szenario == "Drohnenreferenzpunkte":
                    if int(durchgang) == 1:
                        name = "HAS - 10 Epochen"

                    if int(durchgang) == 2:
                        name = "HAS - 60 Epochen"


                elif mess == "Normal_mit_Seedpoint":
                    name = "HAS - mit Seedpoint"
                    linienstil = "solid"

                elif mess == "Normal_ohne_Seedpoint":
                    name = f"HAS - Messdurchgang {int(durchgang)}"
                    linienstil = "solid"

                else:
                    name = f"HAS - Messdurchgang {int(durchgang)}"
                    linienstil = "solid"

################# HAS normal #####################

                fig_diff.add_trace(gr_obj.Scatter(
                        x=dg_table["Punkt_ID"],
                        y=dg_table["Diff_HAS_SAPOS_cm"],
                        mode="lines+markers",
                        name=name,
                        hovertemplate=("HAS - SAPOS: %{y:.2f} cm<extra></extra>")
                    )
                )


############## HAS StopGo ##########################

        stopgo_szenario = big_table_stopgo.loc[big_table_stopgo["Szenario"] == szenario].copy()

        rep = (stopgo_szenario["Wiederholung"].dropna().unique())

        for wiederholung in rep:

            stopgo_table = stopgo_szenario.loc[stopgo_szenario["Wiederholung"] == wiederholung].copy()


            fig_diff.add_trace(gr_obj.Scatter(
                    x=stopgo_table["Punkt_ID"],
                    y=stopgo_table["Diff_HAS_SAPOS_cm"],
                    mode="lines+markers",
                    name=f"HAS - StopGo {int(wiederholung)}",
                    line=dict(dash="dash"),
                    hovertemplate=("HAS - SAPOS: %{y:.2f} cm<extra></extra>")
                )
            )


        fig_diff.add_hline(y=0,line_dash="dash",)



        fig_diff.update_layout(
            title=f"Höhendifferenzen HAS gegenüber SAPOS - {szenario}",
            xaxis_title="Messpunkt",
            yaxis_title="Höhendifferenz HAS - SAPOS [cm]",
            hovermode="x unified",
            template="plotly_white"
        )


        save_path = os.path.join(save_location,"Differenzplot_HAS_SAPOS_" + str(szenario))
        fig_diff.write_html(save_path + ".html")
        fig_diff.write_image(save_path + ".png",width=1400,height=700)



#################################################### Perzentilplots #############################################################################################


    for szenario in szenarien:

        max_diff_plot = 0

        rmse_normal = None
        rmse_stopgo = None
        rmse10 = None
        rmse60 = None
        rmse_seed = None
        rmse_no_seed = None


        fig_perz = gr_obj.Figure()

        szenario_table = big_table_normal.loc[big_table_normal["Szenario"] == szenario].copy()


############### HAS normal #####################

####Drohnenreferenzpunkte einzeln (trennen von 10 ;60 Epochen)
        if szenario == "Drohnenreferenzpunkte":

            dg = szenario_table["Messdurchgang"].unique()

            for durchgang in dg:

                dg_table = szenario_table.loc[szenario_table["Messdurchgang"] == durchgang].copy()

                legend_group = f"HAS_{durchgang}"
    
                sorted_diff = np.sort(dg_table["Diff_HAS_SAPOS_cm_abs"].dropna().to_numpy())
                max_diff_plot = max(max_diff_plot, np.max(sorted_diff))
                cumulative_percentage = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff) * 100
                count_val = len(sorted_diff)

                empir_68 = int(np.ceil(0.68 * count_val)) - 1
                empir_95 = int(np.ceil(0.95 * count_val)) - 1

                p68 = sorted_diff[empir_68]
                p95 = sorted_diff[empir_95]

                prop_p68 = (np.count_nonzero(sorted_diff <= p68)/ count_val* 100)
                prop_p95 = (np.count_nonzero(sorted_diff <= p95)/ count_val* 100)



                if int(durchgang) == 1:
                    name = "HAS - 10 Epochen"
                    diff10 = dg_table["Diff_HAS_SAPOS_cm"].dropna().to_numpy()
                    rmse10 = np.sqrt(np.mean(diff10 ** 2))

                if int(durchgang) == 2:
                    name = "HAS - 60 Epochen"
                    diff60 = dg_table["Diff_HAS_SAPOS_cm"].dropna().to_numpy()
                    rmse60 = np.sqrt(np.mean(diff60 ** 2))


                fig_perz.add_trace(
                    gr_obj.Scatter(
                        x=sorted_diff,
                        y=cumulative_percentage,
                        mode="lines",
                        name=name,
                        legendgroup=legend_group,
                        hovertemplate=("Abs. Differenz: %{x:.2f} cm<br>Kumulativer Anteil: %{y:.2f} %<extra></extra>")
                    )
                )

                fig_perz.add_trace(
                    gr_obj.Scatter(
                        x=[p68, p95],
                        y=[prop_p68, prop_p95],
                        mode = "markers",
                        name = "68p und 95p",
                        marker=dict(color="red", size=10),
                        text = ["P68", "P95"],
                        legendgroup=legend_group,
                        showlegend=False,
                        hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
                    )
                )

    ########### Weingut Seedpoint/ ohne Seedpoint getrennt ###########
        elif szenario == "Weingut":

            sp = szenario_table["Seedpoint"].unique()

            for seedpoint in sp:

                sp_table = szenario_table.loc[szenario_table["Seedpoint"] == seedpoint].copy()

                sorted_diff = np.sort(sp_table["Diff_HAS_SAPOS_cm_abs"].dropna().to_numpy())
                max_diff_plot = max(max_diff_plot, np.max(sorted_diff))
                cumulative_percentage = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff) * 100
                count_val = len(sorted_diff)

                empir_68 = int(np.ceil(0.68 * count_val)) - 1
                empir_95 = int(np.ceil(0.95 * count_val)) - 1

                p68 = sorted_diff[empir_68]
                p95 = sorted_diff[empir_95]

                prop_p68 = (np.count_nonzero(sorted_diff <= p68)/ count_val* 100)
                prop_p95 = (np.count_nonzero(sorted_diff <= p95)/ count_val* 100)



                if int(seedpoint) == 1:
                    name = "HAS mit Seedpoint"
                    legend_group = "HAS_mit_Seedpoint"
                    diff_seed = sp_table["Diff_HAS_SAPOS_cm"].dropna().to_numpy()
                    rmse_seed = np.sqrt(np.mean(diff_seed ** 2))

                if int(seedpoint) == 0:
                    name = "HAS ohne Seedpoint"
                    legend_group = "HAS_ohne_Seedpoint"
                    diff_no_seed = sp_table["Diff_HAS_SAPOS_cm"].dropna().to_numpy()
                    rmse_no_seed = np.sqrt(np.mean(diff_no_seed ** 2))


                fig_perz.add_trace(
                    gr_obj.Scatter(
                        x=sorted_diff,
                        y=cumulative_percentage,
                        mode="lines",
                        name=name,
                        legendgroup=legend_group,
                        hovertemplate=("Abs. Differenz: %{x:.2f} cm<br>Kumulativer Anteil: %{y:.2f} %<extra></extra>")
                    )
                )

                fig_perz.add_trace(
                    gr_obj.Scatter(
                        x=[p68, p95],
                        y=[prop_p68, prop_p95],
                        mode = "markers",
                        name = "68p und 95p",
                        marker=dict(color="red", size=10),
                        text = ["P68", "P95"],
                        legendgroup=legend_group,
                        showlegend=False,
                        hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
                    )
                )

 ###### andere durchgänge ######

        else:

            sorted_diff = np.sort(szenario_table["Diff_HAS_SAPOS_cm_abs"].dropna().to_numpy())
            max_diff_plot = max(max_diff_plot, np.max(sorted_diff))
            cumulative_percentage = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff) * 100

            count_val = len(sorted_diff)

            empir_68 = int(np.ceil(0.68 * count_val)) - 1
            empir_95 = int(np.ceil(0.95 * count_val)) - 1

            p68 = sorted_diff[empir_68]
            p95 = sorted_diff[empir_95]

            prop_p68 = (np.count_nonzero(sorted_diff <= p68)/ count_val* 100)
            prop_p95 = (np.count_nonzero(sorted_diff <= p95)/ count_val* 100)


            diff = szenario_table["Diff_HAS_SAPOS_cm"].dropna().to_numpy()
            rmse_normal = np.sqrt(np.mean(diff ** 2))


            fig_perz.add_trace(
                gr_obj.Scatter(
                    x=sorted_diff,
                    y=cumulative_percentage,
                    mode="lines",
                    name="Kumulative Verteilung HAS",
                    legendgroup="HAS",
                    hovertemplate=("Abs. Differenz: %{x:.2f} cm<br>Kumulativer Anteil: %{y:.2f} %<extra></extra>")
                )
            )

            fig_perz.add_trace(
                gr_obj.Scatter(
                    x=[p68, p95],
                    y=[prop_p68, prop_p95],
                    mode = "markers",
                    name = "68p und 95p",
                    marker=dict(color="red", size=10),
                    text = ["P68", "P95"],
                    legendgroup="HAS",
                    showlegend=False,
                    hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
                )
            )





    ############# StopGo ##########

            if szenario in ["Parkplatz","Feldweg","Weinberg","Forst mit Seedpoint","Grünfläche mit Seedpoint"]:

                stopgo_sz = big_table_stopgo.loc[big_table_stopgo["Szenario"] == szenario].copy()

                sorted_diff = np.sort(stopgo_sz["Diff_HAS_SAPOS_cm_abs"].dropna().to_numpy())
                max_diff_plot = max(max_diff_plot, np.max(sorted_diff))

                cumulative_percentage = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff) * 100

                count_val = len(sorted_diff)

                empir_68 = int(np.ceil(0.68 * count_val)) - 1
                empir_95 = int(np.ceil(0.95 * count_val)) - 1

                p68 = sorted_diff[empir_68]
                p95 = sorted_diff[empir_95]

                prop_p68 = (np.count_nonzero(sorted_diff <= p68)/ count_val* 100)
                prop_p95 = (np.count_nonzero(sorted_diff <= p95)/ count_val* 100)


                diff = stopgo_sz["Diff_HAS_SAPOS_cm"].dropna().to_numpy()
                rmse_stopgo = np.sqrt(np.mean(diff ** 2))


                fig_perz.add_trace(
                    gr_obj.Scatter(
                        x=sorted_diff,
                        y=cumulative_percentage,
                        mode="lines",
                        name="Kumulative Verteilung HAS StopGo",
                        line=dict(dash="dash"),
                        legendgroup="StopGo",
                        hovertemplate=("Abs. Differenz: %{x:.2f} cm<br>Kumulativer Anteil: %{y:.2f} %<extra></extra>")
                    )
                )

                fig_perz.add_trace(
                    gr_obj.Scatter(
                        x=[p68, p95],
                        y=[prop_p68, prop_p95],
                        mode = "markers",
                        name = "68p und 95p",
                        marker=dict(color="red", size=10),
                        text = ["P68", "P95"],
                        legendgroup="StopGo",
                        showlegend=False,
                        hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
                    )
                )

######## Fake Punkt; für Legende######################
        fig_perz.add_trace(
            gr_obj.Scatter(
                x=[None],
                y=[None],
                mode = "markers",
                name = "Empirisches P68 / P95",
                marker=dict(color="red", size=10),
                showlegend = True
            )
        )



        fig_perz.add_hline(
            y=68,
            line_dash="dash",
            line_color="grey",
            annotation_text="68%",
            annotation_position="bottom right"
        )

        fig_perz.add_hline(
            y=95,
            line_dash="dot",
            line_color="grey",
            annotation_text="95%",
            annotation_position="bottom right"
        )

        if max_diff_plot > 40:
            fig_perz.add_vline(
                x=40,
                line_dash="dash",
                line_color="red",
                annotation_text="HAS Full-Service-Ziel: P95 <= 40 cm",
                annotation_position="top right"
            )


        if szenario == "Drohnenreferenzpunkte":
            annotation_text = (f"RMSE 10 Epochen: {rmse10:.2f} cm <br>RMSE 60 Epochen: {rmse60:.2f} cm")

        elif szenario == "Weingut":
            annotation_text = (f"RMSE mit Seedoint: {rmse_seed:.2f} cm <br>RMSE ohne Seedpoint: {rmse_no_seed:.2f} cm")

        else:
            annotation_text = ""

            if rmse_normal is not None:
                annotation_text = f"RMSE HAS Normal: {rmse_normal:.2f} cm"

            if rmse_stopgo is not None:
                annotation_text = annotation_text  + f"<br>RMSE HAS StopGo: {rmse_stopgo:.2f} cm"



        fig_perz.add_annotation(
            x=0.07,
            y=0.93,
            xref="paper",
            yref="paper",
            text=annotation_text,
            showarrow=False,
        )


        fig_perz.update_layout(
            title=f"Empirische kumulative Verteilung der absoluten Höhendifferenzen (HAS - SAPOS) - {szenario}",
            xaxis_title="Absolute Differenz: HAS - SAPOS [cm]",
            yaxis_title="Kumulativer Anteil [%]",
            hovermode="closest",
            template="plotly_white"
        )

        fig_perz.update_yaxes(
            range=[0, 101],
            showgrid=True,
            dtick=10,
        )

        fig_perz.update_xaxes(
            showgrid=True,
            rangemode="tozero",
        )

        save_path = os.path.join(save_location,"Perzentilplot_HAS_SAPOS_" + str(szenario))
        fig_perz.write_html(save_path + ".html")
        fig_perz.write_image(save_path + ".png",width=1400,height=700)



############################################################## Tabelle ############################################################################################

    table_accuracy_rows = []


######## Tabelle vorbereiten ##########

    table_normal = big_table_normal.loc[big_table_normal["Szenario"] != "Weingut"].copy()
    table_normal["Messart_Tabelle"] = "HAS - Normal"

    table_normal.loc[(table_normal["Szenario"] == "Drohnenreferenzpunkte") &(table_normal["Messdurchgang"] == 1),"Messart_Tabelle"] = "HAS - 10 Epochen"

    table_normal.loc[(table_normal["Szenario"] == "Drohnenreferenzpunkte") &(table_normal["Messdurchgang"] == 2),"Messart_Tabelle"] = "HAS - 60 Epochen"

    table_stopgo = big_table_stopgo.loc[big_table_stopgo["Szenario"] != "Weingut"].copy()
    table_stopgo["Messart_Tabelle"] = "HAS - StopGo"


    table_acc = pd.concat([table_normal, table_stopgo],ignore_index=True)


######## Weingut gesamt ##########

    weingut_szenarien = ["Weingut mit Seedpoint", "Weingut ohne Seedpoint"]

    weingut_gesamt = table_acc.loc[table_acc["Szenario"].isin(weingut_szenarien)].copy()

    weingut_gesamt["Szenario"] = "Weingut gesamt"

    table_acc = pd.concat([table_acc, weingut_gesamt],ignore_index=True)


########## Tabelle nach Szenario, Messart und Lösungsstatus #########

    szenarien_tabelle = table_acc["Szenario"].unique()

    for szenario in szenarien_tabelle:
        szenario_table = table_acc.loc[table_acc["Szenario"] == szenario].copy()

        messarten_tabelle = szenario_table["Messart_Tabelle"].unique()

        for messart in messarten_tabelle:

            messart_table = szenario_table.loc[szenario_table["Messart_Tabelle"] == messart].copy()

            sol_stat = ["Gesamt", "Float", "Konvergierend"]

            for status in sol_stat:
                if status == "Gesamt":
                    status_table = messart_table.copy()

                elif status == "Float":
                    status_table = messart_table.loc[messart_table["Avail_Code"] == 1].copy()

                elif status == "Konvergierend":
                    status_table = messart_table.loc[messart_table["Avail_Code"] == 0].copy()

                if len(status_table) == 0:
                    continue


########## Kennwerte  ##########

                diff = status_table["Diff_HAS_SAPOS_cm"].to_numpy()

                abs_diff = np.sort(np.abs(diff))
                count_val = len(abs_diff)
                mean = np.mean(diff)
                median = np.median(diff)
                stdev = np.std(diff, ddof=1)
                rmse = np.sqrt(np.mean(diff ** 2))
                p68_calc = np.percentile(abs_diff, 68)
                p95_calc = np.percentile(abs_diff, 95)
                empir_68 = int(np.ceil(0.68 * count_val)) - 1
                empir_95 = int(np.ceil(0.95 * count_val)) - 1
                p68 = abs_diff[empir_68]
                p95 = abs_diff[empir_95]
                perc_below_40 = np.count_nonzero(abs_diff <= 40) / count_val * 100
                mittel_vdop = status_table["VDop"].mean()
                median_vdop = status_table["VDop"].median()
                mittel_galileo = status_table["GalileoSats"].mean()
                median_galileo = status_table["GalileoSats"].median()
                mittel_gps = status_table["GPSSats"].mean()
                median_gps = status_table["GPSSats"].median()


########## Zeile an Tabelle anhängen ##########

                table_accuracy_rows.append({
                    "Szenario": szenario,
                    "Messart": messart,
                    "Lösungsstatus": status,
                    "Anzahl": count_val,
                    "Mittelwert Differenz [cm]": mean,
                    "Median Differenz [cm]": median,
                    "Standardabweichung [cm]": stdev,
                    "RMSE [cm]": rmse,
                    "Mittelwert VDOP": mittel_vdop,
                    "Median VDOP": median_vdop,
                    "Mittelwert Galileo Satelliten": mittel_galileo,
                    "Median Galileo Satelliten": median_galileo,
                    "Mittelwert GPS Satelliten": mittel_gps,
                    "Median GPS Satelliten": median_gps,
                    "P68 interpoliert (Absolut) [cm]": p68_calc,
                    "P68 empirisch (Absolut) [cm]": p68,
                    "P95 interpoliert (Absolut) [cm]": p95_calc,
                    "P95 empirisch (Absolut) [cm]": p95,
                    "Anteil Differenz <= 40 cm [%]": perc_below_40
                })


########## Tabelle speichern ##########

    table_accuracy = pd.DataFrame(table_accuracy_rows)
    table_accuracy = table_accuracy.round(2)

    table_accuracy = table_accuracy[[
        "Szenario",
        "Messart",
        "Lösungsstatus",
        "Anzahl",
        "Mittelwert Differenz [cm]",
        "Median Differenz [cm]",
        "Standardabweichung [cm]",
        "RMSE [cm]",
        "Mittelwert VDOP",
        "Median VDOP",
        "Mittelwert Galileo Satelliten",
        "Median Galileo Satelliten",
        "Mittelwert GPS Satelliten",
        "Median GPS Satelliten",
        "P68 interpoliert (Absolut) [cm]",
        "P68 empirisch (Absolut) [cm]",
        "P95 interpoliert (Absolut) [cm]",
        "P95 empirisch (Absolut) [cm]",
        "Anteil Differenz <= 40 cm [%]"
    ]]

    save_path = os.path.join(save_location,"Tabelle_Höhengenauigkeit_HAS_SAPOS.csv")
    table_accuracy.to_csv(save_path, sep=";", decimal=",", index=False)

############################################################## Scatterplot (absol) Differenz / VDOP ############################################################

#########Trennu ng nach Lösungsstatus #############

    float_normal = big_table_normal["Avail_Code"] == 1
    convergence_normal = big_table_normal["Avail_Code"] == 0

    float_stopgo = big_table_stopgo["Avail_Code"] == 1
    convergence_stopgo = big_table_stopgo["Avail_Code"] == 0

    fig_scatter_status = make_subplots(rows=1, cols=2, subplot_titles=("Normale Messungen", "StopGo Messungen"))

### normal ###
#Float
    fig_scatter_status.add_trace(
        gr_obj.Scatter(
            x =big_table_normal.loc[float_normal, "VDop"],
            y = big_table_normal.loc[float_normal, "Diff_HAS_SAPOS_cm_abs"],
            mode = "markers",
            name = "Float",
            marker_color = "blue",
            text = ("Szenario: " + big_table_normal.loc[float_normal, "Szenario"] + "<br>Messpunkt: " + big_table_normal.loc[float_normal, "Punktname"]),
            hovertemplate = "%{text} <br>VDOP: %{x:.2f} <br>Absolute Höhendifferenz HAS - SAPOS: %{y:.2f} cm <extra></extra>",
            legendgroup = "Float",
            showlegend =True
        ),
        row = 1,
        col = 1
    )

#Konvergierend
    fig_scatter_status.add_trace(
        gr_obj.Scatter(
            x =big_table_normal.loc[convergence_normal, "VDop"],
            y = big_table_normal.loc[convergence_normal, "Diff_HAS_SAPOS_cm_abs"],
            mode = "markers",
            name = "Konvergierend",
            marker_color = "orange",
            text = ("Szenario: " + big_table_normal.loc[convergence_normal, "Szenario"] + "<br>Messpunkt: " + big_table_normal.loc[convergence_normal, "Punktname"]),
            hovertemplate = "%{text} <br>VDOP: %{x:.2f} <br>Absolute Höhendifferenz HAS - SAPOS: %{y:.2f} cm <extra></extra>",
            legendgroup = "Konvergierend",
            showlegend =True
        ),
        row = 1,
        col = 1
    )

### StopGo ###
#Float
    fig_scatter_status.add_trace(
        gr_obj.Scatter(
            x =big_table_stopgo.loc[float_stopgo, "VDop"],
            y = big_table_stopgo.loc[float_stopgo, "Diff_HAS_SAPOS_cm_abs"],
            mode = "markers",
            name = "Float",
            marker_color = "blue",
            text = ("Szenario: " + big_table_stopgo.loc[float_stopgo, "Szenario"] + "<br>Messpunkt: " + big_table_stopgo.loc[float_stopgo, "Punktname"]),
            hovertemplate = "%{text} <br>VDOP: %{x:.2f} <br>Absolute Höhendifferenz HAS - SAPOS: %{y:.2f} cm <extra></extra>",
            legendgroup = "Float",
            showlegend =False
        ),
        row = 1,
        col = 2
    )

#Konvergierend
    fig_scatter_status.add_trace(
        gr_obj.Scatter(
            x =big_table_stopgo.loc[convergence_stopgo, "VDop"],
            y = big_table_stopgo.loc[convergence_stopgo, "Diff_HAS_SAPOS_cm_abs"],
            mode = "markers",
            name = "Konvergierend",
            marker_color = "orange",
            text = ("Szenario: " + big_table_stopgo.loc[convergence_stopgo, "Szenario"] + "<br>Messpunkt: " + big_table_stopgo.loc[convergence_stopgo, "Punktname"]),
            hovertemplate = "%{text} <br>VDOP: %{x:.2f} <br>Absolute Höhendifferenz HAS - SAPOS: %{y:.2f} cm <extra></extra>",
            legendgroup = "Konvergierend",
            showlegend =False
        ),
        row = 1,
        col = 2
    )

#Beschriften
    fig_scatter_status.update_layout(
        title = "Scatterplot der absoluten Höhendifferenz HAS - SAPOS und des VDOP getrennt nach Lösungsstatus",
        hovermode = "closest",
        template = "plotly_white"
    )

    fig_scatter_status.update_xaxes(title_text="VDOP", showgrid=True, rangemode="tozero", row=1, col=1)
    fig_scatter_status.update_xaxes(title_text="VDOP", showgrid=True, rangemode="tozero", row=1, col=2)
    fig_scatter_status.update_yaxes(title_text="Absolute Höhendifferenz HAS - SAPOS [cm]", showgrid=True, rangemode="tozero", row=1, col=1)
    fig_scatter_status.update_yaxes(title_text="Absolute Höhendifferenz HAS - SAPOS [cm]", showgrid=True, rangemode="tozero", row=1, col=2)

#Speichern
    save_path = os.path.join(save_location, "Scatterplot_Absolute_Differenz_VDOP_Lösungsstatus")
    fig_scatter_status.write_html(save_path + ".html")
    fig_scatter_status.write_image(save_path + ".png", width=1400, height=700)




#########Trennung nach Szenario #############

    fig_scatter_szenario = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Normale Messungen", "StopGo Messungen")
    )


### Normal ####
    szenarien_scatter_normal = big_table_normal["Szenario"].unique()

    for szenario in szenarien_scatter_normal:

        szenario_table = big_table_normal.loc[big_table_normal["Szenario"] == szenario].copy()

        fig_scatter_szenario.add_trace(
            gr_obj.Scatter(
                x =szenario_table["VDop"],
                y = szenario_table["Diff_HAS_SAPOS_cm_abs"],
                mode = "markers",
                name = szenario,
                marker_color = szenario_farben.get(szenario),
                text= ("Szenario: " + szenario_table["Szenario"] + "<br>Messpunkt: " + szenario_table["Punktname"]),
                hovertemplate = "%{text}<br>VDOP: %{x:.2f}<br>Absolute Höhendifferenz HAS - SAPOS: %{y:.2f} cm<extra></extra>",
                legendgroup = szenario,
                showlegend =True
            ),
            row = 1,
            col = 1
        )


### StopGo ####
    szenarien_scatter_stopgo = big_table_stopgo["Szenario"].unique()

    for szenario in szenarien_scatter_stopgo:

        szenario_table = big_table_stopgo.loc[big_table_stopgo["Szenario"] == szenario].copy()

        fig_scatter_szenario.add_trace(
            gr_obj.Scatter(
                x =szenario_table["VDop"],
                y = szenario_table["Diff_HAS_SAPOS_cm_abs"],
                mode = "markers",
                name = szenario,
                showlegend = False,
                marker_color = szenario_farben.get(szenario),
                text= ("Szenario: " + szenario_table["Szenario"] + "<br>Messpunkt: " + szenario_table["Punktname"]),
                legendgroup = szenario,
                hovertemplate = "%{text}<br>VDOP: %{x:.2f}<br>Absolute Höhendifferenz HAS - SAPOS: %{y:.2f} cm<extra></extra>"
            ),
            row = 1,
            col = 2
        )


#Beschriften
    fig_scatter_szenario.update_layout(
        title = "Scatterplot der absoluten Höhendifferenz HAS - SAPOS und des VDOP getrennt nach Szenario",
        hovermode = "closest",
        template = "plotly_white"
    )

    fig_scatter_szenario.update_xaxes(title_text="VDOP", showgrid=True, rangemode="tozero", row=1, col=1)
    fig_scatter_szenario.update_xaxes(title_text="VDOP", showgrid=True, rangemode="tozero", row=1, col=2)
    fig_scatter_szenario.update_yaxes(title_text="Absolute Höhendifferenz HAS - SAPOS [cm]", showgrid=True, rangemode="tozero", row=1, col=1)
    fig_scatter_szenario.update_yaxes(title_text="Absolute Höhendifferenz HAS - SAPOS [cm]", showgrid=True, rangemode="tozero", row=1, col=2)

#Speichern
    save_path = os.path.join(save_location, "Scatterplot_Absolute_Differenz_VDOP_Szenario")
    fig_scatter_szenario.write_html(save_path + ".html")
    fig_scatter_szenario.write_image(save_path + ".png", width=1400, height=700)

    print("\nAlles gespeichert!")
    tools.threedots()  