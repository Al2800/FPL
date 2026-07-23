# Live-faithful calibration artifacts

These reports preserve the calibration path, including candidates rejected before a replay proposal was frozen:

- `live-faithful-v1-calibration.json` and `live-faithful-v1.cold-start-calibrated.json` are the initial cold-start-only candidate.
- `live-faithful-v1-structured-calibration.json` and `live-faithful-v1.structured-calibrated.json` add calibrated team strength but do not shrink sparse individual priors. Their sealed GW2 application was rejected and is documented by `reports/benchmarks/2025-26/gw-02/setup/sparse-prior-rejection.json`.
- `live-faithful-v1-reliability-calibration.json` and `live-faithful-v1.reliability-calibrated.json` are the accepted forecast artifacts. They add training-selected sample-minute reliability shrinkage and underpin `forecast-reliability-comparison.json`.
- `live-faithful-v1-feature-complete-calibration.json` and `live-faithful-v1.feature-complete.json` are the final structured-data gate. The event decomposition candidate was tested and rejected at weight zero; a 0.5 recent-minutes trajectory was selected. These artifacts underpin `forecast-feature-complete-comparison.json`.

All candidates were selected using target seasons no later than 2023/24. The 2024/25 season was opened once as locked validation. No 2025/26 outcome was used for fitting or setup review.
