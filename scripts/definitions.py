from abc import ABC, abstractmethod
from typing import Dict


class NFTType(ABC):

    schema: str = NotImplemented

    @abstractmethod
    def deploy(self, caller: Dict):
        pass

    @abstractmethod
    def mint(self, address: str, _id: int, url: str, caller: Dict):
        pass

    @abstractmethod
    def approve(self, to: str, _id: int, caller: Dict):
        pass

    @abstractmethod
    def getApproved(self, _id: int) -> str:
        pass

    @abstractmethod
    def ownerOf(self, _id: int) -> str:
        pass

    @abstractmethod
    def wait(self, value: int):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class AuctionType(ABC):


    # Attributes of the contract (getters to us outside the chain)
    @abstractmethod
    def nft(self) -> str:
        pass

    @abstractmethod
    def nftId(self) -> int:
        pass

    @abstractmethod
    def seller(self) -> str:
        pass

    @abstractmethod
    def startAt(self) -> int:
        pass

    @abstractmethod
    def duration(self) -> int:
        pass

    @abstractmethod
    def startingPrice(self) -> int:
        pass

    @abstractmethod
    def reservePrice(self) -> int:
        pass

    @abstractmethod
    def auctionGreenlit(self) -> bool:
        pass


    # Methods of the contract
    @abstractmethod
    def deploy(self, start_price: int, reserve_price: int, duration: int, nft: str, nft_id: int, caller: Dict):
        pass

    @abstractmethod
    def startAuction(self, caller: Dict):
        pass

    @abstractmethod
    def getPrice(self) -> int:
        pass

    @abstractmethod
    def buy(self, caller: Dict):
        pass

    @abstractmethod
    def auctionAge(self):
        pass

    @abstractmethod
    def wait(self, value: int):
        pass

    @abstractmethod
    def paused(self) -> bool:
        pass
