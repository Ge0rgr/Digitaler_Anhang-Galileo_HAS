import pandas as pd
import numpy as np
import os #Zum erstellen von Ordnern
import glob #Zum Suchen von Dateipfaden, die best. Mustern entspr. 
import sys 
import time
import plotly.graph_objects as gr_obj


#
#
# Zur Erstellung der skripte wurde KI unterstützend verwendet
#
#


#Spielerei
def threedots( sleep = 0.4):
    three_dots ="..."
    for char in three_dots:
        print(char,end="",flush=True)
        time.sleep(sleep)
    print("\n")


#Schaut ob Ordner und Daten existieren
def foldercheck(input_data,save_location):

    #Check Ordner und Daten existieren
    if not os.path.exists(input_data):
        print(f"Der Ordner \"{input_data}\" exisitert nicht. Neuer Ordner wird erstellt",end="")
        threedots()
        os.makedirs(input_data)

    if not os.listdir(input_data):
        print(f"\nDer Ordner \"{input_data}\" existiert, aber es wurden keine Dateien zum Bearbeiten gefunden\n")
        sys.exit("Füge zuerst die Dateien in den Ordner ein\n")

    if not os.path.exists(save_location):
        print(f"Der Ordner \"{save_location}\" exisitert nicht. Neuer Ordner wird erstellt",end="")
        threedots()
        os.makedirs(save_location)


#Anpassen der Excel (vorher wurde sie aber schon per Hand etwas umgeändert)
def excelTimePDop(input_data,save_location):

    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    for file in files:

        filename = os.path.basename(file) 

        table = pd.read_csv(file, sep =";", decimal=",")

        table.columns = table.columns.str.strip()

        #Entfernen von ns1 in den Spaltennamen -> Entfernen von Zahlen an diesem Punkt Fehler im Output??
        table.columns = table.columns.str.replace("ns1:", "", regex=False)
        


        #Spalte Time umbenennen
        if "Time" in table.columns:
            table.rename(columns={"Time": "Date_Time"}, inplace=True)

        elif "Time57" in table.columns:
            table.rename(columns={"Time57": "Date_Time"}, inplace=True)


        table["Date_Time"] = pd.to_datetime(table["Date_Time"])
        table["Date_Time"] = table["Date_Time"].dt.tz_localize(None) #Zeitzonen entfernen, da sonst Fehler: "Excel does not support datetimes with timezones. Please ensure that datetimes are timezone unaware before writing to Excel."


        #Spalte mit [Datum]T[Zeit]Z aufteilen in spalten Datum und Uhrzeit
        table["Date"] = table["Date_Time"].dt.strftime("%d.%m.%Y")
        table["Time"] = table["Date_Time"].dt.strftime("%H:%M:%S")


        table["PDop"] = np.sqrt(table["HDop"]**2 + table["VDop"]**2)


        cols = list(table.columns)

        datetime_i = cols.index("Date_Time")
        date_i = cols.index("Date")

        cols.insert(datetime_i, cols.pop(date_i))
            
        date_i = cols.index("Date")
        time_i = cols.index("Time")
        cols.insert(date_i, cols.pop(time_i))
            
        hdop_i = cols.index("HDop")
        pdop_i = cols.index("PDop")
        cols.insert(hdop_i, cols.pop(pdop_i))


        table = table[cols]

        
        del table["Date_Time"]
        del table[table.columns[0]]

        #Entfernen von Zahlen; am Ende vom Skript, um Fehler im Output zu vermeiden
        table.columns = table.columns.str.replace("[0-9+]", "", regex=True)

        save_path = os.path.join(save_location, filename)
        table.to_csv(save_path, sep = ";", decimal = ",", index=False)
        print(f"Datei \"{filename}\" mit PDop, Datum und Zeit gespeichert!\n")

    print("Alle Dateien wurden gespeichert\n")
    threedots()


#Codierung der einzelnen Lösungsstatus
def excelAvailability(input_data,save_location):


    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    for file in files:

        filename = os.path.basename(file) 

        table = pd.read_csv(file, sep =";", decimal=",")

        type_sol_i = table.columns.get_loc("TypeSolution")
        table.insert(type_sol_i + 1, "Avail_Code", np.nan)

        for value in table.index:

            type_sol =table.at[value, "TypeSolution"] 

            if type_sol == "ppp_float" or type_sol == "phase_diff_fixed":
                table.at[value,"Avail_Code"] = 1

            elif type_sol == "ppp_convergence" or type_sol == "phase_diff_float":
                table.at[value,"Avail_Code"] = 0
            
            elif type_sol == "code_diff" :
                table.at[value,"Avail_Code"] = -1

            elif type_sol == "standalone" :
                table.at[value,"Avail_Code"] = -2

        save_path = os.path.join(save_location, filename)
        table.to_csv(save_path, sep=";", decimal=",", index=False)
        print(f"Datei \"{filename}\" mit Verfügbarkeitscodes gespeichert!\n")

    print("Alle Dateien wurden gespeichert\n")
    threedots()

#Anteile der Lösungsstatus in einer Tabelle zusammenfassen und Balkendiagramm erstellen
def completeAvailability(input_data,save_location):


    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    data = []

    for file in files:

        table = pd.read_csv(file, sep =";", decimal=",")

        filename= os.path.splitext(os.path.basename(file))[0]
        avail_cellname = os.path.splitext(os.path.basename(file))[0]

        total_rows = len(table)

        if "feldweg" in filename:
            filename = "Feldweg"

        elif "parkplatz" in filename:
            filename = "Parkplatz"

        elif "gruenflaeche_bitburg" in filename:
            filename = "Grünfläche"

        elif "schlosspark_trier" in filename:
            filename = "Schlosspark"

        elif "forst" in filename:
            filename = "Forst"

        elif "wein_drohne" in filename:
            filename = "Weinberg / Drohnenpunkte"

        elif "weingut" in filename:
            filename = "Weingut"

        if "_HAS" in avail_cellname:
            avail_cellname = filename + "_HAS"

        elif "_SAPOS" in avail_cellname:
            avail_cellname = filename + "_SAPOS"

        # Verfügbarkeiten % berechnen
        avail_fix_pppfloat = ((table["Avail_Code"] == 1).sum() / total_rows) * 100
        avail_float_pppconv = ((table["Avail_Code"] == 0).sum() / total_rows) * 100
        #avail_code_diff = ((table["Avail_Code"] == -1).sum() / total_rows) * 100   Nicht mehr nötig, da Projekt uni entfällt
        #avail_standalone = ((table["Avail_Code"] == -2).sum() / total_rows) * 100


        avail_cols = {
            "Messszenario / Datei": avail_cellname,
            "Anzahl Sapos Fixed / PPP Float (Code 1)": (table["Avail_Code"] == 1).sum(),
            "Anzahl Sapos Float / PPP Konvergierend (Code 0)": (table["Avail_Code"] == 0).sum(),
            "Sapos Fixed / PPP Float (Code 1) [%]": round(avail_fix_pppfloat, 2),
            "Sapos Float / PPP Konvergierend (Code 0) [%]": round(avail_float_pppconv, 2),
# Messszenario Uni fällt raus, da kein TILT für HAS
    #        "Sapos_Code_Diff (Code -1) [%]": round(avail_code_diff, 2),
    #        "Sapos_-/ PPP_Standalone (Code -2) [%]": round(avail_standalone, 2),
            "Gesamtanzahl Messungen": total_rows
        }

        data.append(avail_cols)    


    #Tabelle erzeugen
    avail_table = pd.DataFrame(data)

    avail_filename = "Verfügbarkeitstabelle.csv"

    save_path = os.path.join(save_location, avail_filename)
    avail_table.to_csv(save_path, sep=";", decimal=",", index=False)

    print("Dateien mit den Gesamtverfügbarkeiten gespeichert!\n")
    threedots()



############# Balkendiagramm ######################
    fig_balk = gr_obj.Figure()

    fig_balk.add_trace(gr_obj.Bar(
        x=avail_table["Messszenario / Datei"],
        y=avail_table["Sapos Fixed / PPP Float (Code 1) [%]"],
        name="Sapos Fixed / PPP Float",
        marker_color="blue",
        text=avail_table["Messszenario / Datei"],
        textposition="none",
        customdata=np.column_stack([avail_table["Anzahl Sapos Fixed / PPP Float (Code 1)"],avail_table["Gesamtanzahl Messungen"]]),
        hovertemplate=("Messung: %{text} <br>Anteil: %{y:.2f} %<br>Anzahl: %{customdata[0]:.0f} von %{customdata[1]:.0f}<extra></extra>")
        )
    )

    fig_balk.add_trace(gr_obj.Bar(
        x=avail_table["Messszenario / Datei"],
        y=avail_table["Sapos Float / PPP Konvergierend (Code 0) [%]"],
        name="Sapos Float / PPP Konvergierend",
        marker_color="orange",
        text=avail_table["Messszenario / Datei"],
        textposition="none",
        customdata=np.column_stack([avail_table["Anzahl Sapos Float / PPP Konvergierend (Code 0)"],avail_table["Gesamtanzahl Messungen"]]),
        hovertemplate=("Messung: %{text}<br>Anteil: %{y:.2f} %<br>Anzahl: %{customdata[0]:.0f} von %{customdata[1]:.0f}<extra></extra>")
        )
    )

    fig_balk.update_layout(
        title="Verfügbarkeit pro Messszenario",
        xaxis_title="Messszenario",
        yaxis_title="Verfügbarkeit [%]",
        yaxis=dict(range=[0, 100]),
        template="plotly_white"
    )


    fig_balk.update_xaxes(
    tickmode="array",
    tickvals=avail_table["Messszenario / Datei"],
    ticktext=[
        f"{name}<br>n={int(n)}"
        for name, n in zip(
            avail_table["Messszenario / Datei"],
            avail_table["Gesamtanzahl Messungen"]
        )
    ],
    tickangle=-20
    )

    save_path_balk = os.path.join(save_location, "Verfügbarkeitstabelle_Balkendiagramm")
    fig_balk.write_html(save_path_balk + ".html")
    fig_balk.write_image(save_path_balk + ".png", width=1400, height=700)

    threedots()
    
    print(f"Balkendiagramm mit Gesamtverfügbarkeiten gespeichert!\n")

# Umbenennung der Spalten für eine bessere Übersichtlichkeit
# Idee der Analyse der vom Empfänger geschätzten Varianzen und Kovarianzen wurde verworfen
def varianceName(input_data, save_location):

    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    for file in files:


        filename = os.path.basename(file) 

        table = pd.read_csv(file, sep =";", decimal=",")

        table.rename(columns={"XX": "XX_Variance_cartesian"}, inplace=True)
        table.rename(columns={"YY": "YY_Variance_cartesian"}, inplace=True)
        table.rename(columns={"ZZ": "ZZ_Variance_cartesian"}, inplace=True)
        table.rename(columns={"XY": "XY_Covariance_cartesian"}, inplace=True)
        table.rename(columns={"XZ": "XZ_Covariance_cartesian"}, inplace=True)
        table.rename(columns={"YZ": "YZ_Covariance_cartesian"}, inplace=True)

        table.rename(columns={"XX.1": "Variance_North"}, inplace=True)
        table.rename(columns={"YY.1": "Variance_East"}, inplace=True)
        table.rename(columns={"ZZ.1": "Variance_Up"}, inplace=True)
        table.rename(columns={"XY.1": "Covariance_North_East"}, inplace=True)
        table.rename(columns={"XZ.1": "Covariance_North_Up"}, inplace=True)
        table.rename(columns={"YZ.1": "Covariance_East_Up"}, inplace=True)

        table.rename(columns={"Height": "Height_cartesian"}, inplace=True)
        table.rename(columns={"Height.1": "Height_projected"}, inplace=True)

        save_path = os.path.join(save_location, filename)
        table.to_csv(save_path, sep = ";", decimal = ",", index=False)


    print("Alle Dateien wurden gespeichert\n")
    threedots()




# Definierungen der ungenutzten Funktionen
'''
def tableSplit(input_data, save_location):

    sapos_search = os.path.join(input_data,"*_SAPOS.csv")
    sapos_files = glob.glob(sapos_search) 


    for file in sapos_files:

        sapos_table = pd.read_csv(file, sep =";", decimal=",")

        #Zeilen von SAPOS ref zählen, um HAS file dann um diese Zahl zu splitten
        colsize = len(sapos_table)

        filename = os.path.basename(file).replace("_SAPOS.csv","")
        has_file = os.path.join(input_data,filename+"_HAS.csv")

        has_table = pd.read_csv(has_file, sep =";", decimal=",")

        has_lines = len(has_table)

        scenarios = int(has_lines / colsize)

       # print(f"Datei \"{has_file}\" hat \"{colsize}\" Zeilen")


        sapos_data = sapos_table[["Name","Height_projected", "VDop","Avail_Code","GPSSats", "GalileoSats" ]].reset_index(drop=True) 

        new_table = pd.DataFrame()

        new_table["SAPOS_Name"] = sapos_data["Name"]
        new_table["SAPOS_Height"] = sapos_data["Height_projected"]
        new_table["SAPOS_VDop"] = sapos_data["VDop"]
        new_table["SAPOS_Avail_Code"] = sapos_data["Avail_Code"]
        new_table["SAPOS_GPSSats"] = sapos_data["GPSSats"]
        new_table["SAPOS_GalileoSats"] = sapos_data["GalileoSats"]
        


        for scenario in range(scenarios):
            start_index = scenario * colsize
            end_index = start_index + colsize

            scenario_data = has_table.iloc[start_index:end_index].reset_index(drop=True)

            columnname = f"HAS_{scenario+1}"

            new_table[f"{columnname}_Name"] = scenario_data["Name"]
            new_table[f"{columnname}_Height"] = scenario_data["Height_projected"]
            new_table[f"{columnname}_VDop"] = scenario_data["VDop"]
            new_table[f"{columnname}_Avail_Code"] = scenario_data["Avail_Code"]
            new_table[f"{columnname}_GPSSats"] = scenario_data["GPSSats"]
            new_table[f"{columnname}_GalileoSats"] = scenario_data["GalileoSats"]
            new_table["DGM"] = scenario_data["DGM"]

        new_filename = filename + "_HAS_SAPOS_DGM1.csv"
        save_path = os.path.join(save_location, new_filename)
        new_table.to_csv(save_path, sep=";", decimal=",", index=False)
        print(f"Datei \"{new_filename}\" mit Verfügbarkeitscodes gespeichert!\n")

    threedots()
    print("Alle Dateien wurden gespeichert\n")




def covarianceAnalysis(input_data,save_location):

    search_path = os.path.join(input_data,"*.csv")
    files = glob.glob(search_path) 

    for file in files:

        filename = os.path.basename(file) 
        shorter_filename = os.path.splitext(os.path.basename(file))[0]

        table = pd.read_csv(file, sep =";", decimal=",")

        table["Sigma_North"] = np.sqrt(table["Variance_North"])
        table["Sigma_East"] = np.sqrt(table["Variance_East"])
        table["Sigma_Up"] = np.sqrt(table["Variance_Up"]) #Ist gleich rmse und 68% percentile

        table["Uncertainty_Up_68"] = table["Sigma_Up"]
        table["Uncertainty_Up_95"] = 1,96 * table["Sigma_Up"]

        table["receiver_RMS_Horizontal_RMS_Up"] = table["Sigma_Up"]
        table["receiver_RMS_Horizontal"] = np.sqrt(table["Variance_East"] + table["Variance_North"])

        table["Scenario"] = shorter_filename

        if "_HAS" in filename: 
            table["System"] = "HAS"

        if "_SAPOS" in filename: 
            table["System"] = "SAPOS"


#### Spalte mit Messmethode hinzufügen -> für Graphen am Ende ####'

        lower_name = (table["Name"].str.lower())

        table["Method"] = "Punktmessung"

        tmp = lower_name.str.contains("seedpoint")

        table.loc[tmp,"Method"] = "SeedPoint"

        tmp = lower_name.str.contains("stopgo")

        table.loc[tmp,"Method"] = "stopgo"

        tmp = lower_name.str.contains("autotopo")

        table.loc[tmp,"Method"] = "autotopo"

### DUrchgägne Trennen #####

        table["Durchgang"] = 1

        tmp = lower_name.str.contains("gang2")

        table.loc[tmp,"Durchgang"] = 2

        tmp = lower_name.str.contains("gang3")

        table.loc[tmp,"Durchgang"] = 3

### Unterscheidung von Baumart in forst, drohnen refpkte#####

        if "forst" in filename and "autotopo" not in filename:

            tmp = lower_name.str.contains("buche")
            table.loc[tmp,"Baumart"] = "Buche"

            tmp = lower_name.str.contains("fichte")
            table.loc[tmp,"Baumart"] = "Fichte"



        if "wein_drohne" in filename and "autotopo" not in filename:

            tmp = lower_name.str.contains("drohne")
            table.loc[tmp,"Messobjekt"] = "Drohnenreferenzpunkt"

            tmp = lower_name.str.contains("weinreben")
            table.loc[tmp,"Messobjekt"] = "Weinreben"
'''