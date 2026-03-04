import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pathlib

here = pathlib.Path(__file__).resolve().parent
style_path = here / "../styles" / "secularisation.mplstyle"

base_path = here / "../combined_data/"

figure_path = here / "../plot_graphics" / "marriage_histograms.pdf"

# Mapping from filename stem to display name
title_map = [
    ("italy__marriages.csv", "Italy"),
    ("spain__marriages.csv", "Spain"),    
    ("poland__marriages.csv", "Poland"),
]

# PARAMETERS
years = range(2000, 2025)
offset_step = 5.0

cmap_rescale = 1.3
cmap = plt.cm.cividis

ignore_colormap = True
fixed_color = "#222"

plt.style.use(style_path)

# FIGURE WITH 3 SIDE-BY-SIDE PANELS
FIGURE_WIDTH = 7
FIGURE_HEIGHT = 3
fig, axes = plt.subplots(
    ncols=3,
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
    constrained_layout=True,
    sharey=True,
)

for ax, (file_name, country_name) in zip(axes, title_map):
    # Read CSV
    df = pd.read_csv(base_path / file_name)

    # Remove rows with missing or zero totals
    df = df[df["civil_marriage_share"] > 0]

    N = len(years)

    for i, year in enumerate(years):
        df_year = df[df["year"] == year]

        bw = 0.05
        bins = np.arange(0, 1 + bw, bw)
        counts, bin_edges = np.histogram(
            df_year["civil_marriage_share"], bins=bins, density=True
        )

        offset = i * offset_step
        color = cmap(i / (cmap_rescale*N - 1)) if N > 1 else cmap(0.5)
        if ignore_colormap:
            color = fixed_color

        x = bin_edges
        y = np.concatenate([[0], counts]) + offset
        y_ref = offset

        # STEP PLOT
        ax.step(
            x,
            y,
            where="pre",
            linewidth=0.8,
            color=color,
        )

        # FILL
        ax.fill_between(
            x,
            y_ref,
            y,
            step="pre",
            color=color,
            alpha=0.3,
        )

        if len(df_year) == 0:            
            ax.plot(
                [0, 1],
                [offset, offset],
                color="#ccc",
                alpha=1,
                zorder=-99,
            )

        # YEAR LABEL at x=0.9
        ax.text(
            0.9,
            offset + 0.4 * offset_step,
            f"{year}",
            va="center",
            ha="center",
            fontsize=6,
            color=color,
        )

    # AXIS CLEANUP
    if country_name == "Spain":
        ax.set_xlabel("Civil marriage share")
    ax.set_xlim([0, 1])

    ax.set_title(country_name)

    ax.set_yticks([])

# plt.tight_layout(rect=[0, 0, 1, 1])

plt.savefig(figure_path)

if __name__ == "__main__":
    plt.show()
