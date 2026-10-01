"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

from qfbench2_track_forecasting.ceiling01.decomposition import partitions,pair_kind

def test_horizon_partition_keeps_nonstandard_horizons():
 rows=[{'horizon':h} for h in (5,21,63,64,126,129,189)]
 parts=partitions(rows,'horizon');assert sum(map(len,parts.values()))==7
 assert '64' in parts and '129' in parts
 assert pair_kind('a',21,'a',63)=='same_asset_different_horizon'
 assert pair_kind('a',21,'b',21)=='different_asset_same_horizon'
 assert pair_kind('a',21,'b',63)=='different_asset_different_horizon'
