"""T-M09-10: càlcul del marge sense base de dades, amb els exemples de M09-7 (dades inventades)."""

import json

import pytest

from apps.margins.calc import FORECAST, REAL, MarginInputs, compute

# Sortida d'un dia a les Medes (M09-7): 10 participants a 60 €.
MEDES = MarginInputs(
    enrolments_cents=10 * 6000,
    real_costs_cents={"embarcació": 25000, "aire": 20 * 600},
    rental_estimated_cents=3 * 2500,
    material_real_cents=7 * 350,
    participants=10,
)


def _with(**changes):
    return MarginInputs(**{**MEDES.__dict__, **changes})


def test_ca_m09_07_medes_marge_real_percentatge_i_per_participant():
    m = compute(MEDES, REAL)
    assert m.income_enrolments_cents == 60000
    assert m.direct_costs_cents == 25000 + 12000 + 7500
    assert m.material_cost_cents == 2450
    assert m.margin_cents == 13050
    assert m.margin_pct_tenths == 218  # 21,75 % → 21,8 %
    assert m.per_participant_cents == 1305
    assert m.participants == 10
    assert m.breakdown["rental"] == {"source": "estimated", "cents": 7500}
    assert m.breakdown["material_source"] == "real"


def test_comissions_reals_pugen_els_costos_directes():
    m = compute(_with(commissions_cents=10 * 30), REAL)
    assert m.margin_cents == 12750
    assert m.breakdown["commissions_cents"] == 300


def test_ca_m09_08_factura_del_centre_substitueix_l_estimacio():
    m = compute(_with(rental_invoiced_cents=7800), REAL)
    assert m.margin_cents == 12750
    assert m.breakdown["rental"] == {"source": "invoiced", "cents": 7800, "deviation_cents": 300}


def test_marge_previst_negatiu_de_l_exemple_d_avis():
    inputs = MarginInputs(
        enrolments_cents=8 * 4500,
        planned_costs_cents={"embarcació": 25000, "aire": 12000},
        participants=8,
    )
    m = compute(inputs, FORECAST)
    assert m.margin_cents == -1000
    assert m.margin_pct_tenths == -28  # -2,78 % → -2,8 %


def test_previst_fa_servir_el_real_de_la_categoria_si_n_hi_ha():
    inputs = MarginInputs(
        enrolments_cents=36000,
        real_costs_cents={"embarcació": 26000},
        planned_costs_cents={"embarcació": 25000, "aire": 12000},
    )
    m = compute(inputs, FORECAST)
    assert m.breakdown["costs_by_category"] == {"embarcació": 26000, "aire": 12000}
    assert m.margin_cents == 36000 - 26000 - 12000


def test_categoria_real_a_zero_tambe_substitueix_la_prevista():
    inputs = MarginInputs(
        enrolments_cents=1000, real_costs_cents={"aire": 0}, planned_costs_cents={"aire": 500}
    )
    assert compute(inputs, FORECAST).margin_cents == 1000


def test_el_real_no_compta_els_costos_previstos():
    m = compute(_with(planned_costs_cents={"instructor": 5000}), REAL)
    assert m.margin_cents == 13050
    assert "instructor" not in m.breakdown["costs_by_category"]


def test_rn_m02_43_material_previst_nomes_sense_cost_real_i_nomes_al_previst():
    planned_only = _with(material_real_cents=None, material_planned_cents=3000)
    forecast = compute(planned_only, FORECAST)
    assert forecast.material_cost_cents == 3000
    assert forecast.breakdown["material_source"] == "planned"

    real = compute(planned_only, REAL)
    assert real.material_cost_cents == 0
    assert real.breakdown["material_source"] == "none"

    both = compute(_with(material_planned_cents=3000), FORECAST)
    assert both.material_cost_cents == 2450  # mai tots dos alhora
    assert both.breakdown["material_source"] == "real"


def test_sense_el_03_no_hi_ha_cost_de_material():
    m = compute(_with(material_real_cents=None), FORECAST)
    assert m.material_cost_cents == 0
    assert m.margin_cents == 13050 + 2450


def test_altres_ingressos_directes_sumen_i_entren_al_percentatge():
    m = compute(_with(other_direct_income_cents=7500), REAL)
    assert m.margin_cents == 13050 + 7500
    assert m.margin_pct_tenths == 304  # 20.550 ÷ 67.500 = 30,44 %


def test_l_m09_03_sortida_gratuita_marge_negatiu_sense_percentatge():
    m = compute(MarginInputs(enrolments_cents=0, real_costs_cents={"aire": 1200}), REAL)
    assert m.margin_cents == -1200
    assert m.margin_pct_tenths is None
    assert m.per_participant_cents is None


def test_ca_m09_39_factura_de_cancel_lacio_del_centre_sense_estimacio():
    inputs = MarginInputs(enrolments_cents=0, rental_invoiced_cents=3000)
    m = compute(inputs, REAL)
    assert m.margin_cents == -3000
    assert m.breakdown["rental"]["deviation_cents"] == 3000


@pytest.mark.parametrize(
    ("margin", "participants", "expected"),
    [(15, 2, 8), (-15, 2, -8), (14, 3, 5), (-14, 3, -5), (13, 2, 7)],
)
def test_per_participant_arrodonit_al_centim_meitat_lluny_del_zero(margin, participants, expected):
    inputs = MarginInputs(
        enrolments_cents=max(margin, 0),
        real_costs_cents={"x": max(-margin, 0)},
        participants=participants,
    )
    assert compute(inputs, REAL).per_participant_cents == expected


def test_percentatge_negatiu_simetric():
    m = compute(MarginInputs(enrolments_cents=60000, real_costs_cents={"x": 73050}), REAL)
    assert m.margin_cents == -13050
    assert m.margin_pct_tenths == -218


def test_imports_molt_grans_sense_perdre_precisio():
    big = 9_000_000_000_000_000
    m = compute(MarginInputs(enrolments_cents=big, real_costs_cents={"x": 1}), REAL)
    assert m.margin_cents == big - 1
    assert m.margin_pct_tenths == 1000


def test_el_detall_es_serialitzable_per_al_marge_congelat():
    json.dumps(compute(_with(rental_invoiced_cents=7800), REAL).breakdown)


def test_tipus_desconegut():
    with pytest.raises(ValueError, match="tipus"):
        compute(MEDES, "provisional")


@pytest.mark.parametrize(
    "changes",
    [
        {"enrolments_cents": 600.0},
        {"commissions_cents": True},
        {"material_real_cents": "2450"},
        {"real_costs_cents": {"aire": 12.5}},
    ],
)
def test_rn_m09_22_nomes_centims_enters(changes):
    with pytest.raises(TypeError):
        compute(_with(**changes), REAL)


@pytest.mark.parametrize(
    "changes",
    [
        {"enrolments_cents": -1},
        {"rental_estimated_cents": -1},
        {"rental_invoiced_cents": -1},
        {"material_planned_cents": -1},
        {"participants": -1},
        {"planned_costs_cents": {"aire": -1}},
    ],
)
def test_imports_negatius_a_l_entrada_es_rebutgen(changes):
    with pytest.raises(ValueError):
        compute(_with(**changes), FORECAST)
