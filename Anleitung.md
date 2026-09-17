
# Diagramm-Tool für Energie- und Analyseberichte
Diese Anleitung beschreibt, wie das Tool Diagramme erstellen und exportieren kann.

## 1. Ziel
Mit diesem Tool können Diagramme über eine einfache Konfigurationsdatei erzeugt werden, statt für jedes Diagramm neuen Python-Code zu schreiben.

Die Berechnung der Daten bleibt im Python-Code. Die Diagramme selbst werden über die Datei charts.yml definiert.

## 2. Wichtige Dateien
- main.py – startet die Diagramm-Erzeugung
- charts.yml – enthält alle Diagrammdefinitionen
- factory.py – erzeugt die Diagramme
- style.py – definiert Farben und Layout
- export.py – exportiert die Diagramme
- output – Ordner mit den erzeugten Diagrammen

## 3. So wird ein Diagramm definiert
Alle Diagramme werden in charts.yml beschrieben.

Beispiel:
```
charts:
  - name: name_des_ersten_diagramms
    title: "Titel des Diagramms"
    x: "timestamp" # muss mit dem Namen der Spalte übereinstimmen, die die x-Achse darstellt
    x_title: "Titel der x-Achse"
    y_title: "Titel der y-Achse"
    dataset: part1 # muss mit den Namen des Datensatzes übereinstimmen, der in den Berechnungen erstellt wurde
 
    series:
      - column: spaltenname1 # muss mit dem Namen der Spalte übereinstimmen, die die Daten für diese Serie enthält
        label: "Label für die Serie"
        color: dark_blue # kann dark_blue, medium_blue, light_blue oder grid sein
        kind: area # kann area, line, scatter oder bar sein

      - column: spaltenname2
        label: "Label für die zweite Serie"
        color: medium_blue
        kind: area

      - column: spaltenname3
        label: "Label für die dritte Serie"
        color: light_blue
        kind: area

      - column: spaltenname4
        label: "Label für die vierte Serie"
        color: dark_blue
        kind: line
        line_width: 1 # optional, nur relevant für Linien-Diagramme, gibt die Breite der Linie an
```

## 4. Bedeutung der Felder
Allgemeine Diagrammparameter
- name: Name des Diagramms
- dataset: Datensatz, z. B. woche, monthly, annual (muss mit den Namen des Datensatzes übereinstimmen, der in den Berechnungen erstellt wurde)
- x: Spalte für die x-Achse (muss mit dem Namen der Spalte übereinstimmen, die die x-Achse darstellt)
- title: Diagrammtitel
- x_title: Beschriftung der x-Achse
- y_title: Beschriftung der y-Achse
- barmode: bei Balkendiagrammen, z. B. stack oder group
- Serien
- column: Spalte im Datensatz
- label: Bezeichnung in der Legende
- color: Farbe
- kind: Typ der Serie (line, area, bar)
- stackgroup: nur bei Flächendiagrammen
- line_width: nur bei Linien

## 5. Diagrammtypen
Linien-Diagramm
```
- column: last_W_kw
  label: "Last W"
  color: dark_blue
  kind: line
  line_width: 2
```
Flächendiagramm
```
- column: pv_sharing_kw
  label: "PV → Sharing R"
  color: dark_blue
  kind: area
  stackgroup: one
```
Balkendiagramm
```
- column: pv_selbst_W_month
  label: "PV Eigenverbrauch W"
  color: dark_blue
  kind: bar
  ```
Gestapelte Balken
```
barmode: stack
```

## 6. Diagramme erzeugen
Das Tool besteht aus zwei Teilen:

1. `config/charts.yml` beschreibt das Diagramm und die Serien.
2. `calculations.py` stellt die benötigten Datensätze und Spalten bereit.

In der charts.yml werden wie oben beschrieben die Diagramme definiert.
In der calculations.py werden alle Berechnungen durchgeführt. Es kann alles so gemacht werden wie man es möchte. Das Einzige was immer enthalten sein muss ist die `calc_results` Funktion. Diese soll die einzelnen Berechnungsschritte ausführen und und die notwendigen DataFrames oder Dictionaries zu einem dictionary zusammenpacken und zurückgeben. 

Wichtig: Die Bennenung der DataFrames im zurückgegebenen Dictionary MUSS mit der Bennenung des `datasets` in der chars.yml übereinstimmen.

Beispiel:
```python
def calc_results() -> dict:
    """Performs the calculations and returns the prepared data sets."""
    # This is a placeholder for the actual calculation logic. Implement the necessary steps to load data, perform calculations, and prepare the datasets.
    df = load_profile(BASE_DIR)
    df_1 = part_1(df)
    df_2 = part_2(df_1)
    
    datasets = {
        "part1": df_1,
        "part2": df_2
    }
    # Optionally, call the report function
    # print_report(res)
    return datasets
```
  
Im Projektordner ausführen:
```
python main.py
```

Das Tool liest dann automatisch die Konfiguration aus charts.yml und erzeugt alle dort definierten Diagramme.

## 7. Ausgabe
Die fertigen Diagramme werden im Ordner output gespeichert.

Beispiel:
```
output/
  plot_1_pv_verwendung.html
```

## 8. Neues Diagramm hinzufügen
Ein neues Diagramm wird einfach als weiterer Eintrag in charts.yml ergänzt.

Beispiel:
```
  - name: neues_diagramm
    dataset: woche
    x: timestamp
    title: "Neues Diagramm"
    x_title: "Zeit"
    y_title: "Leistung (kW)"
    series:
      - column: pv_selbst_W_kw
        label: "PV"
        color: pv
        kind: area
        stackgroup: one
```

Danach erneut:
```
python template.py
```

ausführen.

## 11. Beispiel für gestapelte Monatsbalken
```
charts:
  - name: monatsbilanz
    dataset: monthly
    x: month
    title: "Monatsbilanz"
    x_title: "Monat"
    y_title: "Energie (MWh)"
    barmode: stack
    series:
      - column: pv_selbst_W_month
        label: "PV Eigenverbrauch W"
        color: pv
        kind: bar

      - column: pv_sharing_month
        label: "PV-Sharing"
        color: primary
        kind: bar

      - column: wind_nutzung_month
        label: "Wind"
        color: secondary
        kind: bar

      - column: netz_gesamt_month
        label: "Netzbezug"
        color: gray
        kind: bar
```
