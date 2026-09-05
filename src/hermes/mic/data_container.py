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

from collections import OrderedDict
from hermes.utils.types import AudioFormatEnum

from hermes.base.data_container import DataContainer


class MicrophoneDataContainer(DataContainer):
    def __init__(
        self,
        audio_format: str,
        audio_backend: str,
        audio_device_name: str,
        audio_rate_hz: int,
        num_sample_bytes: int,
        num_audio_channels: int,
        buf_len: int,
        read_size: int,
        read_duration_s: int,
        **_,
    ) -> None:
        super().__init__()

        self._audio_backend = audio_backend
        self._audio_device_name = audio_device_name
        self._num_audio_channels = num_audio_channels
        self._num_sample_bytes = num_sample_bytes
        self._audio_rate_hz = audio_rate_hz
        self._chunk_rate_hz = 1 / read_duration_s
        self._read_size = read_size
        self._define_data_notes()

        self.add_channel(
            bundle_name="mic",
            channel_name="samples",
            data_type=f"S{read_size}",
            sample_size=[1],
            buf_len=buf_len,
            sampling_rate_hz=self._audio_rate_hz,
            is_audio=True,
            audio_format=AudioFormatEnum[audio_format],
            num_audio_channels=num_audio_channels,
        )
        self.add_channel(
            bundle_name="mic",
            channel_name="toa_s",
            data_type="float64",
            sample_size=[1],
            buf_len=buf_len,
            sampling_rate_hz=self._chunk_rate_hz,
            data_notes=self._data_notes["mic"]["toa_s"],
        )

    def _define_data_notes(self):
        self._data_notes = {
            "mic": {
                "toa_s": OrderedDict(
                    [
                        ("Device name", self._audio_device_name),
                        ("Captured by", self._audio_backend),
                        ("Audio rate", f"{self._audio_rate_hz} Hz"),
                        ("Chunk rate", f"{self._chunk_rate_hz} Hz"),
                        ("Channels", f"{self._num_audio_channels}"),
                        ("Samples per chunk", f"{self._read_size / self._num_audio_channels / self._num_sample_bytes}"),
                        (
                            "Notes",
                            f"Time of arrival of a {self._read_size} bytes chunk of audio samples from {self._num_audio_channels} channels, "
                            f"{self._num_sample_bytes} bytes each, captured by FFmpeg subprocess from the host device ADC. "
                            f"Maps one-to-one to each {self._read_size} chunk of audio samples, and timestamps the newest audio sample in the chunk.",
                        ),
                    ]
                )
            }
        }
