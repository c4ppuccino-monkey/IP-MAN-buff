import streamlit as st
import queries
import pandas as pd
import altair as alt
import accounts_management as am
import enrichment as en
import app_functions as af
import maps
import comparison_charts


# Loading the database and creating a cursor
conn = queries.get_connection()
cur = conn.cursor()

# Loading saved accounts from json
accounts = am.load_accounts()

heroes_dicts = maps.load_heroes()
heroes_names = af.heroes_names_list(heroes_dicts)
items_dicts = maps.load_items()
items = af.items_options_list(items_dicts)

st.set_page_config(layout="wide")

st.title("Dota Dashboard")

compare = st.toggle("Compare accounts", key="compare_accounts")

# Filters
filters = af.all_filters(accounts, heroes_names, items, compare)
parse_filter = filters["parse_filter"]
result_filter = filters["result_filter"]
matches_filter = filters["matches_filter"]
peer_id = filters["peer_filter"]
first_item, second_item = filters["item_order"]
item = filters["item"]
hero_filter = filters["hero_filter"]


# Caching data to avoid reruns of the full script when filtering
# aka (manipulating different widgets)
@st.cache_data(show_spinner=True)
def load_match_rows(
    account_id, result_filter, matches_filter, peer_id,
    parse_filter, item, first_item, second_item
):
    local_conn = queries.get_connection()
    local_cur = local_conn.cursor()
    rows = queries.get_matches_by_account(
        local_cur, account_id, result_filter, matches_filter,
        peer_id, parse_filter, item, first_item, second_item
    )
    local_conn.close()
    return [dict(row) for row in rows]


def data_loader(compare, accounts):

    if compare == False:

        col1, col2 = st.columns([1,3])

        with col1:
            # Select the account to show its dashboard
            selected_acc = st.selectbox(
                "Choose account", accounts, 
                format_func=lambda acc: f"{acc['name']} ({acc['id']})",
                key="selected_account"
            )
        
        singel_account_dashboard(selected_acc)
    
    else:
        selected_rows = []

        col1, col3 = st.columns([3,1], border=True)

        with col3:
            st.write("Add accounts here")
            new_name = st.text_input("New account name")
            new_id = st.text_input("New account ID")

            if st.button("Add account"):
                if new_name and new_id:
                    accounts.append({
                        "name": new_name,
                        "id": new_id
                    })

        with col1:
            st.write("accounts to compare")
            selected_accounts = st.multiselect(
                "What accounts do you want to compare", accounts,
                format_func=lambda acc: f"{acc['name']} ({acc['id']})",
                key="selected_accounts_compare_"
            )
        
        # You can't compare with 1 account!
        if len(selected_accounts) >= 2:

            for account in selected_accounts:
                if isinstance(account, dict):
                    account_id = account["id"]
                    account_name = account["name"]
                    player_data = data_per_account(account_id, account_name)

                if player_data != None:
                    selected_rows.append(player_data)
        
        else:
            st.info("Choose 2 accounts at least")
        
        if not selected_rows:
            st.warning("No data found for the selected filters")
            return
        
        compare_df = pd.DataFrame(selected_rows)
        compare_accounts_dashboard(compare_df)



def data_per_account(account_id, account_name):

    df = pd.DataFrame(load_match_rows(
        account_id, result_filter, matches_filter, peer_id,
        parse_filter, item, first_item, second_item
    ))

    if df.empty:
        st.warning(f"No matches found for the account '{account_name}'.")
        return None

    if hero_filter != "All":
        df = df[df["hero_localized_name"] == hero_filter]

    if df.empty:
        st.warning(f"No matches found for the account '{account_name}'.")
        return None
    
    else:
        player_name = df["personaname"].dropna().iloc[0]


        # Required data for each section
        # Overview data
        matches_count = len(df)
        avg_duration, duration_games = af.non_null_mean(df, "duration")
        avg_mins = avg_duration/60

        if hero_filter != all:
            most_played_hero = df['hero_localized_name'].mode().iloc[0]
            most_played_hero_count = (df['hero_localized_name']==most_played_hero).sum()
            hero_img, _ = af.hero_img_loader(heroes_dicts, most_played_hero)
        wins = df["win"].sum()
        win_rate = wins/matches_count*100
        df["start_time"] = pd.to_datetime(df["start_time"], unit="s")

        # Computing matches date
        earlies_match_date = df["start_time"].min()
        if pd.isna(earlies_match_date):
            earlies_match_date = "N/A"
        else:
            earlies_match_date = earlies_match_date.strftime("%Y-%m-%d")

        latest_match_date = df["start_time"].max()
        if pd.isna(latest_match_date):
            latest_match_date = "N/A"
        else:
            latest_match_date = latest_match_date.strftime("%Y-%m-%d")

        # Combat data
        avg_kda, kda_games = af.non_null_mean(df, "kda")
        max_kda = df["kda"].max()
        avg_kills, kills_games = af.non_null_mean(df, "kills")
        max_kills = df["kills"].max()
        avg_deaths, deaths_games = af.non_null_mean(df, "deaths")
        max_deaths = df["deaths"].max()
        avg_assists, assists_games = af.non_null_mean(df, "assists")
        max_assists = df["assists"].max()
        avg_hero_damage, hero_games = af.non_null_mean(df, "hero_damage")
        max_hero_damage = df["hero_damage"].max()
        avg_tower_damage, tower_games = af.non_null_mean(df, "tower_damage")
        max_tower_damage = df["tower_damage"].max()
        
        # Farming data
        avg_net_worth, worth_games = af.non_null_mean(df, "net_worth")
        max_net_worth = df["net_worth"].max()
        avg_gpm, gpm_games = af.non_null_mean(df, "gold_per_min")
        max_gpm = df["gold_per_min"].max()
        avg_xp, xp_games = af.non_null_mean(df, "xp_per_min")
        max_xp = df["xp_per_min"].max()
        avg_lh, lh_games = af.non_null_mean(df, "last_hits")
        max_lh = df["last_hits"].max()
        avg_denies, denies_games = af.non_null_mean(df, "denies")
        max_denies = df["denies"].max()

        # Benchmarks
        benchmarks = False
        if "pct_gold" in df.columns and not df["pct_gold"].isna().all():
            bench_count = len(df["pct_gold"])
            avg_gold_bm = df["pct_gold"].mean()*100
            avg_xp_bm = df["pct_xp"].mean()*100
            avg_hero_damage_bm = df["pct_hero_dmg"].mean()*100
            avg_tower_damage_bm = df["pct_tower_dmg"].mean()*100
            avg_lh_bm = df["pct_lh"].mean()*100
            avg_kills_bm = df["pct_kills"].mean()*100

            benchmarks = True

        player_rows = {
            "player": player_name,
            "account_name": account_name,
            "matches_count": matches_count,
            "average_duration": avg_mins,
            "duration_games": duration_games,
            "most_played_hero": most_played_hero,
            "most_played_hero_count": most_played_hero_count,
            "wins": wins,
            "win_rate": win_rate,
            "earliest_match_date": earlies_match_date,
            "latest_match_date": latest_match_date,
            "average_kda": avg_kda,
            "kda_games": kda_games,
            "max_kda": max_kda,
            "average_kills": avg_kills,
            "kills_games": kills_games,
            "max_kills": max_kills,
            "average_deaths": avg_deaths,
            "deaths_games": deaths_games,
            "max_deaths": max_deaths,
            "average_assists": avg_assists,
            "assists_games": assists_games,
            "max_assists": max_assists,
            "average_hero_damage": avg_hero_damage,
            "hero_damage_games": hero_games,
            "max_hero_damage": max_hero_damage,
            "average_tower_damage": avg_tower_damage,
            "tower_damage_games": tower_games,
            "max_tower_damage": max_tower_damage,
            "average_net_worth": avg_net_worth,
            "net_worth_games": worth_games,
            "max_net_worth": max_net_worth,
            "average_gpm": avg_gpm,
            "gpm_games": gpm_games,
            "max_gpm": max_gpm,
            "average_xpm": avg_xp,
            "xp_games": xp_games,
            "max_xpm": max_xp,
            "average_lh": avg_lh,
            "lh_games": lh_games,
            "max_lh": max_lh,
            "average_denies": avg_denies,
            "denies_games": denies_games,
            "max_denies": max_denies
        }

        if benchmarks:
            player_rows["benchmarks_games"] = bench_count
            player_rows["average_gold_bm"] = avg_gold_bm
            player_rows["average_xpm_bm"] = avg_xp_bm
            player_rows["average_hero_damage_bm"] = avg_hero_damage_bm
            player_rows["average_tower_damage_bm"] = avg_tower_damage_bm
            player_rows["average_lh_bm"] = avg_lh_bm
            player_rows["average_kills_bm"] = avg_kills_bm
            
    return player_rows

 

def singel_account_dashboard(account):
    account_id = int(account["id"])
    account_name = account["name"]

    df = pd.DataFrame(load_match_rows(
        account_id, result_filter, matches_filter, peer_id,
        parse_filter, item, first_item, second_item
    ))

    if df.empty:
        st.warning(f"No matches found for this account.{account_name}")
        return None

    if hero_filter != "All":
        df = df[df["hero_localized_name"] == hero_filter]

    if df.empty:
        st.warning(f"No matches found for this account.{account_name}")
        return None
    else:
        player_name = df["personaname"].dropna().iloc[0]

        cola, colb = st.columns([3,1])
        with cola:
            st.header(f"{player_name.title()} ({account_name})")

        if hero_filter != "All":
            with colb:
                chosen_hero_img,chosen_hero_icon = af.hero_img_loader(
                    heroes_dicts, hero_filter
                    )
                st.image(chosen_hero_img, width=150)
    

        # Required data for each section
        # Overview data
        matches_count = len(df)
        avg_duration, duration_games = af.non_null_mean(df, "duration")
        avg_mins = avg_duration/60
        most_played_hero = df['hero_localized_name'].mode().iloc[0]
        most_played_hero_count = (df['hero_localized_name']==most_played_hero).sum()
        hero_img, _ = af.hero_img_loader(heroes_dicts, most_played_hero)
        wins = df["win"].sum()
        win_rate = wins/matches_count*100
        df["start_time"] = pd.to_datetime(df["start_time"], unit="s")

        # Computing matches date
        earlies_match_date = df["start_time"].min()
        if pd.isna(earlies_match_date):
            earlies_match_date = "N/A"
        else:
            earlies_match_date = earlies_match_date.strftime("%Y-%m-%d")

        latest_match_date = df["start_time"].max()
        if pd.isna(latest_match_date):
            latest_match_date = "N/A"
        else:
            latest_match_date = latest_match_date.strftime("%Y-%m-%d")

        # Combat data
        avg_kda, kda_games = af.non_null_mean(df, "kda")
        max_kda = df["kda"].max()
        avg_kills, kills_games = af.non_null_mean(df, "kills")
        max_kills = df["kills"].max()
        avg_deaths, deaths_games = af.non_null_mean(df, "deaths")
        max_deaths = df["deaths"].max()
        avg_assists, assists_games = af.non_null_mean(df, "assists")
        max_assists = df["assists"].max()
        avg_hero_damage, hero_games = af.non_null_mean(df, "hero_damage")
        max_hero_damage = df["hero_damage"].max()
        avg_tower_damage, tower_games = af.non_null_mean(df, "tower_damage")
        max_tower_damage = df["tower_damage"].max()
        
        # Farming data
        avg_net_worth, worth_games = af.non_null_mean(df, "net_worth")
        max_net_worth = df["net_worth"].max()
        avg_gpm, gpm_games = af.non_null_mean(df, "gold_per_min")
        max_gpm = df["gold_per_min"].max()
        avg_xp, xp_games = af.non_null_mean(df, "xp_per_min")
        max_xp = df["xp_per_min"].max()
        avg_lh, lh_games = af.non_null_mean(df, "last_hits")
        max_lh = df["last_hits"].max()
        avg_denies, denies_games = af.non_null_mean(df, "denies")
        max_denies = df["denies"].max()

        # Benchmarks
        benchmarks = False
        if "pct_gold" in df.columns and not df["pct_gold"].isna().all():
            avg_gold_bm = df["pct_gold"].mean()*100
            avg_xp_bm = df["pct_xp"].mean()*100
            avg_hero_damage_bm = df["pct_hero_dmg"].mean()*100
            avg_tower_damage_bm = df["pct_tower_dmg"].mean()*100
            avg_lh_bm = df["pct_lh"].mean()*100
            avg_kills_bm = df["pct_kills"].mean()*100

            benchmarks = True

    # Different tabs for different stats
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Farming", "Combat", "Benchmarks"])
    
    # Overview section
    with tab1:
        st.subheader("Overview")

        col1, col2, right_group_1 = st.columns([1, 1, 2])
        col1.metric("Analyzed Matches", matches_count)
        col2.metric("Win rate", f"{win_rate:.1f}%")
        with right_group_1:
            with st.container(border=True):
                col3, col4 = st.columns(2)
                col3.metric("Earliest match date", earlies_match_date)
                col4.metric("Latest match date", latest_match_date)

        col5, col6, right_group_2 = st.columns([1, 1, 2])
        col5.metric("Average game duration", f"{avg_mins:.0f}")
        col6.metric("Number of wins", wins)

        if hero_filter == "All":
            with right_group_2:
                with st.container(border=True):
                    col7, col8 = st.columns(2)
                    if hero_img == None:
                        col7.metric("Most played hero", most_played_hero)
                    else:
                        with col7:
                            st.image(hero_img)
                    col8.metric("Number of matches", most_played_hero_count)
                    st.caption("Most played hero")
        
        st.divider()
        st.header("Charts")

        st.subheader("Played heroes distribution")
        heroes_distribution = (
            df.groupby("hero_localized_name")
            .agg(
                Games=("hero_localized_name", "count"),
                **{"Win Rate (%)": ("win", lambda wins: wins.mean() * 100)}
            )
            .reset_index()
            .rename(columns={"hero_localized_name": "Hero"})
            .sort_values("Games", ascending=False)
        )
        hero_order = heroes_distribution["Hero"].tolist()
        heroes_distribution_chart = heroes_distribution.melt(
            id_vars="Hero",
            value_vars=["Games", "Win Rate (%)"],
            var_name="Metric",
            value_name="Value"
        )

        chart = (
            alt.Chart(heroes_distribution_chart)
            .mark_bar()
            .encode(
                x=alt.X("Hero:N", sort=hero_order, title="Hero"),
                xOffset=alt.XOffset("Metric:N"),
                y=alt.Y("Value:Q", title="Games / Win Rate (%)"),
                color=alt.Color("Metric:N", title="Metric"),
                tooltip=[
                    alt.Tooltip("Hero:N"),
                    alt.Tooltip("Metric:N"),
                    alt.Tooltip("Value:Q", format=".1f"),
                ],
            )
        )
        st.altair_chart(
            chart,
            use_container_width=True
        )

        st.subheader("Rolling win rate")
        win_rate_chart_df = df.sort_values("start_time").copy()
        win_rate_chart_df["Rolling Win Rate (%)"] = (
            win_rate_chart_df["win"]
            .rolling(20, min_periods=1)
            .mean() * 100
        )
        rolling_win_chart = (
            alt.Chart(win_rate_chart_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("start_time:T", title="Match date"),
                y=alt.Y(
                    "Rolling Win Rate (%):Q",
                    title="Rolling Win Rate (%)",
                    scale=alt.Scale(domain=[0, 100])
                ),
                tooltip=[
                    alt.Tooltip("match_id:N", title="Match ID"),
                    alt.Tooltip("hero_localized_name:N", title="Hero"),
                    alt.Tooltip("Rolling Win Rate (%):Q", format=".1f"),
                ],
            )
        )
        st.altair_chart(
            rolling_win_chart,
            use_container_width=True
        )
        
        st.divider()

    with tab2:

        # Farming stats
        st.subheader("Farming")
            
        col9, col10, col11, col12 = st.columns(4)
        col9.metric("Average denies", f"{avg_denies:.0f}")
        col10.metric("Highest denies", f"{max_denies:.0f}")
        col11.metric("Average last hits", f"{avg_lh:.0f}")
        col12.metric("Highes last hits", f"{max_lh:.0f}")

        col13, col14, col15, col16 = st.columns(4)
        col13.metric("Average Net Worth", f"{avg_net_worth:.0f}")
        col14.metric("Highest networth", f"{max_net_worth:.0f}")
        col15.metric("Average GPM", f"{avg_gpm:.0f}")
        col16.metric("Highest GPM", f"{max_gpm:.0f}")

        col17, col18, cole1, cole2 = st.columns(4)
        col17.metric("Average XPM", f"{avg_xp:.0f}")
        col18.metric("Highest XPM", f"{max_xp:.0f}")

        st.divider()
        st.header("Charts")

        st.subheader("GPM and XPM over time")
        farming_chart_df = (
            df.sort_values("start_time")[
                ["start_time", "match_id", "hero_localized_name",
                "gold_per_min", "xp_per_min"]
            ]
            .melt(
                id_vars=["start_time", "match_id", "hero_localized_name"],
                value_vars=["gold_per_min", "xp_per_min"],
                var_name="Metric",
                value_name="Value"
            )
        )
        farming_chart = (
            alt.Chart(farming_chart_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("start_time:T", title="Match date"),
                y=alt.Y("Value:Q", title="Value"),
                color=alt.Color("Metric:N", title="Metric"),
                tooltip=[
                    alt.Tooltip("match_id:N", title="Match ID"),
                    alt.Tooltip("hero_localized_name:N", title="Hero"),
                    alt.Tooltip("Metric:N"),
                    alt.Tooltip("Value:Q", format=".0f"),
                ],
            )
        )
        st.altair_chart(
            farming_chart,
            use_container_width=True
        )


    with tab3:
        # Combat stats
        st.subheader("Combat")

        col19, col20, col21, col22 = st.columns(4)
        col19.metric("Average KDA", f"{avg_kda:.2f}")
        col20.metric("Highest KDA", f"{max_kda:.2f}")
        col21.metric("Average kills", f"{avg_kills:.0f}")
        col22.metric("Highest kills", f"{max_kills:.0f}")

        col23, col24, col25, col26 = st.columns(4)
        col23.metric("Average deaths", f"{avg_deaths:.0f}")
        col24.metric("Highest deaths", f"{max_deaths}")
        col25.metric("Average assists", f"{avg_assists:.0f}")
        col26.metric("Highest assists", f"{max_assists:.0f}")

        col27, col28, col29, col30 = st.columns(4)
        col27.metric("Average hero damage", f"{avg_hero_damage:.0f}")
        col28.metric("Highest hero damage", f"{max_hero_damage:.0f}")
        col29.metric("Average Tower Damage", f"{avg_tower_damage:.0f}")
        col30.metric("Highest tower_damage", f"{max_tower_damage:.0f}")

        st.divider()
        st.header("Charts")

        st.subheader("KDA over time")
        kda_chart_df = df.sort_values("start_time").copy()
        kda_chart_df["Rolling KDA"] = (
            kda_chart_df["kda"]
            .rolling(10, min_periods=1)
            .mean()
        )
        kda_chart_df = kda_chart_df.melt(
            id_vars=["start_time", "match_id", "hero_localized_name"],
            value_vars=["kda", "Rolling KDA"],
            var_name="Metric",
            value_name="Value"
        )
        kda_chart = (
            alt.Chart(kda_chart_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("start_time:T", title="Match date"),
                y=alt.Y("Value:Q", title="KDA"),
                color=alt.Color("Metric:N", title="Metric"),
                tooltip=[
                    alt.Tooltip("match_id:N", title="Match ID"),
                    alt.Tooltip("hero_localized_name:N", title="Hero"),
                    alt.Tooltip("Metric:N"),
                    alt.Tooltip("Value:Q", format=".2f"),
                ],
            )
        )
        st.altair_chart(
            kda_chart,
            use_container_width=True
        )

        st.subheader("Hero damage vs net worth")
        damage_networth_chart = (
            alt.Chart(df)
            .mark_circle(size=80, opacity=0.75)
            .encode(
                x=alt.X("net_worth:Q", title="Net Worth"),
                y=alt.Y("hero_damage:Q", title="Hero Damage"),
                color=alt.Color("win:N", title="Win"),
                tooltip=[
                    alt.Tooltip("match_id:N", title="Match ID"),
                    alt.Tooltip("hero_localized_name:N", title="Hero"),
                    alt.Tooltip("kda:Q", title="KDA", format=".2f"),
                    alt.Tooltip("net_worth:Q", title="Net Worth", format=".0f"),
                    alt.Tooltip("hero_damage:Q", title="Hero Damage", format=".0f"),
                    alt.Tooltip("win:N", title="Win"),
                ],
            )
        )
        st.altair_chart(
            damage_networth_chart,
            use_container_width=True
        )

        if hero_filter == "All":
            st.subheader("KDA distribution by hero")
            kda_boxplot = (
                alt.Chart(df)
                .mark_boxplot()
                .encode(
                    x=alt.X(
                        "hero_localized_name:N",
                        sort="-y",
                        title="Hero"
                    ),
                    y=alt.Y("kda:Q", title="KDA"),
                    tooltip=[
                        alt.Tooltip("hero_localized_name:N", title="Hero"),
                    ],
                )
            )
            st.altair_chart(
                kda_boxplot,
                use_container_width=True
            )
    

    with tab4:
        # Benchmarks
        st.subheader("Benchmarks")

        if benchmarks == True:
            col31, col32, col33, col34 = st.columns(4)
            col31.metric("GPM", f"{avg_gold_bm:.2f}%")
            col32.metric("XPM", f"{avg_xp_bm:.2f}%")
            col33.metric("Hero damage", f"{avg_hero_damage_bm:.2f}%")
            col34.metric("Tower damage", f"{avg_tower_damage_bm:.2f}%")

            col35, col36, col37, col38 = st.columns(4)
            col35.metric("lh", f"{avg_lh_bm:.2f}%")
            col36.metric("Kills", f"{avg_kills_bm:.2f}%")

            st.divider()
            st.header("Charts")

            st.subheader("Average benchmark percentiles")
            benchmark_chart_df = pd.DataFrame([
                {"Metric": "GPM", "Percentile": avg_gold_bm},
                {"Metric": "XPM", "Percentile": avg_xp_bm},
                {"Metric": "Last Hits", "Percentile": avg_lh_bm},
                {"Metric": "Kills", "Percentile": avg_kills_bm},
                {"Metric": "Hero Damage", "Percentile": avg_hero_damage_bm},
                {"Metric": "Tower Damage", "Percentile": avg_tower_damage_bm},
            ])
            benchmark_chart = (
                alt.Chart(benchmark_chart_df)
                .mark_bar()
                .encode(
                    x=alt.X("Metric:N", sort=None, title="Metric"),
                    y=alt.Y(
                        "Percentile:Q",
                        title="Percentile",
                        scale=alt.Scale(domain=[0, 100])
                    ),
                    color=alt.Color("Metric:N", legend=None),
                    tooltip=[
                        alt.Tooltip("Metric:N"),
                        alt.Tooltip("Percentile:Q", format=".1f"),
                    ],
                )
            )
            st.altair_chart(
                benchmark_chart,
                use_container_width=True
            )
        else:
            st.info("No benchmarks data available for this hero.") 
    

# The compare accounts dashboard
def compare_accounts_dashboard(compare_df):

    st.header ("Accounts Comparison")

    st.subheader("Data-frame")
    st.dataframe(compare_df, use_container_width=True)

    # Overview
    st.subheader("Overview")
    comparison_charts.overview_charts(compare_df)

    st.divider()

    # Combat charts including (KDA, kills, assists, deaths, tower damage and hero damage)
    st.subheader("Combat")
    comparison_charts.kills_deaths_assists_charts(compare_df)
    comparison_charts.hero_tower_damage_chart(compare_df)

    # Farming charts
    st.subheader("Farming charts")
    comparison_charts.lh_denies_net_worth_charts(compare_df)
    comparison_charts.gpm_xpm_charts(compare_df)

    # Benchmarks charts
    st.subheader("Benchmarks chart")
    comparison_charts.bench_charts(compare_df)


data_loader(compare, accounts)
