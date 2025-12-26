// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract IceGodsSystem is ERC20, Ownable {
    uint256 public constant TOTAL_SUPPLY = 30_000_000_000 * 10**18;
    uint256 public taxFee = 1; // 1% Revenue Tax
    address public vault;

    constructor(address _vault) ERC20("Ice Gods System", "IBS") Ownable(msg.sender) {
        vault = _vault;
        _mint(msg.sender, TOTAL_SUPPLY);
    }

    function _update(address from, address to, uint256 amount) internal virtual override {
        uint256 tax = (amount * taxFee) / 100;
        super._update(from, vault, tax);
        super._update(from, to, amount - tax);
    }
}
