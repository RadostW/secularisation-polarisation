import pathlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

here = pathlib.Path(__file__).resolve().parent

style_path = here / "../styles" / "secularisation.mplstyle"

variances_path = here / "../combined_data" / "explained_variance_shares.csv"
correlations_path = here / "../combined_data" / "poland__ess_correlations.csv"

output_path = here / "../plot_graphics" / "variance_decomposition_poland.pdf"

variances = pd.read_csv(variances_path)
correlations = pd.read_csv(correlations_path)

plt.style.use(style_path)

FIGURE_WIDTH = 3.3
FIGURE_HEIGHT = 4.0
FONT_SIZE = 9
fig, (axupper, axlower) = plt.subplots(
    nrows=2,
    height_ratios=[2, 1],
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
    constrained_layout=True,
    sharex=True,
)

axupper.scatter(variances["year"], variances["pc1_evs"], label="PC1")
axupper.scatter(variances["year"], variances["model_evs"], label="Civil marriage share")
axupper.set_ylim(0, 1)
axupper.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
axupper.set_ylabel("share of explained variance")

axlower.scatter(
    correlations["year"],
    correlations["religiosity"],
    c="C2",
    label="Secularity - PiS vote",
)
axlower.set_ylabel("correlation")
axlower.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
axlower.set_ylim(0, 0.5)

axupper.legend(
    ncols=1,
    loc="lower right",
)  # bbox_to_anchor=(1, -0.2),
axlower.legend(
    ncols=1,
    loc="lower right",
)

for ax, label, yoffset in zip((axupper, axlower), ["(A)", "(B)"], [1,2]):
    ax.text(
        0.02,
        1 - 0.03*yoffset,
        label,
        transform=ax.transAxes,
        fontsize=FONT_SIZE,
        horizontalalignment="left",
        verticalalignment="top",
    )

plt.savefig(output_path)

if __name__ == "__main__":
    plt.show()
