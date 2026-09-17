# =============================================================================
# calculations.py
# =============================================================================

# =============================================================================
# IMPORTS 
# =============================================================================
import pandas as pd
import numpy as np
from pathlib import Path

# TODO: Add any other necessary imports here


# =============================================================================
# PARAMETER
# =============================================================================
# TODO: Define any parameters or constants needed for calculations
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
FILE_LASTGANG = INPUT_DIR / "Lastgangdaten_Strom_2024_2025_-_KI_fähig.xlsx"
LASTGANG_SHEET = "Strom 2025"
LASTGANG_SPALTE = 3
FILE_WP = INPUT_DIR / "data_table.xlsx"
FILE_WP_FALLBACK = INPUT_DIR / "Bilanz_WP_PV_Wind_2025.xlsx"
FILE_PV = INPUT_DIR / "PV_500_kWp_skaliert.xlsx"
FILE_WIND = INPUT_DIR / "WEA_Profil_E82_Nordhorn.xlsx"
OUTPUT_XLSX = BASE_DIR / "ES_Bilanz_2025_v2.xlsx"

print(f"Arbeitsordner: {BASE_DIR}")


# --- Preise [ct/kWh] (Vorgaben Unternehmen W) ---
# Referenzsystem: Vollversorgung aus dem Netz (Bestandsvertrag)
NETZSTROMPREIS_REF_CT = 13.931   # Strompreis + Netznutzung, Referenzfall
# Neues System: nur noch Reststrombezug -> schlechtere Konditionen
NETZSTROMPREIS_NEU_CT = 18.241     # Strompreis + Netznutzung, Reststrom
NETZENTGELT_CT        = 4.241    # Netznutzungsgebühr
STROMPREIS_CT         = 14.0    # Arbeitspreis ohne Netzentgelt (Bewertung Wind-EV)
PV_EINSPEISE_CT   = 5.0
WIND_EINSPEISE_CT = 8.0
GASPREIS_CT       = 8.0
GASVERBRAUCH_IST_KWH = 1_140_000  # lt. Kunde; dient nur dem Konsistenz-Check

# Konsistenzoption: Wind aus dem Energy Sharing spart im neuen System den
# Reststrompreis abzueglich des weiterhin faelligen Netzentgelts.
# True  -> STROMPREIS_CT wird aus NETZSTROMPREIS_NEU_CT - NETZENTGELT_CT abgeleitet
# False -> vom Kunden vorgegebener Wert bleibt stehen (Default)
STROMPREIS_ABLEITEN = False
if STROMPREIS_ABLEITEN:
    STROMPREIS_CT = NETZSTROMPREIS_NEU_CT - NETZENTGELT_CT

# --- Anlagen ---
PV1_PEAK_KWP   = 500
PV2_PEAK_KWP   = 336          # Carport
WKA_NENN_MW    = 2.0          # Altanlage 2 MW (fix)

# --- Verschattung PV ---
# Kundenangabe: ein Huegel verschattet Dach- UND Carportflaeche in den
# genannten Monaten vollstaendig -> Erzeugung wird auf 0 kWh gesetzt.
PV_VERSCHATTUNG_MONATE = (1, 12)   # Januar, Dezember; () = keine Verschattung

# --- Investitionen [EUR] ---
PV1_INVEST_EUR = 410_890      # konkretes Angebot 
PV2_INVEST_EUR = 625_000      # Carport, daher hoeherer spez. Preis
WKA_INVEST_EUR = 600_000      # gebrauchte 2-MW-Anlage (Kundenannahme)
WP_INVEST_EUR  = 600_000      # konkretes Angebot (Sonderfall)

# --- Betriebskosten [EUR/a] ---
PV1_OPEX_EUR = 0.015 * PV1_INVEST_EUR   # 1,5 %/a (Vorgabe)
PV2_OPEX_EUR = 0.015 * PV2_INVEST_EUR   # 1,5 %/a (Vorgabe)
WKA_OPEX_EUR = 10_000                   # Vorgabe (Fixbetrag; entspricht ~1,7 %/a)
WP_OPEX_EUR  = 0.025 * WP_INVEST_EUR    # 2,5 %/a der Investition


# Quelle WP-OPEX: VDI 2067 (Wartungsanteil Waermepumpe 2,5 % der Investition,
# vgl. npro.energy/main/de/documentation/economic-parameters)

# --- Waermeseite ---
# Das gelieferte WP-Profil summiert sich auf 500.000 kWh Waerme/a, der
# Gasverbrauch (1.140.000 kWh/a) entspricht aber ~1.026.000 kWh Waerme.
# Vorgabe Kunde: WP ersetzt die komplette Gasheizung -> Profil (Heizlast UND
# WP-Strombedarf) wird formtreu auf die Zielwaerme skaliert, COP unveraendert.
WP_AUF_GASVERBRAUCH_SKALIEREN = True

KESSEL_NUTZUNGSGRAD = 0.90
# Quelle: Richtwerte Jahresnutzungsgrad Gas-Brennwertkessel 89-96 %
# (SHKwissen/haustechnikdialog.de "Wirkungs- und Nutzungsgrad einer
# Heizungsanlage"). Bestands-Gaskessel ohne Brennwert: ~77 %.
# -> Bei bekanntem Kesseltyp des Kunden anpassen!

# --- Windprofil ---
# Verwendet wird das anlagenspezifisch simulierte Profil aus
# wea_profilsimulation.py (ENERCON E-82, 2.000 kW, Standort Nordhorn):
# reale SMARD-15-min-Profilform 2025 -> effektive Windgeschwindigkeit
# (v ~ cf^(1/3)) -> offizielle ENERCON-Leistungskennlinie, kalibriert auf
# WIND_VLH_ERWARTET Volllaststunden.
# Das Profil bildet bereits die KOMPLETTE Anlage ab -> keine weitere
# Skalierung mit WKA_NENN_MW im Einleseblock!
WIND_VLH_ERWARTET = 2400
# Quellen: ENERCON/TUEV Rheinland, E-82 E2 typischer Binnenlandstandort
# ~5.100 MWh/a (= ~2.400 VLh); LEE Niedersachsen, Wertschoepfungsstudie
# Emsland/Osnabrueck/Grafschaft Bentheim 2024: generischer Windpark mit
# modernen Anlagen 2.983 VLh (Obergrenze der Region).
# Bruttoertrag ohne Verfuegbarkeits-, Abschalt- und Parkverluste.
# -> Durch Ertragsgutachten bzw. SCADA-/EEG-Daten der Kaufanlage ersetzen!

INTERVALLE_ERWARTET = 35_040  # 365 Tage x 96 Viertelstunden
WARNUNGEN = []

# =============================================================================
# IMPORT & HARMONIZE DATA
# =============================================================================
# TODO: Implement functions to load and harmonize data from input files
def warn(text):
    WARNUNGEN.append(text)
    print(f"  !! WARNUNG: {text}")

def kopf(text):
    print("\n" + "=" * 68 + f"\n{text}\n" + "=" * 68)

def pruefe_reihe(name, df, energie_spalten):
    """Standard-Validierung je Zeitreihe nach dem Einlesen."""
    n = len(df)
    print(f"  Zeilen: {n:,} (erwartet ~{INTERVALLE_ERWARTET:,})")
    print(f"  Zeitraum: {df['Zeitstempel'].min()}  bis  {df['Zeitstempel'].max()}")
    dup = df["Zeitstempel"].duplicated().sum()
    if dup:
        print(f"  Doppelte Zeitstempel: {dup} (Zeitumstellung Okt.) -> werden aggregiert")
    for sp in energie_spalten:
        nan = df[sp].isna().sum()
        print(f"  {sp}: Summe {df[sp].sum():,.0f} kWh | NaN: {nan}")
        if nan > 0:
            warn(f"{name}: {nan} fehlende Werte in {sp}")
    if abs(n - INTERVALLE_ERWARTET) > 10:
        warn(f"{name}: Zeilenzahl {n:,} weicht deutlich von {INTERVALLE_ERWARTET:,} ab")

def dedupliziere(df, summen_spalten, mittel_spalten=()):
    """Zeitumstellungs-Duplikate: Energie summieren, Zustandsgroessen mitteln."""
    agg = {s: "sum" for s in summen_spalten}
    agg.update({s: "mean" for s in mittel_spalten})
    return df.groupby("Zeitstempel", as_index=False).agg(agg)

# --- Preis-Plausibilitaet ---
kopf("0. PREISPARAMETER")
print(f"  Referenzsystem (Vollversorgung): {NETZSTROMPREIS_REF_CT} ct/kWh")
print(f"  Neues System (Reststrombezug):   {NETZSTROMPREIS_NEU_CT} ct/kWh "
      f"({NETZSTROMPREIS_NEU_CT - NETZSTROMPREIS_REF_CT:+.3f} ct)")
print(f"  Wind-EV (Arbeitspreis o. NNE):   {STROMPREIS_CT} ct/kWh")
_impliziert = NETZSTROMPREIS_NEU_CT - NETZENTGELT_CT
if abs(STROMPREIS_CT - _impliziert) > 0.001:
    warn(f"STROMPREIS_CT ({STROMPREIS_CT} ct) passt nicht zum neuen Reststrompreis: "
         f"{NETZSTROMPREIS_NEU_CT} - {NETZENTGELT_CT} = {_impliziert:.3f} ct. "
         f"Der Wind-Eigenverbrauch wird damit um {(_impliziert-STROMPREIS_CT):.3f} "
         f"ct/kWh konservativ bewertet. Konsistente Ableitung ueber "
         f"STROMPREIS_ABLEITEN = True aktivierbar.")

kopf("2a. LASTGANG (Strom, 15 min)")
raw = pd.read_excel(FILE_LASTGANG, sheet_name=LASTGANG_SHEET, header=None)
last = raw.iloc[7:, [0, 1, LASTGANG_SPALTE]].copy()
last.columns = ["Datum", "Uhrzeit", "Last_kW"]
# Datum ist echtes Datum je Zeile, Uhrzeit = Intervall-Ende (00:15 ... 00:00 Folgetag)
last["Zeitstempel"] = pd.to_datetime(last["Datum"]) + pd.to_timedelta(
    last["Uhrzeit"].astype(str))
last["Unternehmenslast_kWh"] = pd.to_numeric(last["Last_kW"], errors="coerce") * 0.25
last = last[["Zeitstempel", "Unternehmenslast_kWh"]].dropna(subset=["Zeitstempel"])
# Kontrolle: beide Kandidatenspalten ausweisen
s2 = pd.to_numeric(raw.iloc[7:, 2], errors="coerce").sum() * 0.25
s3 = pd.to_numeric(raw.iloc[7:, 3], errors="coerce").sum() * 0.25
print(f"  Spalte 2 ('Unternehmen W' lt. Kopfzeile): {s2:,.0f} kWh/a")
print(f"  Spalte 3 (verwendet, wie Vorgaengermodell): {s3:,.0f} kWh/a")
print(f"  -> Spalte {LASTGANG_SPALTE} verwendet (Kundenbestaetigung 07.09.2026)")
pruefe_reihe("Lastgang", last, ["Unternehmenslast_kWh"])
last = dedupliziere(last, ["Unternehmenslast_kWh"])

kopf("2b. WAERMEPUMPE (Heizlast, COP, Strombedarf)")
try:
    wp = pd.read_excel(FILE_WP)
    wp["Zeitstempel"] = pd.to_datetime(wp["Zeitstempel"])
    wp_quelle = FILE_WP
except FileNotFoundError:
    wp = pd.read_excel(FILE_WP_FALLBACK, sheet_name="Zeitreihe",
                       usecols=["Zeitstempel", "Temperatur_C", "COP",
                                "Heizlast_kWh", "Strombedarf_WP_kWh"])
    wp = wp.drop_duplicates()  # Kreuzprodukt-Duplikate des alten Merges entfernen
    wp_quelle = FILE_WP_FALLBACK + " (Blatt 'Zeitreihe')"
    warn("WP-Originaldatei data_table.xlsx nicht gefunden -> WP-Daten aus alter "
         "Bilanzdatei rekonstruiert. Fuer den Endstand Originaldatei verwenden.")
print(f"  Quelle: {wp_quelle}")
for sp in ["Heizlast_kWh", "Strombedarf_WP_kWh", "COP", "Temperatur_C"]:
    wp[sp] = pd.to_numeric(wp[sp], errors="coerce")
wp = wp.dropna(subset=["Zeitstempel", "Heizlast_kWh", "Strombedarf_WP_kWh"])
pruefe_reihe("WP", wp, ["Heizlast_kWh", "Strombedarf_WP_kWh"])
print(f"  COP min/Mittel/max: {wp['COP'].min():.2f} / {wp['COP'].mean():.2f} / "
      f"{wp['COP'].max():.2f} | JAZ (Heizlast/Strom): "
      f"{wp['Heizlast_kWh'].sum()/wp['Strombedarf_WP_kWh'].sum():.2f}")
wp = dedupliziere(wp, ["Heizlast_kWh", "Strombedarf_WP_kWh"],
                  ["COP", "Temperatur_C"])
if WP_AUF_GASVERBRAUCH_SKALIEREN:
    waerme_ziel = GASVERBRAUCH_IST_KWH * KESSEL_NUTZUNGSGRAD
    wp_faktor = waerme_ziel / wp["Heizlast_kWh"].sum()
    wp["Heizlast_kWh"] *= wp_faktor
    wp["Strombedarf_WP_kWh"] *= wp_faktor
    print(f"  WP-Profil skaliert: Faktor {wp_faktor:.3f} -> Waerme "
          f"{wp['Heizlast_kWh'].sum():,.0f} kWh/a "
          f"(= {GASVERBRAUCH_IST_KWH:,.0f} kWh Gas x eta {KESSEL_NUTZUNGSGRAD:.0%})")
    warn(f"WP-Profil formtreu um Faktor {wp_faktor:.2f} hochskaliert, damit die "
         f"WP den kompletten Gasverbrauch ersetzt (Kundenvorgabe). Achtung: "
         f"WP-Angebot (600 T EUR) und COP-Kennlinie muessen zur ~doppelten "
         f"thermischen Leistung passen -> mit Anbieter verifizieren!")

kopf("2c. PV-PROFIL 500 kWp")
pv = pd.read_excel(FILE_PV, header=None).iloc[10:, [0, 2]].copy()
pv.columns = ["Zeitstempel", "PV1_kWh"]
# Deutsche Textzeitstempel -> explizites Format (Kernfehler des Altskripts!)
pv["Zeitstempel"] = pd.to_datetime(pv["Zeitstempel"],
                                   format="%d.%m.%Y %H:%M:%S", errors="coerce")
pv["PV1_kWh"] = pd.to_numeric(pv["PV1_kWh"], errors="coerce")
n_vor = len(pv)
pv = pv.dropna()
if n_vor - len(pv) > 10:
    warn(f"PV: {n_vor - len(pv)} Zeilen beim Parsen verloren")
pruefe_reihe("PV", pv, ["PV1_kWh"])
pv = dedupliziere(pv, ["PV1_kWh"])
pv1_spez_roh = pv["PV1_kWh"].sum() / PV1_PEAK_KWP
print(f"  Spezifischer Ertrag PV1 unverschattet: {pv1_spez_roh:,.0f} kWh/kWp "
      f"(Plausibilitaet DE: ~900-1.100)")
if not 800 <= pv1_spez_roh <= 1200:
    warn(f"PV: spezifischer Ertrag {pv1_spez_roh:,.0f} kWh/kWp ausserhalb 800-1200")

# --- Verschattung durch Huegel: betroffene Monate auf 0 setzen ---
pv1_spez = pv1_spez_roh
if PV_VERSCHATTUNG_MONATE:
    monatsnamen = {1: "Jan", 2: "Feb", 3: "Mrz", 4: "Apr", 5: "Mai", 6: "Jun",
                   7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez"}
    namen = ", ".join(monatsnamen[m] for m in PV_VERSCHATTUNG_MONATE)
    maske = pv["Zeitstempel"].dt.month.isin(PV_VERSCHATTUNG_MONATE)
    verlust = pv.loc[maske, "PV1_kWh"].sum()
    pv.loc[maske, "PV1_kWh"] = 0.0
    pv1_spez = pv["PV1_kWh"].sum() / PV1_PEAK_KWP
    anteil = verlust / (pv1_spez_roh * PV1_PEAK_KWP) * 100
    print(f"  Verschattung ({namen}): PV1 -{verlust:,.0f} kWh/a "
          f"(-{anteil:.1f} %) -> {pv1_spez:,.0f} kWh/kWp")
    warn(f"PV-Erzeugung in {namen} vollstaendig auf 0 gesetzt (Verschattung durch "
         f"Huegel, Kundenangabe). Betrifft PV1 UND PV2 (Carport). Ertragsverlust "
         f"PV1 {verlust:,.0f} kWh/a (-{anteil:.1f} %), PV2 anteilig. Empfehlung: "
         f"Verschattung durch Horizontvermessung bzw. Verschattungssimulation "
         f"(PVsol o. ae.) belegen -- eine Voll-Nullsetzung ist die konservative "
         f"Obergrenze, real bleibt meist Diffusstrahlung nutzbar. Pruefen, ob "
         f"der Carport (andere Hoehe/Ausrichtung) gleich stark betroffen ist.")

kopf("2d. WINDPROFIL (ENERCON E-82, 2 MW, Nordhorn – simuliert)")
wind = pd.read_excel(FILE_WIND, sheet_name="Profil")
wind["Zeitstempel"] = pd.to_datetime(wind["Zeitstempel"])
wind["Wind_kWh"] = pd.to_numeric(wind["Wind_kWh"], errors="coerce")
wind = wind[["Zeitstempel", "Wind_kWh"]].dropna()
wind = dedupliziere(wind, ["Wind_kWh"])
vlh_ist = wind["Wind_kWh"].sum() / (WKA_NENN_MW * 1000)
print(f"  Jahresertrag: {wind['Wind_kWh'].sum():,.0f} kWh "
      f"({wind['Wind_kWh'].sum()/1e6:.2f} GWh) | Volllaststunden: {vlh_ist:,.0f} h/a")
print(f"  Max. Leistung: {wind['Wind_kWh'].max()/0.25:,.0f} kW "
      f"(Nennleistung {WKA_NENN_MW*1000:,.0f} kW)")
if abs(vlh_ist - WIND_VLH_ERWARTET) > 50:
    warn(f"Windprofil liefert {vlh_ist:,.0f} VLh, erwartet {WIND_VLH_ERWARTET} "
         f"-> Kalibrierung in wea_profilsimulation.py pruefen")
warn("Windprofil ist SIMULIERT (ENERCON-Kennlinie auf SMARD-Profilform, "
     "kalibriert auf ~2.400 VLh Binnenland). Bruttoertrag ohne Verfuegbarkeits-, "
     "Abschalt- und Parkverluste; Einzelanlagen-Volatilitaet durch die regionale "
     "Profilform gedaempft. Vor Kaufentscheidung durch Ertragsgutachten bzw. "
     "SCADA-/EEG-Produktionsdaten der Anlage ersetzen!")
pruefe_reihe("Wind", wind, ["Wind_kWh"])
# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================
# TODO: Implement the calculation functions as needed for the project
kopf("3. ZUSAMMENFUEHRUNG (inner join auf Zeitstempel)")
df = (last.merge(wp, on="Zeitstempel", how="inner")
          .merge(pv, on="Zeitstempel", how="inner")
          .merge(wind[["Zeitstempel", "Wind_kWh"]], on="Zeitstempel", how="inner")
          .sort_values("Zeitstempel").reset_index(drop=True))
print(f"  Gemeinsame Intervalle: {len(df):,}")
for name, quelle in [("Lastgang", last), ("WP", wp), ("PV", pv), ("Wind", wind)]:
    verloren = len(quelle) - len(df)
    if verloren > 20:
        warn(f"Merge: {verloren} Intervalle aus {name} ohne Gegenstueck")
if len(df) < INTERVALLE_ERWARTET - 50:
    warn(f"Nur {len(df):,} gemeinsame Intervalle -> Jahreswerte anteilig zu klein")

# PV2 = Carport, gleiche Profilform wie PV1 (inkl. Verschattung), skaliert
# ueber das kWp-Verhaeltnis
df["PV2_kWh"] = df["PV1_kWh"] * (PV2_PEAK_KWP / PV1_PEAK_KWP)
df["Gesamtstrombedarf_kWh"] = df["Unternehmenslast_kWh"] + df["Strombedarf_WP_kWh"]

def decke(erzeugung, restlast):
    ev = np.minimum(erzeugung, restlast)
    return ev, erzeugung - ev, restlast - ev

df["PV1_EV_kWh"],  df["PV1_Einsp_kWh"],  rest = decke(df["PV1_kWh"],
                                                      df["Gesamtstrombedarf_kWh"])
df["PV2_EV_kWh"],  df["PV2_Einsp_kWh"],  rest = decke(df["PV2_kWh"], rest)
df["Wind_EV_kWh"], df["Wind_Einsp_kWh"], df["Netzbezug_kWh"] = decke(
    df["Wind_kWh"], rest)

# WP-Strommix: anteilige Zuordnung nach Lastanteil im Intervall
wp_anteil = np.where(df["Gesamtstrombedarf_kWh"] > 0,
                     df["Strombedarf_WP_kWh"] / df["Gesamtstrombedarf_kWh"], 0)
for q in ["PV1_EV", "PV2_EV", "Wind_EV", "Netzbezug"]:
    df[f"WP_{q}_kWh"] = df[f"{q}_kWh"] * wp_anteil

kopf("4. ENERGIEBILANZ-CHECK")
erz  = df[["PV1_kWh", "PV2_kWh", "Wind_kWh"]].sum().sum()
einsp = df[["PV1_Einsp_kWh", "PV2_Einsp_kWh", "Wind_Einsp_kWh"]].sum().sum()
netz = df["Netzbezug_kWh"].sum()
verbrauch = df["Gesamtstrombedarf_kWh"].sum()
fehler = erz + netz - verbrauch - einsp

print(f"  Erzeugung {erz:,.0f} + Netzbezug {netz:,.0f} "
      f"- Verbrauch {verbrauch:,.0f} - Einspeisung {einsp:,.0f} "
      f"= {fehler:,.6f} kWh")
assert abs(fehler) < 1, "Energiebilanz verletzt!"

print("  Bilanz geschlossen (Fehler < 1 kWh). OK")

# Waermeseite: Konsistenz Heizlast vs. Gasverbrauch
waerme = df["Heizlast_kWh"].sum()
gas_fuer_waerme = waerme / KESSEL_NUTZUNGSGRAD
print(f"\n  Waermelieferung WP-Profil:      {waerme:,.0f} kWh/a")
print(f"  Gasbedarf dafuer (eta={KESSEL_NUTZUNGSGRAD:.0%}): "
      f"{gas_fuer_waerme:,.0f} kWh/a")
print(f"  Gasverbrauch lt. Kunde:         {GASVERBRAUCH_IST_KWH:,.0f} kWh/a")
if gas_fuer_waerme < 0.7 * GASVERBRAUCH_IST_KWH:
    warn(f"Waerme-Diskrepanz: WP-Profil deckt nur {waerme:,.0f} kWh Waerme "
         f"(~{gas_fuer_waerme:,.0f} kWh Gas), Kunde verbraucht "
         f"{GASVERBRAUCH_IST_KWH:,.0f} kWh Gas. Die WP ersetzt damit NICHT die "
         f"komplette Gasheizung -> Gasersparnis wird nur fuer die gelieferte "
         f"Waerme angesetzt. Klaeren: deckt das Heizlastprofil den ganzen "
         f"Bedarf, oder enthaelt der Gasverbrauch weitere Verbraucher?")

kopf("5. WIRTSCHAFTLICHKEIT")
ct = 1 / 100  # ct -> EUR

sums = df.sum(numeric_only=True)
pv1_ev, pv1_ei = sums["PV1_EV_kWh"], sums["PV1_Einsp_kWh"]
pv2_ev, pv2_ei = sums["PV2_EV_kWh"], sums["PV2_Einsp_kWh"]
w_ev,  w_ei    = sums["Wind_EV_kWh"], sums["Wind_Einsp_kWh"]
# Eigenverbrauchsersparnis:
# selbst erzeugter und direkt selbst verbrauchter Strom × Referenzpreis
eigenverbrauch_kwh = pv1_ev + pv2_ev + w_ev
eigenverbrauchsersparnis = (
    eigenverbrauch_kwh * NETZSTROMPREIS_REF_CT * ct
)

print(f"  Eigenverbrauch: {eigenverbrauch_kwh:,.0f} kWh/a")
print(f"  Eigenverbrauchsersparnis zum Referenzpreis "
      f"({NETZSTROMPREIS_REF_CT:.3f} ct/kWh): "
      f"{eigenverbrauchsersparnis:,.0f} EUR/a")
last_a         = sums["Unternehmenslast_kWh"]
wp_strom       = sums["Strombedarf_WP_kWh"]

# --- Referenzfall: Gaskessel + kompletter Strombezug aus dem Netz (OHNE WP!) ---
# Preis: Bestandsvertrag Vollversorgung
kosten_strom_ref = last_a * NETZSTROMPREIS_REF_CT * ct
kosten_gas_ref   = gas_fuer_waerme * GASPREIS_CT * ct   # nur ersetzte Waerme
kosten_ref = kosten_strom_ref + kosten_gas_ref

# --- Neues System: Reststrombezug zum hoeheren Preis ---
kosten_netz  = netz * NETZSTROMPREIS_NEU_CT * ct
kosten_es    = w_ev * NETZENTGELT_CT * ct          # ES-Wind zahlt Netzentgelt
erloes_einsp = (pv1_ei + pv2_ei) * PV_EINSPEISE_CT * ct + w_ei * WIND_EINSPEISE_CT * ct
opex_gesamt  = PV1_OPEX_EUR + PV2_OPEX_EUR + WKA_OPEX_EUR + WP_OPEX_EUR
kosten_neu   = kosten_netz + kosten_es - erloes_einsp + opex_gesamt

gesamteinsparung = kosten_ref - kosten_neu
invest_gesamt = PV1_INVEST_EUR + PV2_INVEST_EUR + WKA_INVEST_EUR + WP_INVEST_EUR
amort_gesamt = invest_gesamt / gesamteinsparung if gesamteinsparung > 0 else np.inf

print(f"  Referenz  : Strom {kosten_strom_ref:,.0f} ({NETZSTROMPREIS_REF_CT} ct) "
      f"+ Gas {kosten_gas_ref:,.0f} = {kosten_ref:,.0f} EUR/a")
print(f"  Neu       : Netz {kosten_netz:,.0f} ({NETZSTROMPREIS_NEU_CT} ct) "
      f"+ ES-Netzentgelt {kosten_es:,.0f} "
      f"- Einspeiseerloese {erloes_einsp:,.0f} + OPEX {opex_gesamt:,.0f} "
      f"= {kosten_neu:,.0f} EUR/a")
print(f"  Einsparung: {gesamteinsparung:,.0f} EUR/a "
      f"({gesamteinsparung/kosten_ref*100:.1f} % der Referenz)")
print(f"  Investition gesamt: {invest_gesamt:,.0f} EUR "
      f"-> statische Amortisation {amort_gesamt:.1f} a")

# --- Vorteil je Massnahme (Merit-Order-Zuordnung, inkl. OPEX) ---
# PV-EV vermeidet Reststrombezug im NEUEN System -> Bewertung mit
# NETZSTROMPREIS_NEU_CT. Wind-EV vermeidet Reststrombezug, zahlt aber weiter
# Netzentgelt -> Bewertung mit STROMPREIS_CT.
def massnahme(name, ev, ei, ev_ct, ei_ct, invest, opex):
    brutto = ev * ev_ct * ct + ei * ei_ct * ct
    netto = brutto - opex
    return dict(Massnahme=name, EV_kWh=ev, Einspeisung_kWh=ei,
                Vorteil_brutto_EUR=brutto, OPEX_EUR=opex,
                Vorteil_netto_EUR=netto, Invest_EUR=invest,
                Amortisation_a=invest / netto if netto > 0 else np.inf)

# WP: Gasersparnis minus Stromkosten. Zwei Sichten:
#   konservativ = gesamter WP-Strom zum Reststrompreis
#   systemisch  = WP-Strom zum tatsaechlichen Mix (EE-Anteile guenstiger)
wp_gasersparnis = kosten_gas_ref
wp_strom_netzpreis = wp_strom * NETZSTROMPREIS_NEU_CT * ct
wp_strom_mix = (sums["WP_Netzbezug_kWh"] * NETZSTROMPREIS_NEU_CT
                + sums["WP_Wind_EV_kWh"] * NETZENTGELT_CT
                + (sums["WP_PV1_EV_kWh"] + sums["WP_PV2_EV_kWh"]) * 0) * ct
# (PV-Strom fuer die WP kostet nichts; entgangene Einspeiseverguetung wird den
#  PV-/Wind-Massnahmen nicht abgezogen, da EV dort bereits bewertet ist ->
#  keine Doppelzaehlung: die WP-Massnahme wird konservativ separat gerechnet)

wp_netto_kons = wp_gasersparnis - wp_strom_netzpreis - WP_OPEX_EUR
wp_netto_sys  = wp_gasersparnis - wp_strom_mix - WP_OPEX_EUR

tab = pd.DataFrame([
    massnahme("PV1 500 kWp", pv1_ev, pv1_ei, NETZSTROMPREIS_NEU_CT,
              PV_EINSPEISE_CT, PV1_INVEST_EUR, PV1_OPEX_EUR),
    massnahme("PV2 336 kWp Carport", pv2_ev, pv2_ei, NETZSTROMPREIS_NEU_CT,
              PV_EINSPEISE_CT, PV2_INVEST_EUR, PV2_OPEX_EUR),
    massnahme("WKA 2 MW (ES)", w_ev, w_ei, STROMPREIS_CT, WIND_EINSPEISE_CT,
              WKA_INVEST_EUR, WKA_OPEX_EUR),
    dict(Massnahme="WP (konservativ: Strom zum Reststrompreis)", EV_kWh=np.nan,
         Einspeisung_kWh=np.nan, Vorteil_brutto_EUR=wp_gasersparnis - wp_strom_netzpreis,
         OPEX_EUR=WP_OPEX_EUR, Vorteil_netto_EUR=wp_netto_kons,
         Invest_EUR=WP_INVEST_EUR,
         Amortisation_a=WP_INVEST_EUR / wp_netto_kons if wp_netto_kons > 0 else np.inf),
    dict(Massnahme="WP (systemisch: Strom zum Ist-Mix)", EV_kWh=np.nan,
         Einspeisung_kWh=np.nan, Vorteil_brutto_EUR=wp_gasersparnis - wp_strom_mix,
         OPEX_EUR=WP_OPEX_EUR, Vorteil_netto_EUR=wp_netto_sys,
         Invest_EUR=WP_INVEST_EUR,
         Amortisation_a=WP_INVEST_EUR / wp_netto_sys if wp_netto_sys > 0 else np.inf),
])
print("\n  VORTEIL JE MASSNAHME (inkl. OPEX):")
print(tab.to_string(index=False,
      formatters={c: (lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
                  for c in tab.columns if c not in ("Massnahme", "Amortisation_a")}
      | {"Amortisation_a": lambda x: f"{x:.1f}"}))

# --- Kennzahlen ---
autarkie = (pv1_ev + pv2_ev + w_ev) / verbrauch * 100
ev_quote = (pv1_ev + pv2_ev + w_ev) / erz * 100
print(f"\n  Autarkiegrad: {autarkie:.1f} % | EV-Quote der Erzeugung: {ev_quote:.1f} %")
for n, e, ev in [("PV1", sums["PV1_kWh"], pv1_ev), ("PV2", sums["PV2_kWh"], pv2_ev),
                 ("Wind", sums["Wind_kWh"], w_ev)]:
    print(f"  {n}: Erzeugung {e:,.0f} kWh | EV-Quote {ev/e*100:.1f} % "
          f"| Einspeisequote {(e-ev)/e*100:.1f} %")
print(f"  Max. Netzbezug: {df['Netzbezug_kWh'].max()/0.25:,.0f} kW | "
      f"Max. Einspeisung: "
      f"{(df[['PV1_Einsp_kWh','PV2_Einsp_kWh','Wind_Einsp_kWh']].sum(axis=1).max())/0.25:,.0f} kW")

kopf("6. SENSITIVITAETEN")

def rechne_gesamt(preis_faktor=1.0, wind_vlh=WIND_VLH_ERWARTET):
    """Gesamtsystem-Einsparung fuer skaliertes Preisniveau / Wind-Ertrag.

    preis_faktor skaliert BEIDE Netzstrompreise (Referenz und Reststrom) sowie
    den Arbeitspreis der Wind-EV-Bewertung -- ein Preisszenario betrifft Alt-
    und Neusystem gleichermassen.
    """
    p_ref = NETZSTROMPREIS_REF_CT * preis_faktor
    p_neu = NETZSTROMPREIS_NEU_CT * preis_faktor
    f = wind_vlh / WIND_VLH_ERWARTET
    wk = df["Wind_kWh"] * f
    r = (df["Gesamtstrombedarf_kWh"] - df["PV1_EV_kWh"] - df["PV2_EV_kWh"]).clip(lower=0)
    wev = np.minimum(wk, r); wei = wk - wev; nb = r - wev
    ref = last_a * p_ref * ct + kosten_gas_ref
    neu = (nb.sum() * p_neu * ct + wev.sum() * NETZENTGELT_CT * ct
           - (pv1_ei + pv2_ei) * PV_EINSPEISE_CT * ct
           - wei.sum() * WIND_EINSPEISE_CT * ct + opex_gesamt)
    return ref - neu

sens_preis = pd.DataFrame([
    {"Preisfaktor": f,
     "Netzstrom_Ref_ct": NETZSTROMPREIS_REF_CT * f,
     "Netzstrom_Neu_ct": NETZSTROMPREIS_NEU_CT * f,
     "Einsparung_EUR": rechne_gesamt(preis_faktor=f),
     "Amortisation_a": invest_gesamt / rechne_gesamt(preis_faktor=f)}
    for f in (0.8, 0.9, 1.0, 1.1, 1.2)])
sens_vlh = pd.DataFrame([
    {"Wind_VLh": v, "Einsparung_EUR": rechne_gesamt(wind_vlh=v),
     "Amortisation_a": invest_gesamt / rechne_gesamt(wind_vlh=v)}
    for v in (1800, 2100, 2400, 2700, 3000)])
print("Preisniveau +-20 % (beide Netzstrompreise skaliert):")
print(sens_preis.round(2).to_string(index=False))
print("\n  Wind-Volllaststunden 1.800-3.000 h:")
print(sens_vlh.round(1).to_string(index=False))

# =============================================================================
# REPORT
# =============================================================================
# Optionally, you can implement a function to print or generate a report based on the results of the calculations.

# Not necessary here


# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================
def calc_results() -> dict:
    """Bereitet alle für die Plotly-Charts benötigten Datensätze auf."""

    basis = df.copy()
    basis["Monat"] = basis["Zeitstempel"].dt.month

    # Monatswerte für V1, E1 und E2
    monatlich = basis.groupby("Monat").agg(
        Last_MWh=("Unternehmenslast_kWh", lambda x: x.sum() / 1000),
        WP_MWh=("Strombedarf_WP_kWh", lambda x: x.sum() / 1000),
        Heizlast_MWh=("Heizlast_kWh", lambda x: x.sum() / 1000),
        PV1_MWh=("PV1_kWh", lambda x: x.sum() / 1000),
        PV2_MWh=("PV2_kWh", lambda x: x.sum() / 1000),
        Wind_MWh=("Wind_kWh", lambda x: x.sum() / 1000),
        PV1_EV_MWh=("PV1_EV_kWh", lambda x: x.sum() / 1000),
        PV2_EV_MWh=("PV2_EV_kWh", lambda x: x.sum() / 1000),
        Wind_EV_MWh=("Wind_EV_kWh", lambda x: x.sum() / 1000),
        Netz_MWh=("Netzbezug_kWh", lambda x: x.sum() / 1000),
    ).reset_index()
    monatlich["Netzbezug_+_wind"] = monatlich["Netz_MWh"] + monatlich["Wind_EV_MWh"]
    monatlich["Deckungsgrad_%"] = (
        monatlich[["PV1_EV_MWh", "PV2_EV_MWh", "Wind_EV_MWh"]].sum(axis=1)
        / (monatlich["Last_MWh"] + monatlich["WP_MWh"])
        * 100
    )

    monatlich["Monat_Name"] = monatlich["Monat"].map({
        1: "Jan",
        2: "Feb",
        3: "Mrz",
        4: "Apr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Okt",
        11: "Nov",
        12: "Dez",
    })

    # Monatlicher wirtschaftlicher Vorteil
    basis["PV1_EV_EUR"] = basis["PV1_EV_kWh"] * NETZSTROMPREIS_NEU_CT * ct
    basis["PV1_Einsp_EUR"] = basis["PV1_Einsp_kWh"] * PV_EINSPEISE_CT * ct
    basis["PV2_EV_EUR"] = basis["PV2_EV_kWh"] * NETZSTROMPREIS_NEU_CT * ct
    basis["PV2_Einsp_EUR"] = basis["PV2_Einsp_kWh"] * PV_EINSPEISE_CT * ct
    basis["Wind_EV_EUR"] = basis["Wind_EV_kWh"] * STROMPREIS_CT * ct
    basis["Wind_Einsp_EUR"] = basis["Wind_Einsp_kWh"] * WIND_EINSPEISE_CT * ct

    mon_euro = basis.groupby("Monat")[
        [
            "PV1_EV_EUR",
            "PV1_Einsp_EUR",
            "PV2_EV_EUR",
            "PV2_Einsp_EUR",
            "Wind_EV_EUR",
            "Wind_Einsp_EUR",
        ]
    ].sum().reset_index()

    # Lastgang
    lastgang = basis[
        [
            "Zeitstempel",
            "Unternehmenslast_kWh",
            "Strombedarf_WP_kWh",
            "Gesamtstrombedarf_kWh",
        ]
    ].copy()

    lastgang["Alter_Lastgang_kW"] = (
        lastgang["Unternehmenslast_kWh"] / 0.25
    )
    lastgang["Neuer_Lastgang_kW"] = (
        lastgang["Gesamtstrombedarf_kWh"] / 0.25
    )

    # Dauerlinien
    erzeugung_kw = (
        basis[["PV1_kWh", "PV2_kWh", "Wind_kWh"]]
        .sum(axis=1)
        .div(0.25)
        .sort_values(ascending=False)
        .reset_index(drop=True)
    )

    gesamtlast_kw = (
        basis["Gesamtstrombedarf_kWh"]
        .div(0.25)
        .sort_values(ascending=False)
        .reset_index(drop=True)
    )

    netzbezug_kw = (
        basis["Netzbezug_kWh"]
        .div(0.25)
        .sort_values(ascending=False)
        .reset_index(drop=True)
    )

    einspeisung_kw = (
        basis[["PV1_Einsp_kWh", "PV2_Einsp_kWh", "Wind_Einsp_kWh"]]
        .sum(axis=1)
        .div(0.25)
        .sort_values(ascending=False)
        .reset_index(drop=True)
    )

    alter_lastgang_kw = (
        basis["Unternehmenslast_kWh"]
        .div(0.25)
        .sort_values(ascending=False)
        .reset_index(drop=True)
    )

    neuer_lastgang_kw = (
        basis["Gesamtstrombedarf_kWh"]
        .div(0.25)
        .sort_values(ascending=False)
        .reset_index(drop=True)
    )

    dauerlinie = pd.DataFrame({
        "Intervall": range(len(basis)),
        "Erzeugung_kW": erzeugung_kw,
        "Gesamtlast_kW": gesamtlast_kw,
        "Netzbezug_kW": netzbezug_kw,
        "Einspeisung_kW": einspeisung_kw,
        "Alter_Lastgang_kW": alter_lastgang_kw,
        "Neuer_Lastgang_kW": neuer_lastgang_kw,
    })

    # Wochenansichten aus V2
    def wochenansicht(start):
        start = pd.Timestamp(start)
        ende = start + pd.Timedelta(days=7)
        woche = basis[
            (basis["Zeitstempel"] >= start)
            & (basis["Zeitstempel"] < ende)
        ].copy()

        return pd.DataFrame({
            "Zeitstempel": woche["Zeitstempel"],
            "Gesamtlast_kW": woche["Gesamtstrombedarf_kWh"] / 0.25,
            "PV1_kW": woche["PV1_kWh"] / 0.25,
            "PV2_kW": woche["PV2_kWh"] / 0.25,
            "Wind_kW": woche["Wind_kWh"] / 0.25,
        }).reset_index(drop=True)

    winterwoche = wochenansicht("2025-01-13")
    sommerwoche = wochenansicht("2025-06-16")

    # WP-Strommix
    wp_strommix = pd.DataFrame({
        "Quelle": ["PV1", "PV2", "Wind", "Netz"],
        "Energie_kWh": [
            sums["WP_PV1_EV_kWh"],
            sums["WP_PV2_EV_kWh"],
            sums["WP_Wind_EV_kWh"],
            sums["WP_Netzbezug_kWh"],
        ],
    })

    # Amortisation je Maßnahme
    amortisation = tab[
    ["Massnahme", "Amortisation_a"]
    ].copy()

    amortisation["Massnahme_kurz"] = [
        "PV1",
        "PV2",
        "WKA",
        "WP k.",
        "WP s.",
    ]
    amortisation = amortisation[
        amortisation["Amortisation_a"] < 100
    ].reset_index(drop=True)

    # Kumulierter Cashflow
    cashflow = pd.DataFrame({
        "Jahr": np.arange(0, 21),
    })
    cashflow["Cashflow_EUR"] = (
        cashflow["Jahr"] * gesamteinsparung - invest_gesamt
    )

    return {
        "zeitreihe": basis,
        "monatlich": monatlich,
        "mon_euro": mon_euro,
        "winterwoche": winterwoche,
        "sommerwoche": sommerwoche,
        "lastgang": lastgang,
        "dauerlinie": dauerlinie,
        "massnahmen": tab,
        "amortisation": amortisation,
        "wp_strommix": wp_strommix,
        "cashflow": cashflow,
        "sens_preis": sens_preis,
        "sens_vlh": sens_vlh,
    }