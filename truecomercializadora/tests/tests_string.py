from unittest import TestCase

from truecomercializadora import utils_string

class TestSafeReplace(TestCase):

    def test_safe_replace_works_when_match_string_exists(self):
        with self.subTest():
            input_str = 'This is an example of string. Where a substring such as: a long black jacket, should be replaced as a test'
            match_str = 'a long black jacket'
            replace_str = 'a big blue ocean'

            output_str = utils_string.safe_replace(
                input_str=input_str,
                match_str=match_str,
                replace_str=replace_str)
            check_str = 'This is an example of string. Where a substring such as: a big blue ocean, should be replaced as a test'

            self.assertEqual(output_str, check_str)

    def test_safe_replace_breaks_when_match_string_does_not_exists(self):
        with self.subTest():
            input_str = 'This is an example of string. Where a substring such as: a long black jacket, should be replaced as a test'
            match_str = 'a big blue ocean'
            replace_str = 'a lonely old person'

            with self.assertRaises(Exception):
                utils_string.safe_replace(
                    input_str=input_str,
                    match_str=match_str,
                    replace_str=replace_str)