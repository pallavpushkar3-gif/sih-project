import pytest

from fleet_maintenance.integrations.example_csv import AdapterValidationError, adapt_csv
from fleet_maintenance.science.data.loaders import FEATURE_NAMES


def test_csv_adapter_validates_atomic_batches_and_row_errors():
    header = ','.join(('cycle', *FEATURE_NAMES))
    row = '1,' + ','.join(['0', '0', '100'] + ['1'] * 21)
    parsed = adapt_csv(header + '\n' + row, 'adapter-v1', 'NASA_CMAPSS:FD001:train:1')
    assert parsed.rows[0].cycle == 1
    with pytest.raises(AdapterValidationError) as failure:
        adapt_csv(header + '\n' + row + '\n' + row, 'v2', parsed.engine_identity)
    assert failure.value.errors[0]['row'] == 3
    assert 'consecutive' in failure.value.errors[0]['error']
    with pytest.raises(AdapterValidationError):
        adapt_csv(header + '\n' + row.replace(',100,', ',NaN,'), 'v3', parsed.engine_identity)
