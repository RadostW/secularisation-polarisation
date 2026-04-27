import pathlib
import pandas as pd
import yaml

here = pathlib.Path(__file__).resolve().parent
input_path = here / "../raw_data/poland__ess_raw.csv"
config_path = here / "ess_dictionaries.yaml"

output_path = here / "../combined_data/poland__ess_clean.csv"

df_raw = pd.read_csv(input_path, low_memory=False)

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

df_clean = pd.DataFrame()
df_clean["year"] = df_raw["essround"].map(config["round_to_year"])
df_clean["region"] = df_raw["region"]
df_clean.loc[df_clean["region"].isna(), "region"] = (
    "T_"
    + df_raw.loc[df_clean["region"].isna(), "regionpl"]
    .astype(int)
    .astype(str)
    .str.zfill(2)
).map(config["teryt_to_nuts"])

df_clean["rlgdgr"] = df_raw["rlgdgr"].where(df_raw["rlgdgr"] < 11)
df_clean["pray"] = df_raw["pray"].where(df_raw["pray"] < 8)
df_clean["rlgatnd"] = df_raw["rlgatnd"].where(df_raw["rlgatnd"] < 8)

df_clean["religiosity"] = (
    df_clean["rlgdgr"] + (7 - df_clean["pray"]) + (7 - df_clean["rlgatnd"])
)
df_clean["trust"] = df_raw["trstplc"].where(df_raw["trstplc"] < 11)

for vote_column in config["vote_columns"]:
    df_clean[vote_column] = df_raw[vote_column].map(config[vote_column])

df_clean["last_vote"] = df_clean[config["vote_columns"]].bfill(axis=1).iloc[:, 0]
df_clean = df_clean[
    [
        "year",
        "region",
        "religiosity",
        "trust",
        "last_vote",
        "rlgdgr",
        "pray",
        "rlgatnd",
        "prtvtpl",
        "prtvtapl",
        "prtvtbpl",
        "prtvtcpl",
        "prtvtdpl",
        "prtvtepl",
        "prtvtfpl",
    ]
]

df_clean.to_csv(output_path, index=False)