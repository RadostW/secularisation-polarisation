import pathlib
from tqdm import tqdm
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

here = pathlib.Path(__file__).resolve().parent
files = [
    ("italy", here / "../raw_data/italy__votes.csv"),
    ("spain", here / "../raw_data/spain__votes.csv"),
    ("poland", here / "../raw_data/poland__votes.csv"),
    ("germany", here / "../raw_data/germany__votes.csv"),
    ("france", here / "../raw_data/france__votes.csv"),
]
style_path = here / "../styles" / "secularisation.mplstyle"
figure_path = here / "../plot_graphics" / "pca_shares.pdf"


def compute_pca_variance(df_votes):

    # germany fix
    if "cdu" in df_votes.columns and "csu" in df_votes.columns:
        df_votes["cdu_csu"] = df_votes["cdu"] + df_votes["csu"]
        df_votes.drop(columns=["cdu", "csu"])

    if df_votes.shape[0] < 2 or df_votes.shape[1] < 1:
        return None

    # Remove zero-variance parties
    df_votes = df_votes.loc[:, df_votes.var() > 0]
    if df_votes.shape[1] < 1:
        return None

    X = df_votes.fillna(0)

    n_components = min(3, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_components)
    pca.fit(X)

    vars_out = list(pca.explained_variance_ratio_)
    while len(vars_out) < 3:
        vars_out.append(0.0)

    return {
        "pca_var_pc1": vars_out[0],
        "pca_var_pc2": vars_out[1],
        "pca_var_pc3": vars_out[2],
    }


all_rows = []
for country, csv_path in files:
    df = pd.read_csv(csv_path)
    df = df[df["type"] == 2].copy()
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)

    for (e_date, e_type), sub in tqdm(
        df.groupby(["election_date", "election_type"]), desc=f"{country} elections"
    ):

        pivot = (
            sub.groupby(["harmonised_code", "name"], as_index=False)["votes"]
            .sum()
            .pivot(index="harmonised_code", columns="name", values="votes")
            .fillna(0)
        )

        # votes to vote shares
        pivot = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)

        if e_type == "president_b":
            continue
        res = compute_pca_variance(pivot)
        if res is None:
            continue

        res["country"] = country
        res["election_date"] = e_date
        res["election_type"] = e_type

        all_rows.append(res)

df_all = pd.DataFrame.from_dict(all_rows)
df_all["year"] = df_all.election_date.str[:4].astype(int)
df_all["month"] = df_all.election_date.str[5:7].astype(int)
df_all["time"] = df_all["year"] + ((df_all["month"] - 1) / 12)

plt.style.use(style_path)

FIGURE_WIDTH = 3.3
FIGURE_HEIGHT = 2.2
fig, ax = plt.subplots(
    ncols=1,
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
    constrained_layout=True,
    sharey=True,
)

countries = [    
    "germany",
    "france",
    "italy",
    "spain",
    "poland",
]

tab20 = plt.get_cmap("tab20").colors
color_map = {
    "italy": tab20[1],
    "spain": tab20[3],
    "poland": tab20[5],
    "germany": tab20[7],
    "france": tab20[9],
}
edge_color_map = {
    "italy": tab20[1],
    "spain": tab20[3],
    "poland": tab20[4],
    "germany": tab20[7],
    "france": tab20[9],
}
marker_map = {
    "italy": "v",
    "spain": "s",
    "poland": "o",
    "germany": "p",
    "france": "D",
}

# Plot: nested groupby country -> election_type
for country in countries:
    df_c = df_all.query(f"country == '{country}'")
    for election_type, g in df_c.groupby("election_type"):
        g = g.sort_values("time")
        g = g[g["time"] > 1999]
        x = g["time"]
        y = g["pca_var_pc1"]

        # draw only the line (transparent)
        ax.plot(
            x,
            y,
            color="#ccc",
            linewidth=0.1,
        )

        # draw only the markers (opaque)
        ax.scatter(
            x,
            y,
            marker=marker_map[country],
            facecolors=color_map[country],
            edgecolors=edge_color_map[country],
            zorder=3,
        )


# Country legend handles
country_handles = [
    Line2D(
        [0],
        [0],
        color="w",
        label=country.title(),
        marker=marker_map[country],
        markerfacecolor=color_map[country],
        markeredgecolor=edge_color_map[country],
    )
    for country in countries
]

# ---- FUSE LEGENDS INTO ONE ----
all_handles = country_handles
all_labels = [h.get_label() for h in all_handles]

ax.set_xlim(1999,2026)
ax.set_ylim((0,1))

ax.legend(
    handles=all_handles,
    labels=all_labels,
    loc="lower center",
    ncol=3,
    bbox_to_anchor=(0.5, -0.5),
)

ax.set_ylabel("PC1 explained variance")

fig.savefig(figure_path)

if __name__ == "__main__":
    plt.show()
