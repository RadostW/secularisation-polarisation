import pandas as pd
import pathlib
import yaml

# CONFIG
here = pathlib.Path(__file__).resolve().parent
elections_path = here / "../raw_data" / "italy__votes.csv"
incomes_path = here / "../raw_data" / "italy__incomes.zip"
marriages_path = here / "../raw_data" / "italy__marriages.csv"
alignment_path = here / "../raw_data" / "italy__alignment.yaml"
regions_path = here / "../raw_data" / "italy__regions.csv"

combined_path = here / "../combined_data" / "italy__vote_income_marriage.csv"

## ##########################################
## ELECTIONS
## ##########################################

elections = pd.read_csv(elections_path, index_col=0)

# Extract year from election_date
elections["year"] = elections["election_date"].str[:4].astype(int)

with open(alignment_path, "r") as f:
    alignment_yaml = yaml.safe_load(f)

# ------------------------------------------
# Assign coalition labels
# ------------------------------------------

elections["alignment"] = pd.NA

for election_date, df_idx in elections.groupby("election_date").groups.items():

    # mapping for this election (party -> alignment)
    mapping = {}
    if election_date in alignment_yaml:
        for alignment, parties in alignment_yaml[election_date].items():
            for party in parties:
                mapping[party] = alignment

    # mask: party vote rows for this election
    mask = (elections["election_date"] == election_date) & (elections["type"] == 2)

    # assign alignment, defaulting to 'small_party'
    elections.loc[mask, "alignment"] = (
        elections.loc[mask, "name"].map(mapping).fillna("small_party")
    )

elections["alignment"] = elections["alignment"].fillna("not_applicable")

# ------------------------------------------
# Compute vote shares by coalition
# ------------------------------------------

candidate_votes = elections[elections["type"] == 2].copy()

# total party votes per election
candidate_votes["total_votes"] = candidate_votes.groupby(
    ["election_date", "harmonised_code"]
)["votes"].transform("sum")

# votes by alignment per election
candidate_votes["alignment_votes"] = candidate_votes.groupby(
    ["election_date", "harmonised_code", "harmonised_name", "alignment"]
)["votes"].transform("sum")

# vote share by alignment
candidate_votes["alignment_share"] = (
    candidate_votes["alignment_votes"] / candidate_votes["total_votes"]
)

# ------------------------------------------
# Summarise results
# ------------------------------------------

alignment_shares = candidate_votes.drop_duplicates(
    subset=["election_date", "harmonised_code", "alignment"]
)

alignment_shares = alignment_shares[alignment_shares["alignment"] == "right"]
alignment_shares = alignment_shares[
    [
        "election_date",
        "year",
        "election_type",
        "harmonised_code",
        "harmonised_name",
        "alignment_share",
    ]
]

elections_clean = alignment_shares.copy()

## ##########################################
## INCOMES
## ##########################################


df = pd.read_csv(incomes_path)
df = df.rename(
    columns={
        "Anno_riferimento": "year",
        "Sesso": "sex",
        "Provincia": "provincia",
        "Classe_eta": "classe_eta",
        "Qualifica": "qualifica",
        "Media_salario_sett": "mean_weekly_wage",
        "Numero_lavoratori": "n_workers",
    }
)

# -----------------------------
# Filter only totals
# -----------------------------
df_tot = df[
    (df["classe_eta"] == "nonripartibili")
    & (df["qualifica"] == "NP")
    & (df["sex"] == "NP")
].copy()

df_tot["mean_weekly_wage"] = pd.to_numeric(df_tot["mean_weekly_wage"])
df_tot["n_workers"] = pd.to_numeric(df_tot["n_workers"])
df_tot["total_weekly_wage"] = df_tot["mean_weekly_wage"] * df_tot["n_workers"]
df_tot = df_tot[["year", "provincia", "total_weekly_wage", "n_workers"]]

df_prov = df_tot.groupby(["year", "provincia"]).sum().reset_index()
df_prov["national_total_weekly_wage"] = (
    df_prov[["year", "total_weekly_wage"]].groupby("year").transform("sum")
)
df_prov["national_n_workers"] = (
    df_prov[["year", "n_workers"]].groupby("year").transform("sum")
)

df_prov["province_mean_wage"] = df_prov["total_weekly_wage"] / df_prov["n_workers"]
df_prov["national_mean_wage"] = (
    df_prov["national_total_weekly_wage"] / df_prov["national_n_workers"]
)

df_prov["wage_index"] = df_prov["province_mean_wage"] / df_prov["national_mean_wage"]

communes = pd.read_csv(regions_path, sep=";", encoding="latin1")
communes = communes.rename(
    columns={
        "Denominazione dell'Unità territoriale sovracomunale \n(valida a fini statistici)": "province_name",
        "Sigla automobilistica": "licence_plate_prefix",
        "Codice NUTS3 2024": "nuts3_code",
    }
)
provinces = communes[
    ["licence_plate_prefix", "province_name", "nuts3_code"]
].drop_duplicates(subset="nuts3_code")

merged = pd.merge(
    left=df_prov,
    right=provinces,
    how="left",
    left_on="provincia",
    right_on="licence_plate_prefix",
)

incomes_clean = merged[["year", "nuts3_code", "province_name", "wage_index"]].copy()

## ##########################################
## MARRIAGES
## ##########################################

marriages = pd.read_csv(marriages_path)

# Civil marriage share
marriages["civil_marriage_share"] = marriages["marriages_civil"] / (
    marriages["marriages_civil"] + marriages["marriages_religious"]
)
marriages_clean = marriages[
    ["year", "nuts3_code", "harmonised_name", "civil_marriage_share"]
]


## ##########################################
## FUSE DATASETS
## ##########################################

elections_incomes = pd.merge(
    left=elections_clean,
    right=incomes_clean,
    left_on=["harmonised_code", "year"],
    right_on=["nuts3_code", "year"],
    how="inner",
)
elections_incomes_marriages = pd.merge(
    left=elections_incomes,
    right=marriages_clean,
    left_on=["nuts3_code", "year"],
    right_on=["nuts3_code", "year"],
)
merged_data = elections_incomes_marriages[
    [
        "year",
        "election_date",
        "election_type",
        "nuts3_code",
        "province_name",
        "alignment_share",
        "wage_index",
        "civil_marriage_share",
    ]
].copy()
merged_data = merged_data.rename(columns={        
        "nuts3_code":"region_code",
        "province_name": "reigion_name",
        "alignment_share": "vote_share",        
})

merged_data.to_csv(combined_path,index=False)