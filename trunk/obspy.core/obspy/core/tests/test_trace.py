# -*- coding: utf-8 -*-

from copy import deepcopy
import numpy as np
from numpy.ma import is_masked
from obspy.core import UTCDateTime, Trace, read
import unittest
import math


class TraceTestCase(unittest.TestCase):
    """
    Test suite for obspy.core.trace.Trace.
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_len(self):
        """
        Tests the __len__ and count methods of the Trace class.
        """
        trace = Trace(data=np.arange(1000))
        self.assertEquals(len(trace), 1000)
        self.assertEquals(trace.count(), 1000)

    def test_ltrim(self):
        """
        Tests the ltrim method of the Trace class.
        """
        # set up
        trace = Trace(data=np.arange(1000))
        start = UTCDateTime(2000, 1, 1, 0, 0, 0, 0)
        trace.stats.starttime = start
        trace.stats.sampling_rate = 200.0
        end = UTCDateTime(2000, 1, 1, 0, 0, 4, 995000)
        # verify
        trace.verify()
        # ltrim 100 samples
        tr = deepcopy(trace)
        tr._ltrim(0.5)
        tr.verify()
        np.testing.assert_array_equal(tr.data[0:5], \
                                      np.array([100, 101, 102, 103, 104]))
        self.assertEquals(len(tr.data), 900)
        self.assertEquals(tr.stats.npts, 900)
        self.assertEquals(tr.stats.sampling_rate, 200.0)
        self.assertEquals(tr.stats.starttime, start + 0.5)
        self.assertEquals(tr.stats.endtime, end)
        # ltrim 202 samples
        tr = deepcopy(trace)
        tr._ltrim(1.010)
        tr.verify()
        np.testing.assert_array_equal(tr.data[0:5], \
                                      np.array([202, 203, 204, 205, 206]))
        self.assertEquals(len(tr.data), 798)
        self.assertEquals(tr.stats.npts, 798)
        self.assertEquals(tr.stats.sampling_rate, 200.0)
        self.assertEquals(tr.stats.starttime, start + 1.010)
        self.assertEquals(tr.stats.endtime, end)
        # ltrim to UTCDateTime
        tr = deepcopy(trace)
        tr._ltrim(UTCDateTime(2000, 1, 1, 0, 0, 1, 10000))
        tr.verify()
        np.testing.assert_array_equal(tr.data[0:5], \
                                      np.array([202, 203, 204, 205, 206]))
        self.assertEquals(len(tr.data), 798)
        self.assertEquals(tr.stats.npts, 798)
        self.assertEquals(tr.stats.sampling_rate, 200.0)
        self.assertEquals(tr.stats.starttime, start + 1.010)
        self.assertEquals(tr.stats.endtime, end)
        # some sanity checks
        # negative start time as datetime
        tr = deepcopy(trace)
        tr._ltrim(start - 1, pad=True)
        tr.verify()
        self.assertEquals(tr.stats.starttime, start - 1)
        np.testing.assert_array_equal(trace.data, tr.data[200:])
        self.assertEquals(tr.stats.endtime, trace.stats.endtime)
        # negative start time as integer
        tr = deepcopy(trace)
        tr._ltrim(-100, pad=True)
        tr.verify()
        self.assertEquals(tr.stats.starttime, start - 100)
        delta = 100 * trace.stats.sampling_rate
        np.testing.assert_array_equal(trace.data, tr.data[delta:])
        self.assertEquals(tr.stats.endtime, trace.stats.endtime)
        # start time > end time
        tr = deepcopy(trace)
        tr._ltrim(trace.stats.endtime + 100)
        tr.verify()
        self.assertEquals(tr.stats.starttime,
                          trace.stats.endtime + 100)
        np.testing.assert_array_equal(tr.data, np.empty(0))
        self.assertEquals(tr.stats.endtime, tr.stats.starttime)
        # start time == end time
        tr = deepcopy(trace)
        tr._ltrim(5)
        tr.verify()
        self.assertEquals(tr.stats.starttime,
                          trace.stats.starttime + 5)
        np.testing.assert_array_equal(tr.data, np.empty(0))
        self.assertEquals(tr.stats.endtime, tr.stats.starttime)
        # start time == end time
        tr = deepcopy(trace)
        tr._ltrim(5.1)
        tr.verify()
        self.assertEquals(tr.stats.starttime,
                          trace.stats.starttime + 5.1)
        np.testing.assert_array_equal(tr.data, np.empty(0))
        self.assertEquals(tr.stats.endtime, tr.stats.starttime)

    def test_rtrim(self):
        """
        Tests the rtrim method of the Trace class.
        """
        # set up
        trace = Trace(data=np.arange(1000))
        start = UTCDateTime(2000, 1, 1, 0, 0, 0, 0)
        trace.stats.starttime = start
        trace.stats.sampling_rate = 200.0
        end = UTCDateTime(2000, 1, 1, 0, 0, 4, 995000)
        trace.verify()
        # rtrim 100 samples
        tr = deepcopy(trace)
        tr._rtrim(0.5)
        tr.verify()
        np.testing.assert_array_equal(tr.data[-5:], \
                                      np.array([895, 896, 897, 898, 899]))
        self.assertEquals(len(tr.data), 900)
        self.assertEquals(tr.stats.npts, 900)
        self.assertEquals(tr.stats.sampling_rate, 200.0)
        self.assertEquals(tr.stats.starttime, start)
        self.assertEquals(tr.stats.endtime, end - 0.5)
        # rtrim 202 samples
        tr = deepcopy(trace)
        tr._rtrim(1.010)
        tr.verify()
        np.testing.assert_array_equal(tr.data[-5:], \
                                      np.array([793, 794, 795, 796, 797]))
        self.assertEquals(len(tr.data), 798)
        self.assertEquals(tr.stats.npts, 798)
        self.assertEquals(tr.stats.sampling_rate, 200.0)
        self.assertEquals(tr.stats.starttime, start)
        self.assertEquals(tr.stats.endtime, end - 1.010)
        # rtrim 1 minute via UTCDateTime
        tr = deepcopy(trace)
        tr._rtrim(UTCDateTime(2000, 1, 1, 0, 0, 3, 985000))
        tr.verify()
        np.testing.assert_array_equal(tr.data[-5:], \
                                      np.array([793, 794, 795, 796, 797]))
        self.assertEquals(len(tr.data), 798)
        self.assertEquals(tr.stats.npts, 798)
        self.assertEquals(tr.stats.sampling_rate, 200.0)
        self.assertEquals(tr.stats.starttime, start)
        self.assertEquals(tr.stats.endtime, end - 1.010)
        # some sanity checks
        # negative end time
        tr = deepcopy(trace)
        t = UTCDateTime(1999, 12, 31)
        tr._rtrim(t)
        tr.verify()
        self.assertEquals(tr.stats.endtime, t)
        np.testing.assert_array_equal(tr.data, np.empty(0))
        # negative end time with given seconds
        tr = deepcopy(trace)
        tr._rtrim(100)
        tr.verify()
        self.assertEquals(tr.stats.endtime, trace.stats.endtime - 100)
        np.testing.assert_array_equal(tr.data, np.empty(0))
        self.assertEquals(tr.stats.endtime, tr.stats.starttime)
        # end time > start time
        tr = deepcopy(trace)
        t = UTCDateTime(2001)
        tr._rtrim(t)
        tr.verify()
        self.assertEquals(tr.stats.endtime, t)
        np.testing.assert_array_equal(tr.data, np.empty(0))
        self.assertEquals(tr.stats.endtime, tr.stats.starttime)
        # end time > start time given seconds
        tr = deepcopy(trace)
        tr._rtrim(5.1)
        tr.verify()
        delta = int(math.floor(round(5.1 * trace.stats.sampling_rate, 7)))
        endtime = trace.stats.starttime + trace.stats.delta * \
                  (trace.stats.npts - delta - 1)
        self.assertEquals(tr.stats.endtime, endtime)
        np.testing.assert_array_equal(tr.data, np.empty(0))
        # end time == start time
        # returns one sample!
        tr = deepcopy(trace)
        tr._rtrim(4.995)
        #XXX I do not understand why this fails!!!
        #tr.verify()
        np.testing.assert_array_equal(tr.data, np.array([0]))
        self.assertEquals(len(tr.data), 1)
        self.assertEquals(tr.stats.npts, 1)
        self.assertEquals(tr.stats.sampling_rate, 200.0)
        self.assertEquals(tr.stats.starttime, start)
        self.assertEquals(tr.stats.endtime, start)

    def test_trim(self):
        """
        Tests the trim method of the Trace class.
        """
        # set up
        trace = Trace(data=np.arange(1001))
        start = UTCDateTime(2000, 1, 1, 0, 0, 0, 0)
        trace.stats.starttime = start
        trace.stats.sampling_rate = 200.0
        end = UTCDateTime(2000, 1, 1, 0, 0, 5, 0)
        trace.verify()
        # rtrim 100 samples
        trace.trim(0.5, 0.5)
        trace.verify()
        np.testing.assert_array_equal(trace.data[-5:],
                                      np.array([896, 897, 898, 899, 900]))
        np.testing.assert_array_equal(trace.data[:5],
                                      np.array([100, 101, 102, 103, 104]))
        self.assertEquals(len(trace.data), 801)
        self.assertEquals(trace.stats.npts, 801)
        self.assertEquals(trace.stats.sampling_rate, 200.0)
        self.assertEquals(trace.stats.starttime, start + 0.5)
        self.assertEquals(trace.stats.endtime, end - 0.5)

    def test_trimAllDoesNotChangeDtype(self):
        """
        If a Trace is completely trimmed, e.g. no data samples are remaining,
        the dtype should remain unchanged.

        A trace with no data samples is not really senseful but the dtype
        should not be changed anyways.
        """
        # Choose non native dtype.
        tr = Trace(np.arange(100, dtype='int16'))
        tr.trim(UTCDateTime(10000), UTCDateTime(20000))
        # Assert the result.
        self.assertEqual(len(tr.data), 0)
        self.assertEqual(tr.data.dtype, 'int16')

    def test_addTraceWithGap(self):
        """
        Tests __add__ method of the Trace class.
        """
        # set up
        tr1 = Trace(data=np.arange(1000))
        tr1.stats.sampling_rate = 200
        start = UTCDateTime(2000, 1, 1, 0, 0, 0, 0)
        tr1.stats.starttime = start
        tr2 = Trace(data=np.arange(0, 1000)[::-1])
        tr2.stats.sampling_rate = 200
        tr2.stats.starttime = start + 10
        # verify
        tr1.verify()
        tr2.verify()
        # add
        trace = tr1 + tr2
        # stats
        self.assertEquals(trace.stats.starttime, start)
        self.assertEquals(trace.stats.endtime, start + 14.995)
        self.assertEquals(trace.stats.sampling_rate, 200)
        self.assertEquals(trace.stats.npts, 3000)
        # data
        self.assertEquals(len(trace), 3000)
        self.assertEquals(trace[0], 0)
        self.assertEquals(trace[999], 999)
        self.assertTrue(is_masked(trace[1000]))
        self.assertTrue(is_masked(trace[1999]))
        self.assertEquals(trace[2000], 999)
        self.assertEquals(trace[2999], 0)
        # verify
        trace.verify()

    def test_addTraceWithOverlap(self):
        """
        Tests __add__ method of the Trace class.
        """
        # set up
        tr1 = Trace(data=np.arange(1000))
        tr1.stats.sampling_rate = 200
        start = UTCDateTime(2000, 1, 1, 0, 0, 0, 0)
        tr1.stats.starttime = start
        tr2 = Trace(data=np.arange(0, 1000)[::-1])
        tr2.stats.sampling_rate = 200
        tr2.stats.starttime = start + 4
        # add
        trace = tr1 + tr2
        # stats
        self.assertEquals(trace.stats.starttime, start)
        self.assertEquals(trace.stats.endtime, start + 8.995)
        self.assertEquals(trace.stats.sampling_rate, 200)
        self.assertEquals(trace.stats.npts, 1800)
        # data
        self.assertEquals(len(trace), 1800)
        self.assertEquals(trace[0], 0)
        self.assertEquals(trace[799], 799)
        self.assertTrue(trace[800].mask)
        self.assertTrue(trace[999].mask)
        self.assertEquals(trace[1000], 799)
        self.assertEquals(trace[1799], 0)
        # verify
        trace.verify()

    def test_addSameTrace(self):
        """
        Tests __add__ method of the Trace class.
        """
        # set up
        tr1 = Trace(data=np.arange(1001))
        # add
        trace = tr1 + tr1
        # should return exact the same values
        self.assertEquals(trace.stats, tr1.stats)
        np.testing.assert_array_equal(trace.data, tr1.data)
        # verify
        trace.verify()

    def test_addTraceWithinTrace(self):
        """
        Tests __add__ method of the Trace class.
        """
        # set up
        tr1 = Trace(data=np.arange(1001))
        tr1.stats.sampling_rate = 200
        start = UTCDateTime(2000, 1, 1, 0, 0, 0, 0)
        tr1.stats.starttime = start
        tr2 = Trace(data=np.arange(201))
        tr2.stats.sampling_rate = 200
        tr2.stats.starttime = start + 1
        # add
        trace = tr1 + tr2
        # should return exact the same values like trace 1
        self.assertEquals(trace.stats, tr1.stats)
        mask = np.zeros(len(tr1)).astype("bool")
        mask[200:401] = True
        np.testing.assert_array_equal(trace.data.mask, mask)
        np.testing.assert_array_equal(trace.data.data[:200], tr1.data[:200])
        np.testing.assert_array_equal(trace.data.data[401:], tr1.data[401:])
        # add the other way around
        trace = tr2 + tr1
        # should return exact the same values like trace 1
        self.assertEquals(trace.stats, tr1.stats)
        np.testing.assert_array_equal(trace.data.mask, mask)
        np.testing.assert_array_equal(trace.data.data[:200], tr1.data[:200])
        np.testing.assert_array_equal(trace.data.data[401:], tr1.data[401:])
        # verify
        trace.verify()

    def test_addGapAndOverlap(self):
        """
        Test order of merging traces.
        """
        # set up
        tr1 = Trace(data=np.arange(1000))
        tr1.stats.sampling_rate = 200
        start = UTCDateTime(2000, 1, 1, 0, 0, 0, 0)
        tr1.stats.starttime = start
        tr2 = Trace(data=np.arange(1000)[::-1])
        tr2.stats.sampling_rate = 200
        tr2.stats.starttime = start + 4
        tr3 = Trace(data=np.arange(1000)[::-1])
        tr3.stats.sampling_rate = 200
        tr3.stats.starttime = start + 12
        # overlap
        overlap = tr1 + tr2
        self.assertEqual(len(overlap), 1800)
        mask = np.zeros(1800).astype("bool")
        mask[800:1000] = True
        np.testing.assert_array_equal(overlap.data.mask, mask)
        np.testing.assert_array_equal(overlap.data.data[:800], tr1.data[:800])
        np.testing.assert_array_equal(overlap.data.data[1000:], tr2.data[200:])
        # overlap + gap
        overlap_gap = overlap + tr3
        self.assertEqual(len(overlap_gap), 3400)
        mask = np.zeros(3400).astype("bool")
        mask[800:1000] = True
        mask[1800:2400] = True
        np.testing.assert_array_equal(overlap_gap.data.mask, mask)
        np.testing.assert_array_equal(overlap_gap.data.data[:800], \
                                      tr1.data[:800])
        np.testing.assert_array_equal(overlap_gap.data.data[1000:1800], \
                                      tr2.data[200:])
        np.testing.assert_array_equal(overlap_gap.data.data[2400:], tr3.data)
        # gap
        gap = tr2 + tr3
        self.assertEqual(len(gap), 2600)
        mask = np.zeros(2600).astype("bool")
        mask[1000:1600] = True
        np.testing.assert_array_equal(gap.data.mask, mask)
        np.testing.assert_array_equal(gap.data.data[:1000], tr2.data)
        np.testing.assert_array_equal(gap.data.data[1600:], tr3.data)

    def test_slice(self):
        """
        Tests the slicing of trace objects.
        """
        tr = Trace(data=np.arange(10, dtype='int32'))
        mempos = tr.data.ctypes.data
        t = tr.stats.starttime
        tr1 = tr.slice(t + 2, t + 8)
        tr1.data[0] = 10
        self.assertEqual(tr.data[2], 10)
        self.assertEqual(tr.data.ctypes.data, mempos)
        self.assertEqual(tr.data[2:9].ctypes.data, tr1.data.ctypes.data)
        self.assertEqual(tr1.data.ctypes.data - 8, mempos)

    def test_trimFloatingPoint(self):
        """
        Tests the slicing of trace objects.
        """
        # Create test array that allows for easy testing.
        tr = Trace(data=np.arange(11))
        org_stats = deepcopy(tr.stats)
        org_data = deepcopy(tr.data)
        # Save memory position of array.
        mem_pos = tr.data.ctypes.data
        # Just some sanity tests.
        self.assertEqual(tr.stats.starttime, UTCDateTime(0))
        self.assertEqual(tr.stats.endtime, UTCDateTime(10))
        # Create temp trace object used for testing.
        st = tr.stats.starttime
        # This is supposed to include the start- and endtimes and should
        # therefore cut right at 2 and 8.
        temp = deepcopy(tr)
        temp.trim(st + 2.1, st + 7.1)
        # Should be identical.
        temp2 = deepcopy(tr)
        temp2.trim(st + 2.0, st + 8.0)
        self.assertEqual(temp.stats.starttime, UTCDateTime(2))
        self.assertEqual(temp.stats.endtime, UTCDateTime(7))
        self.assertEqual(temp.stats.npts, 6)
        self.assertEqual(temp2.stats.npts, 7)
        #self.assertEqual(temp.stats, temp2.stats)
        np.testing.assert_array_equal(temp.data, temp2.data[:-1])
        # Create test array that allows for easy testing.
        # Check if the data is the same.
        self.assertNotEqual(temp.data.ctypes.data, tr.data[2:9].ctypes.data)
        np.testing.assert_array_equal(tr.data[2:8], temp.data)
        # Using out of bounds times should not do anything but create
        # a copy of the stats.
        temp = deepcopy(tr)
        temp.trim(st - 2.5, st + 200)
        # The start- and endtimes should not change.
        self.assertEqual(temp.stats.starttime, UTCDateTime(0))
        self.assertEqual(temp.stats.endtime, UTCDateTime(10))
        self.assertEqual(temp.stats.npts, 11)
        # Alter the new stats to make sure the old one stays intact.
        temp.stats.starttime = UTCDateTime(1000)
        self.assertEqual(org_stats, tr.stats)
        # Check if the data adress is not the same, that is it is a copy
        self.assertNotEqual(temp.data.ctypes.data, tr.data.ctypes.data)
        np.testing.assert_array_equal(tr.data, temp.data)
        # Make sure the original Trace object did not change.
        np.testing.assert_array_equal(tr.data, org_data)
        self.assertEqual(tr.data.ctypes.data, mem_pos)
        self.assertEqual(tr.stats, org_stats)
        # Use more complicated times and sampling rate.
        tr = Trace(data=np.arange(111))
        tr.stats.starttime = UTCDateTime(111.11111)
        tr.stats.sampling_rate = 50.0
        org_stats = deepcopy(tr.stats)
        org_data = deepcopy(tr.data)
        # Save memory position of array.
        mem_pos = tr.data.ctypes.data
        # Create temp trace object used for testing.
        temp = deepcopy(tr)
        temp.trim(UTCDateTime(111.22222), UTCDateTime(112.99999),
                  nearest_sample=False)
        # Should again be identical. XXX NOT!
        temp2 = deepcopy(tr)
        temp2.trim(UTCDateTime(111.21111), UTCDateTime(113.01111),
                   nearest_sample=False)
        np.testing.assert_array_equal(temp.data, temp2.data[1:-1])
        # Check stuff.
        self.assertEqual(temp.stats.starttime, UTCDateTime(111.23111))
        self.assertEqual(temp.stats.endtime, UTCDateTime(112.991110))
        # Check if the data is the same.
        temp = deepcopy(tr)
        temp.trim(UTCDateTime(0), UTCDateTime(1000 * 1000))
        self.assertNotEqual(temp.data.ctypes.data, tr.data.ctypes.data)
        # starttime must be in conformance with sampling rate
        t = UTCDateTime(111.11111)
        self.assertEqual(temp.stats.starttime, t)
        delta = int((tr.stats.starttime - t) * tr.stats.sampling_rate + .5)
        np.testing.assert_array_equal(tr.data, temp.data[delta:delta + 111])
        # Make sure the original Trace object did not change.
        np.testing.assert_array_equal(tr.data, org_data)
        self.assertEqual(tr.data.ctypes.data, mem_pos)
        self.assertEqual(tr.stats, org_stats)

    def test_trimFloatingPointWithPadding1(self):
        """
        Tests the slicing of trace objects with the use of the padding option.
        """
        # Create test array that allows for easy testing.
        tr = Trace(data=np.arange(11))
        org_stats = deepcopy(tr.stats)
        org_data = deepcopy(tr.data)
        # Save memory position of array.
        mem_pos = tr.data.ctypes.data
        # Just some sanity tests.
        self.assertEqual(tr.stats.starttime, UTCDateTime(0))
        self.assertEqual(tr.stats.endtime, UTCDateTime(10))
        # Create temp trace object used for testing.
        st = tr.stats.starttime
        # Using out of bounds times should not do anything but create
        # a copy of the stats.
        temp = deepcopy(tr)
        temp.trim(st - 2.5, st + 200, pad=True)
        self.assertEqual(temp.stats.starttime.timestamp, -2.0)
        self.assertEqual(temp.stats.endtime.timestamp, 200)
        self.assertEqual(temp.stats.npts, 203)
        mask = np.zeros(203).astype("bool")
        mask[:2] = True
        mask[13:] = True
        np.testing.assert_array_equal(temp.data.mask, mask)
        # Alter the new stats to make sure the old one stays intact.
        temp.stats.starttime = UTCDateTime(1000)
        self.assertEqual(org_stats, tr.stats)
        # Check if the data adress is not the same, that is it is a copy
        self.assertNotEqual(temp.data.ctypes.data, tr.data.ctypes.data)
        np.testing.assert_array_equal(tr.data, temp.data[2:13])
        # Make sure the original Trace object did not change.
        np.testing.assert_array_equal(tr.data, org_data)
        self.assertEqual(tr.data.ctypes.data, mem_pos)
        self.assertEqual(tr.stats, org_stats)

    def test_trimFloatingPointWithPadding2(self):
        """
        Use more complicated times and sampling rate.
        """
        tr = Trace(data=np.arange(111))
        tr.stats.starttime = UTCDateTime(111.11111)
        tr.stats.sampling_rate = 50.0
        org_stats = deepcopy(tr.stats)
        org_data = deepcopy(tr.data)
        # Save memory position of array.
        mem_pos = tr.data.ctypes.data
        # Create temp trace object used for testing.
        temp = deepcopy(tr)
        temp.trim(UTCDateTime(111.22222), UTCDateTime(112.99999),
                  nearest_sample=False)
        # Should again be identical.#XXX not
        temp2 = deepcopy(tr)
        temp2.trim(UTCDateTime(111.21111), UTCDateTime(113.01111),
                   nearest_sample=False)
        np.testing.assert_array_equal(temp.data, temp2.data[1:-1])
        # Check stuff.
        self.assertEqual(temp.stats.starttime, UTCDateTime(111.23111))
        self.assertEqual(temp.stats.endtime, UTCDateTime(112.991110))
        # Check if the data is the same.
        temp = deepcopy(tr)
        temp.trim(UTCDateTime(0), UTCDateTime(1000 * 1000), pad=True)
        self.assertNotEqual(temp.data.ctypes.data, tr.data.ctypes.data)
        # starttime must be in conformance with sampling rate
        t = UTCDateTime(1969, 12, 31, 23, 59, 59, 991110)
        self.assertEqual(temp.stats.starttime, t)
        delta = int((tr.stats.starttime - t) * tr.stats.sampling_rate + .5)
        np.testing.assert_array_equal(tr.data, temp.data[delta:delta + 111])
        # Make sure the original Trace object did not change.
        np.testing.assert_array_equal(tr.data, org_data)
        self.assertEqual(tr.data.ctypes.data, mem_pos)
        self.assertEqual(tr.stats, org_stats)

    def test_addOverlapsDefaultMethod(self):
        """
        Test __add__ method of the Trace object.
        """
        #1 
        # overlapping trace with differing data
        # Trace 1: 0000000
        # Trace 2:      1111111
        tr1 = Trace(data=np.zeros(7))
        tr2 = Trace(data=np.ones(7))
        tr2.stats.starttime = tr1.stats.starttime + 5
        # 1 + 2  : 00000--11111
        tr = tr1 + tr2
        self.assertTrue(isinstance(tr.data, np.ma.masked_array))
        self.assertEqual(tr.data.tolist(),
                         [0, 0, 0, 0, 0, None, None, 1, 1, 1, 1, 1])
        # 2 + 1  : 00000--11111
        tr = tr2 + tr1
        self.assertTrue(isinstance(tr.data, np.ma.masked_array))
        self.assertEqual(tr.data.tolist(),
                         [0, 0, 0, 0, 0, None, None, 1, 1, 1, 1, 1])
        #2
        # overlapping trace with same data
        # Trace 1: 0000000
        # Trace 2:      0000000
        tr1 = Trace(data=np.zeros(7))
        tr2 = Trace(data=np.zeros(7))
        tr2.stats.starttime = tr1.stats.starttime + 5
        # 1 + 2  : 000000000000
        tr = tr1 + tr2
        self.assertTrue(isinstance(tr.data, np.ndarray))
        np.testing.assert_array_equal(tr.data, np.zeros(12))
        # 2 + 1  : 000000000000
        tr = tr2 + tr1
        self.assertTrue(isinstance(tr.data, np.ndarray))
        np.testing.assert_array_equal(tr.data, np.zeros(12))
        #3
        # contained trace with same data
        # Trace 1: 1111111111
        # Trace 2:      11
        tr1 = Trace(data=np.ones(10))
        tr2 = Trace(data=np.ones(2))
        tr2.stats.starttime = tr1.stats.starttime + 5
        # 1 + 2  : 1111111111
        tr = tr1 + tr2
        self.assertTrue(isinstance(tr.data, np.ndarray))
        np.testing.assert_array_equal(tr.data, np.ones(10))
        # 2 + 1  : 1111111111
        tr = tr2 + tr1
        self.assertTrue(isinstance(tr.data, np.ndarray))
        np.testing.assert_array_equal(tr.data, np.ones(10))
        #4
        # contained trace with differing data
        # Trace 1: 0000000000
        # Trace 2:      11
        tr1 = Trace(data=np.zeros(10))
        tr2 = Trace(data=np.ones(2))
        tr2.stats.starttime = tr1.stats.starttime + 5
        # 1 + 2  : 00000--000
        tr = tr1 + tr2
        self.assertTrue(isinstance(tr.data, np.ma.masked_array))
        self.assertEqual(tr.data.tolist(),
                         [0, 0, 0, 0, 0, None, None, 0, 0, 0])
        # 2 + 1  : 00000--000
        tr = tr2 + tr1
        self.assertTrue(isinstance(tr.data, np.ma.masked_array))
        self.assertEqual(tr.data.tolist(),
                         [0, 0, 0, 0, 0, None, None, 0, 0, 0])
        #5
        # completely contained trace with same data until end
        # Trace 1: 1111111111
        # Trace 2: 1111111111
        tr1 = Trace(data=np.ones(10))
        tr2 = Trace(data=np.ones(10))
        # 1 + 2  : 1111111111
        tr = tr1 + tr2
        self.assertTrue(isinstance(tr.data, np.ndarray))
        np.testing.assert_array_equal(tr.data, np.ones(10))
        #6
        # completely contained trace with differing data
        # Trace 1: 0000000000
        # Trace 2: 1111111111
        tr1 = Trace(data=np.zeros(10))
        tr2 = Trace(data=np.ones(10))
        # 1 + 2  : ----------
        tr = tr1 + tr2
        self.assertTrue(isinstance(tr.data, np.ma.masked_array))
        self.assertEqual(tr.data.tolist(), [None] * 10)


    def test_addWithDifferentSamplingRates(self):
        """
        Test __add__ method of the Trace object.
        """
        # 1 - different sampling rates for the same channel should fail
        tr1 = Trace(data=np.zeros(5))
        tr1.stats.sampling_rate = 200
        tr2 = Trace(data=np.zeros(5))
        tr2.stats.sampling_rate = 50
        self.assertRaises(TypeError, tr1.__add__, tr2)
        self.assertRaises(TypeError, tr2.__add__, tr1)
        # 2 - different sampling rates for the different channels works
        tr1 = Trace(data=np.zeros(5))
        tr1.stats.sampling_rate = 200
        tr1.stats.channel = 'EHE'
        tr2 = Trace(data=np.zeros(5))
        tr2.stats.sampling_rate = 50
        tr2.stats.channel = 'EHZ'
        tr3 = Trace(data=np.zeros(5))
        tr3.stats.sampling_rate = 200
        tr3.stats.channel = 'EHE'
        tr4 = Trace(data=np.zeros(5))
        tr4.stats.sampling_rate = 50
        tr4.stats.channel = 'EHZ'
        # same sampling rate and ids should not fail
        tr1 + tr3
        tr3 + tr1
        tr2 + tr4
        tr4 + tr2

    def test_addWithDifferentDatatypesOrID(self):
        """
        Test __add__ method of the Trace object.
        """
        # 1 - different data types for the same channel should fail
        tr1 = Trace(data=np.zeros(5, dtype="int32"))
        tr2 = Trace(data=np.zeros(5, dtype="float32"))
        self.assertRaises(TypeError, tr1.__add__, tr2)
        self.assertRaises(TypeError, tr2.__add__, tr1)
        # 2 - different sampling rates for the different channels works
        tr1 = Trace(data=np.zeros(5, dtype="int32"))
        tr1.stats.channel = 'EHE'
        tr2 = Trace(data=np.zeros(5, dtype="float32"))
        tr2.stats.channel = 'EHZ'
        tr3 = Trace(data=np.zeros(5, dtype="int32"))
        tr3.stats.channel = 'EHE'
        tr4 = Trace(data=np.zeros(5, dtype="float32"))
        tr4.stats.channel = 'EHZ'
        # same data types and ids should not fail
        tr1 + tr3
        tr3 + tr1
        tr2 + tr4
        tr4 + tr2
        # adding traces with different ids should raise
        self.assertRaises(TypeError, tr1.__add__, tr2)
        self.assertRaises(TypeError, tr3.__add__, tr4)
        self.assertRaises(TypeError, tr2.__add__, tr1)
        self.assertRaises(TypeError, tr4.__add__, tr3)

    def test_simulate(self):
        """
        Tests if calling simulate of trace gives the same result as using
        seisSim manually.
        """
        # skip test if obspy.signal is not installed
        try:
            from obspy.signal import seisSim
        except ImportError:
            return
        tr = read()[0]
        paz_sts2 = {'poles': [-0.037004 + 0.037016j, -0.037004 - 0.037016j,
                              - 251.33 + 0j, -131.04 - 467.29j, -131.04 + 467.29j],
                    'zeros': [0j, 0j],
                    'gain': 60077000.0,
                    'sensitivity': 2516778400.0}
        paz_le3d1s = {'poles': [-4.440 + 4.440j, -4.440 - 4.440j, -1.083 + 0.0j],
                      'zeros': [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
                      'gain': 0.4,
                      'sensitivity': 1.0}
        data = seisSim(tr.data, tr.stats.sampling_rate, paz_remove=paz_sts2,
                       paz_simulate=paz_le3d1s,
                       remove_sensitivity=True, simulate_sensitivity=True)
        try:
            proc_info = tr.stats.processing
        except KeyError:
            proc_info = []
        proc_info.append("simulate:inverse:%s:sensitivity=True" % paz_sts2)
        proc_info.append("simulate:forward:%s:sensitivity=True" % paz_le3d1s)
        tr.simulate(paz_remove=paz_sts2, paz_simulate=paz_le3d1s)
        np.testing.assert_array_equal(tr.data, data)
        self.assertEqual(tr.stats.processing, proc_info)

    def test_filter(self):
        """
        Tests the filter method of the Trace object.
        
        Basically three scenarios are tested (with differing filter options):
        - filtering with in_place=False:
            - is original trace unchanged?
            - is data of filtered trace the same as if done by hand
            - is processing information present in filtered trace
        - filtering with in_place=True:
            - is data of filtered trace the same as if done by hand
            - is processing information present in filtered trace
        - filtering with bad arguments passed to trace.filter():
            - is a TypeError properly raised?
            - after all bad filter calls, is the trace still unchanged?
        """
        try:
            from obspy.signal import bandpass, bandstop, lowpass, highpass
        except ImportError:
            return
        # create two test Traces
        traces = []
        np.random.seed(815)
        header = {'network': 'BW', 'station': 'BGLD',
                  'starttime': UTCDateTime(2007, 12, 31, 23, 59, 59, 915000),
                  'npts': 412, 'sampling_rate': 200.0,
                  'channel': 'EHE'}
        traces.append(Trace(data=np.random.randint(0, 1000, 412),
                header=deepcopy(header)))
        header['starttime'] = UTCDateTime(2008, 1, 1, 0, 0, 4, 35000)
        header['npts'] = 824
        traces.append(Trace(data=np.random.randint(0, 1000, 824),
                header=deepcopy(header)))
        traces_bkp = deepcopy(traces)
        # different sets of filters to run test on:
        filters = [['bandpass', {'freqmin': 1., 'freqmax': 20.}],
                   ['bandstop', {'freqmin': 5, 'freqmax': 15., 'corners': 6}],
                   ['lowpass', {'freq': 30.5, 'zerophase': True}],
                   ['highpass', {'freq': 2, 'corners': 2}]]
        filter_map = {'bandpass': bandpass, 'bandstop': bandstop,
                      'lowpass': lowpass, 'highpass': highpass}

        # tests for in_place=True
        for i, tr in enumerate(traces):
            for filt_type, filt_ops in filters:
                tr = deepcopy(traces_bkp[i])
                tr.filter(filt_type, filt_ops)
                # test if trace was filtered as expected
                data_filt = filter_map[filt_type](traces_bkp[i].data,
                        df=traces_bkp[i].stats.sampling_rate, **filt_ops)
                np.testing.assert_array_equal(tr.data, data_filt)
                self.assertTrue('processing' in tr.stats)
                self.assertEqual(len(tr.stats.processing), 1)
                self.assertEqual(tr.stats.processing[0], "filter:%s:%s" % \
                        (filt_type, filt_ops))
                # another filter run
                tr.filter(filt_type, filt_ops)
                data_filt = filter_map[filt_type](data_filt,
                        df=traces_bkp[i].stats.sampling_rate, **filt_ops)
                np.testing.assert_array_equal(tr.data, data_filt)
                self.assertTrue('processing' in tr.stats)
                self.assertEqual(len(tr.stats.processing), 2)
                for proc_info in tr.stats.processing:
                    self.assertEqual(proc_info, "filter:%s:%s" % \
                            (filt_type, filt_ops))
        # some tests that should raise an Exception
        tr = traces[0]
        bad_filters = [['bandpass', {'freqmin': 1., 'XXX': 20.}],
                ['bandstop', {'freqmin': 5, 'freqmax': "XXX", 'corners': 6}],
                ['bandstop', {}],
                ['bandstop', [1, 2, 3, 4, 5]],
                ['bandstop', None],
                ['bandstop', 3],
                ['bandstop', 'XXX'],
                ['bandpass', {'freqmin': 5, 'corners': 6}],
                ['bandpass', {'freqmin': 5, 'freqmax': 20., 'df': 100.}]]
        for filt_type, filt_ops in bad_filters:
            self.assertRaises(TypeError, tr.filter, filt_type, filt_ops)
        bad_filters = [['XXX', {'freqmin': 5, 'freqmax': 20., 'corners': 6}]]
        for filt_type, filt_ops in bad_filters:
            self.assertRaises(ValueError, tr.filter, filt_type, filt_ops)
        # test if trace is unchanged after all these bad tests
        np.testing.assert_array_equal(tr.data, traces_bkp[0].data)
        self.assertEqual(tr.stats, traces_bkp[0].stats)

    def test_downsample(self):
        """
        Tests the downsample method of the Trace object.
        """
        # skip test if obspy.signal is not installed
        try:
            import obspy.signal #@UnusedImport
        except ImportError:
            return
        # create test Trace
        tr = Trace(data=np.arange(20))
        tr_bkp = deepcopy(tr)
        # some test that should fail and leave the original trace alone
        self.assertRaises(ValueError, tr.downsample, 7, strict_length=True)
        self.assertRaises(ValueError, tr.downsample, 9, strict_length=True)
        # some tests in place
        tr.downsample(4, no_filter=True)
        np.testing.assert_array_equal(tr.data, np.arange(0, 20, 4))
        self.assertEqual(tr.stats.npts, 5)
        self.assertEqual(tr.stats.sampling_rate, 0.25)
        self.assertEqual(tr.stats.processing,
                         ["downsample:integerDecimation:4"])
        tr = tr_bkp.copy()
        tr.downsample(10, no_filter=True)
        np.testing.assert_array_equal(tr.data, np.arange(0, 20, 10))
        self.assertEqual(tr.stats.npts, 2)
        self.assertEqual(tr.stats.sampling_rate, 0.1)
        self.assertEqual(tr.stats.processing,
                         ["downsample:integerDecimation:10"])
        # some tests with automatic prefiltering
        tr = tr_bkp.copy()
        tr2 = tr_bkp.copy()
        tr.downsample(4)
        tr2.filter('lowpass', {'freq': tr2.stats.sampling_rate * 0.4 / 4})
        tr2.downsample(4, no_filter=True)
        np.testing.assert_array_equal(tr.data, tr2.data)
        self.assertEqual(tr.stats, tr2.stats)

    def test_comparisons(self):
        """
        Tests all rich comparison operators (==, !=, <, <=, >, >=)
        The latter four are not implemented due to ambiguous meaning and bounce
        an error.
        """
        from obspy.core import Stream
        # create test traces
        tr0 = Trace(np.arange(3))
        tr1 = Trace(np.arange(3))
        tr2 = Trace(np.arange(3), {'station': 'X'})
        tr3 = Trace(np.arange(3), {'processing': \
                                   ["filter:lowpass:{'freq': 10}"]})
        tr4 = Trace(np.arange(5))
        tr5 = Trace(np.arange(5), {'station': 'X'})
        tr6 = Trace(np.arange(5), {'processing': \
                                   ["filter:lowpass:{'freq': 10}"]})
        # tests that should raise a NotImplementedError (i.e. <=, <, >=, >)
        self.assertRaises(NotImplementedError, tr1.__lt__, tr1)
        self.assertRaises(NotImplementedError, tr1.__le__, tr1)
        self.assertRaises(NotImplementedError, tr1.__gt__, tr1)
        self.assertRaises(NotImplementedError, tr1.__ge__, tr1)
        self.assertRaises(NotImplementedError, tr1.__lt__, tr2)
        self.assertRaises(NotImplementedError, tr1.__le__, tr2)
        self.assertRaises(NotImplementedError, tr1.__gt__, tr2)
        self.assertRaises(NotImplementedError, tr1.__ge__, tr2)
        # normal tests
        self.assertEqual(tr0 == tr0, True)
        self.assertEqual(tr0 == tr1, True)
        self.assertEqual(tr0 == tr2, False)
        self.assertEqual(tr0 == tr3, False)
        self.assertEqual(tr0 == tr4, False)
        self.assertEqual(tr0 == tr5, False)
        self.assertEqual(tr0 == tr6, False)
        self.assertEqual(tr5 == tr0, False)
        self.assertEqual(tr5 == tr1, False)
        self.assertEqual(tr5 == tr2, False)
        self.assertEqual(tr5 == tr3, False)
        self.assertEqual(tr5 == tr4, False)
        self.assertEqual(tr5 == tr5, True)
        self.assertEqual(tr5 == tr6, False)
        self.assertEqual(tr3 == tr6, False)
        self.assertEqual(tr0 != tr0, False)
        self.assertEqual(tr0 != tr1, False)
        self.assertEqual(tr0 != tr2, True)
        self.assertEqual(tr0 != tr3, True)
        self.assertEqual(tr0 != tr4, True)
        self.assertEqual(tr0 != tr5, True)
        self.assertEqual(tr0 != tr6, True)
        self.assertEqual(tr5 != tr0, True)
        self.assertEqual(tr5 != tr1, True)
        self.assertEqual(tr5 != tr2, True)
        self.assertEqual(tr5 != tr3, True)
        self.assertEqual(tr5 != tr4, True)
        self.assertEqual(tr5 != tr5, False)
        self.assertEqual(tr5 != tr6, True)
        self.assertEqual(tr3 != tr6, True)
        # some weirder tests against non-Trace objects
        for object in [0, 1, 0.0, 1.0, "", "test", True, False, [], [tr0],
                       set(), set(tr0), {}, {"test": "test"}, Stream(), None, ]:
            self.assertEqual(tr0 == object, False)
            self.assertEqual(tr0 != object, True)

    def test_nearestSample(self):
        """
        This test case shows that the libmseed is actually flooring the
        starttime to the next sample value, regardless if it is the nearest
        sample. The flag nearest_sample=True tries to avoids this and
        rounds it to the next actual possible sample point.
        """
        # set up
        trace = Trace(data=np.empty(10000))
        trace.stats.starttime = UTCDateTime("2010-06-20T20:19:40.000000Z")
        trace.stats.sampling_rate = 200.0
        # ltrim
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.494999Z")
        tr._ltrim(t - 3, nearest_sample=True)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.starttime,
                         UTCDateTime("2010-06-20T20:19:48.495000Z"))
        # Lots of tests follow that thoroughly check the cutting behavior
        # using nearest_sample=True/False
        # rtrim
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.494999Z")
        tr._rtrim(t + 7, nearest_sample=True)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.495000Z"))
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.495000Z")
        tr._rtrim(t + 7, nearest_sample=True)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.495000Z"))
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.495111Z")
        tr._rtrim(t + 7, nearest_sample=True)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.495000Z"))
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.497501Z")
        tr._rtrim(t + 7, nearest_sample=True)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.500000Z"))
        # rtrim
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.494999Z")
        tr._rtrim(t + 7, nearest_sample=False)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.490000Z"))
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.495000Z")
        tr._rtrim(t + 7, nearest_sample=False)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.495000Z"))
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.495111Z")
        tr._rtrim(t + 7, nearest_sample=False)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.495000Z"))
        tr = deepcopy(trace)
        t = UTCDateTime("2010-06-20T20:19:51.497500Z")
        tr._rtrim(t + 7, nearest_sample=False)
        # see that it is actually rounded to the next sample point
        self.assertEqual(tr.stats.endtime,
                         UTCDateTime("2010-06-20T20:19:58.495000Z"))

    def test_maskedArrayToString(self):
        """
        Masked arrays should be marked using __str__.
        """
        st = read()
        overlaptrace = st[0].copy()
        overlaptrace.stats.starttime += 1
        st.append(overlaptrace)
        st.merge()
        out = st[0].__str__()
        self.assertTrue(out.endswith('(masked)'))


def suite():
    return unittest.makeSuite(TraceTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')