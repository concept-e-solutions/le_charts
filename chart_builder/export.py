
from pathlib import Path


def export_chart(fig, filename: str, output_dir: str, formats=None):
    if formats is None:
        formats = ["html"]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for fmt in formats:
        if fmt == "html":
            fig.write_html(out / f"{filename}.html", include_plotlyjs="directory")
        elif fmt == "png":
            fig.write_image(out / f"{filename}.png", scale=2)
        elif fmt == "svg":
            fig.write_image(out / f"{filename}.svg")
        elif fmt == "pdf":
            fig.write_image(out / f"{filename}.pdf")
        else:
            raise ValueError(f"Unsupported format: {fmt}")