"""Deterministic sample Bitcoin blockchain payloads for offline testing and demo mode."""

# Sample Bitcoin addresses
BTC_SAMPLE_ADDRESS_1 = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
BTC_SAMPLE_ADDRESS_2 = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
BTC_SAMPLE_ADDRESS_3 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
BTC_SAMPLE_ADDRESS_4 = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
BTC_SAMPLE_ADDRESS_5 = "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97"

# Bitcoin Transaction 1: Multi-input, Multi-output transaction (Hop 1)
# Consumes UTXOs from Address 1 and Address 4 -> Creates outputs to Address 2 and Address 3 (change)
BTC_SAMPLE_TX_1 = {
    "txid": "95d0a2736b04394cd16bc0b12bc1a851eb3a77ceb7c02c61ee1b474cb4532c1e",
    "version": 2,
    "locktime": 0,
    "size": 372,
    "weight": 861,
    "fee": 14200,
    "status": {
        "confirmed": True,
        "block_height": 830120,
        "block_hash": "00000000000000000001a4e17ef1bc2cd56037f37f382a89cbff7d99cb29e248",
        "block_time": 1707800000,
    },
    "vin": [
        {
            "txid": "7b0451ff7328bf58c06e00b84c0429f4b50c05df1363673ab1ff5733f3eb3c46",
            "vout": 0,
            "prevout": {
                "scriptpubkey": "0014a0f443e2e0e565983781289196b054238e55e8c1",
                "scriptpubkey_asm": "OP_0 OP_PUSHBYTES_20 a0f443e2e0e565983781289196b054238e55e8c1",
                "scriptpubkey_type": "v0_p2wpkh",
                "scriptpubkey_address": BTC_SAMPLE_ADDRESS_1,
                "value": 150000000,  # 1.5 BTC
            },
            "scriptsig": "",
            "sequence": 4294967295,
            "witness": [
                "304402206775079a4734898154e207921a971d6f1a80e123456789abcdef0123456789",
                "02a1633caf1297f081f8d3742990491ff602e932c841f48b04f118337b415fa508",
            ],
        },
        {
            "txid": "893c5443210abcedef0123456789abcdef0123456789abcdef0123456789abcdef",
            "vout": 1,
            "prevout": {
                "scriptpubkey": "a914a0f443e2e0e565983781289196b054238e55e8c187",
                "scriptpubkey_asm": "OP_HASH160 OP_PUSHBYTES_20 a0f443e2e0e565983781289196b054238e55e8c1 OP_EQUAL",
                "scriptpubkey_type": "p2sh",
                "scriptpubkey_address": BTC_SAMPLE_ADDRESS_4,
                "value": 250000000,  # 2.5 BTC
            },
            "scriptsig": "160014a0f443e2e0e565983781289196b054238e55e8c1",
            "sequence": 4294967295,
            "witness": [],
        },
    ],
    "vout": [
        {
            "scriptpubkey": "0014751e76e8199196d454941c45d1b3a323f1433bd6",
            "scriptpubkey_asm": "OP_0 OP_PUSHBYTES_20 751e76e8199196d454941c45d1b3a323f1433bd6",
            "scriptpubkey_type": "v0_p2wpkh",
            "scriptpubkey_address": BTC_SAMPLE_ADDRESS_2,
            "value": 320000000,  # 3.2 BTC
        },
        {
            "scriptpubkey": "76a91462e907b15cbf27d5425399ebf6f02f7d2067c60d88ac",
            "scriptpubkey_asm": "OP_DUP OP_HASH160 OP_PUSHBYTES_20 62e907b15cbf27d5425399ebf6f02f7d2067c60d OP_EQUALVERIFY OP_CHECKSIG",
            "scriptpubkey_type": "p2pkh",
            "scriptpubkey_address": BTC_SAMPLE_ADDRESS_3,
            "value": 79985800,  # 0.799858 BTC (change output)
        },
    ],
}

# Bitcoin Transaction 2: Hop 2 from Address 2 -> Address 5
BTC_SAMPLE_TX_2 = {
    "txid": "f8a023901b2c453890123abcdef890123456789abcdef0123456789abcdef012",
    "version": 2,
    "locktime": 0,
    "size": 222,
    "weight": 560,
    "fee": 9800,
    "status": {
        "confirmed": True,
        "block_height": 830150,
        "block_hash": "00000000000000000002b5f28ef2bc2cd56037f37f382a89cbff7d99cb30f359",
        "block_time": 1707803600,
    },
    "vin": [
        {
            "txid": "95d0a2736b04394cd16bc0b12bc1a851eb3a77ceb7c02c61ee1b474cb4532c1e",
            "vout": 0,
            "prevout": {
                "scriptpubkey": "0014751e76e8199196d454941c45d1b3a323f1433bd6",
                "scriptpubkey_address": BTC_SAMPLE_ADDRESS_2,
                "value": 320000000,
            },
            "sequence": 4294967295,
            "witness": ["sample_witness_sig"],
        }
    ],
    "vout": [
        {
            "scriptpubkey": "0020d0f443e2e0e565983781289196b054238e55e8c1d0f443e2e0e5659837812891",
            "scriptpubkey_address": BTC_SAMPLE_ADDRESS_5,
            "value": 319990200,  # 3.199902 BTC
        }
    ],
}

# Bitcoin Transaction 3: Hop 3 from Address 5 -> Address 1 (loop / dispersion)
BTC_SAMPLE_TX_3 = {
    "txid": "11223344556677889900aabbccddeeff00112233445566778899aabbccddeeff",
    "version": 2,
    "locktime": 0,
    "size": 225,
    "weight": 565,
    "fee": 8500,
    "status": {
        "confirmed": True,
        "block_height": 830180,
        "block_hash": "00000000000000000003c6f39ef3bc2cd56037f37f382a89cbff7d99cb41a460",
        "block_time": 1707807200,
    },
    "vin": [
        {
            "txid": "f8a023901b2c453890123abcdef890123456789abcdef0123456789abcdef012",
            "vout": 0,
            "prevout": {
                "scriptpubkey": "0020d0f443e2e0e565983781289196b054238e55e8c1d0f443e2e0e5659837812891",
                "scriptpubkey_address": BTC_SAMPLE_ADDRESS_5,
                "value": 319990200,
            },
            "sequence": 4294967295,
            "witness": ["sample_sig"],
        }
    ],
    "vout": [
        {
            "scriptpubkey": "0014a0f443e2e0e565983781289196b054238e55e8c1",
            "scriptpubkey_address": BTC_SAMPLE_ADDRESS_1,
            "value": 150000000,
        },
        {
            "scriptpubkey": "0014751e76e8199196d454941c45d1b3a323f1433bd6",
            "scriptpubkey_address": BTC_SAMPLE_ADDRESS_2,
            "value": 169981700,
        },
    ],
}

BTC_FIXTURE_DATABASE = {
    BTC_SAMPLE_ADDRESS_1: {
        "address": BTC_SAMPLE_ADDRESS_1,
        "chain_stats": {
            "funded_txo_count": 5,
            "funded_txo_sum": 450000000,
            "spent_txo_count": 3,
            "spent_txo_sum": 300000000,
            "tx_count": 6,
        },
        "mempool_stats": {
            "funded_txo_count": 0,
            "funded_txo_sum": 0,
            "spent_txo_count": 0,
            "spent_txo_sum": 0,
            "tx_count": 0,
        },
        "transactions": [BTC_SAMPLE_TX_1, BTC_SAMPLE_TX_3],
    },
    BTC_SAMPLE_ADDRESS_2: {
        "address": BTC_SAMPLE_ADDRESS_2,
        "chain_stats": {
            "funded_txo_count": 3,
            "funded_txo_sum": 489981700,
            "spent_txo_count": 1,
            "spent_txo_sum": 320000000,
            "tx_count": 3,
        },
        "mempool_stats": {"funded_txo_count": 0, "funded_txo_sum": 0, "spent_txo_count": 0, "spent_txo_sum": 0, "tx_count": 0},
        "transactions": [BTC_SAMPLE_TX_1, BTC_SAMPLE_TX_2, BTC_SAMPLE_TX_3],
    },
    BTC_SAMPLE_ADDRESS_5: {
        "address": BTC_SAMPLE_ADDRESS_5,
        "chain_stats": {
            "funded_txo_count": 1,
            "funded_txo_sum": 319990200,
            "spent_txo_count": 1,
            "spent_txo_sum": 319990200,
            "tx_count": 2,
        },
        "mempool_stats": {"funded_txo_count": 0, "funded_txo_sum": 0, "spent_txo_count": 0, "spent_txo_sum": 0, "tx_count": 0},
        "transactions": [BTC_SAMPLE_TX_2, BTC_SAMPLE_TX_3],
    },
}

BTC_TRANSACTIONS_BY_HASH = {
    BTC_SAMPLE_TX_1["txid"]: BTC_SAMPLE_TX_1,
    BTC_SAMPLE_TX_2["txid"]: BTC_SAMPLE_TX_2,
    BTC_SAMPLE_TX_3["txid"]: BTC_SAMPLE_TX_3,
}
