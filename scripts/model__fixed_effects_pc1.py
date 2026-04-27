import pathlib
import pandas as pd
import statsmodels.api as sm

here = pathlib.Path(__file__).resolve().parent

style_path = here / "../styles" / "secularisation.mplstyle"
regressors_path = here / "../combined_data" / "poland__vote_income_marriage.csv"
pc1_path = here / "../combined_data" / "poland__pc1.csv"

output_path = here / "../combined_data" / "explained_variance_shares.csv"

regressors = pd.read_csv(regressors_path)
pc1 = pd.read_csv(pc1_path, index_col=0)

poland_total_variance = pd.DataFrame(
    [
        ("2000_10_08", 0.0257),
        ("2001_09_23", 0.0293),
        ("2004_06_13", 0.0307),
        ("2005_09_25", 0.0304),
        ("2005_10_09", 0.0309),
        ("2007_10_21", 0.0320),
        ("2009_06_07", 0.0379),
        ("2010_06_20", 0.0296),
        ("2011_10_09", 0.0314),
        ("2014_05_25", 0.0325),
        ("2015_05_10", 0.0197),
        ("2015_10_25", 0.0231),
        ("2019_05_26", 0.0285),
        ("2019_10_13", 0.0276),
        ("2020_06_28", 0.0237),
        ("2023_10_15", 0.0227),
        ("2024_06_09", 0.0279),
        ("2025_05_18", 0.0177),
    ],
    columns=["election_date", "total_variance"],
)

df = pd.merge(
    left=regressors,
    right=pc1,
    left_on=["election_date", "election_type", "region_code", "reigion_name"],
    right_on=["election_date", "election_type", "harmonised_code", "harmonised_name"],
    how="inner",
)[
    [
        "year",
        "election_date",
        "election_type",
        "region_code",
        "reigion_name",
        "pc1",
        "wage_index",
        "civil_marriage_share",
    ]
]

# Civil marriage share
civil_share = df["civil_marriage_share"]

# Election date fixed effects
date_fe = pd.get_dummies(
    df["election_date"],
    prefix="e",
    dtype=int,
)

# # Municipality fixed effects
# muni_fe = pd.get_dummies(
#     df["region_code"],
#     prefix="r",
#     dtype=int,
#     drop_first=True,
# )

X = pd.concat([civil_share, date_fe], axis=1)
y = df["pc1"]
model = sm.OLS(y, X).fit(cov_type="HC3")

print(model.summary())

df["predicted"] = model.predict(X)
df["pc1_residuals"] = df["pc1"] - df["predicted"]

variance_df = pd.DataFrame()
variance_df["pc1_residuals_variance"] = df.groupby("election_date")[
    "pc1_residuals"
].var()
variance_df["pc1_variance"] = df.groupby("election_date")["pc1"].var()
variance_df["year"] = df.groupby("election_date")["year"].mean()
variance_df = pd.merge(variance_df, poland_total_variance, on="election_date")
variance_df["pc1_evs"] = variance_df["pc1_variance"] / variance_df["total_variance"]
variance_df["model_evs"] = (
    variance_df["pc1_variance"] / variance_df["total_variance"]
) - (variance_df["pc1_residuals_variance"] / variance_df["total_variance"])


variance_df[["year","pc1_evs","model_evs"]].to_csv(output_path,index=False)
