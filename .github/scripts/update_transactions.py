import requests
import yaml
import os

def get_transactions(addresses):
    url = 'https://preprod.koios.rest/api/v1/address_txs'
    headers = {'accept': 'application/json', 'content-type': 'application/json'}
    data = {'_addresses': addresses}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def get_balance(addresses):
    url = 'https://preprod.koios.rest/api/v1/address_info'
    headers = {'accept': 'application/json', 'content-type': 'application/json'}
    data = {'_addresses': addresses}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def get_tx_info(tx_hashes):
    url = 'https://preprod.koios.rest/api/v1/tx_info'
    headers = {'accept': 'application/json', 'content-type': 'application/json'}
    data = {'_tx_hashes': tx_hashes}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def update_committee_markdown(file_path, transactions):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    try:
        tx_table_start = lines.index('| txid | epoch_no | block_height |\n')
        tx_table_end = lines.index('\n', tx_table_start + 1)
    except ValueError:
        # If the table header is not found, add it
        tx_table_start = len(lines)
        lines.append('\n## All Transactions\n\n')
        lines.append('| txid | epoch_no | block_height |\n')
        lines.append('| --- | --- | --- |\n')
        tx_table_end = len(lines)

    existing_txids = [line.split('|')[1].strip() for line in lines[tx_table_start + 2:tx_table_end]]

    new_lines = lines[:tx_table_end]
    for tx in transactions:
        if tx['tx_hash'] not in existing_txids:
            new_lines.append(f"| {tx['tx_hash']} | {tx['epoch_no']} | {tx['block_height']} |\n")
    new_lines.extend(lines[tx_table_end:])

    with open(file_path, 'w') as file:
        file.writelines(new_lines)

# go to the summary.md page and update the table there
def update_summary_markdown(file_path, addresses, balances):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    try:
        balance_table_start = lines.index('| address | balance |\n')
        balance_table_end = lines.index('\n', balance_table_start + 1)
    except ValueError:
        # If the table header is not found, add it
        balance_table_start = len(lines)
        lines.append('\n## Committee Address Balances\n\n')
        lines.append('| address | balance |\n')
        lines.append('| --- | --- |\n')
        balance_table_end = len(lines)

    new_lines = lines[:balance_table_end]
    for address, balance in zip(addresses, balances):
        new_lines.append(f"| {address} | {balance['balance']} |\n")
    new_lines.extend(lines[balance_table_end:])

    with open(file_path, 'w') as file:
        file.writelines(new_lines)


# Update committee pages

# Iterate through committee pages find addresses to monitor
addresses = []
for file_name in os.listdir('gitbook'):
    if file_name.endswith('committee.md'):
        with open(f'gitbook/{file_name}', 'r') as file:
            for line in file:
                if line.startswith('- `addr'):
                    addresses.append(line.strip().strip('- `'))

# Get balance for the addresses
balances = get_balance(addresses)

# Update the summary markdown file
update_summary_markdown('gitbook/summary.md', addresses, balances)

# Get transactions for the addresses
transactions = get_transactions(addresses)
tx_hashes = [tx['tx_hash'] for tx in transactions]
# For each transaction found, use the transaction info endpoint
tx_info = get_tx_info(tx_hashes)

for file_name in os.listdir('gitbook'):
    if file_name.endswith('committee.md'):
        update_committee_markdown(f'gitbook/{file_name}', tx_info)