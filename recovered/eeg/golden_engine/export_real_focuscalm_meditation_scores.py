import pandas as pd
import numpy as np
from reconstruct_meditation_features import meditation_features
from run_fusi_network import load_network, run_network

df = pd.read_csv("fc11_stream_1781471387_eeg.csv")
eeg = df["raw_s24"].to_numpy(dtype=np.float64)

net = load_network("meditation")

win = 800
step = 160
rows = []

for start in range(0, len(eeg) - win + 1, step):
    window = eeg[start:start+win]
    window = window - np.mean(window)
    features = meditation_features(window)
    out = run_network(net, features)

    rows.append({
        "sample_start": start,
        "sample_end": start + win,
        "score0": float(out[0] * 100),
        "score1": float(out[1] * 100),
        "meditation_candidate": float(out[1] * 100),
    })

pd.DataFrame(rows).to_csv("focuscalm_meditation_scores.csv", index=False)
print("written focuscalm_meditation_scores.csv")
