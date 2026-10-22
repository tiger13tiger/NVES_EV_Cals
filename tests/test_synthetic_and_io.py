from nves_au.engine import aggregate_by_supplier_year, score_fleet
from nves_au.io import read_fleet_csv, write_fleet_csv
from nves_au.synthetic import generate_demo_fleet


def test_generate_demo_fleet_is_reproducible():
    a = generate_demo_fleet(years=(2025,), seed=7)
    b = generate_demo_fleet(years=(2025,), seed=7)
    assert a == b


def test_generate_demo_fleet_varies_with_seed():
    a = generate_demo_fleet(years=(2025,), seed=1)
    b = generate_demo_fleet(years=(2025,), seed=2)
    assert [r.units_sold for r in a] != [r.units_sold for r in b]


def test_demo_fleet_scores_without_error(config):
    fleet = generate_demo_fleet(years=(2025,))
    results = score_fleet(fleet, config)
    assert len(results) == len(fleet)
    positions = aggregate_by_supplier_year(results)
    suppliers = {p.supplier for p in positions}
    assert "Dragonfly Motors" in suppliers
    assert "Ironclad Trucks" in suppliers
    # The EV-only brand should be solidly in credit, the ICE ute/truck
    # brand solidly in debit -- sanity-checks the lineup's spread.
    ev_brand = next(p for p in positions if p.supplier == "Dragonfly Motors")
    ice_brand = next(p for p in positions if p.supplier == "Ironclad Trucks")
    assert ev_brand.iev_units < 0
    assert ice_brand.iev_units > 0


def test_csv_roundtrip(tmp_path):
    fleet = generate_demo_fleet(years=(2025,))
    csv_path = tmp_path / "fleet.csv"
    write_fleet_csv(fleet, csv_path)
    roundtrip = read_fleet_csv(csv_path)
    assert roundtrip == fleet


def test_csv_roundtrip_keeps_na_adr_category(tmp_path):
    # "NA" (light commercial) must not be read back as a missing value.
    fleet = [r for r in generate_demo_fleet(years=(2025,)) if r.adr_category == "NA"]
    assert fleet, "fixture should include at least one NA-category vehicle"
    csv_path = tmp_path / "fleet.csv"
    write_fleet_csv(fleet, csv_path)
    roundtrip = read_fleet_csv(csv_path)
    assert all(r.adr_category == "NA" for r in roundtrip)
