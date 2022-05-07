## Dutch auction in solidity:
### A tested implementation using Brownie for any EVM-compatible chain.
#### Víctor Marín Felip


### Operation:

The contract is able to auction an NFT to the highest bidder using the reverse-auction method,
where a initial price, a reserve price, and an auction duration have been defined, and the
buy price lowers with time until duration is reached and the auction ends. If the token is
purchased before the auction ends, the transfer happens instantly and in a fair way: any extra ETH sent
will be refunded to the buyer.

Deploying the auction consists of these steps:

1 - Have an NFT (ERC721) in property.

2 - Deploy the Auction contract with the desired parameters. These parameters are:
   - Start price (1 wei or more).
   - Reserve price (can be 0).
   - Duration, in seconds.
   - Address of the NFT contract.
   - ID of the NFT contract representing the asset to be auctioned.

3 - Approve the Auction contract addres in the NFT contract. This will enable the contract
to transfer the token if anyone pays enough for it.

4 - Start the auction by calling a function in the contract.

At this time the clock will start ticking and the price will drop, linearly, between
initial and reserve price across the specified duration. After the auction has ended
the only thing that can be done with the contract is to selfdestruct it.

The owner must be do steps 1-4. Anyone can then check the price and buy the NFT. The owner
can destroy the auction at any time, before, during, and after it (if the asset wasn't sold).

### Code:

Under `contracts/` there are two solidity files: `Auction.sol` and `QuickNFT.sol`. The
first one represent the logic described above. The second one is used to provide a 
real NFT for testing (not a mock).

Under `scripts/` there is a `definitions.py` file, where I replicate the interfaces of the Auction and NFT contracts.
This way I can use proper typehints while testing and use autocomplete, etc.

Under `tests/` there are the tests. I make use of three custom fixtures (check `conftest.py`), one to reset the environment after very
test, other to provide every test with a minted NFT, and another to trick brownie's coverage into considering
the Auction contract, which is not otherwise used in testing (the fixture). All tests are in `test_main.py` and
are divided into three categories. One for the constructor and overall permissions, other for
the price calculations and the act of buying, and a last one for the selfdestructs and a general test.
