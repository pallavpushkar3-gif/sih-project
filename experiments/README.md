# Experiments

Implement experiment entry points as thin scripts importing the backend package. Configurations belong in `configs/`; datasets/models/results are versioned artifacts; MLflow records runs where configured.

Each experiment records method, dataset/split/target/transforms, revision/environment, configuration/seeds, commands and output hashes. Reproduction status and failures belong in the research log. Notebooks are optional exploratory tools and must not become the only implementation of production transformations.
