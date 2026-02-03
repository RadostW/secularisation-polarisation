import pathlib
import pandas as pd
import statsmodels.api as sm

print("Making models")

here = pathlib.Path(__file__).resolve().parent

path_2fe_results = here / "../regression_results" / "2fe_results.txt"
path_int_results = here / "../regression_results" / "int_results.txt"
path_by_year_results = here / "../regression_results" / "by_year_results.txt"
marriage_coefficient_results = (
    here / "../regression_results" / "marriage_coefficient_results.csv"
)

contry_data = {
    "Italy": here / "../combined_data" / "italy__vote_income_marriage.csv",
    "Spain": here / "../combined_data" / "spain__vote_income_marriage.csv",
    "Poland": here / "../combined_data" / "poland__vote_income_marriage.csv",
}

model_summaries = []
int_model_summaries = []
split_fits = []
marriage_coefficients = []

for country_name, combined_path in contry_data.items():
    df = pd.read_csv(combined_path)
    df = df[df["vote_share"].notna()].copy().reset_index(drop=True)

    # Main regressors
    base_regressors = df[["wage_index", "civil_marriage_share"]]

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
    X = pd.concat([base_regressors, date_fe, muni_fe], axis=1)
    y = df["vote_share"]

    ######################################
    # BASE MODEL
    ######################################
    # Fit 2-way FE model
    model_2fe = sm.OLS(y, X).fit(cov_type="HC3")

    summary_string_raw = model_2fe.summary().__str__().split("\n")
    summary_string = "\n".join(
        [f"{country_name}", "Results: Election date and region fixed effects"]
        + summary_string_raw[:20]
        + ["...", "..."]
        + summary_string_raw[-15:]
    )
    model_summaries.append(summary_string)
    model_2fe_result = pd.DataFrame(
        {
            "election_date": ["none"],
            "country": [country_name],
            "model_type": ["no_interactions"],
            "civil_marriage_share_value": [model_2fe.params["civil_marriage_share"]],
            "civil_marriage_share_se": [model_2fe.bse["civil_marriage_share"]],
        }
    )

    ######################################
    # MODELS WITH INTERACTIONS
    ######################################
    wage_date_int = date_fe.mul(df["wage_index"], axis=0)
    civil_date_int = date_fe.mul(df["civil_marriage_share"], axis=0)

    wage_date_int = wage_date_int.add_prefix("wage_")
    civil_date_int = civil_date_int.add_prefix("civil_")

    #
    # Both interactions
    #

    # Combine regressors and FE
    X_int_both = pd.concat(
        [
            wage_date_int,
            civil_date_int,
            date_fe,
            muni_fe,
        ],
        axis=1,
    )
    model_2fe_int_both = sm.OLS(y, X_int_both).fit(cov_type="HC3")
    int_both_summary_string_raw = model_2fe_int_both.summary().__str__().split("\n")
    int_both_summary_string = "\n".join(
        [f"{country_name}", "Results: Wage and marriage interaction, and region fe"]
        + [
            x
            for idx, x in enumerate(int_both_summary_string_raw)
            if (("civil_e_" in x) or (idx < 20))
        ]
        + ["...", "..."]
        + int_both_summary_string_raw[-15:]
    )
    int_model_summaries.append(int_both_summary_string)
    int_both_df = pd.concat(
        [
            model_2fe_int_both.params.rename("value"),
            model_2fe_int_both.bse.rename("se"),
        ],
        axis=1,
    )
    int_both_df = int_both_df[int_both_df.index.str.contains("civil")]
    int_both_df["election_date"] = int_both_df.index.str[-10:]
    int_both_df["model_type"] = "one_interaction"
    int_both_df["country"] = country_name
    int_both_df = int_both_df.rename(
        columns={"value": "civil_marriage_share_value", "se": "civil_marriage_share_se"}
    )

    #
    # One interaction
    #

    # Combine regressors and FE
    X_int_one = pd.concat(
        [
            df[["wage_index"]],
            civil_date_int,
            date_fe,
            muni_fe,
        ],
        axis=1,
    )
    model_2fe_int_one = sm.OLS(y, X_int_one).fit(cov_type="HC3")
    int_one_summary_string_raw = model_2fe_int_one.summary().__str__().split("\n")
    int_one_summary_string = "\n".join(
        [f"{country_name}", "Results: marriage interaction, plain wages, and region fe"]
        + [
            x
            for idx, x in enumerate(int_one_summary_string_raw)
            if (("civil_e_" in x) or (idx < 20))
        ]
        + ["...", "..."]
        + int_one_summary_string_raw[-15:]
    )
    int_model_summaries.append(int_one_summary_string)
    int_one_df = pd.concat(
        [
            model_2fe_int_one.params.rename("value"),
            model_2fe_int_one.bse.rename("se"),
        ],
        axis=1,
    )
    int_one_df = int_one_df[int_one_df.index.str.contains("civil")]
    int_one_df["election_date"] = int_one_df.index.str[-10:]
    int_one_df["model_type"] = "both_interactions"
    int_one_df["country"] = country_name
    int_one_df = int_one_df.rename(
        columns={"value": "civil_marriage_share_value", "se": "civil_marriage_share_se"}
    )

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
            pd.concat([model_election.params, model_election.bse], axis=1)
            .set_axis(["value", "se"], axis=1)
            .stack()
            .to_frame()
            .T
        )
        election_fit.columns = [a + "_" + b for (a, b) in election_fit.columns]
        election_fit.index = [election_year]
        election_fit["election_date"] = ed
        election_fits.append(election_fit)
    election_fits_df = pd.concat(election_fits)
    election_fits_df["country"] = country_name
    election_fits_df["model_type"] = "split_fits"
    split_fits.append(election_fits_df)

    marriage_split_fit = election_fits_df[
        [
            "election_date",
            "country",
            "model_type",
            "civil_marriage_share_value",
            "civil_marriage_share_se",
        ]
    ]
    marriage_coefficient = (
        pd.concat([int_one_df, int_both_df, marriage_split_fit,model_2fe_result])
        .reset_index(drop=True)
        .copy()
    )
    marriage_coefficients.append(marriage_coefficient)

split_fits = pd.concat(split_fits)
marriage_coefficients = pd.concat(marriage_coefficients)

marriage_coefficients.to_csv(marriage_coefficient_results,index=False)

with open(path_2fe_results, "w") as text_file:
    text_file.write("\n###\n".join(model_summaries))

with open(path_int_results, "w") as text_file:
    text_file.write("\n###\n".join(int_model_summaries))
