import pandas as pd
import numpy as np
from focuscalm_sample_decoder import scale_raw_s24
from reconstruct_meditation_features import meditation_features
from run_fusi_network import load_network, run_network

df = pd.read_csv("fc11_stream_1781471387_eeg.csv")

# raw_s24 is the signed 24-bit integer extracted from the BLE EEG chunk.
# The native pipeline scales it as sample = raw24 * 0.040690104166666664 / 128.
raw = df["raw_s24"].to_numpy(dtype=np.float64)
eeg = scale_raw_s24(raw)

# first 800-sample window
window = eeg[:800]

# the native FFT/moment code does *not* remove the mean, so we keep DC here.
features = meditation_features(window)
net = load_network("meditation")
out = run_network(net, features)

print("samples:", window.shape)
print("feature min/max:", features.min(), features.max())
print("network output:", out)
print("score candidate:", out[1] * 100)
