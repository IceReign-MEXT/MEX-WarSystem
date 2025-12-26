// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract IceGodsSystem is ERC20, Ownable {
    address public vault = 0x7D7A4820355E8597e089BEeB15cEa308cEf3eda3;
    
    constructor() ERC20("Ice Gods System", "IBS") Ownable(msg.sender) {
        _mint(msg.sender, 30_000_000_000 * 10**18);
    }

    function _update(address from, address to, uint256 amount) internal override {
        // 2% War Tax: Doubles the treasury growth
        if (from != owner() && to != owner() && from != vault && to != vault) {
            uint256 fee = (amount * 2) / 100; 
            super._update(from, vault, fee);
            super._update(from, to, amount - fee);
        } else {
            super._update(from, to, amount);
        }
    }

    function setVault(address _newVault) external onlyOwner {
        vault = _newVault;
    }
}
