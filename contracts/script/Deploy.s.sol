// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Script, console} from "lib/forge-std/src/Script.sol";
import {SoSoLensSubscription} from "../src/SoSoLensSubscription.sol";

// USDC on Base Sepolia (Circle official)
address constant USDC_BASE_SEPOLIA = 0x036CbD53842c5426634e7929541eC2318f3dCF7e;

contract Deploy is Script {
    function run() external {
        vm.startBroadcast();
        SoSoLensSubscription sub = new SoSoLensSubscription(USDC_BASE_SEPOLIA);
        console.log("SoSoLensSubscription deployed:", address(sub));
        vm.stopBroadcast();
    }
}
