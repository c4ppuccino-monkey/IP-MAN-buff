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

if "account_flash" in st.session_state:
    flash_type, flash_message = st.session_state.pop("account_flash")
    if flash_type == "success":
        st.success(flash_message)
    elif flash_type == "warning":
        st.warning(flash_message)

accounts = am.load_accounts()

st.subheader("Saved accounts")

if accounts:
    st.dataframe(accounts, use_container_width=True, hide_index=True)
else:
    st.info("No saved accounts yet.")

cola, colb = st.columns(2)
with cola:
    with st.form("add_account_form"):
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
                st.session_state["account_flash"] = (
                    "success",
                    "Account added.",
                )
                st.rerun()

with colb:
    if accounts:
        account_to_remove = st.selectbox(
            "Accounts to remove",
            accounts,
            format_func=lambda acc: f"{acc['name']} ({acc['id']})"
        )

        if st.button("Remove"):
            removed = am.remove_account(account_to_remove["id"])

            if removed:
                st.session_state["account_flash"] = (
                    "success",
                    "Account removed.",
                )
                st.rerun()
            else:
                st.warning("Account was not found.")
    else:
        st.info("Add an account before removing one.")

col1, col2, col3 = st.columns([1,1,2])

with col1:
    fetch_matches = st.button("Fetch new matches")

with col2:
    st.write("Fetch all new matches for the saved accounts")

if fetch_matches:
    conn, cur = table.create_database()

    with st.status("Fetching new matches...", expanded=True) as status:

        progress_text = st.empty()
        progress_bar = st.progress(0)
        total_new = 0

        fetch_results = []

        for i, account in enumerate(accounts):
            account_id = account["id"]
            account_name = account["name"]

            # Fetch and select matches to ingest
            all_matches = opendota_client.fetch_matches(account_id)

            known_matches = ingestion.check_match_id(cur)
            all_matches_ids = ingestion.get_match_id(all_matches)
            new_ids = ingestion.new_ids(known_matches, all_matches_ids)

            popul.populate_base_table(all_matches, account_id, cur, conn)

            total_new += len(new_ids)
            progress_bar.progress((i+1)/len(accounts))

            fetch_results.append({
                "account_name": account_name,
                "account_id": account_id,
                "new_matches_count": len(new_ids),
                "new_match_ids": new_ids
            })

        status.update(
            label=f"Done. {total_new} new matches found",
            state="complete",
            expanded=False
        )

    st.session_state["last_fetch_results"] = fetch_results

if "last_fetch_results" in st.session_state:
    with st.expander("Last fetch details"):
        for result in st.session_state["last_fetch_results"]:
            st.write(
                f"{result['account_name']} ({result['account_id']}): "
                f"{result['new_matches_count']} new matches"
            )

            if result["new_match_ids"]:
                st.write(result["new_match_ids"])
