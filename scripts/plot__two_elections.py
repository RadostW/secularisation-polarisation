import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pathlib

here = pathlib.Path(__file__).resolve().parent
style_path = here / "../styles" / "secularisation.mplstyle"

input_path = here / "../combined_data" / "poland__first_and_second.csv"

figure_path = here / "../plot_graphics" / "two_elections.pdf"

plt.style.use(style_path)

FIGURE_WIDTH = 7
FIGURE_HEIGHT = 3
fig, axes = plt.subplots(
    ncols=2,
    nrows=1,
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),    
    constrained_layout=True,
    # sharey=True,
)

df = pd.read_csv(input_path)

(ax_old,ax_new) = axes
ax_old.set_aspect('equal')
ax_new.set_aspect('equal')

a = 0.35
t = [-0.3,-0.2,-0.1,0,0.1,0.2,0.3]

ax_old.set_xlim([-a,a])
ax_old.set_ylim([-a,a])
ax_new.set_xlim([-a,a])
ax_new.set_ylim([-a,a])

ax_old.set_xticks(t)
ax_old.set_yticks(t)
ax_new.set_xticks(t)
ax_new.set_yticks(t)


df_true = df[df["harmonised_code"].str[0] == 'T']
df_pure = df[df["harmonised_code"].str[0] != 'T']

election_old = df_true[df_true["election_date"] == "2005_09_25"]
election_new = df_true[df_true["election_date"] == "2023_10_15"]

ax_old.scatter(election_old["pc1"],election_old["pc2"])
ax_new.scatter(election_new["pc1"],election_new["pc2"])

ax_old.set_xlabel("PC1")
ax_old.set_ylabel("PC2")

ax_new.set_xlabel("PC1")
ax_new.set_ylabel("PC2")

plt.show()
