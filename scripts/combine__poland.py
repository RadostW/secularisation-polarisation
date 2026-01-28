import pandas as pd
import pathlib
import re

# CONFIG
here = pathlib.Path(__file__).resolve().parent
elections_path = here / "../raw_data" / "poland__votes.csv"
incomes_path = here / "../raw_data" / "poland__incomes.csv"
marriages_path = here / "../raw_data" / "poland__marriages.csv"
regions_path = here / "../raw_data" / "poland__regions.csv"

combined_path = here / "../combined_data" / "poland__vote_income_marriage.csv"

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

candidate_votes["party"] = (
    candidate_votes["name"]
    .replace(to_replace="Kaczynski", value="PIS")
    .replace(to_replace="Duda", value="PIS")
    .replace(to_replace="Nawrocki", value="PIS")
)
candidate_votes = candidate_votes[candidate_votes["party"] == "PIS"].copy()

candidate_votes["vote_share"] = (
    candidate_votes["votes"] / candidate_votes["total_votes"]
)
elections_clean = candidate_votes[
    [
        "election_date",
        "year",
        "election_type",
        "harmonised_code",
        "harmonised_name",
        "vote_share",
    ]
]

## ##########################################
## INCOMES
## ##########################################

df = pd.read_csv(incomes_path, sep=";", decimal=",")
wage_index_columns = [
    x
    for x in df.columns
    if "przeciętne miesięczne wynagrodzenia brutto w relacji do średniej krajowej" in x
]
years_map = {
    x: re.match(
        "przeciętne miesięczne wynagrodzenia brutto w relacji do średniej krajowej \(Polska=100\);(....);\[%\]",
        x,
    )[1]
    for x in wage_index_columns
}
index_columns = ["Kod", "Nazwa"]
df = df[index_columns + wage_index_columns]
df = df.rename(columns=years_map)
df = df.rename(columns={"Kod": "code", "Nazwa": "name"})

income_raw = df.melt(id_vars=["code", "name"], var_name="year", value_name="wage_index")
income_raw["wage_index"] = income_raw["wage_index"] / 100
income_raw["harmonised_code"] = (
    "T_" + income_raw["code"].astype(str).str.zfill(7).str[:4]
)
income_raw["year"] = income_raw["year"].astype(int)

incomes_clean = income_raw[["year", "harmonised_code", "name", "wage_index"]].copy()

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
         "harmonised_name_x",
         "vote_share",
         "wage_index",
         "civil_marriage_share",
     ]
 ].copy()
merged_data = merged_data.rename(columns={        
         "harmonised_code":"region_code",
         "harmonised_name_x": "reigion_name",              
 })
merged_data.to_csv(combined_path,index=False)