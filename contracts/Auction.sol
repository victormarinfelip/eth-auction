// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @author Victor Marin Felip
 *
 * @notice An implementation of a Dutch-style reverse Auction. Contract needs to be NFT approved to work.
 *
 */
contract DutchAuction is Ownable, Pausable {

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
    function startAuction() public whenNotPaused onlyOwner contractIsApproved {
        require(auctionGreenlit == false, "Can't start an already started auction");
        startAt = block.timestamp;
        auctionGreenlit = true;
    }

    /**
     * @dev returns the current price based on block.timestamp and the constructor parameters.
     */
    function getPrice() public view whenNotPaused auctionIsLive returns (uint) {
        // New version:
        // S = starting price
        // R = reserve price
        // D = duration
        // st = start time
        // N = current time
        // P = current price
        //
        // So:
        //
        // rate = (R - S) / D
        //
        // P = rate * (N - st) + S
        //  = S + ( (R - S) * (N - st) ) / D
        //  = ((S * D) + (R - S) * (N - st)) / D
        //
        // And this way we can put the division at the end.
        // We also want to keep using uints. The only negative calculation of above's expression is (R - S)
        // If we reverse it to avoid a negative number we can get the same result by:
        //
        // ((S * D) - (S - R) * (N - st)) / D
        //          ^
        // Where each term and operation should yield a positive number for all valid auction values.
        uint price = ((startingPrice * duration) - (startingPrice - reservePrice) * (block.timestamp - startAt)) / duration;
        return price;
    }

    /**
     * @dev Attempts to buy the NFT. If enough ETH was sent with the transaction the NFT will be transferred to the sender.
     * Any extra ETH sent will be returned to the sender. The contract selfdestructs after the process. If not enough ETH
     * is sent to buy it at the current price it reverts and nothing happens. Auction needs to be live to work (started and not finished)
     */
    function buy() external payable whenNotPaused auctionIsLive {
        uint price = getPrice();
        require(msg.value >= price, "Not enough ETH sent for purchase");
        // Sending the NFT to the buyer
        nft.transferFrom(seller, msg.sender, nftId);
        uint slack = msg.value - price;
        // Send back the extra eth that may have been sent to the buy function
        if (slack > 0) {
            payable(msg.sender).transfer(slack);
        }
        // And we pause the contract using Paused
        _pause();
    }

    /**
     * @dev Returns seconds since auction started.
     */
    function auctionAge() public view whenNotPaused auctionIsLive returns(uint) {
        return block.timestamp - startAt;
    }

    /**
     * @dev Sends contract balance to target address. The contract needs to be paused.
     */
    function recoverEth(address payable target) external payable onlyOwner whenPaused {
        target.transfer(address(this).balance);
    }
}