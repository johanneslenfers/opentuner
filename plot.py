import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# plt.style('darkgrid')
# print(f"style: {plt.style.available}")
plt.style.use('seaborn-v0_8-darkgrid')


def plot_performance_evolution(db_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    
    # Query the results table
    query = """
    SELECT time
    FROM result
    WHERE time IS NOT NULL
    """
    data = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert to performance evolution by maintaining a running minimum
    data['performance'] = data['time'].cummin()

    print(f"Performance evolution:\n{data}")

    # Plot performance evolution with log scale
    plt.figure(figsize=(10, 6))
    plt.plot(data['performance'], linestyle="-", label="Performance Evolution")

    baseline: float =  0.011533
    baseline_O3: float = 0.003930


    plt.axhline(y=baseline, color='red', linestyle='--', linewidth=2, label='baseline')
    plt.axhline(y=baseline_O3, color='red', linestyle='--', linewidth=2, label='baseline -O3')

    # plt.xscale('log')  # Set log-scale for x-axis
    plt.yscale('log')  # Set log-scale for y-axis

    plt.title("Performance Evolution (Log-Scale)", fontsize=16)
    plt.xlabel("Sample", fontsize=14)
    plt.ylabel("Time (Log-Scale, Lower is Better)", fontsize=14)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend(fontsize=12)
    plt.tight_layout()

    plt.show()

# Replace with your .db file path
db_file = "llvm.db"
plot_performance_evolution(db_file)
