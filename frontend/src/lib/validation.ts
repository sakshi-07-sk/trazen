import { BlockchainNetwork, TargetType } from "@/types/investigation";

export interface ValidationResult {
  isValid: boolean;
  error?: string;
  detectedType?: TargetType;
  detectedNetwork?: BlockchainNetwork;
}

export function validateCryptoInput(
  input: string,
  expectedNetwork?: BlockchainNetwork,
  expectedType?: TargetType
): ValidationResult {
  const trimmed = input.trim();
  if (!trimmed) {
    return { isValid: false, error: "Input address or transaction hash is required" };
  }

  // Ethereum Address: 0x followed by 40 hex chars
  const isEthAddress = /^0x[a-fA-F0-9]{40}$/.test(trimmed);
  // Ethereum / EVM Tx Hash: 0x followed by 64 hex chars
  const isEthTx = /^0x[a-fA-F0-9]{64}$/.test(trimmed);
  // Bitcoin Bech32 Address: bc1 followed by 25 to 62 alphanumeric chars
  const isBtcBech32 = /^bc1[a-zA-HJ-NP-Z0-9]{25,62}$/i.test(trimmed);
  // Bitcoin Legacy (1...) or Script (3...) Address
  const isBtcLegacyOrScript = /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(trimmed);
  const isBtcAddress = isBtcBech32 || isBtcLegacyOrScript;
  // Bitcoin Tx Hash: 64 hex characters (without 0x prefix)
  const isBtcTx = /^[a-fA-F0-9]{64}$/.test(trimmed) && !trimmed.startsWith("0x");

  let detectedNetwork: BlockchainNetwork | undefined;
  let detectedType: TargetType | undefined;

  if (isEthAddress) {
    detectedNetwork = "ETH";
    detectedType = "address";
  } else if (isEthTx) {
    detectedNetwork = "ETH";
    detectedType = "transaction";
  } else if (isBtcAddress) {
    detectedNetwork = "BTC";
    detectedType = "address";
  } else if (isBtcTx) {
    detectedNetwork = "BTC";
    detectedType = "transaction";
  }

  if (!detectedNetwork || !detectedType) {
    return {
      isValid: false,
      error: "Invalid format. Expected a valid Ethereum address (0x...), Ethereum tx hash (0x...), Bitcoin address (1..., 3..., bc1...), or 64-char Bitcoin tx hash.",
    };
  }

  if (expectedNetwork && detectedNetwork !== expectedNetwork) {
    return {
      isValid: false,
      error: `Input format corresponds to ${detectedNetwork}, but selected network is ${expectedNetwork}.`,
      detectedNetwork,
      detectedType,
    };
  }

  if (expectedType && detectedType !== expectedType) {
    return {
      isValid: false,
      error: `Input format corresponds to a ${detectedType}, but selected target type is ${expectedType}.`,
      detectedNetwork,
      detectedType,
    };
  }

  return {
    isValid: true,
    detectedNetwork,
    detectedType,
  };
}
