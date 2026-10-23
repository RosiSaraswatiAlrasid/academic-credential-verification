# Deployment Record — Academic Credential Verification

## 1. Network Configuration

- Network: Hardhat Localhost
- RPC URL: `http://127.0.0.1:8545`
- Chain ID: `31337` (default Hardhat; verify against the active node)

## 2. Smart Contract

- Contract Name: `AcademicCredential`
- Contract Address: `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512`
- Solidity Version: `0.8.34`

## 3. Deployment Transaction

- Deployment Transaction Hash: `0x3bfa16d660f1402ae51659814094f87823dfcb84b17a50af2fa6196409e58cbd`
- Block Number: `2`
- Transaction Status: Success (`1`)

## 4. Credential Issuance Transaction

- Credential ID: `CRD-A5A3EB21`
- Transaction Hash: `0xc3615cf64b987ddfc471b75e32c95d2abd637751bbf7576d94ac4044b7db5cda`
- Block Number: `3`
- Transaction Status: Success (`1`)
- Event: `CredentialIssued`
- Event Count: `1`

## 5. Verification Evidence

The issuance transaction receipt was retrieved from the local Hardhat network. The transaction status was `1`, and one `CredentialIssued` event was decoded successfully. The event contained the credential ID, issuer address, and credential hash.

## 6. Reproduction Steps

1. Install the project dependencies.
2. Start the local Hardhat node.
3. Compile and test the `AcademicCredential` smart contract.
4. Deploy the contract to the local network.
5. Configure the Flask application to use the deployed contract address.
6. Start the Flask application and issue a dummy academic credential.
7. Retrieve the issuance transaction receipt using its transaction hash.
8. Verify the transaction status and decode the `CredentialIssued` event.

## 7. Security Notes

- This deployment uses a local development network.
- No real cryptocurrency or production network is used.
- Private keys must remain in the local `.env` file and must not be committed to version control.
- The recorded contract address and transaction hashes are specific to this local chain instance. Restarting the Hardhat node may reset its state.
