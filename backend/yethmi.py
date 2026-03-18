import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Load Excel file

file_path = r"yethmi.xlsx"   # Excel file in the same folder
df = pd.read_excel(file_path)

# Extract Monthly Mean Sunspot Number (SSN)
SSN = df["Monthly mean total sunspot number"].astype(float).values
SSN = SSN[SSN >= 0]  # remove invalid values


#  Polynomial coefficients 

# Order 1
C1 = dict(C0=62.31, C1=0.6432)

# Order 2
C2 = dict(C0=62.87, C1=0.6279, C2=1.478e-2)

# Order 3
C3 = dict(C0=65.64, C1=0.9457, C2=1.304e-3, C3=-2.919e-6)

# Order 4
C4 = dict(C0=67.73, C1=1.1348, C2=3.690e-3, C3=-7.197e-5, C4=3.773e-7)

#  Polynomial models

def poly1(N):
    return C1["C0"] + C1["C1"] * N

def poly2(N):
    return C2["C0"] + C2["C1"] * N + C2["C2"] * N**2

def poly3(N):
    return (C3["C0"] + C3["C1"] * N +
            C3["C2"] * N**2 +
            C3["C3"] * N**3)

def poly4(N):
    return (C4["C0"] + C4["C1"] * N +
            C4["C2"] * N**2 +
            C4["C3"] * N**3 +
            C4["C4"] * N**4)


#  Compute F10.7 values

F1 = poly1(SSN)
F2 = poly2(SSN)
F3 = poly3(SSN)
F4 = poly4(SSN)


#  Plot SSN vs F10.7

plt.figure(figsize=(8, 6))

plt.scatter(SSN, F1, s=6, label="Order 1 Polynomial", alpha=0.6)
plt.scatter(SSN, F2, s=6, label="Order 2 Polynomial", alpha=0.6)
plt.scatter(SSN, F3, s=6, label="Order 3 Polynomial", alpha=0.6)
plt.scatter(SSN, F4, s=6, label="Order 4 Polynomial", alpha=0.6)

plt.xlabel("Sunspot Number (SSN)")
plt.ylabel("F10.7 Index (SFU)")
plt.title("Relationship Between SSN and F10.7 (Clette, 2021)")
plt.legend()
plt.grid(True)

plt.show()
