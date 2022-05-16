#!/usr/bin/python3

from brownie import DutchAuction, TestNFT
from scripts.definitions import NFTType, AuctionType
from brownie.test import given, strategy
from brownie import chain
import brownie
import time
from typing import Optional
import math

# ==================================================================
#
# EXPECTED ERROR MESSAGES
#
# ==================================================================

NOT_APPROVED = "Auction cannot be started. NFT owner has not approved this contract yet"
NOT_LIVE_START = "Auction has not started yet!"
NOT_LIVE_END = "Auction has ended"
DURATION_ZERO = "Auction duration must be at least a minute"
START_PRICE_ZERO = "Starting price must be positive"
RESERVE_PRICE_BIGGER = "Reserve price must be less than starting price"
ALREADY_STARTED = "Can't start an already started auction"
NOT_ENOUGH_ETH = "Not enough ETH sent for purchase"
ONLY_OWNER = "Ownable: caller is not the owner"  # From openzeppelin docs


# ==================================================================
#
# CONSTRUCTOR AND THROWS TESTING
#
# ==================================================================


def pass_time(time: int = 1000, blocks: Optional[int] = None):
    now = chain.time()
    blocks = int(time/12) if blocks is None else blocks
    if blocks == 0:
        blocks = 1
    if blocks > 20:
        blocks = 20
    chain.mine(blocks=blocks, timestamp=now + time)


def test_create(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    assert auction.nft() == nft
    assert auction.nftId() == 123
    assert auction.seller() == accounts[0]
    assert auction.startAt() == 0
    assert auction.duration() == 500
    assert auction.startingPrice() == 5000
    assert auction.reservePrice() == 3000
    assert not auction.auctionGreenlit()


def test_nft_approve(nft: NFTType, accounts, auction):
    # Yes this is actually testing the NFT contract approve function, not the auction
    # Quick trick to be 200% sure that our testing setup is a real NFT and not a mock/some hack
    nft.approve(str(auction), 123, {"from": accounts[0]})
    result = nft.getApproved(123)
    assert result == auction


def test_create_raises_price_positive(nft: NFTType, accounts, auction):
    with brownie.reverts(START_PRICE_ZERO):
        DutchAuction.deploy(0, 0, 500, nft, 123, {"from": accounts[0]})


def test_create_raises_duration_zero(nft: NFTType, accounts, auction):
    with brownie.reverts(DURATION_ZERO):
        DutchAuction.deploy(50, 10, 0, nft, 123, {"from": accounts[0]})


def test_create_raises_duration_too_small(nft: NFTType, accounts, auction):
    with brownie.reverts(DURATION_ZERO):
        DutchAuction.deploy(50, 10, 59, nft, 123, {"from": accounts[0]})


def test_create_raises_reserve_less_than_price(nft: NFTType, accounts, auction):
    with brownie.reverts(RESERVE_PRICE_BIGGER):
        DutchAuction.deploy(10, 20, 500, nft, 123, {"from": accounts[0]})

@given(
    duration=strategy("uint"),
    initial_price=strategy("uint", max_value=1000000000000000000000000),  # 1M ETH
    reserve_price=strategy("uint", max_value=1000000000000000000000000)
)
def test_create_fails_invalid(accounts, reserve_price, initial_price, duration):
    # We're testing our expected constructor rules here overall

    # We'll need a new NFT per round of hypothesis testing
    nft: NFTType = TestNFT.deploy({'from': accounts[0]})
    tx = nft.mint(accounts[0], 123, "abc", {'from': accounts[0]})
    tx.wait(1)  # Or web3 disconnects for some reason...

    # Duration has to be 60 or more
    if duration < 60:
        with brownie.reverts():
            DutchAuction.deploy(initial_price, reserve_price, duration, nft, 123, {"from": accounts[0]})

    # initial price cannot be 0
    elif initial_price == 0:
        with brownie.reverts():
            DutchAuction.deploy(initial_price, reserve_price, duration, nft, 123, {"from": accounts[0]})

    # reserve price must be less than initial price
    elif reserve_price >= initial_price:
        with brownie.reverts():
            DutchAuction.deploy(initial_price, reserve_price, duration, nft, 123, {"from": accounts[0]})
    else:
        DutchAuction.deploy(initial_price, reserve_price, duration, nft, 123, {"from": accounts[0]})
        assert True


def test_not_approved_fails_start(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    with brownie.reverts(NOT_APPROVED):
        auction.startAuction({"from": accounts[0]})


def test_start_raises_already_started(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    nft.approve(str(auction), 123, {"from": accounts[0]})
    auction.startAuction({"from": accounts[0]})
    assert auction.auctionGreenlit()
    with brownie.reverts(ALREADY_STARTED):
        auction.startAuction({"from": accounts[0]})


def test_start_auction_only_owner(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    nft.approve(str(auction), 123, {"from": accounts[0]})
    with brownie.reverts(ONLY_OWNER):
        auction.startAuction({"from": accounts[1]})  # Some other account


def test_not_approved_fails_get_price(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    with brownie.reverts(NOT_LIVE_START):
        auction.getPrice()


def test_not_approved_fails_buy(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    with brownie.reverts(NOT_LIVE_START):
        auction.buy({"from": accounts[0]})


def test_approved_but_not_live_not_started(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    nft.approve(str(auction), 123, {"from": accounts[0]})
    assert not auction.auctionGreenlit()
    with brownie.reverts(NOT_LIVE_START):
        auction.getPrice()
    with brownie.reverts(NOT_LIVE_START):
        auction.buy({"from": accounts[0]})


def test_approved_but_not_live_already_ended(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    nft.approve(str(auction), 123, {"from": accounts[0]})
    assert not auction.auctionGreenlit()
    chain.sleep(1)
    chain.mine()
    auction.startAuction({"from": accounts[0]})
    chain.sleep(1)
    chain.mine()
    assert auction.auctionGreenlit()
    chain.sleep(600)  # So the auction should now have ended
    chain.mine()
    with brownie.reverts(NOT_LIVE_END):
        auction.getPrice()
    with brownie.reverts(NOT_LIVE_END):
        auction.buy({"from": accounts[0]})

def test_auction_age_only_live(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    with brownie.reverts(NOT_LIVE_START):
        auction.auctionAge()
    nft.approve(str(auction), 123, {"from": accounts[0]})
    with brownie.reverts(NOT_LIVE_START):
        auction.auctionAge()
    auction.startAuction({"from": accounts[0]})
    pass_time(time=20)
    # Can't get a hang on how to pass some exact amount of time on the chain yet...
    assert auction.auctionAge() in [20, 19, 21]
    pass_time(time=600)  # Auction has ended now
    with brownie.reverts(NOT_LIVE_END):
        auction.auctionAge()


# ==================================================================
#
# BUY AND PRICE TESTING
#
# ==================================================================


@given(
    duration=strategy("uint", max_value=10*365*86400), # Max = 10 years
    initial=strategy("uint", max_value=1000000000000000000000000),  # 1M ETH
    reserve=strategy("uint", max_value=1000000000000000000000000),
    elapsed=strategy("uint", min_value=10, max_value=10*365*86400)
)
def test_get_price(TestNFT, accounts, elapsed, reserve, initial, duration):

    # We're already testing for these in another test, so let's speed up the hypothesis testing and only deal with
    # Valid parameters
    if elapsed >= duration:
        return
    if duration < 60:
        return
    if reserve >= initial:
        return
    if initial == 0:
        return

    # We floor the result so it simulates solidity's decimal truncation
    # ALSO: use // for a true integer division
    price = lambda t: math.floor(((initial * duration) - (initial - reserve) * t) // duration)

    # We want a new NFT each round of hypothesis complains
    nft: NFTType = TestNFT.deploy({'from': accounts[0]})
    nft.mint(accounts[0], 123, "abc", {'from': accounts[0]})
    auction: AuctionType = DutchAuction.deploy(initial, reserve, duration, nft, 123, {"from": accounts[0]})
    tx = nft.approve(str(auction), 123, {"from": accounts[0]})
    tx.wait(1)

    auction.startAuction({"from": accounts[0]})
    # chain.mine/transactions are what actually advances the clock for contract views
    pass_time(time=elapsed)
    # We want to get our expected price using exactly the blockchain elapsed time
    real = auction.getPrice()
    elapsed_chain = auction.auctionAge()
    expected = price(elapsed_chain)
    # We finally make the contract call
    print("\nData:", initial, reserve, duration, elapsed, elapsed_chain)
    assert expected == real
    time.sleep(1)  # So RCP is kept alive enough for transactions to finish...


def test_buy(accounts, nft):
    # Params:
    price_i = 5000
    price_f = 2000
    duration = 100
    elapsed = 50
    slack = 500  # Fraction of price to be sent when buying
    # Price should be: Price = Slope * delta_time + initial_price
    # Slope is delta_price / delta_time
    price = lambda t: math.floor(((price_i * duration) - (price_i - price_f) * t) // duration)

    auction: AuctionType = DutchAuction.deploy(price_i, price_f, duration, nft, 123, {"from": accounts[0]})
    tx = nft.approve(str(auction), 123, {"from": accounts[0]})
    tx.wait(1)
    time.sleep(1)
    # Let's verify that accounts[0] owns the NFT now
    assert accounts[0] == nft.ownerOf(123)

    auction.startAuction({"from": accounts[0]})
    if elapsed > 0:
        pass_time(time = elapsed)

    # Let's say that it is account 1 who buys
    balance_i = accounts[1].balance()
    elapsed_chain = auction.auctionAge()
    expected = price(elapsed_chain)
    auction.buy({"from": accounts[1], "amount": expected + slack})
    tx.wait(1)
    time.sleep(1)
    # Now we get how much eth do we have after the transaction
    pass_time()
    balance_f = accounts[1].balance()
    spent = balance_i - balance_f
    # And since the transaction should send us back the slack then:
    assert spent == expected
    # Finally we verify who is the NFT owner
    assert not (accounts[0] == nft.ownerOf(123))
    assert accounts[1] == nft.ownerOf(123)


def test_buy_fails_not_enough_eth(nft: NFTType, accounts, auction):
    # Params:
    price_i = 5000
    price_f = 2000
    duration = 100
    elapsed = 50
    fraction_of_price = 0.9  # Fraction of price to be sent when buying
    # Price should be: Price = Slope * delta_time + initial_price
    # Slope is delta_price / delta_time
    slope = (price_f - price_i) / duration
    price = lambda t: round(slope * t + price_i)

    auction: AuctionType = DutchAuction.deploy(price_i, price_f, duration, nft, 123, {"from": accounts[0]})
    tx = nft.approve(str(auction), 123, {"from": accounts[0]})
    tx.wait(1)
    time.sleep(1)
    # Let's verify that accounts[0] owns the NFT now
    assert accounts[0] == nft.ownerOf(123)

    start_time = chain.time()
    tx = auction.startAuction({"from": accounts[0]})
    tx.wait(1)
    time.sleep(1)
    chain.sleep(elapsed)
    chain.mine(blocks=20)
    measurement_time = chain.time()
    elapsed_chain = measurement_time - start_time
    expected = price(elapsed_chain)

    # Let's say that it is account 1 who buys
    balance_i = accounts[1].balance()
    with brownie.reverts():
        auction.buy({"from": accounts[1], "amount": fraction_of_price * expected})
    # Now we get how much eth do we have after the transaction
    chain.mine(blocks=20)
    balance_f = accounts[1].balance()
    spent = balance_i - balance_f
    # And since the transaction should revert then:
    assert spent == 0
    # Finally we verifythat the NFT did not change hands
    assert accounts[0] == nft.ownerOf(123)
    assert not (accounts[1] == nft.ownerOf(123))


# # ==================================================================
# #
# # SELFDESTRUCT TESTING
# #
# # ==================================================================


def check_paused(auction) -> bool:
    return auction.paused()


def test_buy_pauses(nft: NFTType, accounts, auction):
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    nft.approve(str(auction), 123, {"from": accounts[0]})
    auction.startAuction({"from": accounts[0]})
    receipt = auction.buy({"from": accounts[1], 'amount': 999999})
    # Now auction should be destroyed with default values:
    assert check_paused(auction)


def test_whole_process_buying(nft: NFTType, accounts, auction):
    # Here we're testing a simulation of the interaction with the contract.
    # Buyers requesting prices, buyers trying to buy at the wrong time, etc.
    auction: AuctionType = DutchAuction.deploy(5000, 3000, 500, nft, 123, {"from": accounts[0]})
    pass_time()
    # The auction is created, people try to interact with it too soon
    with brownie.reverts(NOT_LIVE_START):
        auction.getPrice()
    pass_time()
    # Some hacker wannabe tries to buy it right away
    with brownie.reverts(NOT_LIVE_START):
        auction.buy({"from": accounts[1]})
    pass_time()
    # Trying to start an unapproved auction, not even being the owner
    with brownie.reverts(NOT_APPROVED):
        auction.startAuction({"from": accounts[0]})
    with brownie.reverts(ONLY_OWNER):
        auction.startAuction({"from": accounts[1]})
    nft.approve(str(auction), 123, {"from": accounts[0]})
    pass_time()
    # Approved but unstarted auction
    with brownie.reverts(NOT_LIVE_START):
        auction.getPrice()
    pass_time()
    with brownie.reverts(NOT_LIVE_START):
        auction.buy({"from": accounts[1], "amount": 999999})
    pass_time()
    with brownie.reverts(ONLY_OWNER):
        auction.startAuction({"from": accounts[1]})
    pass_time()
    auction.startAuction({"from": accounts[0]})
    pass_time(time=10)
    # Someone tries to buy without enough ETH
    with brownie.reverts(NOT_ENOUGH_ETH):
        auction.buy({"from": accounts[2], "amount": 1})
    price = auction.getPrice()
    assert isinstance(price, int)
    # Finally someone is going to properly buy it:
    receipt = auction.buy({"from": accounts[1], "amount": 999999})
    assert check_paused(auction)
    pass_time()
    # Now we verify that the NFT changed hands
    assert str(accounts[1]) == nft.ownerOf(123)
    assert not (str(accounts[0]) == nft.ownerOf(123))
