# HERMES - Microphone

Support package to interface built-in or external microphones.

The audio is captured continuously in configurable chunks of samples to balance latency with efficiency;
audio is written to audio files (MP3, WAV, M4A), while arrival timestamps of each chunks are flushed to HDF5 to align audio with other experimental HERMES data. 

## Installation
Node available under the same HERMES namespace of `hermes.mic` as `MicrophoneProducer`.

### From PyPI
```bash
pip install pysio-hermes-mic
```

### From source
```bash
git clone https://github.com/maximyudayev/hermes-mic.git
pip install -e hermes-mic
```

## Usage
Using the device follows the standard [configuration file specification](https://yudayev.com/hermes) process of HERMES nodes.

Some useful commands on Linux, Windows, and macOS to enumerate detected microphones. Use the names of the devices to update the HERMES YAML configuration file.

#### List available devices

*Windows:*
```
ffmpeg -list_devices true -f dshow -i dummy
```

*Linux (Pulse or Alsa):*
```
pactl list short sources
```
```
arecord -l
```

*macOS:*
```
ffmpeg -f avfoundation -list_devices true -i ""
```

#### Check the working settings of a detected device

*Windows:*
```
ffmpeg -list_options true -f dshow -i audio="Microphone (Realtek(R) Audio)"
```

*Linux:*
```
ffmpeg -list_options true -f [alsa|pulse] -i "hw:0,0"```

*macOS:*
```
ffmpeg -list_options true -f avfoundation -i ":default"
```

#### Test record a local device with those settings:

*Windows:*
```
ffmpeg -f dshow -i audio="Microphone (Realtek(R) Audio)" -t 10 -ar 48000 -ac 1 -c:a pcm_s16le test_output.wav
```

*Linux (Pulse or Alsa):*
```
ffmpeg -f pulse -i default -t 10 -ar 48000 -ac 1 -c:a pcm_s16le test_output.wav
```
```
ffmpeg -f alsa -i hw:0,0 -t 10 -ar 48000 -ac 1 -c:a pcm_s16le test_output.wav
```

*macOS:*
```
ffmpeg -f avfoundation -i ":default" -t 10 -ar 48000 -ac 1 -c:a pcm_s16le test_output.wav
```

## Citation
When using any parts of this repository outside of its intended use, please cite the parent project [HERMES](https://github.com/maximyudayev/hermes).
