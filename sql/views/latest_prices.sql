CREATE OR REPLACE VIEW latest_prices AS

SELECT
    f.node_id,
    f.trading_name,
    f.brand_name,
    f.temporary_closure,
    f.permanent_closure,
    f.permanent_closure_date,
    f.is_motorway,
    f.is_supermarket,
    f.address,
    f.postcode,
    f.city,
    f.county,
    f.country,
    f.latitude,
    f.longitude,

    ps.snapshot_at,

    ps.price_e5,
    ps.submitted_e5,
    ps.effective_e5,

    ps.price_e10,
    ps.submitted_e10,
    ps.effective_e10,

    ps.price_b7s,
    ps.submitted_b7s,
    ps.effective_b7s,

    ps.price_b7p,
    ps.submitted_b7p,
    ps.effective_b7p,

    ps.price_b10,
    ps.submitted_b10,
    ps.effective_b10,

    ps.price_hvo,
    ps.submitted_hvo,
    ps.effective_hvo

FROM forecourts f
LEFT JOIN price_snapshots ps
    ON ps.node_id = f.node_id
   AND ps.snapshot_at = (
       SELECT MAX(snapshot_at)
       FROM price_snapshots
   );