#!/usr/bin/env python3
import unittest

import pyattrcache as pac


class TestCache(unittest.TestCase):
    def test_cache(self):
        calls = []

        @pac.cache
        def func(a, b):
            calls.append((a, b))
            return a + b

        self.assertEqual(func(1, 2), 3)
        self.assertEqual(func(1, 2), 3)
        self.assertEqual(func(1, 2), 3)
        self.assertEqual(func(1, 2), 3)

        self.assertEqual(calls, [(1, 2)])

        self.assertEqual(func(1, 3), 4)
        self.assertEqual(func(1, 3), 4)

        self.assertEqual(calls, [(1, 2), (1, 3)])

    def test_cached_property(self):
        calls = []

        class Test:
            attr = 3
            @pac.cached_property
            def prop(self):
                calls.append(1)
                return 1 + self.attr

        t = Test()
        self.assertEqual(t.prop, 4)
        self.assertEqual(t.prop, 4)
        self.assertEqual(t.prop, 4)

        self.assertEqual(calls, [1])

        t.attr = 4
        self.assertEqual(t.prop, 5)
        self.assertEqual(t.prop, 5)

        self.assertEqual(calls, [1, 1])


if __name__ == "__main__":
    unittest.main()
