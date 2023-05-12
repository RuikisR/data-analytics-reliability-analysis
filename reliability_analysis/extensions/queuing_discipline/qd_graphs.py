import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


df = pd.read_csv("qd_data.csv")
# df = df.loc[df.M > 10]

for label, group in df.groupby("R"):
    plt.figure()
    plt.title(f"MTTF R=S={label}")
    plt.xlabel("M=N Lattice Size")
    plt.ylabel("MTTF")
    plt.plot(group.loc[group.SMART==True].M, group.loc[group.SMART==True].MTTF, label="Smart Queue", color="cyan")
    plt.plot(group.loc[group.SMART==False].M, group.loc[group.SMART==False].MTTF, label="Naive Queue", color="magenta")
    plt.legend()


for label, group in df.groupby("R"):
    plt.figure()
    plt.title(f"MTBF R=S={label}")
    plt.xlabel("M=N Lattice Size")
    plt.ylabel("MTBF")
    plt.plot(group.loc[group.SMART==True].M, group.loc[group.SMART==True].MTBF, label="Smart Queue", color="cyan")
    plt.plot(group.loc[group.SMART==False].M, group.loc[group.SMART==False].MTBF, label="Naive Queue", color="magenta")
    plt.legend()

plt.show()
