############
#
# Copyright (c) 2024-2026 Maxim Yudayev and KU Leuven eMedia Lab
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Created 2024-2025 for the KU Leuven AidWear, AidFOG, and RevalExo projects
# by Maxim Yudayev [https://yudayev.com].
#
# ############

from subprocess import DEVNULL

import ffmpeg
from hermes.utils.types import AudioFormatEnum
from hermes.utils.types import AudioBackendEnum
import random
from typing import Optional
import numpy as np

from hermes.utils.time_utils import get_time
from hermes.utils.zmq_utils import PORT_BACKEND, PORT_KILL, PORT_SYNC_HOST
from hermes.utils.types import LoggingSpec

from hermes.mic.data_container import MicrophoneDataContainer
from hermes.base.nodes.producer import Producer


class MicrophoneProducer(Producer):
    def __init__(
        self,
        node_id: str,
        host_ip: str,
        logging_spec: LoggingSpec,
        audio_format: Optional[str] = AudioFormatEnum.PCM_S16LE.value,
        audio_backend: Optional[str] = AudioBackendEnum.DSHOW.value,
        audio_device_name: Optional[str] = "Microphone (Realtek(R) Audio)",
        num_audio_channels: Optional[str] = 1,
        read_duration_s: Optional[float] = 0.020,
        audio_rate_hz: Optional[int] = 48_000,
        thread_queue_size: Optional[int] = 1024,
        audio_buffer_size: Optional[int] = 10,
        buf_len: Optional[int] = 1000,
        port_pub: Optional[str] = PORT_BACKEND,
        port_sync: Optional[str] = PORT_SYNC_HOST,
        port_killsig: Optional[str] = PORT_KILL,
        **_,
    ):
        self._audio_format = AudioFormatEnum[audio_format]
        self._audio_backend = AudioBackendEnum(audio_backend)
        self._audio_device_name = audio_device_name
        self._num_audio_channels = num_audio_channels
        self._audio_rate_hz = audio_rate_hz
        num_samples_per_chunk = round(read_duration_s * audio_rate_hz)
        self._read_size = (
            num_samples_per_chunk
            * num_audio_channels
            * self._audio_format.value.num_bytes
        )
        self._thread_queue_size = thread_queue_size
        self._audio_buffer_size = audio_buffer_size

        data_out_spec = {
            "audio_format": audio_format,
            "audio_backend": audio_backend,
            "audio_device_name": audio_device_name,
            "num_audio_channels": num_audio_channels,
            "num_sample_bytes": self._audio_format.value.num_bytes,
            "audio_rate_hz": self._audio_rate_hz,
            "buf_len": buf_len,
            "read_size": self._read_size,
            "read_duration_s": read_duration_s,
        }

        super().__init__(
            node_id=node_id,
            host_ip=host_ip,
            data_out_spec=data_out_spec,
            logging_spec=logging_spec,
            port_pub=port_pub,
            port_sync=port_sync,
            port_killsig=port_killsig,
        )

    @classmethod
    def create_data_container(cls, data_spec: dict) -> MicrophoneDataContainer:
        return MicrophoneDataContainer(**data_spec)

    def _ping_device(self) -> None:
        return None

    def _connect(self) -> bool:
        self._audio_stream = (
            ffmpeg.input(
                self._audio_device_name,
                format=self._audio_backend.value,
                thread_queue_size=self._thread_queue_size,
                audio_buffer_size=self._audio_buffer_size,
            )
            .output(
                "pipe:",
                format=self._audio_format.value.write_format,
                acodec=self._audio_format.value.codec,
                ar=self._audio_rate_hz,
                ac=self._num_audio_channels,
                fflags="nobuffer",
                flush_packets=1,
            )
            .global_args("-hide_banner")
        )

        return True

    def _keep_samples(self) -> None:
        self._audio_source = ffmpeg.run_async(
            self._audio_stream,
            pipe_stdout=True,
            pipe_stderr=True,
        )

    def _read_exact(self) -> bytearray:
        buffer = bytearray()
        while len(buffer) < self._read_size:
            chunk = self._audio_source.stdout.read(self._read_size - len(buffer))
            buffer.extend(chunk)
        return buffer

    def _process_data(self) -> None:
        if self._is_continue_capture:
            raw_audio = self._read_exact()
            toa_s = get_time()

            # Convert raw binary PCM bytes directly into a NumPy array for processing
            audio_chunk = np.frombuffer(raw_audio, dtype=f"S{self._read_size}")[None]

            self._publish(
                process_time_s=get_time(),
                new_data={
                    "mic": {
                        "samples": audio_chunk,
                        "toa_s": np.array([[toa_s]], dtype=np.float64),
                    },
                },
            )
        else:
            self._send_end_packet()

    def _stop_new_data(self):
        self._audio_source.kill()

    def _cleanup(self) -> None:
        self._audio_source.wait()
        super()._cleanup()
