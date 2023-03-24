import numpy as np
import random

# Define system parameters
m = 5  # number of rows
n = 5  # number of columns
r = 3  # number of consecutive failures in a row
s = 3  # number of consecutive failures in a column
failure_rate = 0.1  # failure rate of each component

# Initialize system components
components = np.ones((m, n), dtype=int)

# Define repair kit parameters
replacement_parts = {"roller": 10, "bearing": 20, "belt": 2}
tools = ["screwdriver", "wrench", "hammer"]


# Define repair function
def repair_component(row, col, repair_kit):
    # Simulate repair time using a normal distribution with mean 2 hours and standard deviation 0.5 hours
    repair_time = random.normalvariate(2, 0.5)

    # Simulate repair effectiveness using a beta distribution with parameters alpha=2 and beta=2
    effectiveness = random.betavariate(2, 2)

    # Apply repair to component with probability equal to the repair effectiveness
    if random.random() < effectiveness:
        # Update component to indicate that it is functional
        components[row][col] = 1
        return repair_time, effectiveness
    else:
        # Component remains non-functional
        return repair_time, 0


# Simulate system over a period of 1000 hours
total_time = 1000
time = 0
failures = 0

while time < total_time:
    # Simulate component failures using a Poisson process with rate equal to the failure rate
    failures += np.sum(np.random.poisson(failure_rate, size=(m, n)) * components)

    # Check for consecutive failures in rows and columns
    for i in range(m):
        for j in range(n - r + 1):
            if np.sum(components[i, j : j + r]) == r:
                # Repair failed components using repair kit
                repair_time, effectiveness = repair_component(
                    i, j, {"parts": replacement_parts, "tools": tools}
                )
                time += repair_time
                if np.random.random() < effectiveness:
                    # Repair successful
                    failures -= r

    for j in range(n):
        for i in range(m - s + 1):
            if np.sum(components[i : i + s, j]) == s:
                # Repair failed components using repair kit
                repair_time, effectiveness = repair_component(
                    i, j, {"parts": replacement_parts, "tools": tools}
                )
                time += repair_time
                if np.random.random() < effectiveness:
                    # Repair successful
                    failures -= s

    # Check if system has failed
    if failures >= r * (m - r + 1) or failures >= s * (n - s + 1):
        # System has failed
        break

    # Increment time
    time += 1

# Calculate system reliability as the proportion of time during which the system is operational
reliability = 1 - failures / (m * n)

print("System reliability: {:.2f}%".format(reliability * 100))
