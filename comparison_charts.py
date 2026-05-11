import altair as alt
import streamlit as st


# Overview comparison including (win rate, number of matches and average match duration)
def overview_charts(compare_df):

    # Win-rate and average duration with duration games used 
    # to point out any discrepencies between different parameters 
    # later on, such as total number of games vs analyzed matches with duration
    # not null in them
    overview_metrics = compare_df.melt(
        id_vars=["player", "duration_games"],
        value_vars=["win_rate", "average_duration"],
        var_name="Metric",
        value_name="Value"
    )

    player_order = (
        compare_df
        .sort_values("win_rate", ascending=False)["player"]
        .tolist()
    )

    overview_chart = (
        alt.Chart(overview_metrics)
        .mark_bar()
        .encode(
            x=alt.X("player:N", title="Account", sort=player_order),
            xOffset="Metric:N",
            y=alt.Y("Value:Q"),
            color=alt.Color("Metric:N"),
            tooltip=[
                "player", 
                "Metric", 
                alt.Tooltip("Value:Q", format=".2f"),
                # Number of matches analyzed present as a tooltip 
                # when hovering over the bar
                alt.Tooltip("duration_games:Q", title="matches_analyzed")
                ]
        )
        .properties(
            title = "Win rate & Duration"
        )
    )

    # Number of games bar chart
    game_count_chart = (
        alt.Chart(compare_df)
        .mark_bar(size=20)
        .encode(
            x=alt.X("player:N", title="Account", sort="-y"),
            y=alt.Y("matches_count:Q", title="Matches Count"),
            tooltip=[
                "player",
                alt.Tooltip("matches_count:Q", title="Matches analyzed")
            ]
        )
        .properties(
            title="Total number of matches"
        )
    )
    
    st.altair_chart(overview_chart, use_container_width=True)
    st.altair_chart(game_count_chart)


# Kills, deaths and assists bar chart
def kills_deaths_assists_charts(compare_df):

    combat_metrics = compare_df.melt(
        id_vars=["player", "deaths_games", "kills_games", "assists_games", "kda_games"],
        value_vars=["average_deaths", "average_kills", "average_assists", "average_kda"],
        var_name="Metric",
        value_name="Value"
    )

    # Adding the number of analyzed matches for each
    # metric to be included in the chart
    def combat_parameters(row):
        if row["Metric"] == "average_kills":
            return row["kills_games"]
        elif row["Metric"] == "average_deaths":
            return row ["deaths_games"]
        elif row["Metric"] == "average_assists":
            return row ["assists_games"]
        else:
            return row["kda_games"]
        
    combat_metrics["parameter_matches"] = combat_metrics.apply(
        combat_parameters,
        axis=1
    )

    col1, col2 = st.columns([0.5,3.5])

    with col1:
        selected_metric = st.selectbox(
            "Chosen metrics",
            ["All", "KDA", "Kills", "Deaths", "Assists"],
            key="kda_metric_filter"
        )
    
    if selected_metric == "Kills":
        combat_metrics = combat_metrics[
            combat_metrics["Metric"] == "average_kills"
            ]
    elif selected_metric == "Deaths":
        combat_metrics = combat_metrics[
            combat_metrics["Metric"] == "average_deaths"
        ]
    elif selected_metric == "Assists":
        combat_metrics = combat_metrics[
            combat_metrics["Metric"] == "average_assists"
        ]
    elif selected_metric == "KDA":
        combat_metrics = combat_metrics[
            combat_metrics["Metric"] == "average_kda"
        ]

    player_order = (
        combat_metrics
        .groupby("player")["Value"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    combat_chart = (
        alt.Chart(combat_metrics)
        .mark_bar()
        .encode(
            x=alt.X("player:N", title="Account", sort=player_order),
            xOffset="Metric:N",
            y=alt.Y("Value:Q"),
            color=alt.Color("Metric:N"),
            tooltip=[
                "player", 
                "Metric", 
                alt.Tooltip("Value:Q", format=".2f"),
                alt.Tooltip("parameter_matches:Q", title="Matches analyzed")]
        )
        .properties(
            title="Average KDA, Kills, Deaths & Assists"
        )
    )
    with col2:
        st.altair_chart(combat_chart, use_container_width=True)


# Hero and tower damage bar charts
def hero_tower_damage_chart(compare_df):

    damage_metrics = compare_df.melt(
        id_vars=["player", "tower_damage_games", "hero_damage_games"],
        value_vars=["average_tower_damage", "average_hero_damage"],
        var_name="Metric",
        value_name="Value"
    )

    # Adding the number of analyzed matches for each
    # metric to be included in the chart
    def damage_parameters(row):
        if row["Metric"] == "average_hero_damage":
            return row["hero_damage_games"]
        elif row["Metric"] == "average_tower_damage":
            return row["tower_damage_games"]
        
    damage_metrics["parameter_matches"] = damage_metrics.apply(
        damage_parameters,
        axis=1
    )

    col1, col2 = st.columns([0.5, 3.5])

    with col1:
        selected_damage_metric = st.selectbox(
            "Damage_metric",
            ["Both", "Tower Damage", "Hero Damage"],
            key="damage_metric_filter"
        )

    if selected_damage_metric == "Tower Damage":
        damage_metrics = damage_metrics[
            damage_metrics["Metric"] == "average_tower_damage"
        ]

    elif selected_damage_metric == "Hero Damage":
        damage_metrics = damage_metrics[
            damage_metrics["Metric"] == "average_hero_damage"
        ]

    player_order = (
        damage_metrics
        .groupby("player")["Value"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
)
    
    damage_chart = (alt.Chart(damage_metrics)
    .mark_bar()
    .encode(
        x=alt.X(
            "player:N", 
            title="Account",
            sort=player_order
            ),
        xOffset="Metric:N",
        y=alt.Y("Value:Q"),
        color=alt.Color("Metric:N"),
        tooltip=[
            "player",
            "Metric",
            alt.Tooltip("Value:Q", format=".0f"),
            alt.Tooltip("parameter_matches:Q", title="Matches analyzed")
        ]
    )
    .properties(title="Average damage")
)
    with col2:
        st.altair_chart(damage_chart, use_container_width=True)


# Last hits, Denies and Networth charts
def lh_denies_net_worth_charts(compare_df):

    farming_metrics = compare_df.melt(
        id_vars=[
            "player", 
            "lh_games", 
            "denies_games", 
            "net_worth_games",
            ],
        value_vars=[
            "average_lh",
            "average_denies",
            "average_net_worth"
        ],
        var_name="Metric",
        value_name="Value"
    )

    def farming_parameters(row):
        if row["Metric"] == "average_lh":
            return row["lh_games"]
        elif row["Metric"] == "average_denies":
            return row["denies_games"]
        elif row["Metric"] == "average_net_worth":
            return row["net_worth_games"]
    
    farming_metrics["parameter_matches"] = farming_metrics.apply(
        farming_parameters,
        axis=1
    )

    col1, col2 = st.columns([0.5,3.5])

    with col1:
        selected_metrics = st.selectbox(
            "Selected metrics",
            ["All", "Last Hits", "Denies", "Networth"],
            key="filtered_farming_metrics"
        )
    
    if selected_metrics == "Last Hits":
        farming_metrics = farming_metrics[
            farming_metrics["Metric"] == "average_lh"
            ]
    elif selected_metrics == "Denies":
        farming_metrics = farming_metrics[
            farming_metrics["Metric"] == "average_denies"
            ]
    elif selected_metrics == "Networth":
        farming_metrics = farming_metrics[
            farming_metrics["Metric"] == "average_net_worth"
            ]
    
    # Sorting data in DESC order
    player_order = (
        farming_metrics
        .groupby("player")["Value"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
)
    
    farming_chart = (alt.Chart(farming_metrics)
        .mark_bar()
        .encode(
            x=alt.X(
                "player:N",
                title="Account",
                sort=player_order
                ),
            xOffset="Metric:N",
            y=alt.Y("Value:Q"),
            color=alt.Color("Metric:N"),
            tooltip=[
                "player",
                "Metric",
                alt.Tooltip("Value:Q", format=".0f"),
                alt.Tooltip("parameter_matches:Q", title="Matches analyzed")
            ]
        )
        .properties(title="Average LH, Denies and Networth")
    )

    with col2:
        st.altair_chart(farming_chart, use_container_width=True)


# GPM and XPM charts
def gpm_xpm_charts(compare_df):

    gpm_xpm_metrics = compare_df.melt(
        id_vars=["player", "gpm_games", "xp_games"],
        value_vars=["average_gpm", "average_xpm"],
        var_name="Metric",
        value_name="Value"
    )

    def gpm_xpm_parameters(row):
        if row["Metric"] == "average_gpm":
            return row["gpm_games"]
        else:
            return row["xp_games"]
    
    gpm_xpm_metrics["parameter_matches"] = gpm_xpm_metrics.apply(
        gpm_xpm_parameters,
        axis=1
    )

    col1, col2 = st.columns([0.5,3.5])

    with col1:
        selected_metrics = st.selectbox(
            "Selected metrics",
            ["All", "GPM", "XPM"],
            key="gpm_xpm_metrics_filter"
            )
    
    if selected_metrics == "GPM":
        gpm_xpm_metrics = gpm_xpm_metrics[
            gpm_xpm_metrics["Metric"] == "average_gpm"
            ]
    elif selected_metrics == "XPM":
        gpm_xpm_metrics = gpm_xpm_metrics[
            gpm_xpm_metrics["Metric"] == "average_xpm"
        ]
    
    player_order = (
        gpm_xpm_metrics
        .groupby("player")["Value"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    gpm_xpm_chart = (alt.Chart(gpm_xpm_metrics)
        .mark_bar()
        .encode(
            x=alt.X(
                "player:N",
                title="Account",
                sort=player_order
            ),
            xOffset="Metric:N",
            y=alt.Y("Value:Q"),
            color=alt.Color("Metric:N"),
            tooltip=[
                "player",
                "Metric",
                alt.Tooltip("Value:Q", format=".0f"),
                alt.Tooltip("parameter_matches:Q", title="Matches analyzed")
            ]
        )
        .properties(title="Average GPM and XPM")
    )

    with col2:
        st.altair_chart(gpm_xpm_chart, use_container_width=True)


# Benchmarks charts
def bench_charts(compare_df):

    required_cols = [
        "player",
        "benchmarks_games",
        "average_gold_bm",
        "average_xpm_bm",
        "average_lh_bm",
        "average_tower_damage_bm",
        "average_hero_damage_bm",
        "average_kills_bm"
    ]

    missing_cols = []

    for col in required_cols:
        if col not in compare_df.columns:
            missing_cols.append(col)
    
    if missing_cols:
        st.info("No benchmarks data available for selcted filters")
        return
    
    benchmarks_metrics = compare_df.melt(
        id_vars=["player", "benchmarks_games"],
        value_vars=[
            "average_gold_bm",
            "average_xpm_bm",
            "average_hero_damage_bm",
            "average_tower_damage_bm",
            "average_lh_bm",
            "average_kills_bm"
            ],
        var_name="Metric",
        value_name="Value"
    )

    if benchmarks_metrics.empty:
        st.info("No benchmarks data available for the selcted filters")
        return

    col1, col2 = st.columns([0.5,3.5])

    with col1:
        selected_metrics = st.selectbox(
            "Selected Metrics",
            [
                "All", "Average LH", "Average Kills", 
                "Average Hero Damage", "Average Tower Damage",
                "Average GPM", "Average XPM"],
                key="benchmarks_metrics_filter"
        )
    
    if selected_metrics == "Average LH":
        benchmarks_metrics = benchmarks_metrics[
            benchmarks_metrics["Metric"] == "average_lh_bm"
        ]
    elif selected_metrics == "Average Kills":
        benchmarks_metrics = benchmarks_metrics[
            benchmarks_metrics["Metric"] == "average_kills_bm"
        ]
    elif selected_metrics == "Average Hero Damage":
        benchmarks_metrics = benchmarks_metrics[
            benchmarks_metrics["Metric"] == "average_hero_damage_bm"
        ]
    elif selected_metrics == "Average Tower Damage":
        benchmarks_metrics = benchmarks_metrics[
            benchmarks_metrics["Metric"] == "average_tower_damage_bm"
        ]
    elif selected_metrics == "Average GPM":
        benchmarks_metrics = benchmarks_metrics[
            benchmarks_metrics["Metric"] == "average_gold_bm"
        ]
    elif selected_metrics == "Average XPM":
        benchmarks_metrics = benchmarks_metrics[
            benchmarks_metrics["Metric"] == "average_xpm_bm"
        ]

    player_order = (
        benchmarks_metrics
        .groupby("player")["Value"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    benchmarks_chart = (alt.Chart(benchmarks_metrics)
    .mark_bar()
    .encode(
        x=alt.X("player:N", title="Account", sort=player_order),
        xOffset="Metric:N",
        y=alt.Y("Value:Q", title= "Percentile"),
        color=alt.Color("Metric:N"),
        tooltip=[
            "player",
            "Metric",
            alt.Tooltip("Value:Q", format=".2f"),
            alt.Tooltip("benchmarks_games:Q", title="Matches analyzed")
        ]
        )
        .properties(title="Benchmarks")
    )

    with col2:
        st.altair_chart(benchmarks_chart, use_container_width=True)