// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @author Victor Marin Felip
 *
 * @notice An implementation of a Dutch-style reverse Auction. Contract needs to be NFT approved to work.
 *
 */
contract DutchAuction is Ownable {

    using SafeMath for uint;

    IERC721 public nft;
    uint public nftId;

    address payable public seller;
    uint public startAt;
    uint public duration;
    uint public startingPrice;
    uint public reservePrice;
    bool public auctionGreenlit = false;

    // We only use this once but this way our intentions are super clear
    modifier contractIsApproved {
        require(address(this) == nft.getApproved(nftId), "Auction cannot be started. NFT owner has not approved this contract yet");
        _;
    }

    modifier auctionIsLive {
        require(auctionGreenlit, "Auction has not started yet!");
        require(block.timestamp < startAt + duration, "Auction has ended");
        _;
    }

    /**
     * @dev The auction needs to be instantiated, then the contract has to be approved at the NFT so it can transfer it to the winner, and then the auction must be started.
     * @param _startingPrice starting price of the auction.
     * @param _reservePrice reserve price of the auction. Must be less than _startingPrice, can be 0.
     * @param _durationSeconds auction duration in seconds, msut be 60 seconds at least.
     * @param _nft address of an ERC721 compatible contract.
     * @param _nftId Id of the token to be auctioned.
     */
    constructor(
        uint _startingPrice,
        uint _reservePrice,
        uint _durationSeconds,
        address _nft,
        uint _nftId
    ) public {
        // We make sure that there is enough time to buy, duration of at least one block
        // usually is between 12/14 seconds, but we're being extra sure with a minute
        // This will prevent many weird shenanigans
        require(_durationSeconds >= 60, "Auction duration must be at least a minute");
        require(_startingPrice > 0, "Starting price must be positive");
        require(_reservePrice < _startingPrice, "Reserve price must be less than starting price");

        seller = payable(msg.sender);
        startingPrice = _startingPrice;
        reservePrice = _reservePrice;
        duration = _durationSeconds;

        nft = IERC721(_nft);
        nftId = _nftId;
    }

    /**
     * @dev Starts the auction. The contract needs to be approved first at the NFT.
     */
    function startAuction() public onlyOwner contractIsApproved {
        require(auctionGreenlit == false, "Can't start an already started auction");
        startAt = block.timestamp;
        auctionGreenlit = true;
    }

    /**
     * @dev returns the current price based on block.timestamp and the constructor parameters.
     */
    function getPrice() public view auctionIsLive returns (uint) {
        // rate = (delta_Y) / (delta_X) -slope of a line- -always negative in our case-
        // we'll use the negative of delta_Y to get a positive rate so we don't stop using uint
        uint rate_pos = (startingPrice - reservePrice) / duration;
        // price = rate * elapsed_time + initial_price, but we have a positive rate
        // price - initial_price = rate * elapsed_time ->
        // initial_price - price = -1 * rate * elapsed_time, and we have basically -1 * rate so ->
        uint price_change_pos = rate_pos * (block.timestamp - startAt);
        uint price = startingPrice - price_change_pos;
        return price;
    }

    /**
     * @dev Attempts to buy the NFT. If enough ETH was sent with the transaction the NFT will be transferred to the sender.
     * Any extra ETH sent will be returned to the sender. The contract selfdestructs after the process. If not enough ETH
     * is sent to buy it at the current price it reverts and nothing happens. Auction needs to be live to work (started and not finished)
     */
    function buy() external payable auctionIsLive {
        uint price = getPrice();
        require(msg.value >= price, "Not enough ETH sent for purchase");
        // Sending the NFT to the buyer
        nft.transferFrom(seller, msg.sender, nftId);
        uint slack = msg.value - price;
        // Send back the extra eth that may have been sent to the buy function
        if (slack > 0) {
            payable(msg.sender).transfer(slack);
        }
        // And we render this unusable
        selfdestruct(seller);
    }

    /**
     * @dev Triggers selfdestruct. Only owner can call this function.
     */
    function destroyAuction() public onlyOwner {
        selfdestruct(seller);
    }

    /**
     * @dev Returns seconds since auction started.
     */
    function auctionAge() public view auctionIsLive returns(uint) {
        return block.timestamp - startAt;
    }
}