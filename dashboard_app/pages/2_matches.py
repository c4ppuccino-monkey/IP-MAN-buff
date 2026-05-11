import streamlit as st
import queries
import pandas as pd


match_id = st.number_input("LOL", min_value=0, step=1)

if match_id:
    conn = None

    try:
        match_id = int(match_id)

        conn = queries.get_connection()
        cur = conn.cursor()

        match_data = queries.full_match(cur, match_id)

        overview_row = match_data["overview"]
        players_row = match_data["players"]
        objectives_row = match_data["objectives"]
        tf_row = match_data["team_fights"]

        tab1, tab2, tab3 = st.tabs(["Overview", "items", "abilities"])

        overview_df = pd.DataFrame([dict(match_data["overview"])])

        with st.expander("Raw overview data"):
            st.dataframe(
            overview_df,
            use_container_width=True,
            hide_index=True
    )

    
    except Exception as e:
        print(f"There was an error {e}")
