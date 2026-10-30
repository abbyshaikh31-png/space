import statistics, json

RAW = [52,55,58,54,57,60,53,56,59,61,57,55,95,62,58,60,56,59,63,58,0,0,94,59]

def preprocess(raw):
    cpu, synth, i = [], [], 0
    while i < len(raw):
        if raw[i] == 0:
            prev, j = raw[i-1], i
            while raw[j] == 0: j += 1
            nxt = raw[j]
            for k in range(i, j):
                cpu.append(round(prev + (nxt-prev)*(k-i+1)/(j-i+1), 1))
                synth.append(True)
            i = j
        else:
            cpu.append(raw[i]); synth.append(False); i += 1
    return cpu, synth

def rolling_ucl(cpu, synth, k=10, mult=2.5):
    ucl = [None]
    for t in range(1, len(cpu)):
        w = [cpu[x] for x in range(max(0, t-k+1), t+1) if not synth[x]]
        ucl.append(round(statistics.mean(w)+mult*statistics.stdev(w), 2) if len(w) >= 2 else None)
    return ucl

cpu, synth = preprocess(RAW)
ucl = rolling_ucl(cpu, synth)
flags = [v if ucl[t] is not None and v > ucl[t] and not synth[t] else None for t, v in enumerate(cpu)]
mc, c = 0, 0
for f in flags:
    c = c+1 if f else 0
    mc = max(mc, c)
status = "SYSTEM_ALERT" if mc > 3 else "NOMINAL"
print(json.dumps({"cpu": cpu, "ucl": ucl, "flags": flags, "status": status, "max_consec": mc}))
