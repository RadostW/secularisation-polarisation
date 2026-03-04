import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pathlib

here = pathlib.Path(__file__).resolve().parent
style_path = here / "../styles" / "secularisation.mplstyle"

marriage_path = here / "../combined_data/poland__marriages.csv"
votes_path = here / "../combined_data/poland__vote_income_marriage.csv"

figure_path = here / "../plot_graphics" / "case_study.pdf"

plt.style.use(style_path)

FIGURE_WIDTH = 3.3
FIGURE_HEIGHT = 5
fig, axes = plt.subplots(
    ncols=1,
    nrows=3,
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
    height_ratios=[3, 2, 2],
    constrained_layout=True,
    sharex=True,
)
df_marriage = pd.read_csv(marriage_path)
df_votes = pd.read_csv(votes_path)


df_votes["year"] = pd.to_numeric(df_votes.election_date.str[:4], errors="coerce")
df_votes["month"] = pd.to_numeric(df_votes.election_date.str[5:7], errors="coerce")
df_votes["year_cts"] = df_votes["year"] + df_votes["month"] / 12
df_votes["country_mean"] = df_votes.groupby("election_date")["vote_share"].transform(
    "mean"
)


(axmarriage, axpresident, axeuropean) = axes

a_code = "T_1611"
b_code = "T_3016"
a_marriage = df_marriage.query(f"region_code == '{a_code}'")
b_marriage = df_marriage.query(f"region_code == '{b_code}'")
# a_votes = df_votes.query(f"region_code == '{a_code}' and election_type == 'sejm'")
# b_votes = df_votes.query(f"region_code == '{b_code}' and election_type == 'sejm'")
a_votes = df_votes.query(f"region_code == '{a_code}'")
b_votes = df_votes.query(f"region_code == '{b_code}'")

axmarriage.scatter(
    a_marriage["year"],
    a_marriage["civil_marriage_share"],
    label="pow. strzelecki",
)
axmarriage.scatter(
    b_marriage["year"],
    b_marriage["civil_marriage_share"],
    label="pow. obornicki",
)
axmarriage.set_ylabel("civil marriage share")
axmarriage.set_ylim(0, 0.7)
axmarriage.legend()

axpresident.scatter(
    a_votes.query("election_type == 'president_a'")["year_cts"],
    a_votes.query("election_type == 'president_a'")["vote_share"],
)
axpresident.scatter(
    b_votes.query("election_type == 'president_a'")["year_cts"],
    b_votes.query("election_type == 'president_a'")["vote_share"],
)
axpresident.set_ylabel("vote share (president)")
axpresident.set_ylim(0.08, 0.42)

axeuropean.scatter(
    a_votes.query("election_type == 'european'")["year_cts"],
    a_votes.query("election_type == 'european'")["vote_share"],
    label="strzelecki",
)
axeuropean.scatter(
    b_votes.query("election_type == 'european'")["year_cts"],
    b_votes.query("election_type == 'european'")["vote_share"],
    label="obornicki",
)
axeuropean.set_ylabel("vote share (european)")
axeuropean.set_ylim(0.08, 0.42)

plt.savefig(figure_path)

plt.show()
