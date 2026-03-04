import pandas as pd
import pathlib


# CONFIG
here = pathlib.Path(__file__).resolve().parent
elections_path = here / "../raw_data" / "spain__votes.csv"
incomes_path = here / "../raw_data" / "spain__incomes.csv"
marriages_path = here / "../raw_data" / "spain__marriages.csv"
regions_path = here / "../raw_data" / "spain__regions.csv"

combined_output_path = here / "../combined_data" / "spain__vote_income_marriage.csv"
marriages_output_path = here / "../combined_data" / "spain__marriages.csv"

## ##########################################
## ELECTIONS
## ##########################################

elections = pd.read_csv(elections_path, index_col=0)

# Extract year from election_date
elections["year"] = elections["election_date"].str[:4].astype(int)

candidate_votes = elections[elections["type"] == 2].copy()

# total party votes per election
candidate_votes["total_votes"] = candidate_votes.groupby(
    ["election_date", "harmonised_code"]
)["votes"].transform("sum")
aligned_shares = candidate_votes[candidate_votes["name"] == "pp"].copy()
aligned_shares["vote_share"] = aligned_shares["votes"] / aligned_shares["total_votes"]

aligned_shares = aligned_shares[
    [
        "election_date",
        "year",
        "election_type",
        "harmonised_code",
        "harmonised_name",
        "vote_share",
    ]
]

elections_clean = aligned_shares.copy()

## ##########################################
## INCOMES
## ##########################################

df = pd.read_csv(incomes_path, sep=";", decimal=",", na_values="NULL")
regions = pd.read_csv(regions_path, index_col=0)

regions_map = (
    regions[["harmonised_code", "harmonised_name"]]
    .drop_duplicates()
    .set_index("harmonised_code")
    .to_dict()
)

df["harmonised_code"] = "I_" + df["PROV"].astype(str).str.zfill(2)
df["harmonised_name"] = df["harmonised_code"].map(regions_map["harmonised_name"])
df = df.rename(
    columns={
        "PROV": "province_id",
        "EJER": "year",
        "M190_2": "annual_salary",
        "M190_3": "worker_count",
    }
)
province_salaries = (
    df.groupby(["year", "harmonised_code", "harmonised_name"])
    .agg({"annual_salary": "sum", "worker_count": "sum"})
    .reset_index()
)
province_salaries["national_annual_salary"] = province_salaries.groupby("year")["annual_salary"].transform("sum")
province_salaries["national_worker_count"] = province_salaries.groupby("year")["worker_count"].transform("sum")
province_salaries["province_mean_wage"] = province_salaries["annual_salary"] / province_salaries["worker_count"]
province_salaries["national_mean_wage"] = province_salaries["national_annual_salary"] / province_salaries["national_worker_count"]
province_salaries["wage_index"] = province_salaries["province_mean_wage"] / province_salaries["national_mean_wage"]

incomes_clean = province_salaries[
    ["year", "harmonised_code", "harmonised_name", "wage_index"]
]

## ##########################################
## MARRIAGES
## ##########################################

marriages = pd.read_csv(marriages_path)

# Civil marriage share
marriages["civil_marriage_share"] = marriages["marriages_civil"] / (
    marriages["marriages_civil"] + marriages["marriages_religious"]
)
marriages_clean = marriages[
    ["year", "harmonised_code", "harmonised_name", "civil_marriage_share"]
]

## ##########################################
## FUSE DATASETS
## ##########################################

elections_incomes = pd.merge(
    left=elections_clean,
    right=incomes_clean,
    left_on=["harmonised_code", "year"],
    right_on=["harmonised_code", "year"],
    how="inner",
)
elections_incomes_marriages = pd.merge(
    left=elections_incomes,
    right=marriages_clean,
    left_on=["harmonised_code", "year"],
    right_on=["harmonised_code", "year"],
)
merged_data = elections_incomes_marriages[
    [
        "year",
        "election_date",
        "election_type",
        "harmonised_code",
        "harmonised_name",
        "vote_share",
        "wage_index",
        "civil_marriage_share",
    ]
].copy()
merged_data = merged_data.rename(columns={        
        "harmonised_code":"region_code",
        "harmonised_name": "reigion_name",              
})

merged_data.to_csv(combined_output_path,index=False)

marriages_clean = marriages_clean.rename(
    columns={
        "harmonised_code": "region_code",
        "harmonised_name": "region_name",
    }
)
marriages_clean.to_csv(marriages_output_path, index=False)