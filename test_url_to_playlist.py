import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import url_to_playlist as updater


APPLE_ID = 'pl.test-archive'
CONFIG = {'page_url': f'https://music.apple.com/us/playlist/archive/{APPLE_ID}', 'playlist_id': 'destination'}


def apple_page(tracks, advertised_count=None):
    items = [
        {'artistName': artist, 'title': title,
         'contentDescriptor': {'kind': 'song', 'identifiers': {'storeAdamID': apple_id}}}
        for apple_id, artist, title in tracks
    ]
    data = {'data': [{
        'intent': {'contentDescriptor': {'identifiers': {'storeAdamID': APPLE_ID}}},
        'data': {'sections': [
            {'id': f'playlist-detail-header-section - {APPLE_ID}',
             'items': [{'trackCount': len(items) if advertised_count is None else advertised_count}]},
            {'id': f'track-list - {APPLE_ID}', 'items': items},
            {'id': 'more-by-curator', 'items': [{'trackCount': 999}]},
        ]},
    }]}
    return f'<script id="serialized-server-data" type="application/json">{json.dumps(data)}</script>'.encode()


def spotify_item(track_id, artist, title):
    return {'track': {'id': track_id, 'name': title, 'artists': [{'name': artist}]}}


class SpotifyArchive:
    def __init__(self, items):
        self.items = list(items)
        self.fail_add = False
        self.search_results = []

    def search(self, query, **kwargs):
        results = self.search_results.get(query, []) if isinstance(self.search_results, dict) else self.search_results
        return {'tracks': {'items': results}}

    def playlist_items(self, playlist_id, limit=100, market=None):
        return self.page(0, limit)

    def page(self, offset, limit):
        end = offset + limit
        return {'items': self.items[offset:end], 'next': end if end < len(self.items) else None}

    def next(self, page):
        return self.page(page['next'], 100)

    def playlist_add_items(self, playlist_id, ids, position):
        if self.fail_add:
            raise RuntimeError('Spotify write failed')
        self.items[position:position] = [spotify_item(track_id, 'Matched', track_id) for track_id in ids]

    def ids(self):
        return [item['track']['id'] for item in self.items]


class AppleArchiveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cache_path = Path(self.directory.name) / 'matches.json'
        self.spotify = SpotifyArchive([
            spotify_item('old-removed-from-apple', 'Old Artist', 'Old Song'),
            spotify_item('already-there', 'Known Artist', 'Known Song'),
        ])

    def run_archive(self, tracks, matcher, advertised_count=None):
        with patch.object(updater, 'sp', self.spotify), \
             patch.object(updater, 'APPLE_MUSIC_CACHE_PATH', str(self.cache_path)), \
             patch.object(updater.requests, 'get') as get, \
             patch.object(updater, 'search_apple_music_track', side_effect=matcher or updater.search_apple_music_track), \
             patch.object(updater.time, 'sleep'), \
             contextlib.redirect_stdout(io.StringIO()):
            get.return_value.content = apple_page(tracks, advertised_count)
            updater.process_apple_music_playlist('test', CONFIG)

    def test_growing_archive_preserves_old_tracks_order_and_retries_misses(self):
        new_tracks = [(f'apple-{i}', 'Artist', f'Song {i}') for i in range(101)]
        source = [('known', 'Known Artist', 'Known Song'), *new_tracks,
                  ('duplicate-recording', 'Another Artist', 'Same Recording'),
                  ('missing', 'Later Artist', 'Not Released Yet')]

        def first_match(sp, artist, title, **kwargs):
            if title == 'Not Released Yet':
                return None
            track_id = 'new-7' if title == 'Same Recording' else f"new-{title.split()[-1]}"
            return track_id, title, artist, 100

        self.run_archive(source, first_match)
        expected = [f'new-{i}' for i in range(101)] + ['old-removed-from-apple', 'already-there']
        self.assertEqual(self.spotify.ids(), expected)
        self.assertNotIn('missing', json.loads(self.cache_path.read_text()))

        def later_match(sp, artist, title, **kwargs):
            # Resolved songs must use their durable mappings, not rematch to a different recording.
            if title == 'Not Released Yet':
                return 'now-available', title, artist, 100
            return 'wrong-rematch', title, artist, 100

        # A removal and source reorder must not delete or reorder the archive.
        self.run_archive(list(reversed(source[2:])), later_match)
        self.assertEqual(self.spotify.ids(), ['now-available', *expected])
        self.run_archive(source, later_match)
        self.assertEqual(self.spotify.ids(), ['now-available', *expected])

    def test_incomplete_source_does_not_change_archive_or_cache(self):
        before = self.spotify.ids()
        with self.assertRaisesRegex(ValueError, 'Incomplete Apple Music playlist'):
            self.run_archive([('one', 'Artist', 'Song')], lambda *args, **kwargs: None, advertised_count=2)
        self.assertEqual(self.spotify.ids(), before)
        self.assertFalse(self.cache_path.exists())

    def test_failed_write_does_not_mark_song_as_archived(self):
        source = [('one', 'Artist', 'New Song')]
        matcher = lambda *args, **kwargs: ('new', 'New Song', 'Artist', 100)
        self.spotify.fail_add = True
        with self.assertRaisesRegex(RuntimeError, 'Spotify write failed'):
            self.run_archive(source, matcher)
        self.assertFalse(self.cache_path.exists())
        self.spotify.fail_add = False
        self.run_archive(source, matcher)
        self.assertEqual(self.spotify.ids(), ['new', 'old-removed-from-apple', 'already-there'])

    def test_requested_remix_does_not_select_original_or_different_remixer(self):
        source = [('remix', 'Logic1000', 'The Only One (feat. Christine and the Queens) [Hercules & Love Affair Remix]')]
        self.spotify.search_results = [
            spotify_item('original', 'Logic1000', 'The Only One (feat. Christine and the Queens)')['track'],
            spotify_item('other-remix', 'Logic1000', 'The Only One - Other Remix')['track'],
            spotify_item('correct-remix', 'Logic1000', 'The Only One (feat. Christine and the Queens) - Hercules & Love Affair Remix')['track'],
        ]
        self.run_archive(source, None)
        self.assertEqual(self.spotify.ids(), ['correct-remix', 'old-removed-from-apple', 'already-there'])

    def test_brackets_separate_search_words(self):
        self.spotify.search_results = {
            'shygirl lucky hymn': [spotify_item('hymn', 'Shygirl', 'Lucky[Hymn]')['track']],
        }
        self.run_archive([('apple-hymn', 'Shygirl', 'Lucky[Hymn]')], None)
        self.assertEqual(self.spotify.ids(), ['hymn', 'old-removed-from-apple', 'already-there'])


class SharedSpotifySearchTests(unittest.TestCase):
    def test_brackets_separate_words_without_changing_other_punctuation(self):
        cases = [
            ('Shygirl', 'Lucky[Hymn]', 'Shygirl Lucky Hymn'),
            ('Singer', 'Song(Live)', 'Singer Song Live'),
            ('Singer', 'Song{Mix}', 'Singer Song Mix'),
            ('Singer[Guest]', 'Song', 'Singer Guest Song'),
            ('Singer', "Don't Stop", 'Singer Dont Stop'),
            ('Dolly Parton', '9 to 5', 'Dolly Parton 9 to 5'),
        ]
        for artist, title, expected_query in cases:
            with self.subTest(artist=artist, title=title):
                class Catalog:
                    def search(self, query, **kwargs):
                        items = [spotify_item('correct', artist, title)['track']] if query == expected_query else []
                        return {'tracks': {'items': items}}

                result = updater.spotify_utils.search_track(Catalog(), artist, title, delay=0)
                self.assertIsNotNone(result)
                self.assertEqual(result[:3], ('correct', title, artist))


if __name__ == '__main__':
    unittest.main()
