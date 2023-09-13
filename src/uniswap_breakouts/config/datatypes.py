from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Optional

from dataclasses_json import DataClassJsonMixin
from marshmallow import Schema, fields, post_load


@dataclass(frozen=True)
class ChainResources:
    name: str
    scanner_base_url: str
    scanner_api_key: str
    rpc_url: str


@dataclass(frozen=True)
class V2PositionSpec(DataClassJsonMixin):
    chain: str
    pool_address: str
    wallet_address: Optional[str]
    lp_balance: Optional[Decimal]
    block_no: Optional[int]

    def __post_init__(self):
        if self.wallet_address is None and self.lp_balance is None:
            raise ValueError("V2 position specifier must include either a wallet address or lp balance")

        if self.wallet_address is not None and self.lp_balance is not None:
            raise ValueError(
                "Only one of wallet address or lp balance may be specified in a V2 position spec"
            )


class V2SpecSchema(Schema):
    chain = fields.String(required=True)
    pool_address = fields.String(required=True)
    wallet_address = fields.String(required=False, missing=None)
    lp_balance = fields.Decimal(required=False, missing=None)
    block_no = fields.Integer(required=False, missing=None)

    @post_load
    def post_load(self, data: dict, **kwargs: Any) -> V2PositionSpec:  # pylint: disable=unused-argument
        return V2PositionSpec(**data)


@dataclass(frozen=True)
class V3PositionSpec(DataClassJsonMixin):
    chain: str
    pool_address: str
    nft_address: str
    nft_id: int
    block_no: Optional[int]


class V3SpecSchema(Schema):
    chain = fields.String(required=True)
    pool_address = fields.String(required=True)
    nft_address = fields.String(required=True)
    nft_id = fields.Integer(required=True)
    block_no = fields.Integer(required=False, missing=None)

    @post_load
    def post_load(self, data: dict, **kwargs: Any) -> V3PositionSpec:  # pylint: disable=unused-argument
        return V3PositionSpec(**data)


@dataclass(frozen=True)
class PositionSpecs:
    v2_positions: List[V2PositionSpec]
    v3_positions: List[V3PositionSpec]


class PositionSpecsSchema(Schema):
    v2_positions = fields.Nested(V2SpecSchema, many=True, missing=[])
    v3_positions = fields.Nested(V3SpecSchema, many=True, missing=[])

    @post_load
    def post_load(self, data: dict, **kwargs: Any) -> PositionSpecs:  # pylint: disable=unused-argument
        return PositionSpecs(**data)
