from __future__ import annotations

import queue
import time
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

from whistleclipboard.config import AppConfig


@dataclass
class AudioChunk:
    samples: np.ndarray
    captured_at: float


class MicrophoneListener:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._queue: queue.Queue[AudioChunk] = queue.Queue(maxsize=64)
        self._stream: sd.InputStream | None = None

    def start(self) -> None:
        self._stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            blocksize=self.config.block_size,
            channels=self.config.channels,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def read(self, timeout: float = 1.0) -> AudioChunk:
        return self._queue.get(timeout=timeout)

    def _callback(self, indata, frames, callback_time, status) -> None:
        if status:
            print(f"[AUDIO STATUS] {status}")

        samples = np.squeeze(np.copy(indata))
        chunk = AudioChunk(samples=samples, captured_at=time.monotonic())

        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            # Keep the newest audio so detection stays low-latency under load.
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(chunk)
