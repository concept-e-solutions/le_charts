# =============================================================================
# calculations.py
# =============================================================================

# =============================================================================
# IMPORTS 
# =============================================================================
import pandas as pd
import numpy as np
from pathlib import Path


# =============================================================================
# PARAMETER
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent

PARAMS = {
    # --- Preise [ct/kWh] ---
    "P_NETZBEZUG":     20.3,   # Strombezug aus dem Netz (alle Standorte)
    "P_EINSP_PV":       5.0,   # Einspeisevergütung PV
    "P_EINSP_WIND":     8.0,   # Einspeisevergütung Wind
    "P_SHARING_PV":     5.9,   # Abgaben je geteilter PV-kWh (Netzentgelte, ohne Stromsteuer)
    "P_SHARING_WIND":   7.9,   # Abgaben je genutzter Wind-kWh (Netzentgelte inkl. Stromsteuer)

    # --- Skalierung der Erzeugungsprofile [-] ---
    "SCALE_PV":         1.0,   # 1.0 = Profil wie geliefert (600 kWp, 530 MWh/a)
    "SCALE_WIND":       1.33,   # 1.0 = Profil wie geliefert (normiert auf 750 MWh/a)

    # --- Zuteilung bei Knappheit: "proportional" oder "reihenfolge" ---
    "ZUTEILUNG":        "proportional",
    "REIHENFOLGE_PV":   ["OHS", "VW"],          # nur bei ZUTEILUNG="reihenfolge"
    "REIHENFOLGE_WIND": ["W", "OHS", "VW"],     # nur bei ZUTEILUNG="reihenfolge"

    # --- Beispielzeitraum für Detail-Plots ---
    "PLOT_WOCHE_START": "2025-05-12",  # Montag einer sonnigen Maiwoche
}

DATEIEN = {
    "last_w":  "input/Lastgang W.csv",
    "pv":      "input/600 kWp PV Erzeugung W.xlsx",
    "last_ohs": "input/R - Lastgang OHS 2025.xlsx",
    "last_vw":  "input/R - Lastgang VW 2025.xlsx",
    "wind":    "input/Erzeugungsprofil 750 MWh Windrad.xlsx",  # alt: Erzeugungsprofil_750_kWp_Windrad.xlsx
}

JAHR = 2025
N_QH = 35040          # Viertelstunden im Jahr 2025
QH_H = 0.25           # Stunden je Viertelstunde


# =============================================================================
# IMPORT & HARMONIZE DATA
# =============================================================================
def _standard_index() -> pd.DatetimeIndex:
    """Gemeinsamer Index: Intervall-BEGINN, 01.01. 00:00 bis 31.12. 23:45."""
    return pd.date_range(f"{JAHR}-01-01 00:00", periods=N_QH, freq="15min")


def _check(name: str, series: pd.Series):
    assert len(series) == N_QH, f"{name}: {len(series)} statt {N_QH} Werten"
    assert series.isna().sum() == 0, f"{name}: {series.isna().sum()} fehlende Werte"
    assert (series >= 0).all(), f"{name}: negative Werte enthalten"


def lade_profile(data_dir: Path) -> pd.DataFrame:
    """Liest alle Profile ein und gibt einen DataFrame [kWh je Viertelstunde] zurück.

    Zeitstempel-Konventionen der Quelldateien:
      - Lastgang W (CSV) & PV (Zählpunkt-Export): Intervall-ENDE (erster Stempel 00:15)
      - OHS / VW (LG Vektor):                     Intervall-ENDE (Tag + Zeit, letzter '24:00')
      - Wind (SMARD):                             Intervall-BEGINN ('Datum von')
    Alle Reihen sind vollständig (35.040 Werte) und chronologisch sortiert;
    sie werden positionsbasiert auf den gemeinsamen Intervall-Beginn-Index gelegt.
    """
    idx = _standard_index()

    # --- Lastgang W: CSV, ';'-getrennt, Dezimalkomma, 1 Kopfzeile, kW ---
    w = pd.read_csv(data_dir / DATEIEN["last_w"], sep=";", skiprows=1, header=None,
                    names=["ts", "kw"], decimal=",", encoding="latin-1")
    w["ts"] = pd.to_datetime(w["ts"], dayfirst=True, errors="coerce")
    w = w.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)

    # --- PV: xlsx, Daten ab Zeile 10, [Zeitstempel, kW] ---
    pv = pd.read_excel(data_dir / DATEIEN["pv"], header=None, skiprows=9,
                       names=["ts", "kw"])
    pv["ts"] = pd.to_datetime(pv["ts"], dayfirst=True, errors="coerce")
    pv = pv.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    pv["kw"] = pd.to_numeric(pv["kw"], errors="coerce")

    # --- OHS & VW: 'LG Vektor', Daten ab Zeile 8, [Tag, Zeit, kW] ---
    def lade_lg_vektor(fname: str) -> pd.Series:
        df = pd.read_excel(data_dir / fname, sheet_name="LG Vektor", header=None,
                           skiprows=7, usecols=[0, 1, 2], names=["tag", "zeit", "kw"])
        df["kw"] = pd.to_numeric(df["kw"], errors="coerce")
        df = df.dropna(subset=["kw"]).reset_index(drop=True)
        return df["kw"]

    ohs_kw = lade_lg_vektor(DATEIEN["last_ohs"])
    vw_kw = lade_lg_vektor(DATEIEN["last_vw"])

    # --- Wind: SMARD-Export, Daten ab Zeile 11, [von, bis, kWh je 15min] ---
    wind = pd.read_excel(data_dir / DATEIEN["wind"], header=None, skiprows=10,
                         usecols=[0, 1, 2], names=["von", "bis", "kwh"])
    wind["kwh"] = pd.to_numeric(wind["kwh"], errors="coerce")
    wind = wind.dropna(subset=["kwh"]).reset_index(drop=True)

    # --- Zusammenführen: alles in kWh je Viertelstunde ---
    df = pd.DataFrame(index=idx)
    df["last_W"] = w["kw"].to_numpy() * QH_H
    df["last_OHS"] = ohs_kw.to_numpy() * QH_H
    df["last_VW"] = vw_kw.to_numpy() * QH_H
    df["pv"] = pv["kw"].to_numpy() * QH_H * PARAMS["SCALE_PV"]
    df["wind"] = wind["kwh"].to_numpy() * PARAMS["SCALE_WIND"]

    for col in df.columns:
        _check(col, df[col])
    return df


# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================

def _verteile(angebot: pd.Series, bedarfe: dict[str, pd.Series],
              modus: str, reihenfolge: list[str]) -> dict[str, pd.Series]:
    """Verteilt 'angebot' auf mehrere Bedarfe (kWh je QH).

    proportional: je QH anteilig zur Höhe des jeweiligen Bedarfs.
    reihenfolge:  Bedarfe werden in fester Reihenfolge nacheinander bedient.
    Rückgabe: zugeteilte Menge je Bedarfsträger.
    """
    zuteilung = {}
    if modus == "proportional":
        summe = sum(bedarfe.values())
        # Anteil = Bedarf/Summe; bei Summe 0 -> 0. Deckung = min(Angebot, Summe).
        deckung = np.minimum(angebot, summe)
        with np.errstate(divide="ignore", invalid="ignore"):
            for name, bedarf in bedarfe.items():
                anteil = np.where(summe > 0, bedarf / summe, 0.0)
                zuteilung[name] = pd.Series(deckung * anteil, index=angebot.index)
    elif modus == "reihenfolge":
        rest = angebot.copy()
        for name in reihenfolge:
            zu = np.minimum(rest, bedarfe[name])
            zuteilung[name] = pd.Series(zu, index=angebot.index)
            rest = rest - zu
    else:
        raise ValueError(f"Unbekannter Zuteilungsmodus: {modus}")
    return zuteilung


def rechne_kaskade(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Führt die vier Kaskadenschritte aus. Alle Spalten in kWh je Viertelstunde."""
    d = df.copy()

    # --- Schritt 1: PV deckt W ---
    d["pv_selbst_W"] = np.minimum(d["pv"], d["last_W"])
    d["pv_ueberschuss"] = d["pv"] - d["pv_selbst_W"]
    d["rest_W_nach_pv"] = d["last_W"] - d["pv_selbst_W"]

    # --- Schritt 2: PV-Überschuss via Sharing an R (OHS + VW) ---
    zu_pv = _verteile(d["pv_ueberschuss"],
                      {"OHS": d["last_OHS"], "VW": d["last_VW"]},
                      p["ZUTEILUNG"], p["REIHENFOLGE_PV"])
    d["pv_sharing_OHS"] = zu_pv["OHS"]
    d["pv_sharing_VW"] = zu_pv["VW"]
    d["pv_sharing"] = d["pv_sharing_OHS"] + d["pv_sharing_VW"]
    d["pv_einspeisung"] = d["pv_ueberschuss"] - d["pv_sharing"]
    d["rest_OHS_nach_pv"] = d["last_OHS"] - d["pv_sharing_OHS"]
    d["rest_VW_nach_pv"] = d["last_VW"] - d["pv_sharing_VW"]

    # --- Schritt 3: Wind deckt Restlasten von W, OHS, VW ---
    zu_wind = _verteile(d["wind"],
                        {"W": d["rest_W_nach_pv"],
                         "OHS": d["rest_OHS_nach_pv"],
                         "VW": d["rest_VW_nach_pv"]},
                        p["ZUTEILUNG"], p["REIHENFOLGE_WIND"])
    d["wind_W"] = zu_wind["W"]
    d["wind_OHS"] = zu_wind["OHS"]
    d["wind_VW"] = zu_wind["VW"]
    d["wind_nutzung"] = d["wind_W"] + d["wind_OHS"] + d["wind_VW"]
    d["wind_einspeisung"] = d["wind"] - d["wind_nutzung"]

    # --- Schritt 4: Netzbezug der verbleibenden Restlast ---
    d["netz_W"] = d["rest_W_nach_pv"] - d["wind_W"]
    d["netz_OHS"] = d["rest_OHS_nach_pv"] - d["wind_OHS"]
    d["netz_VW"] = d["rest_VW_nach_pv"] - d["wind_VW"]
    d["netz_gesamt"] = d["netz_W"] + d["netz_OHS"] + d["netz_VW"]

    # --- Energiebilanz-Prüfung (Toleranz: Rundungsfehler) ---
    last = d["last_W"] + d["last_OHS"] + d["last_VW"]
    deckung = (d["pv_selbst_W"] + d["pv_sharing"] + d["wind_nutzung"] + d["netz_gesamt"])
    fehler = (last - deckung).abs().max()
    assert fehler < 1e-6, f"Energiebilanz verletzt (max. Abweichung {fehler} kWh)"
    erz = d["pv"] + d["wind"]
    verwendung = (d["pv_selbst_W"] + d["pv_sharing"] + d["pv_einspeisung"]
                  + d["wind_nutzung"] + d["wind_einspeisung"])
    assert (erz - verwendung).abs().max() < 1e-6, "Erzeugungsbilanz verletzt"
    return d

def prepare_weekly(d: pd.DataFrame) -> pd.DataFrame:
    start = PARAMS["PLOT_WOCHE_START"]
    end = pd.Timestamp(start) + pd.Timedelta(days=7)

    weekly = d.loc[start:end].copy()
    weekly["timestamp"] = weekly.index

    for column in [
        "pv_sharing",
        "pv_einspeisung",
        "pv_selbst_W",
        "last_W",
        "wind_OHS",
        "wind_VW",
        "netz_OHS",
        "netz_VW",
        "wind_W",
        "wind_einspeisung",
        "wind",
    ]:
        if column in weekly:
            weekly[f"{column}_kw"] = weekly[column] / QH_H

    weekly["wind_r_kw"] = (
        weekly["wind_OHS"] + weekly["wind_VW"]
    ) / QH_H

    weekly["netz_r_kw"] = (
        weekly["netz_OHS"] + weekly["netz_VW"]
    ) / QH_H

    return weekly

def prepare_monthly(d: pd.DataFrame) -> pd.DataFrame:
    monthly = d.resample("MS").sum() / 1000
    monthly["month"] = monthly.index.strftime("%b")

    monthly["pv_selbst_W_month"] = monthly["pv_selbst_W"]
    monthly["pv_sharing_month"] = monthly["pv_sharing"]
    monthly["wind_nutzung_month"] = monthly["wind_nutzung"]
    monthly["netz_gesamt_month"] = monthly["netz_gesamt"]

    return monthly

def prepare_benefit_monthly(d: pd.DataFrame) -> pd.DataFrame:
    monthly = d.resample("MS").sum() / 1000
    monthly["month"] = monthly.index.strftime("%b")

    marge_eigen = PARAMS["P_NETZBEZUG"]
    marge_pv = (
        PARAMS["P_NETZBEZUG"]
        - PARAMS["P_SHARING_PV"]
    )
    marge_wind = (
        PARAMS["P_NETZBEZUG"]
        - PARAMS["P_SHARING_WIND"]
    )

    monthly["eur_eigen"] = (
        monthly["pv_selbst_W"] * 1000 * marge_eigen / 100
    )

    monthly["eur_pv"] = (
        monthly["pv_sharing"] * 1000 * marge_pv / 100
    )

    monthly["eur_wind"] = (
        monthly["wind_nutzung"] * 1000 * marge_wind / 100
    )

    monthly["eur_einsp"] = (
        monthly["pv_einspeisung"] * 1000 * PARAMS["P_EINSP_PV"]
        + monthly["wind_einspeisung"]
        * 1000
        * PARAMS["P_EINSP_WIND"]
    ) / 100

    return monthly

def prepare_annual(d: pd.DataFrame) -> dict:
    return {
        "pv_einspeisung_value": d["pv_einspeisung"].sum() / 1000,
        "pv_sharing_value": d["pv_sharing"].sum() / 1000,
        "pv_selbst_W_value": d["pv_selbst_W"].sum() / 1000,
        "wind_einspeisung_value": d["wind_einspeisung"].sum() / 1000,
        "wind_VW_value": d["wind_VW"].sum() / 1000,
        "wind_OHS_value": d["wind_OHS"].sum() / 1000,
        "wind_W_value": d["wind_W"].sum() / 1000,
    }

def rechne_wirtschaftlichkeit(d: pd.DataFrame) -> dict:
    """Jahreskosten [EUR] im Referenzfall und im Projektfall, Delta = Vorteil.

    Referenzfall (Bestand, KEINE Erzeugung vorhanden):
      - PV und Windrad existieren nicht -> keine Eigennutzung, kein Sharing,
        keine Einspeisung.
      - Alle drei Standorte beziehen ihre VOLLE Last aus dem Netz (P_NETZBEZUG).
    Projektfall (PV + Wind als Neuinvestition, Kaskade):
      - Netzbezug nur noch für die verbleibende Restlast.
      - Sharing-Abgaben auf jede geteilte/eigengenutzte kWh (P_SHARING_*).
      - Einspeiseerlöse für die verbleibenden Überschüsse (P_EINSP_*).
    Vorzeichen: Kosten positiv, Erlöse negativ. Vorteil = Referenz - Projekt.
    """
    ct = 1 / 100.0  # ct -> EUR

    e = {k: d[k].sum() for k in d.columns}  # Jahressummen kWh
    last_gesamt = e["last_W"] + e["last_OHS"] + e["last_VW"]

    referenz = {
        "Netzbezug (volle Last)": last_gesamt * PARAMS["P_NETZBEZUG"] * ct,
        "Einspeiseerlös": 0.0,
        "Abgaben Sharing": 0.0,
    }
    projekt = {
        "Netzbezug (volle Last)": e["netz_gesamt"] * PARAMS["P_NETZBEZUG"] * ct,
        "Einspeiseerlös": -(e["pv_einspeisung"] * PARAMS["P_EINSP_PV"]
                            + e["wind_einspeisung"] * PARAMS["P_EINSP_WIND"]) * ct,
        "Abgaben Sharing": (e["pv_sharing"] * PARAMS["P_SHARING_PV"]
                            + e["wind_nutzung"] * PARAMS["P_SHARING_WIND"]) * ct,
    }
    referenz["Summe"] = sum(referenz.values())
    projekt["Summe"] = sum(projekt.values())
    vorteil = referenz["Summe"] - projekt["Summe"]

    # --- Zerlegung des Vorteils je Mechanismus (Kontrollrechnung) ---
    # Jede genutzte kWh spart vollen Netzbezug, kostet aber ihre Abgabe.
    # Jede eingespeiste kWh bringt zusätzlich den Einspeiseerlös.
    marge_eigen = PARAMS["P_NETZBEZUG"] - 0.0                    # Eigenverbrauch W: keine Abgabe
    marge_pv = PARAMS["P_NETZBEZUG"] - PARAMS["P_SHARING_PV"]         # PV-Sharing an R
    marge_wind = PARAMS["P_NETZBEZUG"] - PARAMS["P_SHARING_WIND"]     # Wind-Nutzung W+R
    beitrag_eigen = e["pv_selbst_W"] * marge_eigen * ct
    beitrag_pv = e["pv_sharing"] * marge_pv * ct
    beitrag_wind = e["wind_nutzung"] * marge_wind * ct
    beitrag_einsp = (e["pv_einspeisung"] * PARAMS["P_EINSP_PV"]
                     + e["wind_einspeisung"] * PARAMS["P_EINSP_WIND"]) * ct

    return {
        "energie": e,
        "referenz": referenz,
        "projekt": projekt,
        "vorteil": vorteil,
        "beitrag_eigen": beitrag_eigen,
        "beitrag_pv": beitrag_pv,
        "beitrag_wind": beitrag_wind,
        "beitrag_einsp": beitrag_einsp,
        "marge_eigen_ct": marge_eigen,
        "marge_pv_ct": marge_pv,
        "marge_wind_ct": marge_wind,
    }


# =============================================================================
# REPORT
# =============================================================================

def print_report(erg: dict):
    """Prints a summary report of the energy balance and economic results."""
    e = erg["energie"]
    mwh = lambda k: e[k] / 1000

    print("=" * 74)
    print("ENERGIEBILANZ (Jahressummen, MWh)")
    print("=" * 74)
    print(f"Lasten:      W {mwh('last_W'):8.1f} | OHS {mwh('last_OHS'):8.1f} | "
          f"VW {mwh('last_VW'):7.1f} | Summe {mwh('last_W')+mwh('last_OHS')+mwh('last_VW'):8.1f}")
    print(f"Erzeugung:   PV {mwh('pv'):7.1f} | Wind {mwh('wind'):7.1f}")
    print("-" * 74)
    print("Schritt 1 – PV bei W:")
    print(f"  Eigenverbrauch W:            {mwh('pv_selbst_W'):8.1f}  "
          f"({e['pv_selbst_W']/e['pv']*100:5.1f} % der PV)")
    print(f"  PV-Überschuss:               {mwh('pv_ueberschuss'):8.1f}")
    print("Schritt 2 – PV-Sharing an R:")
    print(f"  an OHS:                      {mwh('pv_sharing_OHS'):8.1f}")
    print(f"  an VW:                       {mwh('pv_sharing_VW'):8.1f}")
    print(f"  Rest-Einspeisung PV:         {mwh('pv_einspeisung'):8.1f}")
    print("Schritt 3 – Wind an Restlasten:")
    print(f"  an W:                        {mwh('wind_W'):8.1f}")
    print(f"  an OHS:                      {mwh('wind_OHS'):8.1f}")
    print(f"  an VW:                       {mwh('wind_VW'):8.1f}")
    print(f"  genutzt gesamt:              {mwh('wind_nutzung'):8.1f}  "
          f"({e['wind_nutzung']/e['wind']*100:5.1f} % des Winds)")
    print(f"  Rest-Einspeisung Wind:       {mwh('wind_einspeisung'):8.1f}")
    print("Schritt 4 – Netzbezug:")
    print(f"  W {mwh('netz_W'):8.1f} | OHS {mwh('netz_OHS'):8.1f} | VW {mwh('netz_VW'):7.1f} "
          f"| Summe {mwh('netz_gesamt'):8.1f}")

    print()
    print("=" * 74)
    print("WIRTSCHAFTLICHKEIT (systemisch, EUR/Jahr; Kosten +, Erlöse -)")
    print("Referenz = Bestand ohne PV/Wind: alle Standorte voller Netzbezug")
    print("=" * 74)
    kopf = f"{'Position':28s} {'Referenz':>14s} {'Projekt':>14s} {'Delta':>14s}"
    print(kopf)
    print("-" * len(kopf))
    for pos in ["Netzbezug (volle Last)", "Einspeiseerlös", "Abgaben Sharing", "Summe"]:
        r, s = erg["referenz"][pos], erg["projekt"][pos]
        print(f"{pos:28s} {r:14,.0f} {s:14,.0f} {r - s:14,.0f}")
    print("-" * len(kopf))
    print(f"{'VORTEIL PROJEKT (PV + WIND)':28s} {'':14s} {'':14s} {erg['vorteil']:14,.0f}")
    print()
    print("Zerlegung des Vorteils (Kontrollrechnung, gegen vollen Netzbezug):")
    print(f"  PV-Eigenverbr. W:{e['pv_selbst_W']/1000:7.1f} MWh x {erg['marge_eigen_ct']:5.2f} ct/kWh "
          f"(={PARAMS['P_NETZBEZUG']}, keine Abgabe)      = {erg['beitrag_eigen']:10,.0f} EUR")
    print(f"  PV-Sharing an R: {e['pv_sharing']/1000:7.1f} MWh x {erg['marge_pv_ct']:5.2f} ct/kWh "
          f"(={PARAMS['P_NETZBEZUG']}-{PARAMS['P_SHARING_PV']})           = {erg['beitrag_pv']:10,.0f} EUR")
    print(f"  Wind-Nutzung:    {e['wind_nutzung']/1000:7.1f} MWh x {erg['marge_wind_ct']:5.2f} ct/kWh "
          f"(={PARAMS['P_NETZBEZUG']}-{PARAMS['P_SHARING_WIND']})           = {erg['beitrag_wind']:10,.0f} EUR")
    print(f"  Einspeiseerlöse: PV {e['pv_einspeisung']/1000:.1f} MWh x {PARAMS['P_EINSP_PV']} + "
          f"Wind {e['wind_einspeisung']/1000:.1f} MWh x {PARAMS['P_EINSP_WIND']} ct/kWh "
          f"= {erg['beitrag_einsp']:10,.0f} EUR")
    summe_beitraege = (erg["beitrag_eigen"] + erg["beitrag_pv"]
                       + erg["beitrag_wind"] + erg["beitrag_einsp"])
    print(f"  Summe Beiträge: {summe_beitraege:,.0f} EUR "
          f"(Abweichung zum Vorteil: {abs(summe_beitraege - erg['vorteil']):.2f} EUR)")



# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================
def calc_results() -> dict:
    """Performs the calculations and returns the prepared data sets."""
    df = lade_profile(BASE_DIR)
    calculated = rechne_kaskade(df, PARAMS)
    res = rechne_wirtschaftlichkeit(calculated)
    datasets = {
        "weekly": prepare_weekly(calculated),
        "monthly": prepare_monthly(calculated),
        "annual": prepare_annual(calculated),
        "benefit_monthly": prepare_benefit_monthly(calculated),
    }
    print_report(res)
    return datasets

