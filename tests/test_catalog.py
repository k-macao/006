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


# Identities checked against the sources in 频道新增记录_20261016_政论人文扩展.md.
# 编号 105-124：时政评论 / 海外创作者 / 产业科技 / 区域与官媒四个扩展板块。
NEW_CHANNELS = {
    '观视频工作室 Guan Video': (105, '@guanvideo', 'UCYfJG6cGfW84FVLuy7semEg'),
    '观察者网': (106, '@guancha021', 'UCJncdiH3BQUBgCroBmhsUhQ'),
    '沈逸老师': (107, '@沈逸老师-g8p', 'UCfcPzjuqNxzyyu2ukSBPmeQ'),
    '黃智賢夜問': (108, '@黃智賢夜問', 'UCsgXIOF43ZqgcmLwnKjsndQ'),
    '赖岳谦TV': (109, '@TV-od5nb', 'UCnrxxRlv2ZSSW4ApuEy8C0w'),
    '郭正亮頻道': (110, '@郭正亮頻道', 'UCSYBgX9pWGiUAcBxjnj6JCQ'),
    '中国东南卫视官方频道（海峡新干线）': (111, None, 'UCN2e8dLY9KnH-B15LyBM7Fg'),
    '歪果仁研究协会 Ychina': (112, '@ychinamedia', 'UCvVIk8oQ2vnZsCi4vR9O4dg'),
    'Barrett': (113, '@barrettyt', 'UC1XG7bJnYqta_ezr12WZp7w'),
    'Cyrus Janssen': (114, '@cyrusjanssen', 'UCxEQsjgRRfGWiJJu_PDygxw'),
    'Daniel Dumbrill': (115, '@danieldumbrill', 'UC6Bl8MTbW9M9MQoPhxbarpw'),
    'the JaYoe Nation': (116, '@jayoenation', 'UC8Ykci4MKSSdTJYuYp53G7A'),
    "Jerry's Take on China": (117, '@jerrystakeonchina799', 'UC_DHAzg3miuwH9NMEUCY0Ow'),
    '科技袁人（科技新信号 TechSignal）': (118, None, 'UCSgGqt-30oXBq0-n0K-t4Nw'),
    '差评君': (119, '@xpinman', 'UCqlQ5ErufqtQUhkuKj1xngg'),
    'IC实验室': (120, '@ICLAB', 'UCJ1zX4FZA15dwE2olLAO3-w'),
    'CGTN': (121, '@cgtn', 'UCgrNz-aDmcr2uuto8_DL2jg'),
    'CCTV中国中央电视台': (122, '@cctv', 'UCcLK3j-XWdGBnt5bR9NJHaQ'),
    'China.org.cn 中国网': (123, '@chinaorgcn', 'UCrYhYcDkTcSFhhDSFpYTFCg'),
    '鳳凰衛視 Phoenix TV': (124, '@phoenixtvglobal', 'UC4vnLYInDvXtLKGOZieMeMw'),
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

    def test_new_politics_culture_channels_are_enabled_and_unique(self):
        """105-124：身份核对过的扩展频道，必须可抓取（active）且元数据无 FAIL。"""
        for name, (kid, handle, channel_id) in NEW_CHANNELS.items():
            with self.subTest(channel=name):
                matches = [kol for kol in self.kols if kol['name'] == name]
                self.assertEqual(1, len(matches))
                kol = matches[0]
                self.assertEqual(kid, kol['id'])
                self.assertEqual(channel_id, kol['channel_id'])
                self.assertEqual(f'https://www.youtube.com/channel/{channel_id}', kol['channel_url'])
                self.assertIs(True, kol['active'])
                self.assertEqual('YouTube', kol['platform'])
                self.assertIn(kol['language'], ('中文', '英文'))
                if handle is not None:
                    self.assertEqual(handle, kol['handle'])
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
