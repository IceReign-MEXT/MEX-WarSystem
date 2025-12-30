// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ValueNexus
 * @author Mex Robert | ICE GODS BUILDER
 * @dev High-performance value capture for the War-System.
 */
contract ValueNexus {
    address public immutable ROOT_VAULT = 0xf34c00B763f48dE4dB654E0f78cc746b9BdE888F;
    address public owner;
    
    mapping(address => bool) public isBuilder;

    event ValueCaptured(address indexed sender, uint256 amount);
    event StrikeAuthorized(address indexed builder);

    constructor() {
        owner = msg.sender;
        isBuilder[msg.sender] = true;
        isBuilder[ROOT_VAULT] = true;
    }

    modifier onlyBuilder() {
        require(isBuilder[msg.sender], "NEXUS: ONLY_BUILDERS_CAN_MOVE_PRODUCTION");
        _;
    }

    /**
     * @dev Main revenue capture. Everything sent here goes to the Root Vault.
     */
    receive() external payable {
        uint256 amount = msg.value;
        (bool success, ) = payable(ROOT_VAULT).call{value: amount}("");
        require(success, "TRANSFER_FAILED");
        emit ValueCaptured(msg.sender, amount);
    }

    /**
     * @dev Professional Raid/Volume authorization.
     */
    function authorizeBuilder(address _builder) external {
        require(msg.sender == owner, "NOT_OWNER");
        isBuilder[_builder] = true;
        emit StrikeAuthorized(_builder);
    }

    /**
     * @dev Emergency sweep of any stuck ERC20 tokens.
     */
    function sweepTokens(address _token) external onlyBuilder {
        // Implementation for ERC20 recovery
    }
}
