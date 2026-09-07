import asyncio
import random


class ChannelSimulator:
    """
    Simulates real-world network degradation: packet loss, latency, and jitter.
    Sits between the relay's receive and forward steps.
    """

    def __init__(self, loss_rate=0.0, base_latency_ms=0, jitter_ms=0):
        self.loss_rate = loss_rate          # 0.0 - 1.0 (e.g. 0.1 = 10% of packets dropped)
        self.base_latency_ms = base_latency_ms
        self.jitter_ms = jitter_ms
        self.packets_seen = 0
        self.packets_dropped = 0

    def should_drop(self):
        self.packets_seen += 1
        dropped = random.random() < self.loss_rate
        if dropped:
            self.packets_dropped += 1
        return dropped

    async def apply_delay(self):
        jitter = random.uniform(-self.jitter_ms, self.jitter_ms) if self.jitter_ms else 0
        delay_ms = max(0, self.base_latency_ms + jitter)
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)

    def stats(self):
        actual_loss_rate = self.packets_dropped / self.packets_seen if self.packets_seen else 0
        return {
            "packets_seen": self.packets_seen,
            "packets_dropped": self.packets_dropped,
            "configured_loss_rate": self.loss_rate,
            "actual_loss_rate": round(actual_loss_rate, 3),
        }