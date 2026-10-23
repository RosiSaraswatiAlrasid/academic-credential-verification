
import { defineConfig } from "hardhat/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";
import hardhatNodeTestRunner from "@nomicfoundation/hardhat-node-test-runner";

export default defineConfig({
  plugins: [hardhatNodeTestRunner, hardhatEthers],
  solidity: {
    version: "0.8.34",
  },
});
