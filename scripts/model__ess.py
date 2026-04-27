import pathlib
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels
import matplotlib.pyplot as plt

here = pathlib.Path(__file__).resolve().parent

input_path = here / "../combined_data/poland__ess_clean.csv"
output_path = here / "../combined_data/poland__ess_correlations.csv"

df = pd.read_csv(input_path, low_memory=False)

df["voted_pis"] = np.nan
df.loc[~df["last_vote"].str.contains("\*"), "voted_pis"] = 0
df.loc[df["last_vote"] == "Prawo i Sprawiedliwość", "voted_pis"] = 1
df_valid = df[["year", "region", "voted_pis", "religiosity"]].dropna()
df_valid["religiosity"] = df_valid["religiosity"] / 22.0
df_valid["secularity"] = - df_valid["religiosity"]


# Election date fixed effects
date_fe = pd.get_dummies(
    df_valid["year"],
    prefix="e",
    dtype=int,
)

# Municipality fixed effects
muni_fe = pd.get_dummies(
    df_valid["region"],
    prefix="r",
    dtype=int,
    drop_first=True,
)

# Variant (1)
y = df_valid["voted_pis"].copy()
X = pd.concat(
    [
        df_valid["secularity"],
        date_fe,
    ],
    axis=1,
).copy()
model = sm.OLS(y, X).fit(cov_type="HC3")
print(model.summary())


# Variant (2)
y = df_valid["voted_pis"].copy()
X = pd.concat(
    [
        df_valid["secularity"],
        date_fe,
        muni_fe,
    ],
    axis=1,
).copy()
model = sm.OLS(y, X).fit(cov_type="HC3")
print(model.summary())

correlations = df_valid.groupby("year")[["voted_pis", "religiosity"]].corr().iloc[0::2, -1].reset_index()
correlations[["year","religiosity"]].rename(columns={"religiosity":"ess_correlation"})

correlations.to_csv(output_path)

