from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd




#
#
# Zur Erstellung des skriptes wurde KI verwendet
# Dieses Skript wurde von einer KI erstellt; Das skript wurde geprüft
#
#


try:
    from pyproj import Transformer
except ImportError as exc:  # pragma: no cover - klare Meldung für Anwender
    raise SystemExit(
        "Das Paket 'pyproj' fehlt. Installiere es mit:\n"
        "    pip install pyproj\n"
    ) from exc


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

CSV_SEPARATOR = ";"
CSV_DECIMAL = ","
CSV_ENCODING = "utf-8-sig"
TARGET_CRS = "EPSG:25832"  # ETRS89 / UTM Zone 32N

# In den vorliegenden Projekten eindeutig verifizierte Topcon-Codes.
# Unbekannte Codes bleiben im Export zusätzlich als Zahl erhalten.
SOLUTION_TYPE_MAP = {
    4: "phase_diff_fixed",
    15: "ppp_convergence",
    16: "ppp_float",
}


COLUMN_DICTIONARY = [
    ("Project_Name", "Name der verarbeiteten Topcon-Projektdatei", "-", "Dateiname"),
    ("Project_Relative_Path", "Relativer Pfad der MJF-Datei innerhalb des Eingabeordners bzw. ZIP-Archivs", "-", "Dateisystem"),
    ("Point_Name", "In Topcon gespeicherter Punktname", "-", "tblStations / tblSoPoints"),
    ("Record_Type", "single_epoch = einzelne Position; point_average = gespeichertes Mittel mehrerer Epochen", "-", "aus NumberOfEpochs abgeleitet"),
    ("Is_Single_Epoch", "True bei einer einzelnen Epoche", "bool", "aus NumberOfEpochs abgeleitet"),
    ("Is_Point_Average", "True beim gespeicherten Punktmittel", "bool", "aus NumberOfEpochs abgeleitet"),
    ("Epoch_Index_Within_Point", "Fortlaufende Nummer der Einzelepoche innerhalb des Punkts", "-", "aus Zeitstempel abgeleitet"),
    ("NumberOfEpochs", "Anzahl der Epochen, die dieser Datensatz repräsentiert", "-", "tblCrdGnssRaw.NumOfEpochs"),
    ("Point_NumberOfSingleEpochs", "Anzahl der in der Datenbank vorhandenen Einzelepochen dieser Punktaufnahme", "Anzahl", "gruppenweise abgeleitet"),
    ("Timestamp_UTC", "Messzeitpunkt als ISO-Zeit in UTC", "UTC", "tblCrdRawMeas.SecondsFrom1970"),
    ("Date_UTC", "Messdatum in UTC", "YYYY-MM-DD", "aus Timestamp_UTC"),
    ("Time_UTC", "Messuhrzeit in UTC", "HH:MM:SS.sss", "aus Timestamp_UTC"),
    ("Session_Name", "Topcon-Name der Beobachtungssession", "-", "tblCrdObsSession"),
    ("Session_Start_UTC", "Beginn der Beobachtungssession", "UTC", "tblCrdObsSession"),
    ("Session_End_UTC", "Ende der Beobachtungssession", "UTC", "tblCrdObsSession"),
    ("SolutionType", "Lesbarer GNSS-Lösungsstatus", "-", "aus SolutionType_Code übersetzt"),
    ("SolutionType_Code", "Numerischer Topcon-Code des Lösungsstatus", "-", "tblCrdGnssRaw.SolutionType"),
    ("Point_Has_SolutionStatusChange", "True, wenn innerhalb der Einzelepochen des Punkts mehrere Lösungsstatus vorkommen", "bool", "gruppenweise abgeleitet"),
    ("Point_Share_ppp_float", "Anteil der Einzelepochen mit ppp_float", "0 bis 1", "gruppenweise abgeleitet"),
    ("Point_Share_ppp_convergence", "Anteil der Einzelepochen mit ppp_convergence", "0 bis 1", "gruppenweise abgeleitet"),
    ("Latitude_deg", "Geografische Breite der GNSS-Lösung", "Grad", "tblCrdGnssRaw.DLat"),
    ("Longitude_deg", "Geografische Länge der GNSS-Lösung", "Grad", "tblCrdGnssRaw.DLon"),
    ("EllipsoidalHeight_AntennaReferencePoint_m", "Ellipsoidische Höhe der GNSS-Antennenreferenz bzw. internen GNSS-Position", "m", "tblCrdGnssRaw.DHgt"),
    ("EllipsoidalHeight_MeasuredPoint_m", "Aus der Topcon-Punktkorrektur abgeleitete ellipsoidische Höhe des Messpunkts", "m", "aus DHgt und gespeichertem Punkt abgeleitet"),
    ("AntennaToPoint_HeightCorrection_m", "Von Topcon verwendete vertikale Korrektur zwischen GNSS-Position und Messpunkt", "m", "aus repräsentativem GNSS-Datensatz und gespeichertem Punkt abgeleitet"),
    ("East_UTM32_m", "Direkt aus Breite/Länge projizierter Ostwert in ETRS89 / UTM 32N", "m", "pyproj EPSG:25832"),
    ("North_UTM32_m", "Direkt aus Breite/Länge projizierter Nordwert in ETRS89 / UTM 32N", "m", "pyproj EPSG:25832"),
    ("Stored_Point_Latitude_deg", "Geografische Breite des in Topcon gespeicherten Endpunkts", "Grad", "tblStations.C1"),
    ("Stored_Point_Longitude_deg", "Geografische Länge des in Topcon gespeicherten Endpunkts", "Grad", "tblStations.C2"),
    ("Stored_Point_EllipsoidalHeight_m", "Ellipsoidische Höhe des in Topcon gespeicherten Endpunkts", "m", "tblStations.C3"),
    ("Stored_Point_East_UTM32_m", "Projizierter Ostwert des gespeicherten Endpunkts", "m", "aus tblStations.C1/C2"),
    ("Stored_Point_North_UTM32_m", "Projizierter Nordwert des gespeicherten Endpunkts", "m", "aus tblStations.C1/C2"),
    ("Variance_X_Cartesian_m2", "Varianz der geozentrischen X-Komponente", "m²", "tblCrdGnssRaw.xx"),
    ("Variance_Y_Cartesian_m2", "Varianz der geozentrischen Y-Komponente", "m²", "tblCrdGnssRaw.yy"),
    ("Variance_Z_Cartesian_m2", "Varianz der geozentrischen Z-Komponente", "m²", "tblCrdGnssRaw.zz"),
    ("Covariance_XY_Cartesian_m2", "Kovarianz zwischen geozentrischem X und Y", "m²", "tblCrdGnssRaw.xy"),
    ("Covariance_XZ_Cartesian_m2", "Kovarianz zwischen geozentrischem X und Z", "m²", "tblCrdGnssRaw.xz"),
    ("Covariance_YZ_Cartesian_m2", "Kovarianz zwischen geozentrischem Y und Z", "m²", "tblCrdGnssRaw.yz"),
    ("Variance_North_m2", "In das lokale NEU-System transformierte Nordvarianz", "m²", "aus XYZ-Kovarianz transformiert"),
    ("Variance_East_m2", "In das lokale NEU-System transformierte Ostvarianz", "m²", "aus XYZ-Kovarianz transformiert"),
    ("Variance_Up_m2", "In das lokale NEU-System transformierte Höhenvarianz", "m²", "aus XYZ-Kovarianz transformiert"),
    ("Covariance_North_East_m2", "Kovarianz zwischen Nord und Ost", "m²", "aus XYZ-Kovarianz transformiert"),
    ("Covariance_North_Up_m2", "Kovarianz zwischen Nord und Höhe", "m²", "aus XYZ-Kovarianz transformiert"),
    ("Covariance_East_Up_m2", "Kovarianz zwischen Ost und Höhe", "m²", "aus XYZ-Kovarianz transformiert"),
    ("Sigma_North_m", "Formale Standardabweichung in Nordrichtung", "m", "Wurzel aus Variance_North_m2"),
    ("Sigma_East_m", "Formale Standardabweichung in Ostrichtung", "m", "Wurzel aus Variance_East_m2"),
    ("Sigma_Up_m", "Formale Standardabweichung der Höhe", "m", "Wurzel aus Variance_Up_m2"),
    ("HDOP", "Horizontal Dilution of Precision", "-", "tblCrdGnssRaw.HDop"),
    ("VDOP", "Vertical Dilution of Precision", "-", "tblCrdGnssRaw.VDop"),
    ("TDOP", "Time Dilution of Precision", "-", "tblCrdGnssRaw.TDop"),
    ("PDOP_Calculated", "Aus HDOP und VDOP berechneter PDOP", "-", "sqrt(HDOP² + VDOP²)"),
    ("GPS_Satellites", "Im Topcon-Statusfeld protokollierte GPS-Satelliten", "Anzahl", "tblCrdGnssRaw"),
    ("GLONASS_Satellites", "Im Topcon-Statusfeld protokollierte GLONASS-Satelliten", "Anzahl", "tblCrdGnssRaw"),
    ("Galileo_Satellites", "Im Topcon-Statusfeld protokollierte Galileo-Satelliten", "Anzahl", "tblCrdGnssRaw"),
    ("BeiDou_Satellites", "Im Topcon-Statusfeld protokollierte BeiDou-Satelliten", "Anzahl", "tblCrdGnssRaw"),
    ("SBAS_Satellites", "Im Topcon-Statusfeld protokollierte SBAS-Satelliten", "Anzahl", "tblCrdGnssRaw"),
    ("QZSS_Satellites", "Im Topcon-Statusfeld protokollierte QZSS-Satelliten", "Anzahl", "tblCrdGnssRaw"),
    ("NavIC_Satellites", "Im Topcon-Statusfeld protokollierte NavIC-Satelliten", "Anzahl", "tblCrdGnssRaw"),
    ("Total_Satellites_Logged", "Summe aller protokollierten Satellitenzahlen", "Anzahl", "berechnet"),
    ("Satellite_Status_AllZero", "True, wenn sämtliche Satellitenstatusfelder null sind; nicht automatisch als Signalverlust interpretieren", "bool", "berechnet"),
    ("ObservationDuration_ms", "Von Topcon gespeicherte Beobachtungsdauer", "ms", "tblCrdGnssRaw.ObsDuration"),
    ("AntennaHeight_Input_m", "Im Projekt eingegebene Antennenhöhe", "m", "tblCrdGnssRaw.TargetAntHeight"),
    ("AntennaHeight_IsSlant", "True, wenn die Antennenhöhe als Schräghöhe gekennzeichnet ist", "bool", "tblCrdGnssRaw.AntennaSlant"),
    ("Antenna_Model", "Kurzbezeichnung des Antennenmodells", "-", "tblAntennaModels"),
    ("Antenna_RINEX_Name", "RINEX-Bezeichnung des Antennenmodells", "-", "tblAntennaModels"),
    ("Antenna_SerialNumber", "Seriennummer der Antenne bzw. des Empfängers", "-", "tblAntennaModels"),
    ("EpochInterval_ms", "In der Session eingestelltes Epochenintervall", "ms", "tblObsSessionGps"),
    ("ElevationMask_deg", "In der Session eingestellte Elevationsmaske", "Grad", "tblObsSessionGps"),
    ("RawDataLoggingEnabled", "Topcon-Schalter für echtes GNSS-Rohdatenlogging", "0/1", "tblObsSessionGps"),
    ("GNSS_Record_ID", "Primärschlüssel des GNSS-Datensatzes", "-", "tblCrdGnssRaw"),
    ("RawMeasurement_ID", "Primärschlüssel der zugehörigen Rohmessung", "-", "tblCrdRawMeas"),
    ("Station_ID", "Primärschlüssel der Roverstation bzw. Punktaufnahme", "-", "tblStations"),
    ("Session_ID", "Primärschlüssel der Beobachtungssession", "-", "tblCrdObsSession"),
    ("BaseStation_ID", "Referenz auf eine Basisstation; bei autonomem HAS meist leer", "-", "tblCrdGnssRaw"),
    ("MeasurementType_Code", "Topcon-interner Code des Messdatensatztyps; zur Rückverfolgbarkeit unverändert exportiert", "-", "tblCrdRawMeas.MeasType"),
    ("MeasurementExtraType_Code", "Zusätzlicher Topcon-interner Messdatensatzcode; zur Rückverfolgbarkeit unverändert exportiert", "-", "tblCrdRawMeas.MeasExtraType"),
    ("Measurement_TimeSystem_Code", "Topcon-interner Code des Zeitsystems", "-", "tblCrdRawMeas.TimeSystem"),
    ("SurveyType_Code", "Topcon-interner Code des GNSS-Aufnahmetyps", "-", "tblObsSessionGps.SurveyType"),
    ("CorrectionsType_Code", "Topcon-interner Code des verwendeten Korrekturtyps", "-", "tblObsSessionGps.CorrectionsType"),
    ("Measurement_SecondsFrom1970", "Originaler Topcon-Zeitwert der Messung seit Unix-Epoche", "s", "tblCrdRawMeas.SecondsFrom1970"),
    ("Session_Start_SecondsFrom1970", "Originaler Topcon-Zeitwert des Sessionbeginns seit Unix-Epoche", "s", "tblCrdObsSession"),
    ("Session_End_SecondsFrom1970", "Originaler Topcon-Zeitwert des Sessionendes seit Unix-Epoche", "s", "tblCrdObsSession"),
    ("AntennaHeight_IsSlant_Code", "Originaler Topcon-Code zur Kennzeichnung der Antennen-Schräghöhe", "0/1", "tblCrdGnssRaw.AntennaSlant"),
]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def point_name_ci(value_1: object, value_2: object) -> int:
    """Ersatz für die Topcon-eigene SQLite-Sortierung PointName_CI."""
    text_1 = "" if value_1 is None else str(value_1).casefold()
    text_2 = "" if value_2 is None else str(value_2).casefold()
    return (text_1 > text_2) - (text_1 < text_2)


def open_mjf_readonly(path: Path) -> sqlite3.Connection:
    """Öffnet eine MJF-Datenbank schreibgeschützt."""
    uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.create_collation("PointName_CI", point_name_ci)
    return connection


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def safe_label(text: str) -> str:
    """Erzeugt einen für Dateinamen geeigneten Projektnamen."""
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    cleaned = "".join(char if char in allowed else "_" for char in text)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_.") or "topcon_project"


def to_iso_utc(series: pd.Series) -> pd.Series:
    timestamp = pd.to_datetime(series, unit="s", utc=True, errors="coerce")
    return timestamp.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").str.replace(
        r"(\.\d{3})\d{3}Z$", r"\1Z", regex=True
    )


def transform_xyz_covariance_to_neu(data: pd.DataFrame) -> None:
    """
    Transformiert die geozentrische XYZ-Kovarianz in das lokale ENU/NEU-System.

    Die Berechnung wurde mit den in Topcon exportierten Projektkovarianzen
    abgeglichen. Die resultierenden Werte entsprechen den CSV-Spalten
    Variance_East, Variance_North, Variance_Up und den lokalen Kovarianzen.
    """
    required = [
        "Latitude_deg",
        "Longitude_deg",
        "Variance_X_Cartesian_m2",
        "Variance_Y_Cartesian_m2",
        "Variance_Z_Cartesian_m2",
        "Covariance_XY_Cartesian_m2",
        "Covariance_XZ_Cartesian_m2",
        "Covariance_YZ_Cartesian_m2",
    ]

    if any(column not in data.columns for column in required):
        return

    n_rows = len(data)
    lat = np.radians(pd.to_numeric(data["Latitude_deg"], errors="coerce").to_numpy())
    lon = np.radians(pd.to_numeric(data["Longitude_deg"], errors="coerce").to_numpy())

    covariance_xyz = np.full((n_rows, 3, 3), np.nan, dtype=float)
    xx = pd.to_numeric(data["Variance_X_Cartesian_m2"], errors="coerce").to_numpy()
    yy = pd.to_numeric(data["Variance_Y_Cartesian_m2"], errors="coerce").to_numpy()
    zz = pd.to_numeric(data["Variance_Z_Cartesian_m2"], errors="coerce").to_numpy()
    xy = pd.to_numeric(data["Covariance_XY_Cartesian_m2"], errors="coerce").to_numpy()
    xz = pd.to_numeric(data["Covariance_XZ_Cartesian_m2"], errors="coerce").to_numpy()
    yz = pd.to_numeric(data["Covariance_YZ_Cartesian_m2"], errors="coerce").to_numpy()

    covariance_xyz[:, 0, 0] = xx
    covariance_xyz[:, 1, 1] = yy
    covariance_xyz[:, 2, 2] = zz
    covariance_xyz[:, 0, 1] = covariance_xyz[:, 1, 0] = xy
    covariance_xyz[:, 0, 2] = covariance_xyz[:, 2, 0] = xz
    covariance_xyz[:, 1, 2] = covariance_xyz[:, 2, 1] = yz

    sin_lat = np.sin(lat)
    cos_lat = np.cos(lat)
    sin_lon = np.sin(lon)
    cos_lon = np.cos(lon)

    # Reihenfolge der lokalen Achsen: East, North, Up.
    rotation = np.empty((n_rows, 3, 3), dtype=float)
    rotation[:, 0, 0] = -sin_lon
    rotation[:, 0, 1] = cos_lon
    rotation[:, 0, 2] = 0.0
    rotation[:, 1, 0] = -sin_lat * cos_lon
    rotation[:, 1, 1] = -sin_lat * sin_lon
    rotation[:, 1, 2] = cos_lat
    rotation[:, 2, 0] = cos_lat * cos_lon
    rotation[:, 2, 1] = cos_lat * sin_lon
    rotation[:, 2, 2] = sin_lat

    covariance_enu = np.einsum(
        "nia,nab,njb->nij", rotation, covariance_xyz, rotation
    )

    data["Variance_East_m2"] = covariance_enu[:, 0, 0]
    data["Variance_North_m2"] = covariance_enu[:, 1, 1]
    data["Variance_Up_m2"] = covariance_enu[:, 2, 2]
    data["Covariance_North_East_m2"] = covariance_enu[:, 1, 0]
    data["Covariance_North_Up_m2"] = covariance_enu[:, 1, 2]
    data["Covariance_East_Up_m2"] = covariance_enu[:, 0, 2]

    data["Sigma_North_m"] = np.sqrt(data["Variance_North_m2"].clip(lower=0))
    data["Sigma_East_m"] = np.sqrt(data["Variance_East_m2"].clip(lower=0))
    data["Sigma_Up_m"] = np.sqrt(data["Variance_Up_m2"].clip(lower=0))


def add_projected_coordinates(data: pd.DataFrame) -> None:
    """Projiziert geografische Koordinaten direkt nach EPSG:25832."""
    transformer = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)

    valid_epoch = data["Longitude_deg"].notna() & data["Latitude_deg"].notna()
    east = np.full(len(data), np.nan)
    north = np.full(len(data), np.nan)
    if valid_epoch.any():
        east_values, north_values = transformer.transform(
            data.loc[valid_epoch, "Longitude_deg"].to_numpy(dtype=float),
            data.loc[valid_epoch, "Latitude_deg"].to_numpy(dtype=float),
        )
        east[valid_epoch.to_numpy()] = east_values
        north[valid_epoch.to_numpy()] = north_values
    data["East_UTM32_m"] = east
    data["North_UTM32_m"] = north

    valid_stored = (
        data["Stored_Point_Longitude_deg"].notna()
        & data["Stored_Point_Latitude_deg"].notna()
    )
    stored_east = np.full(len(data), np.nan)
    stored_north = np.full(len(data), np.nan)
    if valid_stored.any():
        east_values, north_values = transformer.transform(
            data.loc[valid_stored, "Stored_Point_Longitude_deg"].to_numpy(dtype=float),
            data.loc[valid_stored, "Stored_Point_Latitude_deg"].to_numpy(dtype=float),
        )
        stored_east[valid_stored.to_numpy()] = east_values
        stored_north[valid_stored.to_numpy()] = north_values
    data["Stored_Point_East_UTM32_m"] = stored_east
    data["Stored_Point_North_UTM32_m"] = stored_north


def add_point_height_correction(data: pd.DataFrame) -> None:
    """
    Leitet die von Topcon verwendete Antennen-/Punktkorrektur je Station ab.

    Pro Station wird der Datensatz mit der größten Epochenzahl verwendet. Bei
    gemittelten Punktaufnahmen ist dies der gespeicherte Mittelwert; bei
    StopGo-Aufnahmen ist es die einzelne gespeicherte Position.
    """
    if data.empty:
        return

    representative = (
        data.sort_values(
            ["Station_ID", "NumberOfEpochs", "Measurement_SecondsFrom1970"],
            ascending=[True, False, False],
        )
        .drop_duplicates("Station_ID")
        [[
            "Station_ID",
            "EllipsoidalHeight_AntennaReferencePoint_m",
            "Stored_Point_EllipsoidalHeight_m",
        ]]
        .copy()
    )

    representative["AntennaToPoint_HeightCorrection_m"] = (
        representative["EllipsoidalHeight_AntennaReferencePoint_m"]
        - representative["Stored_Point_EllipsoidalHeight_m"]
    )
    representative = representative[[
        "Station_ID",
        "AntennaToPoint_HeightCorrection_m",
    ]]

    data.merge(representative, on="Station_ID", how="left", copy=False)
    correction_map = representative.set_index("Station_ID")[
        "AntennaToPoint_HeightCorrection_m"
    ]
    data["AntennaToPoint_HeightCorrection_m"] = data["Station_ID"].map(
        correction_map
    )
    data["EllipsoidalHeight_MeasuredPoint_m"] = (
        data["EllipsoidalHeight_AntennaReferencePoint_m"]
        - data["AntennaToPoint_HeightCorrection_m"]
    )


def add_point_quality_fields(data: pd.DataFrame) -> None:
    """Berechnet Statusanteile und Epochennummern je Punktaufnahme."""
    if data.empty:
        return

    data.sort_values(
        ["Station_ID", "Measurement_SecondsFrom1970", "GNSS_Record_ID"],
        inplace=True,
    )

    data["Epoch_Index_Within_Point"] = pd.Series(pd.NA, index=data.index, dtype="Int64")
    single_mask = data["Is_Single_Epoch"]
    data.loc[single_mask, "Epoch_Index_Within_Point"] = (
        data.loc[single_mask]
        .groupby("Station_ID", dropna=False)
        .cumcount()
        .add(1)
        .astype("Int64")
    )

    singles = data.loc[single_mask, ["Station_ID", "SolutionType"]].copy()
    if singles.empty:
        data["Point_Has_SolutionStatusChange"] = False
        data["Point_Share_ppp_float"] = np.nan
        data["Point_Share_ppp_convergence"] = np.nan
        data["Point_NumberOfSingleEpochs"] = 0
        return

    grouped = singles.groupby("Station_ID", dropna=False)["SolutionType"]
    status_count = grouped.nunique(dropna=True)
    number_epochs = grouped.size()
    share_float = singles.assign(
        value=singles["SolutionType"].eq("ppp_float").astype(float)
    ).groupby("Station_ID")["value"].mean()
    share_convergence = singles.assign(
        value=singles["SolutionType"].eq("ppp_convergence").astype(float)
    ).groupby("Station_ID")["value"].mean()

    data["Point_Has_SolutionStatusChange"] = (
        data["Station_ID"].map(status_count).fillna(0).gt(1)
    )
    data["Point_Share_ppp_float"] = data["Station_ID"].map(share_float)
    data["Point_Share_ppp_convergence"] = data["Station_ID"].map(
        share_convergence
    )
    data["Point_NumberOfSingleEpochs"] = (
        data["Station_ID"].map(number_epochs).fillna(0).astype("Int64")
    )


def read_gnss_records(mjf_path: Path, project_relative_path: str) -> pd.DataFrame:
    """Liest und erklärt alle GNSS-Datensätze einer MJF-Datei."""
    with open_mjf_readonly(mjf_path) as connection:
        if not table_exists(connection, "tblCrdGnssRaw"):
            raise ValueError("Tabelle tblCrdGnssRaw fehlt.")

        row_count = connection.execute(
            "SELECT COUNT(*) FROM tblCrdGnssRaw"
        ).fetchone()[0]
        if row_count == 0:
            return pd.DataFrame()

        required_tables = ["tblCrdRawMeas", "tblStations"]
        missing = [
            table for table in required_tables if not table_exists(connection, table)
        ]
        if missing:
            raise ValueError(
                "Für den Export erforderliche Tabellen fehlen: " + ", ".join(missing)
            )

        query = """
            SELECT
                g.keyCrdGnssRaw AS GNSS_Record_ID,
                g.fkeyCrdRawMeas AS RawMeasurement_ID,
                g.fkeyRoverStation AS Station_ID,
                g.fKeyBaseStation AS BaseStation_ID,
                rm.fkeyObsSession AS Session_ID,
                COALESCE(st.Name, sp.Name, 'Station_' || g.fkeyRoverStation) AS Point_Name,
                rm.SecondsFrom1970 AS Measurement_SecondsFrom1970,
                rm.TimeSystem AS Measurement_TimeSystem_Code,
                rm.MeasType AS MeasurementType_Code,
                rm.MeasExtraType AS MeasurementExtraType_Code,
                os.SessionName AS Session_Name,
                os.StartSecondsFrom1970 AS Session_Start_SecondsFrom1970,
                os.EndSecondsFrom1970 AS Session_End_SecondsFrom1970,
                g.DLat AS Latitude_deg,
                g.DLon AS Longitude_deg,
                g.DHgt AS EllipsoidalHeight_AntennaReferencePoint_m,
                st.C1 AS Stored_Point_Latitude_deg,
                st.C2 AS Stored_Point_Longitude_deg,
                st.C3 AS Stored_Point_EllipsoidalHeight_m,
                g.xx AS Variance_X_Cartesian_m2,
                g.yy AS Variance_Y_Cartesian_m2,
                g.zz AS Variance_Z_Cartesian_m2,
                g.xy AS Covariance_XY_Cartesian_m2,
                g.xz AS Covariance_XZ_Cartesian_m2,
                g.yz AS Covariance_YZ_Cartesian_m2,
                g.SolutionType AS SolutionType_Code,
                g.ObsDuration AS ObservationDuration_ms,
                g.NumOfEpochs AS NumberOfEpochs,
                g.HDop AS HDOP,
                g.VDop AS VDOP,
                g.TDop AS TDOP,
                g.NumOfGpsSats AS GPS_Satellites,
                g.NumOfGlonassSats AS GLONASS_Satellites,
                g.NumOfGalileoSats AS Galileo_Satellites,
                g.NumOfBeidouSats AS BeiDou_Satellites,
                g.NumOfSbasSats AS SBAS_Satellites,
                g.NumOfQzssSats AS QZSS_Satellites,
                g.NumOfNavICSats AS NavIC_Satellites,
                g.TargetAntHeight AS AntennaHeight_Input_m,
                g.AntennaSlant AS AntennaHeight_IsSlant_Code,
                am.ShortDescription AS Antenna_Model,
                am.RinexName AS Antenna_RINEX_Name,
                am.SerNum AS Antenna_SerialNumber,
                gps.EpochInterval AS EpochInterval_ms,
                gps.ElevMask AS ElevationMask_deg,
                gps.RawDataLoggingEnabled AS RawDataLoggingEnabled,
                gps.SurveyType AS SurveyType_Code,
                gps.CorrectionsType AS CorrectionsType_Code
            FROM tblCrdGnssRaw AS g
            LEFT JOIN tblCrdRawMeas AS rm
                ON rm.keyCrdRawMeas = g.fkeyCrdRawMeas
            LEFT JOIN tblStations AS st
                ON st.keyStation = g.fkeyRoverStation
            LEFT JOIN tblSoPoints AS sp
                ON sp.keySoPoint = st.fkeySoPoint
            LEFT JOIN tblCrdObsSession AS os
                ON os.keyObsSession = rm.fkeyObsSession
            LEFT JOIN tblObsSessionGps AS gps
                ON gps.fkeyCrdObsSession = os.keyObsSession
            LEFT JOIN tblAntennaModels AS am
                ON am.keyAntennaModel = g.fkeyAntennaModel
            ORDER BY
                g.fkeyRoverStation,
                rm.SecondsFrom1970,
                g.keyCrdGnssRaw
        """
        data = pd.read_sql_query(query, connection)

    data.insert(0, "Project_Name", mjf_path.stem)
    data.insert(1, "Project_Relative_Path", project_relative_path)

    data["NumberOfEpochs"] = pd.to_numeric(
        data["NumberOfEpochs"], errors="coerce"
    ).astype("Int64")
    data["Is_Single_Epoch"] = data["NumberOfEpochs"].eq(1)
    data["Is_Point_Average"] = data["NumberOfEpochs"].gt(1)
    data["Record_Type"] = np.where(
        data["Is_Single_Epoch"], "single_epoch", "point_average"
    )

    data["SolutionType"] = data["SolutionType_Code"].map(SOLUTION_TYPE_MAP)
    unknown_solution = data["SolutionType"].isna() & data["SolutionType_Code"].notna()
    data.loc[unknown_solution, "SolutionType"] = (
        "unknown_code_"
        + data.loc[unknown_solution, "SolutionType_Code"].astype("Int64").astype(str)
    )

    data["Timestamp_UTC"] = to_iso_utc(data["Measurement_SecondsFrom1970"])
    timestamp = pd.to_datetime(
        data["Measurement_SecondsFrom1970"], unit="s", utc=True, errors="coerce"
    )
    data["Date_UTC"] = timestamp.dt.strftime("%Y-%m-%d")
    data["Time_UTC"] = timestamp.dt.strftime("%H:%M:%S.%f").str.rstrip("0").str.rstrip(".")
    data["Session_Start_UTC"] = to_iso_utc(data["Session_Start_SecondsFrom1970"])
    data["Session_End_UTC"] = to_iso_utc(data["Session_End_SecondsFrom1970"])

    data["AntennaHeight_IsSlant"] = data["AntennaHeight_IsSlant_Code"].eq(1)

    add_projected_coordinates(data)
    add_point_height_correction(data)
    transform_xyz_covariance_to_neu(data)

    data["PDOP_Calculated"] = np.sqrt(
        pd.to_numeric(data["HDOP"], errors="coerce") ** 2
        + pd.to_numeric(data["VDOP"], errors="coerce") ** 2
    )

    satellite_columns = [
        "GPS_Satellites",
        "GLONASS_Satellites",
        "Galileo_Satellites",
        "BeiDou_Satellites",
        "SBAS_Satellites",
        "QZSS_Satellites",
        "NavIC_Satellites",
    ]
    for column in satellite_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce").astype("Int64")
    data["Total_Satellites_Logged"] = data[satellite_columns].fillna(0).sum(axis=1).astype("Int64")
    data["Satellite_Status_AllZero"] = data[satellite_columns].fillna(0).eq(0).all(axis=1)

    add_point_quality_fields(data)

    preferred_order = [
        "Project_Name",
        "Project_Relative_Path",
        "Point_Name",
        "Record_Type",
        "Is_Single_Epoch",
        "Is_Point_Average",
        "Epoch_Index_Within_Point",
        "NumberOfEpochs",
        "Point_NumberOfSingleEpochs",
        "Timestamp_UTC",
        "Date_UTC",
        "Time_UTC",
        "Session_Name",
        "Session_Start_UTC",
        "Session_End_UTC",
        "SolutionType",
        "SolutionType_Code",
        "Point_Has_SolutionStatusChange",
        "Point_Share_ppp_float",
        "Point_Share_ppp_convergence",
        "Latitude_deg",
        "Longitude_deg",
        "EllipsoidalHeight_AntennaReferencePoint_m",
        "EllipsoidalHeight_MeasuredPoint_m",
        "AntennaToPoint_HeightCorrection_m",
        "East_UTM32_m",
        "North_UTM32_m",
        "Stored_Point_Latitude_deg",
        "Stored_Point_Longitude_deg",
        "Stored_Point_EllipsoidalHeight_m",
        "Stored_Point_East_UTM32_m",
        "Stored_Point_North_UTM32_m",
        "Variance_X_Cartesian_m2",
        "Variance_Y_Cartesian_m2",
        "Variance_Z_Cartesian_m2",
        "Covariance_XY_Cartesian_m2",
        "Covariance_XZ_Cartesian_m2",
        "Covariance_YZ_Cartesian_m2",
        "Variance_North_m2",
        "Variance_East_m2",
        "Variance_Up_m2",
        "Covariance_North_East_m2",
        "Covariance_North_Up_m2",
        "Covariance_East_Up_m2",
        "Sigma_North_m",
        "Sigma_East_m",
        "Sigma_Up_m",
        "HDOP",
        "VDOP",
        "TDOP",
        "PDOP_Calculated",
        "GPS_Satellites",
        "GLONASS_Satellites",
        "Galileo_Satellites",
        "BeiDou_Satellites",
        "SBAS_Satellites",
        "QZSS_Satellites",
        "NavIC_Satellites",
        "Total_Satellites_Logged",
        "Satellite_Status_AllZero",
        "ObservationDuration_ms",
        "AntennaHeight_Input_m",
        "AntennaHeight_IsSlant",
        "Antenna_Model",
        "Antenna_RINEX_Name",
        "Antenna_SerialNumber",
        "EpochInterval_ms",
        "ElevationMask_deg",
        "RawDataLoggingEnabled",
        "GNSS_Record_ID",
        "RawMeasurement_ID",
        "Station_ID",
        "Session_ID",
        "BaseStation_ID",
        "MeasurementType_Code",
        "MeasurementExtraType_Code",
        "Measurement_TimeSystem_Code",
        "SurveyType_Code",
        "CorrectionsType_Code",
        "Measurement_SecondsFrom1970",
        "Session_Start_SecondsFrom1970",
        "Session_End_SecondsFrom1970",
        "AntennaHeight_IsSlant_Code",
    ]
    existing_preferred = [column for column in preferred_order if column in data.columns]
    remaining = [column for column in data.columns if column not in existing_preferred]
    return data[existing_preferred + remaining]


def write_csv(data: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(
        path,
        index=False,
        sep=CSV_SEPARATOR,
        decimal=CSV_DECIMAL,
        encoding=CSV_ENCODING,
        lineterminator="\n",
    )


def write_column_dictionary(output_directory: Path) -> None:
    dictionary = pd.DataFrame(
        COLUMN_DICTIONARY,
        columns=["Column_Name", "Meaning", "Unit", "Source_or_Calculation"],
    )
    write_csv(dictionary, output_directory / "_column_dictionary.csv")


def find_mjf_files(input_path: Path) -> Iterable[tuple[Path, str]]:
    """Liefert MJF-Dateien samt relativem Pfad."""
    if input_path.is_file() and input_path.suffix.lower() == ".mjf":
        yield input_path.resolve(), input_path.name
        return

    if input_path.is_dir():
        files = sorted(
            path for path in input_path.rglob("*.mjf")
            if not path.name.lower().endswith(".mjf.mirror")
        )
        for path in files:
            yield path.resolve(), str(path.relative_to(input_path))
        return

    raise ValueError(
        "Als Eingabe wird eine .mjf-Datei, eine ZIP-Datei oder ein Ordner erwartet."
    )


def process_projects(input_path: Path, output_directory: Path) -> int:
    output_directory.mkdir(parents=True, exist_ok=True)
    write_column_dictionary(output_directory)

    all_epochs: list[pd.DataFrame] = []
    all_averages: list[pd.DataFrame] = []
    project_summary_rows: list[dict[str, object]] = []

    files = list(find_mjf_files(input_path))
    if not files:
        print(f"Keine .mjf-Dateien gefunden: {input_path}", file=sys.stderr)
        return 1

    print(f"Gefundene MJF-Dateien: {len(files)}")

    for index, (mjf_path, relative_path) in enumerate(files, start=1):
        label = safe_label("__".join(Path(relative_path).with_suffix("").parts))
        print(f"[{index}/{len(files)}] Verarbeite: {relative_path}")

        try:
            data = read_gnss_records(mjf_path, relative_path)
        except Exception as exc:
            print(f"  FEHLER: {exc}", file=sys.stderr)
            project_summary_rows.append({
                "Project_File": relative_path,
                "Status": "error",
                "Message": str(exc),
                "Number_All_Records": 0,
                "Number_Single_Epochs": 0,
                "Number_Point_Averages": 0,
            })
            continue

        if data.empty:
            print("  Keine GNSS-Datensätze vorhanden.")
            project_summary_rows.append({
                "Project_File": relative_path,
                "Status": "no_gnss_records",
                "Message": "tblCrdGnssRaw ist leer",
                "Number_All_Records": 0,
                "Number_Single_Epochs": 0,
                "Number_Point_Averages": 0,
            })
            continue

        epochs = data.loc[data["Is_Single_Epoch"]].copy()
        averages = data.loc[data["Is_Point_Average"]].copy()

        write_csv(data, output_directory / f"{label}__all_gnss_records.csv")
        write_csv(epochs, output_directory / f"{label}__single_epochs.csv")
        write_csv(averages, output_directory / f"{label}__point_averages.csv")

        all_epochs.append(epochs)
        all_averages.append(averages)

        unknown_codes = sorted(
            data.loc[
                data["SolutionType"].astype(str).str.startswith("unknown_code_"),
                "SolutionType_Code",
            ].dropna().unique().tolist()
        )

        project_summary_rows.append({
            "Project_File": relative_path,
            "Status": "ok",
            "Message": "",
            "Number_All_Records": len(data),
            "Number_Single_Epochs": len(epochs),
            "Number_Point_Averages": len(averages),
            "Number_Stations": data["Station_ID"].nunique(dropna=True),
            "Unknown_SolutionType_Codes": ", ".join(map(str, unknown_codes)),
        })

        print(
            f"  Exportiert: {len(epochs)} Einzelepochen, "
            f"{len(averages)} Punktmittel."
        )

    if all_epochs:
        write_csv(
            pd.concat(all_epochs, ignore_index=True),
            output_directory / "_all_projects__single_epochs.csv",
        )
    if all_averages:
        write_csv(
            pd.concat(all_averages, ignore_index=True),
            output_directory / "_all_projects__point_averages.csv",
        )

    write_csv(
        pd.DataFrame(project_summary_rows),
        output_directory / "_export_summary.csv",
    )

    successful = sum(row["Status"] == "ok" for row in project_summary_rows)
    print(f"\nFertig. Erfolgreich verarbeitete Projekte: {successful}/{len(files)}")
    print(f"Ausgabeordner: {output_directory.resolve()}")
    return 0 if successful > 0 else 1


def process_input(input_path: Path, output_directory: Path) -> int:
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory(prefix="topcon_mjf_") as temp_directory:
            extracted = Path(temp_directory)
            with zipfile.ZipFile(input_path, "r") as archive:
                archive.extractall(extracted)
            return process_projects(extracted, output_directory)

    return process_projects(input_path, output_directory)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Exportiert Topcon-Field-GNSS-Einzelepochen aus .mjf-Projekten "
            "in verständlich benannte CSV-Dateien."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Eine .mjf-Datei, eine Topcon-ZIP-Datei oder ein Projektordner",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("topcon_epoch_export"),
        help="Ausgabeordner (Standard: ./topcon_epoch_export)",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    input_path = arguments.input.expanduser().resolve()
    output_directory = arguments.output.expanduser().resolve()

    if not input_path.exists():
        print(f"Eingabe existiert nicht: {input_path}", file=sys.stderr)
        return 2

    try:
        return process_input(input_path, output_directory)
    except (OSError, sqlite3.Error, ValueError, zipfile.BadZipFile) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    input_path = Path(
        r"C:\Users\Michael\Downloads\Topcon_Projektdateien"
    )

    output_directory = Path(
        r"C:\Users\Michael\Downloads\Export_Topcon"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Der Eingabeordner wurde nicht gefunden:\n{input_path}"
        )

    raise SystemExit(
        process_input(
            input_path=input_path,
            output_directory=output_directory,
        )
    )