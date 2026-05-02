import db_tables as table
import db_population as popul
import maps
import ingestion
import opendota_client
from logging_config import configure_logging, get_logger
import accounts_management as am
import cli_menu

accounts = am.load_accounts()
accounts_ids = am.get_accounts_ids(accounts)

# Load constant maps used for enrichment
heroes_map = maps.load_heroes()
abilities_map = maps.load_hero_abilities()
maps.load_items()
maps.load_ancients()
maps.load_aghs_desc()
maps.load_order_types()
maps.load_perma_buffs()
print("loaded maps")

def main():
    
    opendota_client.sync_repo()

    api_calls_remaining = 2000  # Number of free calls per day

    while True:
        """Run the full ingestion pipeline with structured logging."""


        debug = input("Enable debug mode? (y/n): ").lower() == "y"

        configure_logging(level="DEBUG" if debug else None)
        logger = get_logger(__name__)

        conn = None 

        try:
            # Create/open database connection
            conn, cur = table.create_database()
            print("created database connection")

            for account_id in accounts_ids:
                logger.info(
                    "Starting ingestion run. account_id=%s",
                    account_id)

                # Fetch and select matches to ingest
                all_matches = opendota_client.fetch_matches(account_id)

                known_matches = ingestion.check_match_id(cur)
                all_matches_ids = ingestion.get_match_id(all_matches)
                new_ids = ingestion.new_ids(known_matches, all_matches_ids)

                logger.info(
                    "Match discovery complete. known=%d fetched=%d new=%d",
                    len(known_matches),
                    len(all_matches_ids),
                    len(new_ids),
                )

                popul.populate_base_table(all_matches, account_id, cur, conn)
                print(f"{len(new_ids)} matches were added for {account_id}\n"
                      f"Account name: ")

            cli_menu.menu(cur, conn, heroes_map, abilities_map)

        except Exception:
            logger.exception(
                "Fatal error during ingestion run. account_id=%s", 
                account_id)
            raise
        finally:
            if conn is not None:
                conn.close()
                logger.info("Database connection closed.")
                print()


if __name__ == "__main__":
    main()
