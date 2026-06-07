// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {IERC20} from "lib/openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";

/// @notice Monthly USDC subscription paywall for SoSoLens premium signals.
contract SoSoLensSubscription {
    IERC20 public immutable usdc;
    address public immutable owner;

    uint256 public constant PRICE = 5_000_000; // 5 USDC (6 decimals)
    uint256 public constant DURATION = 30 days;

    mapping(address => uint256) public subscriptionExpiry;

    event Subscribed(address indexed subscriber, uint256 newExpiry);
    event Withdrawn(address indexed to, uint256 amount);

    error NotOwner();
    error TransferFailed();
    error InvalidUSDC();
    error InvalidRecipient();

    constructor(address _usdc) {
        if (_usdc == address(0)) revert InvalidUSDC();
        usdc = IERC20(_usdc);
        owner = msg.sender;
    }

    /// @notice Pay 5 USDC to subscribe or extend by 30 days. Caller must approve first.
    function subscribe() external {
        if (!usdc.transferFrom(msg.sender, address(this), PRICE)) revert TransferFailed();

        uint256 current = subscriptionExpiry[msg.sender];
        uint256 base = current > block.timestamp ? current : block.timestamp;
        uint256 newExpiry = base + DURATION;
        subscriptionExpiry[msg.sender] = newExpiry;

        emit Subscribed(msg.sender, newExpiry);
    }

    /// @notice Returns true if `subscriber` has an active subscription.
    function isSubscribed(address subscriber) external view returns (bool) {
        return block.timestamp < subscriptionExpiry[subscriber];
    }

    /// @notice Owner withdraws all USDC to `to`.
    function withdraw(address to) external {
        if (msg.sender != owner) revert NotOwner();
        if (to == address(0)) revert InvalidRecipient();
        uint256 balance = usdc.balanceOf(address(this));
        if (!usdc.transfer(to, balance)) revert TransferFailed();
        emit Withdrawn(to, balance);
    }
}
