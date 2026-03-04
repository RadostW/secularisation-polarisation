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

output_dir = here / "../combined_data/"

all_rows = []
for country, csv_path in files:
    df = pd.read_csv(csv_path)
    df = df[df["type"] == 2].copy()
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)

    pcs = []

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
        df_votes = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)

        if e_type == "president_b":
            continue

        # germany fix
        if "cdu" in df_votes.columns and "csu" in df_votes.columns:
            df_votes["cdu_csu"] = df_votes["cdu"] + df_votes["csu"]
            df_votes.drop(columns=["cdu", "csu"])

        if df_votes.shape[0] < 2 or df_votes.shape[1] < 1:
            continue

        # Remove zero-variance parties
        df_votes = df_votes.loc[:, df_votes.var() > 0]
        if df_votes.shape[1] < 1:
            continue

        X = df_votes.fillna(0)

        pca = PCA(n_components=1)
        pc1 = pca.fit_transform(X)

        df_votes["pc1"] = pc1[:, 0]
        df_votes = df_votes.reset_index()

        if country == "poland":
            tv = X.var(axis=0, ddof=0).sum()
            print(f"{e_date} {tv}")

        df_pc = pd.merge(
            left=df_votes[["harmonised_code", "pc1"]],
            right=sub[
                ["harmonised_code", "harmonised_name", "election_date", "election_type"]
            ],
            on="harmonised_code",
            how="left",
        )
        df_pc = df_pc.groupby("harmonised_code").first().reset_index()
        df_pc = df_pc.rename(columns={"pc1": f"{e_date}_pc1"})

        pcs.append(df_pc.copy())

    aligned_pcs = []
    reference = None
    reference_pc1_col = None

    for df in pcs:
        # find pc1 column
        pc1_col = [c for c in df.columns if c.endswith("pc1")][0]

        if reference is None:
            aligned_pcs.append(df.rename(columns={pc1_col: "pc1"}))
            reference = df[["harmonised_code", pc1_col]].copy()
            reference_pc1_col = pc1_col
            continue

        merged = reference.merge(
            df[["harmonised_code", pc1_col]],
            on="harmonised_code",
            how="inner",
        )

        corr = merged[pc1_col].corr(merged[reference_pc1_col])

        # flip sign if negatively correlated
        if corr < 0:
            # print(f"did a flip : {corr}, {reference_pc1_col}, {pc1_col}")
            df[pc1_col] = -df[pc1_col]

        aligned_pcs.append(df.rename(columns={pc1_col: "pc1"}))
        reference = df[["harmonised_code", pc1_col]].copy()
        reference_pc1_col = pc1_col

    country_pcs = pd.concat(aligned_pcs)
    column_order = [
        "election_date",
        "election_type",
        "harmonised_code",
        "harmonised_name",
        "pc1",
    ]
    country_pcs = country_pcs.sort_values(by=column_order).reset_index(drop=True)[column_order]
    country_pcs.to_csv(output_dir / f"{country}__pc1.csv")
