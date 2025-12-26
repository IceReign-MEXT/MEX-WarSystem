// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract IceGodsSystem is ERC20 {
    address public vault;
    constructor(address _vault) ERC20("Ice Gods System", "IBS") {
        vault = _vault;
        _mint(msg.sender, 30_000_000_000 * 10**18);
    }
    function _update(address from, address to, uint256 amount) internal override {
        uint256 tax = amount / 100; // 1% Tax
        super._update(from, vault, tax);
        super._update(from, to, amount - tax);
    }
}
