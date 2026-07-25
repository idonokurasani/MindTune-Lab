import pandas as pd
import numpy as np
from reconstruct_meditation_features import meditation_features
from run_fusi_network import load_network, run_network

df = pd.read_csv("fc11_stream_1781471387_eeg.csv")
eeg = df["raw_s24"].to_numpy(dtype=np.float64)

net = load_network("meditation")

win = 800
step = 160

scores = []

for start in range(0, len(eeg) - win + 1, step):
    window = eeg[start:start+win]
    window = window - np.mean(window)

    features = meditation_features(window)
    out = run_network(net, features)

    scores.append((start, out[0] * 100, out[1] * 100))

for row in scores[:20]:
    print(row)

print()
print("windows:", len(scores))
print("score0 mean/min/max:", np.mean([s[1] for s in scores]), np.min([s[1] for s in scores]), np.max([s[1] for s in scores]))
print("score1 mean/min/max:", np.mean([s[2] for s in scores]), np.min([s[2] for s in scores]), np.max([s[2] for s in scores]))
