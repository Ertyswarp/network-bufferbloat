"""Regression checks for deterministic service and DropTail buffer semantics."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from simulator import Config, arrivals_for, simulate


class SimulatorTests(unittest.TestCase):
    def test_one_packet_no_wait(self):
        result, _ = simulate(Config(capacity=0, arrival_rate=1, service_rate=1, warmup=0, duration=3), [0.0])
        self.assertEqual(result.arrivals, 1)
        self.assertEqual(result.drops, 0)
        self.assertEqual(result.departures, 1)
        self.assertAlmostEqual(result.mean_queue_wait_ms, 0.0)
        self.assertAlmostEqual(result.mean_system_delay_ms, 1000.0)

    def test_full_buffer_tail_drop(self):
        cfg = Config(capacity=1, arrival_rate=1, service_rate=1, warmup=0, duration=4)
        r, _ = simulate(cfg, [0.0, 0.1, 0.2])
        self.assertEqual((r.arrivals, r.drops, r.departures), (3, 1, 2))
        self.assertAlmostEqual(r.mean_queue_wait_ms, 450.0)
        self.assertEqual(r.max_queue_packets, 1)

    def test_departure_first_at_same_timestamp(self):
        r, _ = simulate(Config(capacity=0, arrival_rate=1, service_rate=1, warmup=0, duration=3), [0.0, 1.0])
        self.assertEqual((r.drops, r.departures), (0, 2))

    def test_reproducible(self):
        c = Config(seed=42, traffic="bursty")
        self.assertEqual(arrivals_for(c), arrivals_for(c))
        self.assertEqual(simulate(c)[0], simulate(c)[0])

    def test_utilization_and_queue_area(self):
        c = Config(capacity=1, arrival_rate=1, service_rate=1, warmup=0, duration=2)
        r, _ = simulate(c, [0.0, 0.5])
        self.assertAlmostEqual(r.utilization_pct, 100)
        self.assertAlmostEqual(r.mean_queue_packets, 0.25)
        self.assertAlmostEqual(r.throughput_pps, 0.5)  # second departure exactly at end is excluded

    def test_no_arrivals(self):
        r, _ = simulate(Config(warmup=0, duration=1), [])
        self.assertEqual(r.loss_pct, 0)
        self.assertEqual(r.throughput_pps, 0)

    def test_invalid_config_and_unsorted_arrivals(self):
        with self.assertRaises(ValueError):
            simulate(Config(capacity=-1))
        with self.assertRaises(ValueError):
            simulate(Config(warmup=0, duration=2), [1.1, 0.4])


if __name__ == "__main__":
    unittest.main()
