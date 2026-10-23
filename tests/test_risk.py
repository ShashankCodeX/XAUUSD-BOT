import pytest

from bot.risk import RiskTooSmall, lot_size, plan_from_prices, spread_share


def test_basic_lot_size():
    result = lot_size(30, 3)
    assert result.lots == 0.10
    assert result.ounces == 10
    assert result.actual_risk == 30


def test_rounds_down_never_over_risks():
    result = lot_size(50, 3)  # 50 / 300 = 0.1666...
    assert result.lots == 0.16
    assert result.actual_risk <= 50


def test_decimal_precision_trap():
    assert lot_size(29, 1).lots == 0.29  # float maths would give 0.28


def test_too_small_risk_raises():
    with pytest.raises(RiskTooSmall):
        lot_size(1, 5)


@pytest.mark.parametrize("risk,stop", [(0, 3), (-5, 3), (30, 0), (30, -1)])
def test_bad_inputs(risk, stop):
    with pytest.raises(ValueError):
        lot_size(risk, stop)


def test_spread_share():
    assert spread_share(0.3, 3) == pytest.approx(0.10)
    with pytest.raises(ValueError):
        spread_share(0.3, 0)


def test_plan_buy_and_sell():
    buy = plan_from_prices(2650, 2647, 2656)
    assert buy.side == "buy" and buy.rr == pytest.approx(2.0)
    sell = plan_from_prices(2650, 2653, 2644)
    assert sell.side == "sell" and sell.rr == pytest.approx(2.0)


def test_plan_invalid_prices():
    with pytest.raises(ValueError):
        plan_from_prices(2650, 2655, 2656)  # stop and target both above entry
