import streamlit as st
import time

import accounts_management as am
import db_tables as table
import db_population as popul
import ingestion
import opendota_client
import maps


st.set_page_config(layout="wide")

st.title("Database Management")


@st.cache_resource
def load_ingestion_maps():
    return maps.load_heroes(), maps.load_hero_abilities()


accounts = am.load_accounts()

st.subheader("Saved accounts")

if accounts:
    st.dataframe(accounts, use_container_width=True, hide_index=True)
else:
    st.info("No saved accounts yet.")

cola, colb = st.columns(2, border=True)
with cola:
    with st.form("add_account_form", border=False):
        new_name = st.text_input("Account name")
        new_id = st.text_input("Account ID")
        submitted = st.form_submit_button("Add account")

    if submitted:
        if not new_name or not new_id:
            st.warning("Account name and ID are required")
        else:
            existing_ids = set()
            for acc in accounts:
                id = acc["id"]
                existing_ids.add(str(id))
            
            if str(new_id) in existing_ids:
                st.warning("That account ID is already saved")
            else:
                accounts.append({
                    "name": new_name.strip(),
                    "id": str(new_id).strip(),
                })
                am.save_accounts(accounts)
                st.success("Account added.")
                st.rerun()

with colb:
    if accounts:
        accounts_to_remove = st.multiselect(
            "Accounts to remove",
            accounts,
            format_func=lambda acc: f"{acc['name']} ({acc['id']})"
        )

        if st.button("Remove", disabled=not accounts_to_remove):
            removed_count = 0
            for account in accounts_to_remove:
                if am.remove_account(account["id"]):
                    removed_count += 1

            if removed_count:
                st.success(f"Removed {removed_count} account(s).")
                st.rerun()
            else:
                st.warning("No selected accounts were found.")
    else:
        st.info("Add an account before removing one.")

st.divider()

st.subheader("Update match history")

if not accounts:
    st.info("Add an account first, then you can update match history.")
else:
    selected_accounts = st.multiselect(
        "Accounts",
        accounts,
        default=accounts,
        format_func=lambda acc: f"{acc['name']} ({acc['id']})",
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        match_limit = st.number_input(
            "Matches per stage",
            min_value=1,
            max_value=500,
            value=50,
            step=10,
        )

    with col2:
        include_detailed = st.toggle(
            "Include detailed match data",
            value=True,
            help=(
                "Slower, but fills fights, damage, purchases, wards, "
                "timings, and other parsed stats when OpenDota has them."
            ),
        )

    with col3:
        request_parsing = st.toggle(
            "Request missing details",
            value=False,
            help=(
                "Ask OpenDota to parse matches that have basic data but "
                "do not have detailed stats yet."
            ),
        )

    selected_account_ids = [str(account["id"]) for account in selected_accounts]

    with st.expander("Advanced queue preview"):
        conn, cur = table.create_database()
        counts = ingestion.queue_counts_for_accounts(cur, selected_account_ids)

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        metric_col1.metric("Known matches", counts["known"])
        metric_col2.metric("Need basic details", counts["needs_basic"])
        metric_col3.metric("Need detailed stats", counts["needs_details"])
        metric_col4.metric("Complete", counts["complete"])

        preview_unparsed = st.selectbox(
            "Basic details filter",
            ["Needs basic details", "Basic details done", "Any"],
        )
        preview_parsed = st.selectbox(
            "Detailed stats filter",
            ["Needs detailed stats", "Detailed stats done", "Any"],
        )

        preview_unparsed_value = {
            "Needs basic details": 0,
            "Basic details done": 1,
            "Any": None,
        }[preview_unparsed]
        preview_parsed_value = {
            "Needs detailed stats": 0,
            "Detailed stats done": 1,
            "Any": None,
        }[preview_parsed]

        preview_ids = ingestion.select_matches_for_accounts(
            cur,
            selected_account_ids,
            limit=10,
            unparsed_pop=preview_unparsed_value,
            parsed_pop=preview_parsed_value,
        )

        if preview_ids:
            st.write(preview_ids)
        else:
            st.caption("No matches in that queue.")

        conn.close()

    update_matches = st.button(
        "Update match history",
        type="primary",
        disabled=not selected_accounts,
    )

    if update_matches:
        conn, cur = table.create_database()
        heroes_map, abilities_map = load_ingestion_maps()
        fetch_results = []
        total_new = 0

        with st.status("Updating match history...", expanded=True) as status:
            fetch_progress = st.progress(0, text="Fetching latest match lists")

            for i, account in enumerate(selected_accounts):
                account_id = str(account["id"])
                account_name = account["name"]

                all_matches = opendota_client.fetch_matches(account_id)
                known_matches = ingestion.check_match_id(cur)
                all_match_ids = ingestion.get_match_id(all_matches)
                new_ids = ingestion.new_ids(known_matches, all_match_ids)

                popul.populate_base_table(all_matches, account_id, cur, conn)

                total_new += len(new_ids)
                fetch_results.append({
                    "account_name": account_name,
                    "account_id": account_id,
                    "new_matches_count": len(new_ids),
                    "new_match_ids": new_ids,
                })

                fetch_progress.progress(
                    (i + 1) / len(selected_accounts),
                    text=f"Fetched matches for {account_name}",
                )

            basic_ids = ingestion.select_matches_for_accounts(
                cur,
                selected_account_ids,
                limit=int(match_limit),
                unparsed_pop=0,
                parsed_pop=None,
            )

            basic_progress = st.progress(0, text="Loading basic match details")

            def basic_progress_callback(done, total, match_id):
                if total:
                    basic_progress.progress(
                        done / total,
                        text=f"Loading basic details for match {match_id}",
                    )

            ingestion.main_pop(
                cur,
                conn,
                basic_ids,
                unparsed_pop=0,
                heroes_map=heroes_map,
                abilities_map=abilities_map,
                include_parsed=False,
                progress_callback=basic_progress_callback,
            )
            basic_progress.progress(1.0, text="Basic match details done")

            detailed_ids = []
            if include_detailed:
                detailed_ids = ingestion.select_matches_for_accounts(
                    cur,
                    selected_account_ids,
                    limit=int(match_limit),
                    unparsed_pop=1,
                    parsed_pop=0,
                )

                detailed_progress = st.progress(
                    0,
                    text="Loading detailed parsed stats",
                )

                def detailed_progress_callback(done, total, match_id):
                    if total:
                        detailed_progress.progress(
                            done / total,
                            text=f"Loading detailed stats for match {match_id}",
                        )

                ingestion.main_pop(
                    cur,
                    conn,
                    detailed_ids,
                    unparsed_pop=1,
                    heroes_map=heroes_map,
                    abilities_map=abilities_map,
                    include_parsed=True,
                    progress_callback=detailed_progress_callback,
                )
                detailed_progress.progress(1.0, text="Detailed stats done")

            parse_requests = []
            if request_parsing:
                parse_ids = ingestion.select_matches_for_accounts(
                    cur,
                    selected_account_ids,
                    limit=int(match_limit),
                    unparsed_pop=1,
                    parsed_pop=0,
                )

                parse_progress = st.progress(0, text="Requesting missing details")
                for i, match_id in enumerate(parse_ids):
                    success, message = opendota_client.parse_request(match_id)
                    if success:
                        opendota_client.increment_match_retries(cur, conn, match_id)

                    parse_requests.append({
                        "match_id": match_id,
                        "success": success,
                        "message": message,
                    })
                    parse_progress.progress(
                        (i + 1) / len(parse_ids),
                        text=f"Requested details for match {match_id}",
                    )
                    time.sleep(1)

                if not parse_ids:
                    parse_progress.progress(1.0, text="No missing details to request")

            status.update(
                label=(
                    f"Done. {total_new} new matches found, "
                    f"{len(basic_ids)} basic updates, "
                    f"{len(detailed_ids)} detailed updates."
                ),
                state="complete",
                expanded=False,
            )

        st.session_state["last_ingestion_results"] = {
            "fetch_results": fetch_results,
            "basic_count": len(basic_ids),
            "detailed_count": len(detailed_ids),
            "parse_requests": parse_requests,
        }
        st.cache_data.clear()
        conn.close()

if "last_ingestion_results" in st.session_state:
    results = st.session_state["last_ingestion_results"]
    with st.expander("Last update details"):
        for result in results["fetch_results"]:
            st.write(
                f"{result['account_name']} ({result['account_id']}): "
                f"{result['new_matches_count']} new matches"
            )

            if result["new_match_ids"]:
                st.write(result["new_match_ids"])

        st.write(f"Basic detail updates: {results['basic_count']}")
        st.write(f"Detailed stat updates: {results['detailed_count']}")

        if results["parse_requests"]:
            st.write("Parse requests")
            st.dataframe(results["parse_requests"], hide_index=True)
