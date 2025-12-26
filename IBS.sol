// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract IceGodsSystem is ERC20 {
    // The Master Vault that receives the 1% Revenue
    address public constant vault = 0x7D7A4820355E8597e089BEeB15cEa308cEf3eda3;
    
    constructor() ERC20("Ice Gods System", "IBS") {
        // Minting the 30 Billion Supply to the Architect
        _mint(msg.sender, 30_000_000_000 * 10**18);
    }

    /**
     * @dev Hook that is called before any transfer of tokens. 
     * This includes minting and burning.
     */
    function _update(address from, address to, uint256 amount) internal override {
        // Exclude the owner and the vault from paying tax to ensure liquidity moves smoothly
        if (from != owner() && to != owner() && from != vault && to != vault) {
            uint256 fee = amount / 100; // 1% Tax calculation
            super._update(from, vault, fee);
            super._update(from, to, amount - fee);
        } else {
            super._update(from, to, amount);
        }
    }
}
