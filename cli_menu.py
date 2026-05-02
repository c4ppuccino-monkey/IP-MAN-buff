
import ingestion
from logging_config import get_logger
import opendota_client
import time

logger = get_logger(__name__)


def menu(cur, conn, heroes_map, abilities_map):
    
    while True:
    
        print("Welcome to IP-man's shithole.")
        print("1. Ingest new matches")
        print("2. Parse matches")
        print("3. Go back\n")

        choice = input("Enter your choice: ")
        print()

        if choice == "1":
            menu_ingestion(cur, conn, heroes_map, abilities_map)

        elif choice == "2":
            menu_parse(cur, conn)

        elif choice == "3":
            print("Exiting...")
            break


        else:
            print("Invalid choice. Please try again.")


def menu_ingestion(cur, conn, heroes_map, abilities_map):
    print("Ingesting new matches...")

    limit = limit_refiner(
        "How many matches do you want to ingest?: ")
    print()

    version = version_refiner()
    
    unparsed_pop = choice_refiner(
        "Has the unparsed data been populated " \
        "yet. 0 if no, 1 if yes, " \
        "leave blank if it doesn't matter: "
    )
    parsed_pop = choice_refiner(
        "Has the parsed_data been populated " \
        "yet. 0 if no, 1 if yes, " \
        "leave blank if it doesn't matter: "
    )

    select_matches_ids = ingestion.select_matches(cur, limit, 
                                                  unparsed_pop, parsed_pop, 
                                                  version)
    
    logger.info(
        "Selected matches for ingestion. selected=%d",
        len(select_matches_ids),
            )

    ingestion.main_pop(
                    cur, conn, select_matches_ids, unparsed_pop,
                    heroes_map, abilities_map)
    logger.info(
                "Ingestion run finished successfully")
    

def menu_parse(cur, conn):
    print("Parsing matches...\n")

    limit = limit_refiner(
        "How many matches do you want to parse?: ")

    
    version = version_refiner()
    
    unparsed_pop = choice_refiner(
        "Has the unparsed data been populated " \
        "yet. 0 if no, 1 if yes, " \
        "leave empty if it doesn't matter: "
    )
    parsed_pop = choice_refiner(
        "Has the parsed_data been populated " \
        "yet. 0 if no, 1 if yes, " \
        "leave empty if it doesn't matter: "
    )
    
    select_matches_ids = ingestion.select_matches(cur, limit, 
                                                  unparsed_pop, parsed_pop,
                                                  version)
    
    logger.info(
        "Selected matches for parsing. selected=%d",
        len(select_matches_ids),
            )
    
    for match_id in select_matches_ids:
        success, message = opendota_client.parse_request(match_id)
        if success:
            logger.info("Parse request successful. match_id=%s", match_id)
            opendota_client.increment_match_retries(cur, conn, match_id)

        else:
            logger.error(
                "Parse request failed. match_id=%s message=%s", 
                match_id, message)

        time.sleep(1)  # Sleep to avoid hitting API rate limits


# Refine choice so that it returns integer or None
# For parsed and unparsed pops
def choice_refiner(prompt):

    while True:

        choice = input(prompt).strip().lower()

        if choice == "0":
            return 0

        elif choice == "1":
            return 1
        
        elif choice == "":
            return None
        else:
            print("Invalid choice. Please try again.")
            continue


# Refine the version inputs so it takes
# Null for no version in DB,
# Integer for the version
# and None to remove it as a filter
def version_refiner():

    while True:

        version = input(
        "Filter by version integer," \
        "'null' for null versions " \
        "leave empty to ignore: "
        ).strip().lower()

        if version == "null":
            return version
        
        elif isinstance(version, str) and version.isdigit():
            version = int(version)
            return version
        
        elif version == "":
            print("No filters applied")
            return None
        
        else:
            print("Ivalid option, please choose one " \
            "of the forementioned ones")
            continue


# Asking for the number of matches
# to parse or ingest
def limit_refiner(prompt):
    
    while True:
        limit = input(prompt)

        if limit.isdigit() and int(limit)>0:
            return int(limit)
        else:
            print('Invalid choice, please use a' \
            'number larger than 0')