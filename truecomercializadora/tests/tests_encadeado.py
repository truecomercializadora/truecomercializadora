from unittest import TestCase

import datetime

from truecomercializadora import encadeado

class TestDeckNames(TestCase):

    def test_get_deck_names(self):


        with self.subTest():
            ref_inicio = '2020-07-0'
            ref_horizonte = '2020-07-0'

            decks = encadeado.get_deck_names(
                ref_inicio=ref_inicio,
                ref_horizonte=ref_horizonte)

            result = {
                'decomp': ['DC202007-sem1'],
                'newave': ['NW202007']
            }

            self.assertEqual(decks, result)


        with self.subTest():
            ref_inicio = '2020-10-0'
            ref_horizonte = '2020-08-0'

            with self.assertRaises(Exception):
                encadeado.get_deck_names(
                    ref_inicio=ref_inicio,
                    ref_horizonte=ref_horizonte)


        with self.subTest():
            ref_inicio = '2020-07-0'
            ref_horizonte = '2021-12-0'

            decks = encadeado.get_deck_names(
                ref_inicio=ref_inicio,
                ref_horizonte=ref_horizonte)

            result = {
                'decomp': [
                    'DC202007-sem1',
                    'DC202008-sem1',
                    'DC202009-sem1',
                    'DC202010-sem1',
                    'DC202011-sem1',
                    'DC202012-sem1',
                    'DC202101-sem1',
                    'DC202102-sem1',
                    'DC202103-sem1',
                    'DC202104-sem1',
                    'DC202105-sem1',
                    'DC202106-sem1',
                    'DC202107-sem1',
                    'DC202108-sem1',
                    'DC202109-sem1',
                    'DC202110-sem1',
                    'DC202111-sem1',
                    'DC202112-sem1'],
                'newave': [
                    'NW202007',
                    'NW202008',
                    'NW202009',
                    'NW202010',
                    'NW202011',
                    'NW202012',
                    'NW202101',
                    'NW202102',
                    'NW202103',
                    'NW202104',
                    'NW202105',
                    'NW202106',
                    'NW202107',
                    'NW202108',
                    'NW202109',
                    'NW202110',
                    'NW202111',
                    'NW202112']
            }

            self.assertEqual(decks, result)

        with self.subTest():
            ref_inicio = '2020-07-0'
            ref_horizonte = '2020-07-1'

            decks = encadeado.get_deck_names(
                ref_inicio=ref_inicio,
                ref_horizonte=ref_horizonte)

            result = {
                'decomp': ['DC202007-sem1','DC202007-sem2'],
                'newave': ['NW202007']
            }

            self.assertEqual(decks, result)
        
        with self.subTest():
            ref_inicio = '2020-07-1'
            ref_horizonte = '2020-07-0'

            with self.assertRaises(Exception):
                encadeado.get_deck_names(
                    ref_inicio=ref_inicio,
                    ref_horizonte=ref_horizonte)

        with self.subTest():
            ref_inicio = '2020-11-0'
            ref_horizonte = '2020-11-0'

            decks = encadeado.get_deck_names(
                ref_inicio=ref_inicio,
                ref_horizonte=ref_horizonte)

            result = {
                'decomp': ['DC202011-sem1'],
                'newave': ['NW202011']
            }

            self.assertEqual(decks, result)