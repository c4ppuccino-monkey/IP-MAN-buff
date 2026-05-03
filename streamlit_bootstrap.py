"""Streamlit startup checks shared by app pages."""

import streamlit as st

import maps
import opendota_client


def require_dotaconstants():
    """Show a setup action instead of crashing when dotaconstants are missing."""
    missing_files = maps.missing_constant_files()
    if not missing_files:
        return

    st.error("Dota constants are missing.")
    st.write(
        "This app needs OpenDota's local `dotaconstants` files before it can "
        "show heroes, items, abilities, and match details."
    )

    with st.expander("Missing files"):
        st.write(missing_files)

    if st.button("Download Dota constants", type="primary"):
        try:
            with st.spinner("Downloading Dota constants from OpenDota..."):
                opendota_client.sync_repo()

            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Dota constants downloaded.")
            st.rerun()

        except Exception as exc:
            st.error(f"Could not download Dota constants: {exc}")

    st.stop()
