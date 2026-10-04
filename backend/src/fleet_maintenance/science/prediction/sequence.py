from dataclasses import dataclass
from typing import cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor, nn
from torch.utils.data import DataLoader, TensorDataset


class RulLstm(nn.Module):
    def __init__(self, feature_count: int, hidden_size: int = 32) -> None:
        super().__init__()
        self.lstm = nn.LSTM(feature_count, hidden_size, batch_first=True)
        self.output = nn.Linear(hidden_size, 1)

    def forward(self, values: Tensor) -> Tensor:
        encoded, _ = self.lstm(values)
        return cast(Tensor, self.output(encoded[:, -1, :]).squeeze(-1))


@dataclass
class SequenceRul:
    model: RulLstm

    @classmethod
    def fit(
        cls,
        features: NDArray[np.float64],
        targets: NDArray[np.float64],
        *,
        seed: int,
        hidden_size: int,
        epochs: int,
        batch_size: int,
        learning_rate: float,
    ) -> "SequenceRul":
        if epochs <= 0 or batch_size <= 0:
            raise ValueError("Epochs and batch size must be positive.")
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
        model = RulLstm(features.shape[2], hidden_size)
        dataset = TensorDataset(
            torch.from_numpy(features.astype(np.float32)),
            torch.from_numpy(targets.astype(np.float32)),
        )
        generator = torch.Generator().manual_seed(seed)
        batches = DataLoader(dataset, batch_size=batch_size, shuffle=True, generator=generator)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        loss_function = nn.MSELoss()
        model.train()
        for _ in range(epochs):
            for batch_features, batch_targets in batches:
                optimizer.zero_grad()
                loss = loss_function(model(batch_features), batch_targets)
                loss.backward()
                optimizer.step()
        return cls(model.eval())

    def predict(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        with torch.no_grad():
            values = torch.from_numpy(features.astype(np.float32))
            predictions = self.model(values).numpy().astype(np.float64)
        return cast(NDArray[np.float64], np.maximum(predictions, 0.0))
