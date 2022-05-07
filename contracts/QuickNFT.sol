// SPDX-License-Identifier: MIT
pragma solidity 0.8.6;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";


contract TestNFT is Ownable, ERC721("Test NFT", "TEST") {

    function mint(address _to, uint256 _tokenId, string calldata _uri) external onlyOwner {
        super._safeMint(_to, _tokenId);
    }

}