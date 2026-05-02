import os
import json


# Loading/Creating a JSON that contains saved account IDs
# and names/titles
def load_accounts():
    """Load account IDs from a JSON file."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            accounts = data.get("accounts", [])
            accounts = sorted(accounts, key=lambda acc: acc["name"].lower())
            return accounts
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading account IDs: {e}")
        return []  
    
    except json.JSONDecodeError as e:
        print(f"Unexpected error: {e}")
        return []


def save_accounts(accounts_list):
    """Save account IDs to a JSON file."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"accounts": accounts_list}, f, indent=4)
            print(f"Account IDs saved successfully to {ACCOUNTS_FILE}")
    
    except IOError as e:
        print(f"Error saving account IDs: {e}")


def add_account(accounts_list):
    """Add a new account ID to the list and save it."""
    account = {}
    account_id = input(
        "Enter the Dota 2 account ID to ingest data for: "
        ).strip()
    
    for existing_account in accounts_list:
        if existing_account["id"] == account_id:
            print(f"Account ID {account_id} already exists.")
            return
        
    account_name = input(
        "Enter a name for the account (e.g, 'pussy_destroyer'): "
        ).strip().lower()
    account = {"name": account_name, "id": account_id}
    
    accounts_list.append(account)
    save_accounts(accounts_list)
    print(f"Account ID {account} added successfully.")


def remove_account(account_id):
    """Remove an account ID from the list and save it."""
    accounts_list = load_accounts()
    if account_id not in accounts_list:
        print(f"Account ID {account_id} not found.")
        return
    
    accounts_list.remove(account_id)
    save_accounts(accounts_list)
    print(f"Account ID {account_id} removed successfully.")


def choose_account():
    accounts_list = load_accounts()

    while True:
        
        if not accounts_list:
            print(
                "No accounts found. Please add an account"
                )
            add_account(accounts_list)
            accounts_list = load_accounts()  # Reload accounts after adding
            continue

        print("Choose an account")
        for i, account in enumerate(accounts_list, start=1):
            print(f"{i}. {account['name']} (ID: {account['id']})")
        print("A. Add a new account ID")

        choice = input("your choice: ").strip().upper()

        if choice == "A":
            add_account(accounts_list)
            accounts_list = load_accounts()  # Reload accounts after adding
            continue

        if choice.isdigit():
            index = int(choice) - 1
            if 0<= index <len(accounts_list):
                return accounts_list[index]
            
        print("Invalid choice. Please try again.")


# Account ids only as integers
def get_accounts_ids(accounts):
    ids = []
    for a in accounts:
        id = a["id"]
        ids.append(id)
    
    return ids