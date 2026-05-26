import pathlib
import pandas as pd
from sklearn.decomposition import PCA
import numpy as np

here = pathlib.Path(__file__).resolve().parent
input_path = here / "../raw_data/poland__votes.csv"

output_path = here / "../combined_data/poland__first_and_second.csv"


df = pd.read_csv(input_path)
df = df[df["type"] == 2].copy()
df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)

pcs = []

old_election_date = "2005_09_25"  # sejm
new_election_date = "2023_10_15"  # sejm

parties = ["PIS", "PO", "LEWICA"]

for e_date in [old_election_date, new_election_date]:

    sub = df[df["election_date"] == e_date]

    pivot = (
        sub.groupby(["harmonised_code", "name"], as_index=False)["votes"]
        .sum()
        .pivot(index="harmonised_code", columns="name", values="votes")
        .fillna(0)
    )

    # votes to vote shares
    df_votes = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)

    # Remove zero-variance parties
    df_votes = df_votes.loc[:, df_votes.var() > 0]
    if df_votes.shape[1] < 1:
        continue

    pca = PCA(n_components=2)
    X = df_votes.fillna(0)
    X = X.rename(columns={"SLD": "LEWICA"})
    pc_loadings = pca.fit_transform(X)

    X_pure = pd.DataFrame(0, index=np.arange(len(parties)), columns=X.columns)
    for i, party in enumerate(parties):
        X_pure.loc[i, party] = 1

    pc_pure_loadings = pca.transform(X_pure)

    df_votes["pc1"] = pc_loadings[:, 0]
    df_votes["pc2"] = pc_loadings[:, 1]

    df_votes = df_votes.reset_index()
    df_votes = df_votes[["harmonised_code", "pc1", "pc2"]]

    df_pure = pd.DataFrame(
        np.array([parties, pc_pure_loadings[:, 0], pc_pure_loadings[:, 1]]).T,
        columns=["harmonised_code", "pc1", "pc2"],
    )

    df_combined = pd.concat([df_votes, df_pure])
    df_combined["election_date"] = e_date

    pcs.append(df_combined.copy())

df_combined_full = pd.concat(pcs)
df_combined_full.to_csv(output_path)