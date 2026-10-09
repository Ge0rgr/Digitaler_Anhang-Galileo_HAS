from matplotlib.table import table
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

# Analyse der Präzision, getrennt nach Messposition und Messdurchgängen. Erstellung von Boxplots, Kreisdiagrammen, Perzentilplots, Scatterplots, Tabellen und einem Balkendiagramm
def precision_evaluation(input_data, save_location):

    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    tables_pro_durchgang = []
    tables_pro_messpos = []

############ Vorbereitung für Boxplots ############

    for file in files:

        filename = os.path.splitext(os.path.basename(file))[0]

        table = pd.read_csv(file, sep =";", decimal=",")

        table["Grosse_achse"] = table[["XStdDist", "YStdDist"]].max(axis=1) 

        table["Kleine_achse"] = table[["XStdDist", "YStdDist"]].min(axis=1)

        table["Achsen_Ratio"] = (table["Grosse_achse"] / table["Kleine_achse"])

        table["Exzentrizität"] = np.sqrt((1- (table["Kleine_achse"] ** 2 / table["Grosse_achse"] ** 2)))

        table["Lösungsstatus"] = np.where(table["Avail_Code"] == 1, "Float", np.where(table["Avail_Code"] == 0, "Konvergierend", "Float = Konvergierend"))




########### Ergänzung der Szenarien für die Boxplots ###########
        if filename.startswith("parkplatz"):
            table["Szenario"] = "Parkplatz"

        elif filename.startswith("feldweg"):
            table["Szenario"] = "Feldweg"

        elif filename.startswith("schlosspark_trier"):
            table["Szenario"] = "Schlosspark mit Seedpoint"

        elif filename.startswith("wein_ohne"):
            table["Szenario"] = "Weinberg"

        elif filename.startswith("wein_nur"):
            table["Szenario"] = "Drohnenreferenzpunkte"

        elif filename.startswith("weingut_seedpoint"):
            table["Szenario"] = ("Weingut mit Seedpoint")

        elif filename.startswith("weingut_ohne") or filename.startswith("weingut_has"):
            table["Szenario"] = ("Weingut ohne Seedpoint")

        elif filename.startswith("forst_has"):
            table["Szenario"] = ("Forst mit Seedpoint")

        elif filename.startswith("gruenflaeche"):
            table["Szenario"] = ("Grünfläche mit Seedpoint")


########### Einteilung der Tabellen für die plots ###########


        if "pro_durchgang" in filename:
            table["Methode"] = "Pro Messdurchgang"
            tables_pro_durchgang.append(table)


        elif "pro_messpos" in filename:
            table["Methode"] = "Pro Messposition"
            tables_pro_messpos.append(table)


        #print(tables_pro_durchgang)
        #print(tables_pro_messpos)

    big_table_pro_durchgang = pd.concat(tables_pro_durchgang, ignore_index=True)

    big_table_pro_messpos = pd.concat(tables_pro_messpos, ignore_index=True)


####################################### Tabellen erstellen #################################################################


########## Tabelle pro Messdurchgang ##########

    table_durchgang_rows = []

    weingut_szenarien = ["Weingut mit Seedpoint", "Weingut ohne Seedpoint"]
    weingut_gesamt_durchgang = big_table_pro_durchgang.loc[big_table_pro_durchgang["Szenario"].isin(weingut_szenarien)].copy()
    
    weingut_gesamt_durchgang["Szenario"] = "Weingut gesamt"

    table_durchgang = pd.concat([big_table_pro_durchgang, weingut_gesamt_durchgang], ignore_index=True)

    szenarien_tabelle_durchgang = table_durchgang["Szenario"].unique()

    for szenario in szenarien_tabelle_durchgang:

        szenario_table = table_durchgang.loc[table_durchgang["Szenario"] == szenario].copy()

########## Gesamtes Szenario ##########

        grosse_achse = szenario_table["Grosse_achse"].to_numpy() * 100
        sorted_grosse_achse = np.sort(grosse_achse)
        count_table = len(grosse_achse)
        kleine_achse = szenario_table["Kleine_achse"].to_numpy() * 100
        achsen_ratio = szenario_table["Achsen_Ratio"].to_numpy()
        exzentrizitaet = szenario_table["Exzentrizität"].to_numpy()
        mittel_grosse_achse = np.mean(grosse_achse)
        median_grosse_achse = np.median(grosse_achse)
        maximum_grosse_achse = np.max(grosse_achse)
        mittel_kleine_achse = np.mean(kleine_achse)
        median_kleine_achse = np.median(kleine_achse)
        p95_calc = np.percentile(grosse_achse, 95)
        empir_95 = int(np.ceil(0.95 * count_table)) - 1
        p95_emp = sorted_grosse_achse[empir_95]
        mittel_achsen_ratio = np.mean(achsen_ratio)
        median_achsen_ratio = np.median(achsen_ratio)
        median_exzentrizitaet = np.median(exzentrizitaet)


        table_durchgang_rows.append({
            "Szenario": szenario,
            "Lösungsstatus": "Gesamt",
            "Anzahl Ellipsen": count_table,
            "Mittelwert Große Achse [cm]": mittel_grosse_achse,
            "Median Große Achse [cm]": median_grosse_achse,
            "Maximum Große Achse [cm]": maximum_grosse_achse,
            "Mittelwert Kleine Achse [cm]": mittel_kleine_achse,
            "Median Kleine Achse [cm]": median_kleine_achse,
            "P95 Große Achse interpoliert [cm]": p95_calc,
            "P95 Große Achse empirisch [cm]": p95_emp,
            "Mittelwert Achsen Ratio": mittel_achsen_ratio,
            "Median Achsen Ratio": median_achsen_ratio,
            "Median Exzentrizität": median_exzentrizitaet
        })


########## Nach Lösungsstatus getrennt ##########

        sol_stat = ["Float", "Konvergierend"]

        for status in sol_stat:

            status_table = szenario_table.loc[szenario_table["Lösungsstatus"] == status].copy()

            if len(status_table) == 0:
                continue


            grosse_achse = status_table["Grosse_achse"].to_numpy() * 100
            sorted_grosse_achse = np.sort(grosse_achse)
            count_table = len(grosse_achse)
            kleine_achse = status_table["Kleine_achse"].to_numpy() * 100
            achsen_ratio = status_table["Achsen_Ratio"].to_numpy()
            exzentrizitaet = status_table["Exzentrizität"].to_numpy()
            mittel_grosse_achse = np.mean(grosse_achse)
            median_grosse_achse = np.median(grosse_achse)
            maximum_grosse_achse = np.max(grosse_achse)
            mittel_kleine_achse = np.mean(kleine_achse)
            median_kleine_achse = np.median(kleine_achse)
            p95_calc = np.percentile(grosse_achse, 95)
            empir_95 = int(np.ceil(0.95 * count_table)) - 1
            p95_emp = sorted_grosse_achse[empir_95]
            mittel_achsen_ratio = np.mean(achsen_ratio)
            median_achsen_ratio = np.median(achsen_ratio)
            median_exzentrizitaet = np.median(exzentrizitaet)


            table_durchgang_rows.append({
                "Szenario": szenario,
                "Lösungsstatus": status,
                "Anzahl Ellipsen": count_table,
                "Mittelwert Große Achse [cm]": mittel_grosse_achse,
                "Median Große Achse [cm]": median_grosse_achse,
                "Maximum Große Achse [cm]": maximum_grosse_achse,
                "Mittelwert Kleine Achse [cm]": mittel_kleine_achse,
                "Median Kleine Achse [cm]": median_kleine_achse,
                "P95 Große Achse interpoliert [cm]": p95_calc,
                "P95 Große Achse empirisch [cm]": p95_emp,
                "Mittelwert Achsen Ratio": mittel_achsen_ratio,
                "Median Achsen Ratio": median_achsen_ratio,
                "Median Exzentrizität": median_exzentrizitaet
            })


########## Speichern ##########

    table_durchgang_ergebnis = pd.DataFrame(table_durchgang_rows)

    table_durchgang_ergebnis = table_durchgang_ergebnis.round(2)

    table_durchgang_ergebnis = table_durchgang_ergebnis[[
        "Szenario",
        "Lösungsstatus",
        "Anzahl Ellipsen",
        "Mittelwert Große Achse [cm]",
        "Median Große Achse [cm]",
        "Maximum Große Achse [cm]",
        "Mittelwert Kleine Achse [cm]",
        "Median Kleine Achse [cm]",
        "P95 Große Achse interpoliert [cm]",
        "P95 Große Achse empirisch [cm]",
        "Mittelwert Achsen Ratio",
        "Median Achsen Ratio",
        "Median Exzentrizität"
    ]]

    save_path = os.path.join(save_location, "Tabelle_Pro_Messdurchgang.csv")
    table_durchgang_ergebnis.to_csv(save_path, sep=";", decimal=",", index=False)



########## Tabelle pro Messposition ##########

    table_messpos_rows = []

    weingut_gesamt_messpos = big_table_pro_messpos.loc[big_table_pro_messpos["Szenario"].isin(weingut_szenarien)].copy()

    weingut_gesamt_messpos["Szenario"] = "Weingut gesamt"

    table_messpos = pd.concat([big_table_pro_messpos, weingut_gesamt_messpos], ignore_index=True)

    szenarien_tabelle_messpos = table_messpos["Szenario"].unique()

    for szenario in szenarien_tabelle_messpos:

        szenario_table = table_messpos.loc[table_messpos["Szenario"] == szenario].copy()


########## Gesamtes Szenario ##########


        grosse_achse = szenario_table["Grosse_achse"].to_numpy() * 100
        sorted_grosse_achse = np.sort(grosse_achse)
        count_table = len(grosse_achse)
        kleine_achse = szenario_table["Kleine_achse"].to_numpy() * 100
        achsen_ratio = szenario_table["Achsen_Ratio"].to_numpy()
        exzentrizitaet = szenario_table["Exzentrizität"].to_numpy()
        mittel_grosse_achse = np.mean(grosse_achse)
        median_grosse_achse = np.median(grosse_achse)
        maximum_grosse_achse = np.max(grosse_achse)
        mittel_kleine_achse = np.mean(kleine_achse)
        median_kleine_achse = np.median(kleine_achse)
        p95_calc = np.percentile(grosse_achse, 95)
        empir_95 = int(np.ceil(0.95 * count_table)) - 1
        p95_emp = sorted_grosse_achse[empir_95]
        mittel_achsen_ratio = np.mean(achsen_ratio)
        median_achsen_ratio = np.median(achsen_ratio)
        median_exzentrizitaet = np.median(exzentrizitaet)


        table_messpos_rows.append({
            "Szenario": szenario,
            "Lösungsstatus": "Gesamt",
            "Anzahl Ellipsen": count_table,
            "Mittelwert Große Achse [cm]": mittel_grosse_achse,
            "Median Große Achse [cm]": median_grosse_achse,
            "Maximum Große Achse [cm]": maximum_grosse_achse,
            "Mittelwert Kleine Achse [cm]": mittel_kleine_achse,
            "Median Kleine Achse [cm]": median_kleine_achse,
            "P95 Große Achse interpoliert [cm]": p95_calc,
            "P95 Große Achse empirisch [cm]": p95_emp,
            "Mittelwert Achsen Ratio": mittel_achsen_ratio,
            "Median Achsen Ratio": median_achsen_ratio,
            "Median Exzentrizität": median_exzentrizitaet
        })


########## Nach Lösungsstatus getrennt ##########

        sol_stat = ["Float", "Konvergierend", "Float = Konvergierend"]

        for status in sol_stat:

            status_table = szenario_table.loc[szenario_table["Lösungsstatus"] == status].copy()

            if len(status_table) == 0:
                continue

            grosse_achse = status_table["Grosse_achse"].to_numpy() * 100
            sorted_grosse_achse = np.sort(grosse_achse)
            count_table = len(grosse_achse)
            kleine_achse = status_table["Kleine_achse"].to_numpy() * 100
            achsen_ratio = status_table["Achsen_Ratio"].to_numpy()
            exzentrizitaet = status_table["Exzentrizität"].to_numpy()
            mittel_grosse_achse = np.mean(grosse_achse)
            median_grosse_achse = np.median(grosse_achse)
            maximum_grosse_achse = np.max(grosse_achse)
            mittel_kleine_achse = np.mean(kleine_achse)
            median_kleine_achse = np.median(kleine_achse)
            p95_calc = np.percentile(grosse_achse, 95)
            empir_95 = int(np.ceil(0.95 * count_table)) - 1
            p95_emp = sorted_grosse_achse[empir_95]
            mittel_achsen_ratio = np.mean(achsen_ratio)
            median_achsen_ratio = np.median(achsen_ratio)
            median_exzentrizitaet = np.median(exzentrizitaet)


            table_messpos_rows.append({
                "Szenario": szenario,
                "Lösungsstatus": status,
                "Anzahl Ellipsen": count_table,
                "Mittelwert Große Achse [cm]": mittel_grosse_achse,
                "Median Große Achse [cm]": median_grosse_achse,
                "Maximum Große Achse [cm]": maximum_grosse_achse,
                "Mittelwert Kleine Achse [cm]": mittel_kleine_achse,
                "Median Kleine Achse [cm]": median_kleine_achse,
                "P95 Große Achse interpoliert [cm]": p95_calc,
                "P95 Große Achse empirisch [cm]": p95_emp,
                "Mittelwert Achsen Ratio": mittel_achsen_ratio,
                "Median Achsen Ratio": median_achsen_ratio,
                "Median Exzentrizität": median_exzentrizitaet
            })


########## Speichern ##########

    table_messpos_ergebnis = pd.DataFrame(table_messpos_rows)

    table_messpos_ergebnis = table_messpos_ergebnis.round(2)

    table_messpos_ergebnis = table_messpos_ergebnis[[
        "Szenario",
        "Lösungsstatus",
        "Anzahl Ellipsen",
        "Mittelwert Große Achse [cm]",
        "Median Große Achse [cm]",
        "Maximum Große Achse [cm]",
        "Mittelwert Kleine Achse [cm]",
        "Median Kleine Achse [cm]",
        "P95 Große Achse interpoliert [cm]",
        "P95 Große Achse empirisch [cm]",
        "Mittelwert Achsen Ratio",
        "Median Achsen Ratio",
        "Median Exzentrizität"
    ]]

    save_path = os.path.join(save_location, "Tabelle_Pro_Messposition.csv")
    table_messpos_ergebnis.to_csv(save_path, sep=";", decimal=",", index=False)

#################################################################### Boxplots erstellen ############################################################################
        

############### Boxplot pro Messdurchgang #####################

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

    np.random.seed(1)

    fig_box_pro_durchgang = gr_obj.Figure()

    szenarien_pro_durchgang = big_table_pro_durchgang["Szenario"].unique()

    for i, szenario in enumerate(szenarien_pro_durchgang):

        szenario_table = big_table_pro_durchgang.loc[big_table_pro_durchgang["Szenario"] == szenario].copy()

        float_sol = szenario_table["Avail_Code"] == 1
        convergence_sol = szenario_table["Avail_Code"] == 0

        fig_box_pro_durchgang.add_trace(
            gr_obj.Box(
                x = np.full(len(szenario_table), i),
                y = szenario_table["Grosse_achse"] *100,
                name = szenario,
                boxmean = True,
                boxpoints = "all",
                marker = dict(opacity=0),
                legendgroup = szenario,
                line_color = szenario_farben.get(szenario),
                marker_color = szenario_farben.get(szenario),
                showlegend = True
            )
        )


        ############ Echte Punkte, aber versteckt; Nur Hover #########

        ######## HAS float ############
        points = szenario_table.loc[float_sol].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_pro_durchgang.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Grosse_achse"] *100,
                mode="markers",
                name="Float",
                hoveron = "points",
                marker_color = "blue",
                showlegend=False,
                text=points["Punktname"].astype(str),
                hovertemplate="Messpunkt: %{text} <br> Lange Halbachse: %{y:.2f} cm <extra></extra>",
                legendgroup=szenario
            )
        )


        ########## HAS convergence ##############
        points = szenario_table.loc[convergence_sol].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_pro_durchgang.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Grosse_achse"] *100,
                mode="markers",
                name="Konvergierend",
                hoveron = "points",
                marker_color = "orange",
                showlegend=False,
                text=points["Punktname"].astype(str),
                hovertemplate="Messpunkt: %{text} <br> Lange Halbachse: %{y:.2f} cm <extra></extra>",
                legendgroup=szenario
            )
        )


  ########## Fake Punkte, nur für Legende ###########
        
    ########## HAS float ##############
    fig_box_pro_durchgang.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float",
            marker = dict( color = "blue", symbol = "circle")
        )
    )

    ######## HAS convergence ############
    fig_box_pro_durchgang.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Konvergierend",
            marker = dict( color = "orange", symbol = "circle")
        )
    )

###### Beschriften######

    fig_box_pro_durchgang.update_layout(
        title = "Boxplot der langen Halbachse pro Messdurchgang",
        xaxis_title = "Messszenario",
        yaxis_title = "Lange Halbachse [cm]",
        hovermode = "closest",
        template = "plotly_white"
    )

    fig_box_pro_durchgang.update_yaxes(
        hoverformat = ".2f",
        showgrid = True
    )

    fig_box_pro_durchgang.update_xaxes(
        tickmode = "array",
        tickvals = np.arange(len(szenarien_pro_durchgang)),
        ticktext = szenarien_pro_durchgang,
        showgrid = False
    )

##### speichern #######

    save_path = os.path.join(save_location, "Boxplot_Große_Achse_pro_Messdurchgang")
    fig_box_pro_durchgang.write_html(save_path + ".html")
    fig_box_pro_durchgang.write_image(save_path + ".png", width=1400, height=700)



######### Boxplot pro Messposition ############

    np.random.seed(1)
    
    fig_box_pro_messposition = gr_obj.Figure()

    szenarien_pro_messpos = big_table_pro_messpos["Szenario"].unique()

    for i, szenario in enumerate(szenarien_pro_messpos):

        szenario_table = big_table_pro_messpos.loc[big_table_pro_messpos["Szenario"] == szenario].copy()

        float_sol = szenario_table["Avail_Code"] == 1
        convergence_sol = szenario_table["Avail_Code"] == 0
        equal_sol = szenario_table["Avail_Code"] == 2

        fig_box_pro_messposition.add_trace(
            gr_obj.Box(
                x = np.full(len(szenario_table), i),
                y = szenario_table["Grosse_achse"] *100,
                name = szenario,
                boxmean = True,
                boxpoints = "all",
                marker = dict(opacity=0),
                legendgroup = szenario,
                line_color = szenario_farben.get(szenario),
                marker_color = szenario_farben.get(szenario),
                showlegend = True
            )
        )


        ############ Echte Punkte, aber versteckt; Nur Hover #########

        ######### HAS float#########
        points = szenario_table.loc[float_sol].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_pro_messposition.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Grosse_achse"] *100,
                mode="markers",
                name="Float",
                hoveron = "points",
                marker_color = "blue",
                showlegend=False,
                text=points["Punktname"].astype(str),
                hovertemplate="Messpunkt: %{text} <br> Lange Halbachse: %{y:.2f} cm <extra></extra>",
                legendgroup=szenario
            )
        )


        ###### HAS convergence #########
        points = szenario_table.loc[convergence_sol].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_pro_messposition.add_trace(
            gr_obj.Scatter(
                x=i + jitter,
                y=points["Grosse_achse"] *100,
                mode="markers",
                name="Konvergierend",
                hoveron = "points",
                marker_color = "orange",
                showlegend=False,
                text=points["Punktname"].astype(str),
                hovertemplate="Messpunkt: %{text} <br> Lange Halbachse: %{y:.2f} cm <extra></extra>",
                legendgroup=szenario
            )
        )


        ####### Beide Lösungen vorhanden ########
        points = szenario_table.loc[equal_sol].copy()
        jitter = np.random.uniform(-0.12, 0.12, len(points))

        fig_box_pro_messposition.add_trace(
            gr_obj.Scatter(
                x = i + jitter,
                y = points["Grosse_achse"] *100,
                mode = "markers",
                name = "Float = Konvergierend",
                marker_color = "purple",
                showlegend=False,
                text=points["Punktname"].astype(str),
                hovertemplate="Messpunkt: %{text} <br> Lange Halbachse: %{y:.2f} cm <extra></extra>",
                legendgroup=szenario
            )
        )


  ########## Fake Punkte, nur für Legende ###########
        
    #HAS float
    fig_box_pro_messposition.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float",
            marker_color = "blue"
        )
    )

    #HAS convergence
    fig_box_pro_messposition.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Konvergierend",
            marker_color = "orange"
        )
    )

    #beides 
    fig_box_pro_messposition.add_trace(
        gr_obj.Scatter(
            x = [None],
            y = [None],
            mode ="markers",
            name = "Float = Konvergierend",
            marker_color = "purple"
        )
    )

###### Beschriften######

    fig_box_pro_messposition.update_layout(
        title = "Boxplot der langen Halbachse pro Messposition",
        xaxis_title = "Messszenario",
        yaxis_title = "Lange Halbachse [cm]",
        hovermode = "closest",
        template = "plotly_white"
    )

    fig_box_pro_messposition.update_yaxes(
        hoverformat = ".2f",
        showgrid = True
    )

    fig_box_pro_messposition.update_xaxes(
        tickmode = "array",
        tickvals = np.arange(len(szenarien_pro_messpos)),
        ticktext = szenarien_pro_messpos,
        showgrid = False
    )

##### speichern #######

    save_path = os.path.join(save_location, "Boxplot_Große_Achse_pro_Messposition")
    fig_box_pro_messposition.write_html(save_path + ".html")
    fig_box_pro_messposition.write_image(save_path + ".png", width=1400, height=700)




    '''   #### Das war die Darstellung der Lösungsstatus in getrennte Boxplots => Teils zu wenige Punkte pro plot + unübersichtlicher; deshalb verworfen
#####float lösung#######
    fig_box_pro_durchgang.add_trace(
        gr_obj.Box(
            x=big_table_pro_durchgang.loc[float_sol, "Szenario"],
            y = big_table_pro_durchgang.loc[float_sol, "Grosse_achse"] *100,
            name = "Float",
            boxmean = True,
            boxpoints = "all",
            jitter = 0.3,
            pointpos=0,
            marker_color = "blue",
            line_color = "blue",
            text = big_table_pro_durchgang.loc[float_sol, "Punktname"],
            hovertemplate = "Messpunkt: %{text}<br>Lange Halbachse: %{y:.2f} cm<extra></extra>"
        )
    )


####### Convergence Lösung ########
    fig_box_pro_durchgang.add_trace(
        gr_obj.Box(
            x=big_table_pro_durchgang.loc[convergence_sol, "Szenario"],
            y=big_table_pro_durchgang.loc[convergence_sol, "Grosse_achse"] *100,
            name="Konvergierend",
            boxmean=True,
            boxpoints="all",
            jitter=0.3,
            pointpos=0,
            marker_color="orange",
            line_color="orange",
            text=big_table_pro_durchgang.loc[convergence_sol, "Punktname"],
            hovertemplate="Messpunkt: %{text}<br>Lange Halbachse: %{y:.2f} cm<extra></extra>"
        )
    )


###### Beschriften######

    fig_box_pro_durchgang.update_layout(
        title="Boxplot der langen Halbachse pro Messdurchgang",
        xaxis_title="Messszenario",
        yaxis_title="Lange Halbachse [cm]",
        boxmode="group",
        hovermode="closest",
        template="plotly_white"
    )

    fig_box_pro_durchgang.update_yaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )

##### speichern #######

    save_path = os.path.join(save_location, "Boxplot_Grosse_Achse_pro_Messdurchgang")
    fig_box_pro_durchgang.write_html(save_path + ".html")
    fig_box_pro_durchgang.write_image(save_path + ".png", width=1400, height=700)



############### Boxplot pro Messposition #####################

    float_sol = big_table_pro_messpos["Avail_Code"] == 1
    convergence_sol = big_table_pro_messpos["Avail_Code"] == 0
    equal_sol = big_table_pro_messpos["Avail_Code"] == 2

    fig_box_pro_messposition = gr_obj.Figure()

#####float lösung#######
    fig_box_pro_messposition.add_trace(
        gr_obj.Box(
            x=big_table_pro_messpos.loc[float_sol, "Szenario"],
            y = big_table_pro_messpos.loc[float_sol, "Grosse_achse"] *100,
            name = "Float",
            boxmean = True,
            boxpoints = "all",
            jitter = 0.3,
            pointpos=0,
            marker_color = "blue",
            line_color = "blue",
            text = big_table_pro_messpos.loc[float_sol, "Punktname"],
            hovertemplate = "Messpunkt: %{text}<br>Lange Halbachse: %{y:.2f} cm<extra></extra>"
        )
    )


####### Convergence Lösung ########
    fig_box_pro_messposition.add_trace(
        gr_obj.Box(
            x=big_table_pro_messpos.loc[convergence_sol, "Szenario"],
            y=big_table_pro_messpos.loc[convergence_sol, "Grosse_achse"] *100,
            name="Konvergierend",
            boxmean=True,
            boxpoints="all",
            jitter=0.3,
            pointpos=0,
            marker_color="orange",
            line_color="orange",
            text=big_table_pro_messpos.loc[convergence_sol, "Punktname"],
            hovertemplate="Messpunkt: %{text}<br>Lange Halbachse: %{y:.2f} cm<extra></extra>"
        )
    )

####### Beide Lösungen vorhanden ########

    fig_box_pro_messposition.add_trace(
        gr_obj.Box(
            x=big_table_pro_messpos.loc[equal_sol, "Szenario"],
            y=big_table_pro_messpos.loc[equal_sol, "Grosse_achse"] *100,
            name="Float = Konvergierend",
            boxmean=True,
            boxpoints="all",
            jitter=0.3,
            pointpos=0,
            marker_color="purple",
            line_color="purple",
            text=big_table_pro_messpos.loc[equal_sol, "Punktname"],
            hovertemplate="Messpunkt: %{text}<br>Lange Halbachse: %{y:.2f} cm<extra></extra>"
        )
    )


###### Beschriften######

    fig_box_pro_messposition.update_layout(
        title="Boxplot der langen Halbachse pro Messposition",
        xaxis_title="Messszenario",
        yaxis_title="Lange Halbachse [cm]",
        boxmode="group",
        hovermode="closest",
        template="plotly_white"
    )

    fig_box_pro_messposition.update_yaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )

##### speichern #######

    save_path = os.path.join(save_location, "Boxplot_Grosse_Achse_pro_Messposition")
    fig_box_pro_messposition.write_html(save_path + ".html")
    fig_box_pro_messposition.write_image(save_path + ".png", width=1400, height=700)

    '''


####################################################################### Scatterplots #########################################################################


######################### Pro Durchgang #######################

    fig_scatter_pro_durchgang = gr_obj.Figure()

    float_sol = big_table_pro_durchgang["Avail_Code"] == 1
    convergence_sol = big_table_pro_durchgang["Avail_Code"] == 0

##### nur float lösung #######
    fig_scatter_pro_durchgang.add_trace(
        gr_obj.Scatter(
            x=big_table_pro_durchgang.loc[float_sol, "Grosse_achse"] *100,
            y=big_table_pro_durchgang.loc[float_sol, "Achsen_Ratio"],
            mode="markers",
            name="Float",
            marker=dict(color="blue", size = 8),
            text=("Szenario: " + big_table_pro_durchgang.loc[float_sol, "Szenario"] + "<br>Messpunkt: " + big_table_pro_durchgang.loc[float_sol, "Punktname"]),
            hovertemplate="%{text}<br>Lange Halbachse: %{x:.2f} cm<br>Achsenverhältnis: %{y:.2f}<extra></extra>"
        )
    )


##### nur convergence lösung #######
    fig_scatter_pro_durchgang.add_trace(
        gr_obj.Scatter(
            x=big_table_pro_durchgang.loc[convergence_sol, "Grosse_achse"] *100,
            y=big_table_pro_durchgang.loc[convergence_sol, "Achsen_Ratio"],
            mode="markers",
            name="Konvergierend",
            marker=dict(color="orange", size = 8),
            text=("Szenario: " + big_table_pro_durchgang.loc[convergence_sol, "Szenario"] + "<br>Messpunkt: " + big_table_pro_durchgang.loc[convergence_sol, "Punktname"]),
            hovertemplate="%{text}<br>Lange Halbachse: %{x:.2f} cm<br>Achsenverhältnis: %{y:.2f}<extra></extra>"
        )
    )


    fig_scatter_pro_durchgang.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Achsenverhältnis = 1", annotation_position="top left")
    
###### Scatterplot beschriften ######

    fig_scatter_pro_durchgang.update_layout(
        title="Scatterplot der langen Halbachse und des Achsenverhältnisses pro Messdurchgang",
        xaxis_title="Lange Halbachse [cm]",
        yaxis_title="Achsenverhältnis",
        hovermode="closest",
        template="plotly_white"
    )

    fig_scatter_pro_durchgang.update_xaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )

    fig_scatter_pro_durchgang.update_yaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )

##### Scatterplot speichern #######

    save_path = os.path.join(save_location, "Scatterplot_Große_Achse_Achsenverhätnis_pro_Messdurchgang")
    fig_scatter_pro_durchgang.write_html(save_path + ".html")
    fig_scatter_pro_durchgang.write_image(save_path + ".png", width=1400, height=700)



###################### Pro Szenario und pro Messdurchgang #########################

    szenarien_pro_durchgang = big_table_pro_durchgang["Szenario"].unique()

    fig_scatter_szenario = gr_obj.Figure()

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

    for szenario in szenarien_pro_durchgang:

        szenario_table = big_table_pro_durchgang.loc[big_table_pro_durchgang["Szenario"] == szenario]

       
        fig_scatter_szenario.add_trace(
            gr_obj.Scatter(
                x=szenario_table["Grosse_achse"] *100,
                y=szenario_table["Achsen_Ratio"],
                mode="markers",
                name=szenario,
                marker = dict(color = szenario_farben.get(szenario), size = 8),
                text=("Szenario: " + szenario_table["Szenario"] + "<br>Messpunkt: " + szenario_table["Punktname"]),
                hovertemplate="%{text}<br>Lange Halbachse: %{x:.2f} cm<br>Achsenverhältnis: %{y:.2f}<extra></extra>"
            )
        )



    fig_scatter_szenario.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Achsenverhältnis = 1", annotation_position="top left")

########### SCattplter beschriften +##############

    fig_scatter_szenario.update_layout(
        title=f"Scatterplot der langen Halbachse und des Achsenverhältnisses pro Szenario und Messdurchgang",
        xaxis_title="Lange Halbachse [cm]",
        yaxis_title="Achsenverhältnis",
        hovermode="closest",
        template="plotly_white"
    )

    fig_scatter_szenario.update_xaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )

    fig_scatter_szenario.update_yaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )


######### Scatterplot speichern #############

    save_path = os.path.join(save_location, "Scatterplot_Große_Achse_Achsenverhältnis_pro_Messdurchgang_und_Szenario")

    fig_scatter_szenario.write_html(save_path + ".html")
    fig_scatter_szenario.write_image(save_path + ".png", width=1400, height=700)  



################## Scenarien pro Szenario und Messposition ################

    szenarien_pos = big_table_pro_messpos["Szenario"].unique()

    fig_scatter_szenario_pos = gr_obj.Figure()

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

    for szenario in szenarien_pos:

        szenario_table = big_table_pro_messpos.loc[big_table_pro_messpos["Szenario"] == szenario]

        fig_scatter_szenario_pos.add_trace(
            gr_obj.Scatter(
                x=szenario_table["Grosse_achse"] *100,
                y=szenario_table["Achsen_Ratio"],
                mode="markers",
                name=szenario,
                marker = dict(color = szenario_farben.get(szenario), size = 8),
                text=("Szenario: " + szenario_table["Szenario"] + "<br>Messpunkt: " + szenario_table["Punktname"]),
                hovertemplate="%{text}<br>Lange Halbachse: %{x:.2f} cm<br>Achsenverhältnis: %{y:.2f}<extra></extra>"
            )
        )



    fig_scatter_szenario_pos.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Achsenverhältnis = 1", annotation_position="top left")

########### SCattplter beschriften +##############

    fig_scatter_szenario_pos.update_layout(
        title=f"Scatterplot der langen Halbachse und des Achsenverhältnisses pro Szenario und Messposition",
        xaxis_title="Lange Halbachse [cm]",
        yaxis_title="Achsenverhältnis",
        hovermode="closest",
        template="plotly_white"
    )

    fig_scatter_szenario_pos.update_xaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )

    fig_scatter_szenario_pos.update_yaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )


######### Scatterplot speichern #############

    save_path = os.path.join(save_location, "Scatterplot_Große_Achse_Achsenverhältnis_pro_Messposition_und_Szenario")

    fig_scatter_szenario_pos.write_html(save_path + ".html")
    fig_scatter_szenario_pos.write_image(save_path + ".png", width=1400, height=700)  




############ Pro Messposition ###############

    fig_scatter_pro_messpos = gr_obj.Figure()
    
    float_sol = big_table_pro_messpos["Avail_Code"] == 1
    convergence_sol = big_table_pro_messpos["Avail_Code"] == 0
    both_sol = big_table_pro_messpos["Avail_Code"] == 2

#### nur float lösung #######

    fig_scatter_pro_messpos.add_trace(
        gr_obj.Scatter(
            x=big_table_pro_messpos.loc[float_sol, "Grosse_achse"] *100,
            y=big_table_pro_messpos.loc[float_sol, "Achsen_Ratio"],
            mode="markers",
            name="Float",
            marker=dict(color="blue", size = 8),
            text=("Szenario: " + big_table_pro_messpos.loc[float_sol, "Szenario"] + "<br>Messpunkt: " + big_table_pro_messpos.loc[float_sol, "Punktname"]),
            hovertemplate="%{text}<br>Lange Halbachse: %{x:.2f} cm<br>Achsenverhältnis: %{y:.2f}<extra></extra>"
        )

    )

#### nur convergence lösung #######

    fig_scatter_pro_messpos.add_trace(
        gr_obj.Scatter(
            x=big_table_pro_messpos.loc[convergence_sol, "Grosse_achse"] *100,
            y=big_table_pro_messpos.loc[convergence_sol, "Achsen_Ratio"],
            mode="markers",
            name="Konvergierend",
            marker=dict(color="orange", size = 8),
            text=("Szenario: " + big_table_pro_messpos.loc[convergence_sol, "Szenario"] + "<br>Messpunkt: " + big_table_pro_messpos.loc[convergence_sol, "Punktname"]),
            hovertemplate="%{text}<br>Lange Halbachse: %{x:.2f} cm<br>Achsenverhältnis: %{y:.2f}<extra></extra>"
        )  

    )

#### beide Lösungen vorhanden #######

    fig_scatter_pro_messpos.add_trace(
        gr_obj.Scatter(
            x=big_table_pro_messpos.loc[both_sol, "Grosse_achse"] *100,
            y=big_table_pro_messpos.loc[both_sol, "Achsen_Ratio"],
            mode="markers",
            name="Float = Konvergierend",
            marker=dict(color="purple", size = 8),
            text=("Szenario: " + big_table_pro_messpos.loc[both_sol, "Szenario"] + "<br>Messpunkt: " + big_table_pro_messpos.loc[both_sol, "Punktname"]),
            hovertemplate="%{text}<br>Lange Halbachse: %{x:.2f} cm<br>Achsenverhältnis: %{y:.2f}<extra></extra>"
        )   

    )


    fig_scatter_pro_messpos.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Achsenverhältnis = 1", annotation_position="top left")

    #### Scatterplot beschriften ######

    fig_scatter_pro_messpos.update_layout(
        title="Scatterplot der langen Halbachse und des Achsenverhältnisses pro Messposition",
        xaxis_title="Lange Halbachse [cm]",
        yaxis_title="Achsenverhältnis",
        hovermode="closest",
        template="plotly_white"
    )

    fig_scatter_pro_messpos.update_xaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )

    fig_scatter_pro_messpos.update_yaxes(
        hoverformat=".2f",
        showgrid=True,
        rangemode="tozero"
    )


##### Scatterplot speichern #######

    save_path = os.path.join(save_location, "Scatterplot_Große_Achse_Achsenverhältnis_pro_Messposition")
    fig_scatter_pro_messpos.write_html(save_path + ".html")
    fig_scatter_pro_messpos.write_image(save_path + ".png", width=1400, height=700)



###################################################### Graphen mit Akkumulierter Häufigkeit ###########################################################


################## Pro MEssdurchgang und Szenario####################

    fig_akkum_durchgang = gr_obj.Figure()
    

    for szenario in szenarien_pro_durchgang:

        szenario_table = big_table_pro_durchgang.loc[big_table_pro_durchgang["Szenario"] == szenario].copy()

        grosse_achsen_sort = np.sort(szenario_table["Grosse_achse"].to_numpy()) *100

        cumulative_percentage = (np.arange(1, len(grosse_achsen_sort)+1) / len(grosse_achsen_sort)) *100

        count_val = len(grosse_achsen_sort)

        #empir_68 = int(np.ceil(0.68 * count_val)) - 1
        empir_95 = int(np.ceil(0.95 * count_val)) - 1

        #p68 = grosse_achsen_sort[empir_68]
        p95 = grosse_achsen_sort[empir_95]

        #prop_p68 = (np.count_nonzero(grosse_achsen_sort <= p68)/ count_val* 100)
        prop_p95 = (np.count_nonzero(grosse_achsen_sort <= p95)/ count_val* 100)

        fig_akkum_durchgang.add_trace(
            gr_obj.Scatter(
                x = grosse_achsen_sort,
                y = cumulative_percentage,
                mode = "lines",
                name = szenario,
                legendgroup=szenario,
                line = dict(color = szenario_farben.get(szenario)),
                hovertemplate=("Szenario: " + str(szenario) +  "<br>Große Halbachse %{x:.2f} cm <br>Kumulativer Anteil: %{y:.2f} % <extra></extra>")
            )
        )
    
        fig_akkum_durchgang.add_trace(
            gr_obj.Scatter(
                #x=[p68, p95],
                #y=[prop_p68, prop_p95],
                x=[p95],
                y=[prop_p95],                
                mode = "markers",
                legendgroup=szenario,
                #name = "68 und 95 Perzentile von" + str(szenario),
                name = "95 Perzentil von" + str(szenario),
                #text = ["P68", "P95"],
                text = ["P95"],
                marker=dict(color="red", size=10),
                hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
                showlegend=False
            )
        )

    ######## Fake Punkt; für Legende######################
    fig_akkum_durchgang.add_trace(
        gr_obj.Scatter(
            x=[None],
            y=[None],
            mode = "markers",
            name = "Empirisches P95",
            marker=dict(color="red", size=10),
            showlegend = True
        )
    )
    
    '''# unnötig
    fig_akkum_durchgang.add_hline(
        y=68,
        line_dash="dash",
        line_color="gray",
        annotation_text="68 %",
        annotation_position="bottom right"
    )
    '''
    
    fig_akkum_durchgang.add_hline(
        y=95,
        line_dash="dot",
        line_color="gray",
        annotation_text="95 %",
        annotation_position="bottom right"
    )
    
    ''' #Zu unübersichtlich
    fig_akkum_durchgang.add_vline(
        x=p68,
        line_dash="dash",
        line_color="gray",
        annotation_text= f"68 Perzentil: {p68:.2f} m",
        annotation_position="top right"
    )
    
    fig_akkum_durchgang.add_vline(
        x=p95,
        line_dash="dot",
        line_color="gray",
        annotation_text= f"95 Perzentil: {p95:.2f} m",
        annotation_position="top left"
    )
    '''

######### Linienplot beschriften ####################

    fig_akkum_durchgang.update_layout(
        title= ("Empirische kumulative Verteilung der großen Halbachse pro Messdurchgang"),
        xaxis_title = "Große Halbachse [cm]",
        yaxis_title = "Kumulativer Anteil [%]",
        legend=dict(groupclick="togglegroup"),
        hovermode = "closest",
        template = "plotly_white"
    )
    
    fig_akkum_durchgang.update_xaxes(
        showgrid = True,
        rangemode = "tozero"
    )
    
    fig_akkum_durchgang.update_yaxes(
        showgrid = True,
        range=[0,101],
        dtick=10
    )

########### Linienplot speichern ###############

    save_path = os.path.join(save_location, "Linienplot_perzentile_der_großen_Halbachse_pro_messdurchgang")
    fig_akkum_durchgang.write_html(save_path + ".html")
    fig_akkum_durchgang.write_image(save_path + ".png", width=1400, height=700)



################## Pro MEssposition und Szenario####################

    fig_akkum_pos = gr_obj.Figure()
    

    for szenario in szenarien_pos:

        szenario_table = big_table_pro_messpos.loc[big_table_pro_messpos["Szenario"] == szenario].copy()

        grosse_achsen_sort = np.sort(szenario_table["Grosse_achse"].to_numpy()) *100

        cumulative_percentage = (np.arange(1, len(grosse_achsen_sort)+1) / len(grosse_achsen_sort)) *100

        count_val = len(grosse_achsen_sort)

        #empir_68 = int(np.ceil(0.68 * count_val)) - 1
        empir_95 = int(np.ceil(0.95 * count_val)) - 1

        #p68 = grosse_achsen_sort[empir_68]
        p95 = grosse_achsen_sort[empir_95]

        #prop_p68 = (np.count_nonzero(grosse_achsen_sort <= p68)/ count_val* 100)
        prop_p95 = (np.count_nonzero(grosse_achsen_sort <= p95)/ count_val* 100)

        fig_akkum_pos.add_trace(
            gr_obj.Scatter(
                x = grosse_achsen_sort,
                y = cumulative_percentage,
                mode = "lines",
                legendgroup=szenario,
                name = szenario,
                line = dict(color = szenario_farben.get(szenario)),
                hovertemplate=("Szenario: " + str(szenario) +  "<br>Große Halbachse %{x:.2f} cm <br>Kumulativer Anteil: %{y:.2f} % <extra></extra>")
            )
        )
    
        fig_akkum_pos.add_trace(
            gr_obj.Scatter(
                #x=[p68, p95],
                #y=[prop_p68, prop_p95],
                x=[p95],
                y=[prop_p95],
                mode = "markers",
                #name = "68 und 95 Perzentile von" + str(szenario),
                name = "95 Perzentil von" + str(szenario),
                legendgroup=szenario,
                #text = ["P68", "P95"],
                text = ["P95"],
                marker=dict(color="red", size=10),
                hovertemplate=("Perzentil: %{text} <br>Empirischer Schwellenwert: %{x:.2f} cm<br> Anteil <= Schwellenwert: %{y:.2f} %<extra></extra>"),
                showlegend=False
            )
        )

    ######## Fake Punkt; für Legende######################
    fig_akkum_pos.add_trace(
        gr_obj.Scatter(
            x=[None],
            y=[None],
            mode = "markers",
            name = "Empirisches P95",
            marker=dict(color="red", size=10),
            showlegend = True
        )
    )
    
    '''
    fig_akkum_pos.add_hline(
        y=68,
        line_dash="dash",
        line_color="gray",
        annotation_text="68 %",
        annotation_position="bottom right"
    )
    '''
    
    fig_akkum_pos.add_hline(
        y=95,
        line_dash="dot",
        line_color="gray",
        annotation_text="95 %",
        annotation_position="bottom right"
    )

############ Linienplot beshriften #################
    
    fig_akkum_pos.update_layout(
        title= ("Empirische kumulative Verteilung der großen Halbachse pro Messposition"),
        xaxis_title = "Große Halbachse [cm]",
        yaxis_title = "Kumulativer Anteil [%]",
        hovermode = "closest",
        legend=dict(groupclick="togglegroup"),
        template = "plotly_white"
    )
    
    fig_akkum_pos.update_xaxes(
        showgrid = True,
        rangemode = "tozero"
    )
    
    fig_akkum_pos.update_yaxes(
        showgrid = True,
        range=[0,101],
        dtick=10
    )

############ Linienplot speichern ################

    save_path = os.path.join(save_location, "Linienplot_perzentile_der_großen_Halbachse_pro_messposition")
    fig_akkum_pos.write_html(save_path + ".html")
    fig_akkum_pos.write_image(save_path + ".png", width=1400, height=700)




###################################################### Kreisdiagramm für Richtung ############################################################

 ######################## Pro Messdurchgang ########################

    fig_richtung_durchgang = gr_obj.Figure()

    for szenario in szenarien_pro_durchgang:

        szenario_table = big_table_pro_durchgang.loc[(big_table_pro_durchgang["Szenario"] == szenario) & (big_table_pro_durchgang["Achsen_Ratio"] >= 1.5)].copy()


        direction = szenario_table["Rotation"].to_numpy()
        direction = direction % 180

        class_size = 10

        direction_added = (direction + class_size / 2) % 180

        classes = np.arange(0, 181, class_size)

        count, empty = np.histogram(direction_added, bins=classes)

        middle_angle = np.arange(0,180,class_size)

        percentage = (count / count.sum())* 100

        direction_label = []
        class_label = []

        for angle in middle_angle:

            opposite_angle = angle + 180
            direction_label.append(f"{angle:.0f}° / {opposite_angle:.0f}°")

            class_label.append(f"{angle - class_size / 2:.0f}°–{angle + class_size / 2:.0f}° / {opposite_angle - class_size / 2:.0f}°–{opposite_angle + class_size / 2:.0f}°")


        direction_label = np.concatenate([direction_label,direction_label])

        class_label = np.concatenate([class_label,class_label])

        direction_all_around = np.concatenate([middle_angle,middle_angle + 180])
        percentage_all_around = np.concatenate([percentage,percentage])

        
        customdata =class_label

        fig_richtung_durchgang.add_trace(
            gr_obj.Barpolar(
                r=percentage_all_around,
                theta=direction_all_around,
                width=10,
                name=szenario,
                marker_color=szenario_farben.get(szenario),
                opacity=0.7,
                customdata=customdata,
                hovertemplate= "Szenario: "+ str(szenario)+ "<br>Richtungsklasse: %{customdata}"+ "<br>Anteil: %{r:.2f} %"+"<extra></extra>"
            )
        )


########### Kreisdiargramm beschriften #############

    fig_richtung_durchgang.update_layout(
        title="Richtung der Präzisionsellipsen pro Szenario und pro Durchgang",
        polar=dict(
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickmode="array",
                tickvals=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                ticktext=["0°/360°", "30°","60°", "90°", "120°", "150°", "180°", "210°", "240°","270°", "300°", "330°"]
            ),
            radialaxis=dict( title="Anteil [%]", showgrid=True)
        ),
        template="plotly_white"
    )

########### Kreisdriagramm speichern ###########

    save_path = os.path.join( save_location, "Kreisdiagramm_der_Richtung_pro_Messdurchgang")
    fig_richtung_durchgang.write_html(save_path + ".html")
    fig_richtung_durchgang.write_image(save_path + ".png",width=1400,height=700)



 ######################## Pro Messposition ########################

    fig_richtung_pos = gr_obj.Figure()

    for szenario in szenarien_pos:

        szenario_table = big_table_pro_messpos.loc[(big_table_pro_messpos["Szenario"] == szenario) & (big_table_pro_messpos["Achsen_Ratio"] >= 1.5)].copy()


        direction = szenario_table["Rotation"].to_numpy()
        direction = direction % 180

        class_size = 10

        direction_added = (direction + class_size / 2) % 180

        classes = np.arange(0, 181, class_size)

        count, empty = np.histogram(direction_added, bins=classes)

        middle_angle = np.arange(0,180,class_size)

        percentage = (count / count.sum())* 100

        direction_label = np.concatenate([
            [f"{angle:.0f}° / {angle + 180:.0f}°" for angle in middle_angle],
            [f"{angle:.0f}° / {angle + 180:.0f}°" for angle in middle_angle]
        ])

        direction_all_around = np.concatenate([middle_angle,middle_angle + 180])
        percentage_all_around = np.concatenate([percentage,percentage])


        fig_richtung_pos.add_trace(
            gr_obj.Barpolar(
                r=percentage_all_around,
                theta=direction_all_around,
                width=10,
                name=szenario,
                marker_color=szenario_farben.get(szenario),
                opacity=0.7,
                customdata=customdata,
                hovertemplate= "Szenario: "+ str(szenario)+ "<br>Richtungsklasse: %{customdata}"+ "<br>Anteil: %{r:.2f} %"+"<extra></extra>"
            )
        )


########### Kreisdiargramm beschriften #############

    fig_richtung_pos.update_layout(
        title="Richtung der Präzisionsellipsen pro Szenario und pro Messposition",
        polar=dict(
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickmode="array",
                tickvals=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
                ticktext=["0°/360°", "30°","60°", "90°", "120°", "150°", "180°", "210°", "240°","270°", "300°", "330°"]
            ),
            radialaxis=dict( title="Anteil [%]", showgrid=True)
        ),
        template="plotly_white"
    )

########### Kreisdriagramm speichern ###########

    save_path = os.path.join( save_location, "Kreisdiagramm_der_Richtung_pro_Messposition")
    fig_richtung_pos.write_html(save_path + ".html")
    fig_richtung_pos.write_image(save_path + ".png",width=1400,height=700)




################################ Vergleichsbalkendiagramm für Messpos und Messdurchgang ##########################################

    vergl_durchgang = table_durchgang_ergebnis.loc[table_durchgang_ergebnis["Lösungsstatus"] == "Gesamt",["Szenario", "Median Große Achse [cm]"]].copy()
    vergl_durchgang = vergl_durchgang.rename(columns={"Median Große Achse [cm]": "Median_pro_Messdurchgang_cm"})

    vergl_messpos = table_messpos_ergebnis.loc[table_messpos_ergebnis["Lösungsstatus"] == "Gesamt",["Szenario", "Median Große Achse [cm]"]].copy()
    vergl_messpos = vergl_messpos.rename(columns={"Median Große Achse [cm]": "Median_pro_Messposition_cm"})

    vergl_median = pd.merge(vergl_durchgang,vergl_messpos,on="Szenario",how="inner")
    vergl_median = vergl_median.loc[vergl_median["Szenario"] != "Weingut gesamt"].copy()

    fig_vergl_median = gr_obj.Figure()

    fig_vergl_median.add_trace(
        gr_obj.Bar(
            x=vergl_median["Szenario"],
            y=vergl_median["Median_pro_Messdurchgang_cm"],
            name="Pro Messdurchgang",
            marker_color="red",
            text=vergl_median["Median_pro_Messdurchgang_cm"],
            texttemplate="%{text:.2f}",
            textposition="outside",
            hovertemplate=(
                "Szenario: %{x}"
                "<br>Median pro Messdurchgang: %{y:.2f} cm"
                "<extra></extra>"
            )
        )
    )


    fig_vergl_median.add_trace(
        gr_obj.Bar(
            x=vergl_median["Szenario"],
            y=vergl_median["Median_pro_Messposition_cm"],
            name="Pro Messposition",
            marker_color="blue",
            text=vergl_median["Median_pro_Messposition_cm"],
            texttemplate="%{text:.2f}",
            hovertemplate=(
                "Szenario: %{x}"
                "<br>Median pro Messposition: %{y:.2f} cm"
                "<extra></extra>"
            )
        )
    )


    fig_vergl_median.update_layout(
        title="Vergleich der medianen großen Halbachse pro Messdurchgang und Messposition",
        xaxis_title="Messszenario",
        yaxis_title="Median der großen Halbachse [cm]",
        barmode="group",
        hovermode="closest",
        template="plotly_white",
        uniformtext_minsize=9,
        uniformtext_mode="hide"
    )


    save_path = os.path.join(save_location,"Balkendiagramm_Vergleich_Große_Achse_Messdurchgang_Messposition")

    fig_vergl_median.write_html(save_path + ".html")
    fig_vergl_median.write_image(save_path + ".png",width=1400,height=700)

    print("\nAlles gespeichert!")
    tools.threedots()  