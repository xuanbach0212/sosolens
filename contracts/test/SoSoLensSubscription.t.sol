// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Test} from "lib/forge-std/src/Test.sol";
import {SoSoLensSubscription} from "../src/SoSoLensSubscription.sol";
import {ERC20} from "lib/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";

contract MockUSDC is ERC20 {
    constructor() ERC20("USD Coin", "USDC") {}

    function decimals() public pure override returns (uint8) {
        return 6;
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}

contract SoSoLensSubscriptionTest is Test {
    SoSoLensSubscription sub;
    MockUSDC usdc;

    address owner = address(this);
    address alice = makeAddr("alice");
    address bob = makeAddr("bob");

    uint256 constant PRICE = 5_000_000;
    uint256 constant DURATION = 30 days;

    function setUp() public {
        usdc = new MockUSDC();
        sub = new SoSoLensSubscription(address(usdc));
    }

    function _fund(address who, uint256 amount) internal {
        usdc.mint(who, amount);
        vm.prank(who);
        usdc.approve(address(sub), amount);
    }

    function test_subscribe_setsExpiry() public {
        _fund(alice, PRICE);
        vm.prank(alice);
        sub.subscribe();

        assertEq(sub.subscriptionExpiry(alice), block.timestamp + DURATION);
        assertTrue(sub.isSubscribed(alice));
    }

    function test_subscribe_stacksDuration() public {
        _fund(alice, PRICE * 2);
        vm.prank(alice);
        sub.subscribe();

        uint256 firstExpiry = sub.subscriptionExpiry(alice);

        vm.prank(alice);
        sub.subscribe();

        assertEq(sub.subscriptionExpiry(alice), firstExpiry + DURATION);
    }

    function test_subscribe_emitsEvent() public {
        _fund(alice, PRICE);
        vm.expectEmit(true, false, false, true);
        emit SoSoLensSubscription.Subscribed(alice, block.timestamp + DURATION);
        vm.prank(alice);
        sub.subscribe();
    }

    function test_isSubscribed_falseAfterExpiry() public {
        _fund(alice, PRICE);
        vm.prank(alice);
        sub.subscribe();

        vm.warp(block.timestamp + DURATION + 1);
        assertFalse(sub.isSubscribed(alice));
    }

    function test_isSubscribed_falseWithNoSubscription() public view {
        assertFalse(sub.isSubscribed(bob));
    }

    function test_withdraw_ownerDrainsBalance() public {
        _fund(alice, PRICE);
        vm.prank(alice);
        sub.subscribe();

        uint256 before = usdc.balanceOf(owner);
        sub.withdraw(owner);
        assertEq(usdc.balanceOf(owner), before + PRICE);
        assertEq(usdc.balanceOf(address(sub)), 0);
    }

    function test_withdraw_nonOwnerReverts() public {
        vm.prank(alice);
        vm.expectRevert(SoSoLensSubscription.NotOwner.selector);
        sub.withdraw(alice);
    }

    function test_subscribe_revertsWithoutApproval() public {
        usdc.mint(alice, PRICE);
        vm.prank(alice);
        vm.expectRevert();
        sub.subscribe();
    }
}
