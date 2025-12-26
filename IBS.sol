// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract IceBoysToken is ERC20, Ownable {
    uint256 public constant TOTAL_SUPPLY = 30_000_000_000 * 10**18;
    address public makerWallet = 0x7D7A4820355E8597e089BEeB15cEa308cEf3eda3;
    constructor() ERC20("ICEBOYS", "IBS") Ownable(msg.sender) {
        _mint(msg.sender, TOTAL_SUPPLY);
    }
    function _update(address from, address to, uint256 value) internal override {
        if (from != owner() && to != owner() && from != makerWallet && to != makerWallet) {
            uint256 fee = value / 100; // 1% Fee Weapon
            super._update(from, makerWallet, fee);
            super._update(from, to, value - fee);
        } else {
            super._update(from, to, value);
        }
    }
}
