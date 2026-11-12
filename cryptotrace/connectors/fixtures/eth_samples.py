"""Deterministic sample Ethereum blockchain payloads for offline testing and demo mode."""

# Sample Ethereum Addresses
ETH_SAMPLE_ADDRESS_1 = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Target Seed EOA
ETH_SAMPLE_ADDRESS_2 = "0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5"  # Counterparty EOA
ETH_SAMPLE_ADDRESS_3 = "0x28C6c06298d514Db089934071355E5743bf21d60"  # Exchange / Binance Deposit
ETH_SAMPLE_ADDRESS_4 = "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE"  # Hop 3 address
ETH_USDT_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"     # USDT Contract
ETH_UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D" # Uniswap Router

# Ethereum Transaction 1: Native ETH Transfer (Hop 1: Address 1 -> Address 2)
ETH_SAMPLE_TX_1 = {
    "blockNumber": "0x12d6870",  # 19753072
    "timeStamp": "1707800000",
    "hash": "0x4b78901234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    "nonce": "12",
    "blockHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    "transactionIndex": "45",
    "from": ETH_SAMPLE_ADDRESS_1.lower(),
    "to": ETH_SAMPLE_ADDRESS_2.lower(),
    "value": "2500000000000000000",  # 2.5 ETH in Wei
    "gas": "21000",
    "gasPrice": "32000000000",  # 32 Gwei
    "isError": "0",
    "txreceipt_status": "1",
    "input": "0x",
    "contractAddress": "",
    "cumulativeGasUsed": "3412091",
    "gasUsed": "21000",
    "confirmations": "1420",
    "tokenTransfers": [],
}

# Ethereum Transaction 2: ERC-20 USDT Transfer (Hop 2: Address 2 -> Address 3)
ETH_SAMPLE_TX_2 = {
    "blockNumber": "0x12d68f0",  # 19753200
    "timeStamp": "1707802400",
    "hash": "0x5c8901234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
    "nonce": "4",
    "blockHash": "0xbcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890a",
    "transactionIndex": "12",
    "from": ETH_SAMPLE_ADDRESS_2.lower(),
    "to": ETH_USDT_CONTRACT.lower(),
    "value": "0",
    "gas": "65000",
    "gasPrice": "28000000000",
    "isError": "0",
    "txreceipt_status": "1",
    # transfer(address to, uint256 value) selector: a9059cbb
    "input": f"0xa9059cbb000000000000000000000000{ETH_SAMPLE_ADDRESS_3[2:].lower()}000000000000000000000000000000000000000000000000000000012a05f200",
    "contractAddress": "",
    "gasUsed": "48231",
    "confirmations": "1292",
    "tokenTransfers": [
        {
            "token_address": ETH_USDT_CONTRACT.lower(),
            "token_name": "Tether USD",
            "token_symbol": "USDT",
            "token_decimals": 6,
            "from_address": ETH_SAMPLE_ADDRESS_2.lower(),
            "to_address": ETH_SAMPLE_ADDRESS_3.lower(),
            "raw_value": "5000000000",  # 5,000 USDT (6 decimals)
            "amount": "5000.000000",
            "log_index": 2,
        }
    ],
}

# Ethereum Transaction 3: Hop 3 from Address 3 -> Address 4
ETH_SAMPLE_TX_3 = {
    "blockNumber": "0x12d6990",  # 19753360
    "timeStamp": "1707805600",
    "hash": "0x6d901234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd",
    "nonce": "89",
    "blockHash": "0xcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
    "transactionIndex": "9",
    "from": ETH_SAMPLE_ADDRESS_3.lower(),
    "to": ETH_SAMPLE_ADDRESS_4.lower(),
    "value": "1800000000000000000",  # 1.8 ETH
    "gas": "21000",
    "gasPrice": "30000000000",
    "isError": "0",
    "txreceipt_status": "1",
    "input": "0x",
    "contractAddress": "",
    "gasUsed": "21000",
    "confirmations": "1132",
    "tokenTransfers": [],
}

ETH_FIXTURE_DATABASE = {
    ETH_SAMPLE_ADDRESS_1.lower(): {
        "address": ETH_SAMPLE_ADDRESS_1.lower(),
        "balance_wei": "14500000000000000000",  # 14.5 ETH
        "tx_count": 14,
        "is_contract": False,
        "transactions": [ETH_SAMPLE_TX_1],
    },
    ETH_SAMPLE_ADDRESS_2.lower(): {
        "address": ETH_SAMPLE_ADDRESS_2.lower(),
        "balance_wei": "3200000000000000000",  # 3.2 ETH
        "tx_count": 8,
        "is_contract": False,
        "transactions": [ETH_SAMPLE_TX_1, ETH_SAMPLE_TX_2],
    },
    ETH_SAMPLE_ADDRESS_3.lower(): {
        "address": ETH_SAMPLE_ADDRESS_3.lower(),
        "balance_wei": "580000000000000000000",  # 580 ETH
        "tx_count": 1205,
        "is_contract": False,
        "transactions": [ETH_SAMPLE_TX_2, ETH_SAMPLE_TX_3],
    },
    ETH_SAMPLE_ADDRESS_4.lower(): {
        "address": ETH_SAMPLE_ADDRESS_4.lower(),
        "balance_wei": "1800000000000000000",
        "tx_count": 1,
        "is_contract": False,
        "transactions": [ETH_SAMPLE_TX_3],
    },
}

ETH_TRANSACTIONS_BY_HASH = {
    ETH_SAMPLE_TX_1["hash"]: ETH_SAMPLE_TX_1,
    ETH_SAMPLE_TX_2["hash"]: ETH_SAMPLE_TX_2,
    ETH_SAMPLE_TX_3["hash"]: ETH_SAMPLE_TX_3,
}
