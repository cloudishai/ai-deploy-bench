"""Black-box verifiers, one per benchmark app, keyed by app id."""

from bench.verify.api import ApiVerifier
from bench.verify.base import Verifier
from bench.verify.crud import CrudVerifier
from bench.verify.dataviz import DatavizVerifier
from bench.verify.realtime import RealtimeVerifier
from bench.verify.static import StaticSiteVerifier

VERIFIERS: dict[str, type[Verifier]] = {
    v.app_id: v for v in (StaticSiteVerifier, CrudVerifier, ApiVerifier, DatavizVerifier, RealtimeVerifier)
}
