import json
import unittest
from unittest.mock import patch

from src.analyzer import global_battle_stats
from src.authenticity_check import check_kol_metadata
from src.config import OUTPUT_DIR, load_kols
from src.fetcher import resolve_channel_id


# Identities checked against the sources in 频道新增记录_20261016.md.
REQUESTED_CHANNELS = {
    'Wally Magazine': (98, '@wallymagazine', 'UCpjqK881YGOy-5k1juphSiw'),
    'The Wall Street Journal': (99, '@wsj', 'UCK7tptUDHh-RYDsdxO1-5QQ'),
    'Bloomberg Television': (100, '@markets', 'UCIALMKvObZNtJ6AmdCLP7Lg'),
    'Reuters': (101, '@Reuters', 'UChqUTb7kYRX8-EiaN3XFrSQ'),
    'RagaFinance財經台': (102, '@RagaFinance', 'UCETuQf4lzTrfevoHdSGo8Ew'),
    'am730': (103, '@am730video', 'UCr_L9cZdbBU_XDsKDHBBlew'),
    '點線面': (104, '@點線面2026', 'UCfkXa49J_3n7a27Pdf4IEng'),
    '硬核刘大': (53, '@硬核刘大', 'UCCeMdcZw1LJsAGKeoYXZw6A'),
}


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kols = load_kols()

    def test_requested_channels_are_enabled_and_unique(self):
        for name, (kid, handle, channel_id) in REQUESTED_CHANNELS.items():
            with self.subTest(channel=name):
                matches = [kol for kol in self.kols if kol['name'] == name]
                self.assertEqual(1, len(matches))
                kol = matches[0]
                self.assertEqual(kid, kol['id'])
                self.assertEqual(handle, kol['handle'])
                self.assertEqual(channel_id, kol['channel_id'])
                self.assertEqual(f'https://www.youtube.com/channel/{channel_id}', kol['channel_url'])
                self.assertIs(True, kol['active'])
                self.assertEqual('YouTube', kol['platform'])
                self.assertIn(kol['language'], ('中文', '英文'))
                failures = [i for i in check_kol_metadata(kol, published=True) if i['level'] == 'FAIL']
                self.assertEqual([], failures)

    def test_catalog_ids_are_unique(self):
        ids = [kol['id'] for kol in self.kols]
        self.assertEqual(len(ids), len(set(ids)))

    def test_enabled_channels_have_no_duplicate_channel_ids(self):
        channel_ids = [
            kol['channel_id'] for kol in self.kols
            if kol.get('active') and kol.get('channel_id')
        ]
        self.assertEqual(len(channel_ids), len(set(channel_ids)))

    def test_new_channel_ids_resolve_without_network(self):
        new_ids = {kid for kid, _, _ in REQUESTED_CHANNELS.values() if kid >= 98}
        with patch('src.fetcher.requests.get') as get:
            for kol in self.kols:
                if kol['id'] in new_ids:
                    with self.subTest(channel=kol['name']):
                        self.assertEqual(kol['channel_id'], resolve_channel_id(kol))
        get.assert_not_called()

    def test_removed_channel_ids_remain_unused(self):
        self.assertFalse({77, 78} & {kol['id'] for kol in self.kols})

    def test_report_snapshot_matches_catalog(self):
        data = json.loads((OUTPUT_DIR / 'data.json').read_text(encoding='utf-8'))
        active = data['active_kols']
        inactive = data['inactive_kols']
        catalog_ids = {kol['id'] for kol in self.kols}
        snapshot_ids = [entry['kol']['id'] for entry in active] + [kol['id'] for kol in inactive]
        self.assertEqual(len(snapshot_ids), len(set(snapshot_ids)))
        self.assertEqual(catalog_ids, set(snapshot_ids))
        meta = data['meta']
        self.assertEqual(len(active), meta['active_count'])
        self.assertEqual(len(active), meta['verified_count'])
        self.assertEqual(len(inactive), meta['inactive_count'])
        self.assertEqual(len(inactive), meta['quarantined_count'])
        self.assertEqual(len(self.kols), meta['total'])
        self.assertEqual(global_battle_stats({e['kol']['id']: e for e in active}), meta['stats'])
        audit = json.loads((OUTPUT_DIR / 'audit_report.json').read_text(encoding='utf-8'))
        self.assertEqual(catalog_ids, {result['id'] for result in audit['results']})
        self.assertEqual(meta['total'], audit['summary']['total_kols'])
        self.assertEqual(meta['active_count'], audit['summary']['included_kols'])
        self.assertEqual(meta['inactive_count'], audit['summary']['quarantined_kols'])
        self.assertEqual(meta['stats']['total'], audit['summary']['total_items'])


if __name__ == '__main__':
    unittest.main()
