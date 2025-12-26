// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract IceGodsSystem is ERC20 {
    address public vault = 0x7D7A4820355E8597e089BEeB15cEa308cEf3eda3;
    constructor() ERC20("Ice Gods System", "IBS") {
        _mint(msg.sender, 30_000_000_000 * 10**18);
    }
    function _update(address from, address to, uint256 amount) internal override {
        if (from != owner() && to != owner() && from != vault && to != vault) {
            uint256 fee = amount / 100; // 1% Tax
            super._update(from, vault, fee);
            super._update(from, to, amount - fee);
        } else {
            super._update(from, to, amount);
        }
    }
}
