# main.py

import yaml
import pandas as pd

from calculations import calc_results

from chart_builder.factory import create_chart
from chart_builder.export import export_chart

if __name__ == "__main__":
    datasets = calc_results()
    print("Starting chart generation...")
    with open("config/charts.yml", encoding="utf-8") as f:
        charts = yaml.safe_load(f)["charts"]

    for cfg in charts:
        data = datasets[cfg["dataset"]]
        fig = create_chart(data, cfg)
        export_chart(fig=fig, filename=cfg["name"], output_dir="output")
    print("Chart generation completed.")