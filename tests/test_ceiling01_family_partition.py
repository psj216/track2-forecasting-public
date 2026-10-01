"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

from qfbench2_track_forecasting.ceiling01.decomposition import partitions

def test_family_partition():
 rows=[{'family':f,'id':(f,i)} for f in ('T2-F1','T2-F2','T2-F3','T2-F4') for i in range(6)]
 parts=partitions(rows,'family')
 assert set(parts)=={'T2-F1','T2-F2','T2-F3','T2-F4'}
 assert sum(map(len,parts.values()))==24
 assert len({r['id'] for p in parts.values() for r in p})==24
