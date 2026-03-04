import statsmodels.api as sm
import pathlib
import pandas as pd
import numpy as np
import itertools
import tqdm

here = pathlib.Path(__file__).resolve().parent
input_path = here / "../raw_data" / "poland__marriages.csv"

# --------------------
# Load and prepare data
# --------------------
df = pd.read_csv(input_path)
df = df.rename(columns={"nuts3_code": "harmonised_code"})

df["total_marriages"] = df["marriages_civil"] + df["marriages_religious"]

df = df[df["total_marriages"] > 0].copy()
df["const"] = 1.0
df["year"] = df["year"]

# --------------------
# Prediction horizon
# --------------------
years_pred = np.arange(2005, 2024)
years_pred = years_pred
X_pred = pd.DataFrame({"year": years_pred, "const": 1.0})

# --------------------
# Fit one logit per region
# --------------------
results = []

for region_code, g in df.groupby("harmonised_code"):
    # Optional: skip regions with too little data
    if g.shape[0] < 10:
        continue

    model = sm.GLM(
        g[["marriages_civil", "marriages_religious"]],
        g[["year", "const"]],
        family=sm.families.Binomial(link=sm.families.links.logit()),
    )

    fit = model.fit()

    # Predict for 1990–2050
    p_civil = fit.predict(X_pred[["year", "const"]])

    region_name = g["harmonised_name"].iloc[0]

    results.append(
        pd.DataFrame(
            {
                "harmonised_code": region_code,
                "harmonised_name": region_name,
                "year": years_pred,
                "p_civil": p_civil,
            }
        )
    )

# --------------------
# Combine all regions
# --------------------
df_pred = pd.concat(results, ignore_index=True)

# Pivot once
pivot = df_pred.pivot(
    index="year", columns="harmonised_code", values="p_civil"
).sort_index()

codes = pivot.columns.to_numpy()
values = pivot.to_numpy()  # shape: (n_years, n_codes)

max_score = -1
best_l_code = None
best_r_code = None

for i, j in tqdm.tqdm(itertools.combinations(range(len(codes)), 2)):
    delta = values[:, i] - values[:, j]

    high = delta[delta > 0].max(initial=0)
    low = (-delta[delta < 0]).max(initial=0)

    score = min(high, low)

    if score > max_score:
        max_score = score
        best_l_code = codes[i]
        best_r_code = codes[j]

df["share"] = df["marriages_civil"] / df["total_marriages"]
print("strongest crossover:")
print(
    df[df["harmonised_code"] == best_l_code][
        ["harmonised_code", "harmonised_name", "share"]
    ].iloc[[0, -1]]
)
print(
    df[df["harmonised_code"] == best_r_code][
        ["harmonised_code", "harmonised_name", "share"]
    ].iloc[[0, -1]]
)
