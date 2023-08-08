import pandas as pd
import re
import matplotlib.pyplot as plt
import statistics

with open('6_sat.txt', 'r') as file:
    data = file.read()

latencies = re.findall(r'Latency for message: (\d+) ms', data)
times = re.findall(r'Current time: (\d+:\d+:\d+)', data)

df = pd.DataFrame({'Latency (ms)': latencies, 'Time': times})

df['Latency (ms)'] = pd.to_numeric(df['Latency (ms)'])

median_latency = statistics.median(df['Latency (ms)'])

plt.plot(df['Time'], df['Latency (ms)'])
plt.xlabel('Time')
plt.ylabel('Latency (ms)')
plt.title('Latency (ms) with 6 satellites in FireSat')
plt.xticks(rotation=45)

plt.text(0.5, 0.95, f'Median Latency: {median_latency} ms',
         horizontalalignment='center', verticalalignment='center',
         transform=plt.gca().transAxes)

plt.show()
