import pathlib
import pandas as pd
import statsmodels.api as sm


print("Making models")

here = pathlib.Path(__file__).resolve().parent

path_2fe_results = here / "../regression_results" / "2fe_results.txt"
path_by_year_results = here / "../regression_results" / "by_year_results.txt"

contry_data = {
    "Italy": here / "../combined_data" / "italy__vote_income_marriage.csv",
    "Spain": here / "../combined_data" / "spain__vote_income_marriage.csv",
    "Poland": here / "../combined_data" / "poland__vote_income_marriage.csv",
}

model_summaries = []

for country_name, combined_path in contry_data.items():
    df = pd.read_csv(combined_path)
    df = df[df["vote_share"].notna()]

    # Main regressors
    X = df[["wage_index", "civil_marriage_share"]]

    # Election date fixed effects
    date_fe = pd.get_dummies(
        df["election_date"],
        prefix="e",
        dtype=int,
        # drop_first=True
    )

    # Municipality fixed effects
    muni_fe = pd.get_dummies(
        df["region_code"],
        prefix="r",
        dtype=int,
        drop_first=True,
    )

    # Combine regressors and FE
    X = pd.concat([X, date_fe, muni_fe], axis=1)

    # Dependent variable
    y = df["vote_share"]

    # Fit 2-way FE model
    model_2fe = sm.OLS(y, X).fit(cov_type="HC3")

    # Output
    # print()
    # print("Results: Election date and region fixed effects")
    # print(model_2fe.summary())
    summary_string_raw = model_2fe.summary().__str__().split("\n")
    summary_string = "\n".join(
        [f"{country_name}", "Results: Election date and region fixed effects"]
        + summary_string_raw[:20]
        + ["...", "..."]
        + summary_string_raw[-15:]
    )
    model_summaries.append(summary_string)

    election_dates = list(df["election_date"].unique())

    election_fits = []
    for ed in election_dates:
        df_election = df[df["election_date"] == ed].copy()
        election_year = df_election["year"].iloc[0]

        X_election = df_election[["wage_index", "civil_marriage_share"]]
        X_election = sm.add_constant(X_election)
        y_election = df_election["vote_share"]

        model_election = sm.OLS(y_election, X_election).fit(cov_type="HC3")
        election_fit = (
            pd.concat([model_election.params, model_election.conf_int()], axis=1)
            .set_axis(["value", "low", "high"], axis=1)
            .stack()
            .to_frame()
            .T
        )
        election_fit.columns = [a + "_" + b for (a, b) in election_fit.columns]
        election_fit.index = [election_year]
        election_fits.append(election_fit)
    election_fits_df = pd.concat(election_fits)

with open(path_2fe_results, "w") as text_file:
    text_file.write("\n###\n".join(model_summaries))

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    q = election_fits_df
    x = q.index
    y = q["civil_marriage_share_value"]
    yerr=(q["civil_marriage_share_high"]-q["civil_marriage_share_low"])
    plt.errorbar(x,y,yerr=yerr)
    plt.show()