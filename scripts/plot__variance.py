import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pathlib

here = pathlib.Path(__file__).resolve().parent
style_path = here / "../styles" / "secularisation.mplstyle"
base_path = here / "../combined_data/"
figure_path = here / "../plot_graphics" / "heterogeneity_trajectory.pdf"

# Mapping from filename stem to display name
title_map = [
    ("italy__marriages.csv", "Italy"),
    ("spain__marriages.csv", "Spain"),
    ("poland__marriages.csv", "Poland"),
]

tab20 = plt.get_cmap("tab20").colors
color_map = {
    "Italy": (tab20[0], tab20[0]),
    "Spain": (tab20[2], tab20[2]),
    "Poland": (tab20[4], tab20[4]),
}
marker_map = {
    "Italy": "v",
    "Spain": "s",
    "Poland": "o",
}

# PARAMETERS
years = range(2000, 2025)
cmap = plt.cm.cividis

plt.style.use(style_path)

FIGURE_WIDTH = 3.3
FIGURE_HEIGHT = 2
fig, ax = plt.subplots(
    ncols=1,
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
    constrained_layout=True,
    sharey=True,
)

for file_name, country_name in title_map:
    # Read CSV
    df = pd.read_csv(base_path / file_name)
    df = df[df["year"] > 1999]
    std_df = df.groupby("year")["civil_marriage_share"].std().reset_index()

    # std_df = (
    #     df.groupby("year")["civil_marriage_share"]
    #     .agg(lambda x: x.quantile(0.75) - x.quantile(0.25))
    #     .reset_index()
    # )

    ax.scatter(
        std_df["year"],
        std_df["civil_marriage_share"],
        label=country_name,
        color=color_map[country_name][1],
        edgecolors=color_map[country_name][0],
        marker=marker_map[country_name],
    )

ax.set_ylabel("std of civil marriage share")
ax.set_ylim(bottom=0)

plt.legend()

plt.savefig(figure_path)    

if __name__ == "__main__":
    plt.show()
