#!/usr/bin/python3

import pytest
from scripts.definitions import NFTType, AuctionType


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass

@pytest.fixture(scope="function")
def nft(TestNFT: NFTType, accounts):
    nft: NFTType = TestNFT.deploy({'from': accounts[0]})
    nft.mint(accounts[0], 123, "abc", {'from': accounts[0]})
    return nft

# This is to trigger coverage for this contract too
@pytest.fixture(scope="function")
def auction(DutchAuction: AuctionType, nft, accounts):
    return DutchAuction.deploy(100,50,100, nft, 123, {'from': accounts[0]})
