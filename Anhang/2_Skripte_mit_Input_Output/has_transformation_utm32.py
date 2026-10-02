"""
Galileo HAS: ITRF2020 -> ETRF2020 -> ETRS89 / UTM Zone 32N

Standalone-Skript fuer VS Code.

Eingabe (Topcon-CSV):
    id, Latitude, Longitude, Height_cartesian, Date und optional Time
    Standard-Trennzeichen: ;
    Dezimalpunkt oder Dezimalkomma werden fuer die relevanten Koordinatenspalten akzeptiert.

Transformation:
    1) ITRF2020 geographisch 3D -> ITRF2020 geozentrisch XYZ
    2) EPSG:10573, ITRF2020 -> ETRF2020, zeitabhaengig mit Messepoche
    3) ETRF2020 XYZ -> ETRF2020 Lat/Lon/h
    4) ETRF2020 -> ETRS89 / UTM Zone 32N (EPSG:25832)

Ausgabe:
    CSV im selben Ordner wie die Eingabe, wenn kein -o/--output angegeben wird.
    Die Originalspalten bleiben erhalten; transformierte Koordinaten werden ergaenzt.
"""


from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
from pyproj import Transformer


#
#
# Zur Erstellung des skriptes wurde KI unterstützend verwendet;
# Dieses Skript wurde vom Betreuer bereitgestellt
#
#


# -----------------------------------------------------------------------------
# EINSTELLUNGEN
# -----------------------------------------------------------------------------
# Wird verwendet, wenn das Skript in VS Code mit "Run Python File" ohne
# Kommandozeilenargument gestartet wird. Fuer andere Dateien einfach aendern
# oder den Dateipfad beim Aufruf als Argument uebergeben.
DEFAULT_INPUT_CSV = Path(
    r"C:\Users\Michael\Downloads\280426_weingut_HAS.csv"
)

CSV_SEPARATOR = ";"
OUTPUT_SEPARATOR = ";"
OUTPUT_DECIMAL = ","

ID_COL = "id"
LAT_COL = "Latitude"
LON_COL = "Longitude"
H_COL = "Height_cartesian"

DATE_COL_CANDIDATES = ["Date", "Datum", "date", "datum"]
TIME_COL_CANDIDATES = ["Time", "Zeit", "time", "zeit", "Uhrzeit"]

# Referenzsysteme
ITRF2020_GEOG3D = "EPSG:9989"
ITRF2020_ECEF = "EPSG:9988"
ETRF2020_GEOG3D = "EPSG:10570"
ETRF2020_ECEF = "EPSG:10569"

# Explizit dieselbe zeitabhaengige Operation wie im getesteten Notebook/EUREF-Vergleich
ITRF2020_TO_ETRF2020_OPERATION = "EPSG:10573"

# ArcGIS-Zielsystem: ETRS89 / UTM Zone 32N
UTM32_CRS = "EPSG:25832"


# -----------------------------------------------------------------------------
# HILFSFUNKTIONEN
# -----------------------------------------------------------------------------
def check_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            "Folgende Spalten fehlen in der CSV: "
            + ", ".join(missing)
            + "\nVorhandene Spalten: "
            + ", ".join(map(str, df.columns))
        )


def find_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    columns_by_name = {str(col).strip().lower(): str(col) for col in df.columns}
    for candidate in candidates:
        column = columns_by_name.get(candidate.lower())
        if column is not None:
            return column
    return None


def to_numeric_column(series: pd.Series) -> pd.Series:
    """Akzeptiert sowohl Dezimalkomma als auch Dezimalpunkt."""
    return pd.to_numeric(
        series.astype(str).str.strip().str.replace(",", ".", regex=False),
        errors="raise",
    )


def decimal_year_from_datetime(dt: pd.Timestamp) -> float:
    dt = pd.Timestamp(dt)
    start = pd.Timestamp(year=dt.year, month=1, day=1)
    end = pd.Timestamp(year=dt.year + 1, month=1, day=1)
    return dt.year + (dt - start).total_seconds() / (end - start).total_seconds()


def detect_epochs_from_csv(df: pd.DataFrame) -> tuple[np.ndarray, str, str | None]:
    date_col = find_existing_column(df, DATE_COL_CANDIDATES)
    if date_col is None:
        raise ValueError(
            "Keine Datumsspalte fuer die Epochenerkennung gefunden. "
            f"Erwartet eine von: {', '.join(DATE_COL_CANDIDATES)}"
        )

    time_col = find_existing_column(df, TIME_COL_CANDIDATES)
    dates = df[date_col].astype(str).str.strip()

    if time_col is not None:
        times = df[time_col].fillna("").astype(str).str.strip()
        raw_datetimes = (dates + " " + times).str.strip()
    else:
        raw_datetimes = dates

    datetimes = pd.to_datetime(raw_datetimes, dayfirst=True, errors="raise")
    epoch_array = datetimes.map(decimal_year_from_datetime).to_numpy(dtype=float)
    return epoch_array, date_col, time_col


def geodetic_to_ecef(
    lon: np.ndarray,
    lat: np.ndarray,
    h: np.ndarray,
    frame: str = "ITRF2020",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if frame.upper() == "ITRF2020":
        source_crs, target_crs = ITRF2020_GEOG3D, ITRF2020_ECEF
    elif frame.upper() == "ETRF2020":
        source_crs, target_crs = ETRF2020_GEOG3D, ETRF2020_ECEF
    else:
        raise ValueError("frame muss 'ITRF2020' oder 'ETRF2020' sein.")

    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return transformer.transform(lon, lat, h)


def ecef_to_geodetic(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    frame: str = "ETRF2020",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if frame.upper() == "ITRF2020":
        source_crs, target_crs = ITRF2020_ECEF, ITRF2020_GEOG3D
    elif frame.upper() == "ETRF2020":
        source_crs, target_crs = ETRF2020_ECEF, ETRF2020_GEOG3D
    else:
        raise ValueError("frame muss 'ITRF2020' oder 'ETRF2020' sein.")

    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return transformer.transform(x, y, z)


def transform_file(input_csv: Path, output_csv: Path) -> pd.DataFrame:
    # CSV bewusst als Text lesen; damit funktionieren deutsche Dezimalkommas robust.
    df = pd.read_csv(input_csv, sep=CSV_SEPARATOR, dtype=str, encoding="utf-8-sig")
    check_columns(df, [ID_COL, LAT_COL, LON_COL, H_COL])

    if df.empty:
        raise ValueError("Die CSV enthaelt keine Datensaetze.")

    # Messepochen aus Date + optional Time
    epoch_array, epoch_date_col, epoch_time_col = detect_epochs_from_csv(df)
    epoch_source = epoch_date_col
    if epoch_time_col is not None:
        epoch_source += f" + {epoch_time_col}"

    print(f"Epoche automatisch aus CSV erkannt: {epoch_source}")
    if np.ptp(epoch_array) < 1e-12:
        print(f"Verwendete Epoche: {epoch_array[0]:.10f}")
    else:
        print(
            "Verwendete Epochen: "
            f"{epoch_array.min():.10f} bis {epoch_array.max():.10f}"
        )

    # Nur die benoetigten Eingabekoordinaten numerisch machen.
    lat_i = to_numeric_column(df[LAT_COL]).to_numpy(dtype=float)
    lon_i = to_numeric_column(df[LON_COL]).to_numpy(dtype=float)
    h_i = to_numeric_column(df[H_COL]).to_numpy(dtype=float)

    # 1) HAS Lat/Lon/h -> ITRF2020 XYZ
    x_i, y_i, z_i = geodetic_to_ecef(lon_i, lat_i, h_i, frame="ITRF2020")

    # 2) ITRF2020 @ Messepoche -> ETRF2020 @ Messepoche
    # Explizit EPSG:10573 statt "erste gefundene Operation", damit der Workflow
    # reproduzierbar dieselbe validierte Operation verwendet.
    itrf_to_etrf = Transformer.from_pipeline(ITRF2020_TO_ETRF2020_OPERATION)

    print("\nVerwendete Referenzrahmentransformation:")
    print(itrf_to_etrf.description)
    print(itrf_to_etrf.definition)

    x_e, y_e, z_e, _ = itrf_to_etrf.transform(x_i, y_i, z_i, epoch_array)

    # 3) ETRF2020 XYZ -> ETRF2020 Lat/Lon/h
    lon_e, lat_e, h_e = ecef_to_geodetic(x_e, y_e, z_e, frame="ETRF2020")

    # 4) ETRF2020 Lat/Lon -> ETRS89 / UTM Zone 32N
    # EPSG:25832 ist das Koordinatensystem, das anschliessend in ArcGIS Pro
    # fuer Easting/Northing angegeben werden kann.
    etrf_to_utm32 = Transformer.from_crs(
        ETRF2020_GEOG3D,
        UTM32_CRS,
        always_xy=True,
    )
    east_utm32, north_utm32 = etrf_to_utm32.transform(lon_e, lat_e)

    # Originalspalten behalten und Transformationswerte ergaenzen.
    result = df.copy()
    result["epoch"] = epoch_array

    result["Lat_ITRF2020"] = lat_i
    result["Lon_ITRF2020"] = lon_i
    result["h_ITRF2020"] = h_i

    result["X_ITRF2020"] = x_i
    result["Y_ITRF2020"] = y_i
    result["Z_ITRF2020"] = z_i

    result["X_ETRF2020"] = x_e
    result["Y_ETRF2020"] = y_e
    result["Z_ETRF2020"] = z_e

    result["Lat_ETRF2020"] = lat_e
    result["Lon_ETRF2020"] = lon_e
    result["h_ETRF2020"] = h_e

    # ArcGIS-fertige UTM-Spalten
    result["East_ETRS89_UTM32"] = east_utm32
    result["North_ETRS89_UTM32"] = north_utm32

    # Falls die Topcon-Datei bereits East/North enthaelt, Korrektur direkt ausgeben.
    if "East" in df.columns and "North" in df.columns:
        east_original = to_numeric_column(df["East"]).to_numpy(dtype=float)
        north_original = to_numeric_column(df["North"]).to_numpy(dtype=float)

        delta_e = east_utm32 - east_original
        delta_n = north_utm32 - north_original

        result["dEast_m"] = delta_e
        result["dNorth_m"] = delta_n
        result["Shift_2D_m"] = np.hypot(delta_e, delta_n)

        print("\nKorrektur gegenueber den vorhandenen East/North-Werten:")
        print(f"  Mittel dE:       {np.mean(delta_e):+.4f} m")
        print(f"  Mittel dN:       {np.mean(delta_n):+.4f} m")
        print(f"  Mittel 2D-Shift: {np.mean(np.hypot(delta_e, delta_n)):.4f} m")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(
        output_csv,
        index=False,
        sep=OUTPUT_SEPARATOR,
        decimal=OUTPUT_DECIMAL,
        float_format="%.10f",
        encoding="utf-8-sig",
    )

    print(f"\n{len(result)} Punkte geschrieben:")
    print(output_csv.resolve())
    print("\nArcGIS Pro:")
    print("  X-Feld: East_ETRS89_UTM32")
    print("  Y-Feld: North_ETRS89_UTM32")
    print("  Koordinatensystem: ETRS89 / UTM Zone 32N (EPSG:25832)")
    print("  h_ETRF2020 ist die ellipsoidische Hoehe, nicht die Normalhoehe.")

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transformiert Galileo-HAS-Koordinaten von ITRF2020 zur Messepoche "
            "nach ETRF2020 und anschliessend nach ETRS89 / UTM Zone 32N."
        )
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT_CSV,
        help="Topcon-HAS-CSV. Ohne Angabe wird DEFAULT_INPUT_CSV verwendet.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Optionale Ausgabe-CSV. Standard: <Eingabe>_ETRF2020_UTM32.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_csv: Path = args.input_csv

    if not input_csv.exists():
        raise FileNotFoundError(
            f"Eingabedatei nicht gefunden: {input_csv}\n"
            "Passe DEFAULT_INPUT_CSV oben im Skript an oder uebergib den "
            "Dateipfad beim Aufruf."
        )

    output_csv = args.output
    if output_csv is None:
        output_csv = input_csv.with_name(
            f"{input_csv.stem}_ETRF2020_UTM32.csv"
        )

    print(f"pyproj: {pyproj.__version__}")
    print(f"PROJ:   {pyproj.proj_version_str}")
    print(f"Eingabe: {input_csv.resolve()}")
    print(f"Ausgabe: {output_csv.resolve()}\n")

    transform_file(input_csv, output_csv)


if __name__ == "__main__":
    main()
