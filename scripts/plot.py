print("Making plots")

import pathlib
import pandas as pd
import matplotlib.pyplot as plt

here = pathlib.Path(__file__).resolve().parent

marriage_coefficient_path = (
    here / "../regression_results" / "marriage_coefficient_results.csv"
)
style_path = here / "../styles" / "secularisation.mplstyle"

figure_path = (
    here / "../plot_graphics" / "time_dependent.pdf"
)

# Data prep

df = pd.read_csv(marriage_coefficient_path)
df = df.rename(
    columns={
        "civil_marriage_share_value": "value",
        "civil_marriage_share_se": "se",
    }
)

df["year"] = pd.to_numeric(df.election_date.str[:4], errors="coerce")
df["month"] = pd.to_numeric(df.election_date.str[5:7], errors="coerce")
df["year_cts"] = df["year"] + df["month"] / 12

# Plotting

plt.style.use(style_path)

FIGURE_WIDTH = 3.3
FIGURE_HEIGHT = 3


def ax_errorbar_black(ax, *args, **kwargs):    
    # kwargs.setdefault("ecolor", "black")  # error bars color
    kwargs.setdefault("elinewidth", 0.8)  # horizontal line width
    kwargs.setdefault("ls", "")  # no connecting line
    return ax.errorbar(*args, **kwargs)



tab20 = plt.get_cmap("tab20").colors

model_eb_colors = {
    "no_interactions": tab20[0],
    "both_interactions": tab20[2],
    "one_interaction": tab20[4],
    "split_fits": tab20[6],
}
model_colors = {
    "no_interactions": tab20[1],
    "both_interactions": tab20[3],
    "one_interaction": tab20[5],
    "split_fits": tab20[7],
}
model_labels = {
    "no_interactions":   "2FE",
    "both_interactions": "2FE, int: marriage \& income",
    "one_interaction":   "2FE, int: marriage",
    "split_fits":        "year-by-year OLS",
}

fig, (ax_no_int, ax_main) = plt.subplots(
    ncols=2,
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
    width_ratios=(1, 20),
    constrained_layout=True,
    sharey=True,
)

df_poland = df[df["country"] == "Poland"].copy()
df_poland.loc[df_poland["model_type"] == "no_interactions", "year_cts"] = 0

for model_type, g in df_poland.groupby("model_type"):
    target_ax = ax_no_int if model_type == "no_interactions" else ax_main

    ax_errorbar_black(
        target_ax,
        g["year_cts"],
        g["value"],
        yerr=g["se"],
        color=model_colors.get(model_type, "gray"),        
        label=model_labels.get(model_type, "---"),
        ecolor=model_eb_colors.get(model_type, "---"),
        markeredgecolor=model_eb_colors.get(model_type, "---"),
        marker="o",        
    )

ax_main.axhline(0, marker="", color="#ccc")
ax_no_int.axhline(0, marker="", color="#ccc")

ax_no_int.set_ylabel("civil marriage coefficient estimate")

ax_main.spines["left"].set_visible(False)
ax_main.tick_params(axis="y", left=False)
ax_no_int.spines["right"].set_visible(False)
ax_no_int.set_xticks([])

fig.legend(frameon=False)

plt.savefig(figure_path)

plt.show()
