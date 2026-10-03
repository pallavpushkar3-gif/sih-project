# Data Directory

`sources.yaml` records actual source/version/checksum/usage metadata when datasets are acquired. `demo/` contains small synthetic mappings, tasks, resources, stock and scenarios with explicit labels. `raw/` preserves downloaded bytes; `processed/` contains reproducible transformations; `splits/` preserves immutable partition artifacts.

Bulk and generated data are ignored by Git but retained through the artifact workflow. Never regenerate a split silently because its local file is missing. Refer to dataset and simulation protocols. No acquisition or dataset validation has been completed by these specifications.
