import re, subprocess, sys

# 1. Scan the file itself to determine which libraries the agent requires.
with open(__file__, 'r', encoding='utf-8') as f:
    code_content = f.read()

# We look for all import lines
imports = set(re.findall(r'^(?:import|from)\s+([a-zA-Z0-9_]+)', code_content, re.M))
std_libs = {'sys', 'os', 're', 'math', 'json', 'datetime', 'io', 'collections', 'time', 'subprocess'}
to_install = imports - std_libs

# If the agent requests pandas, we add openpyxl as a backend—a best practice for Excel.
if 'pandas' in imports:
    to_install.add('openpyxl')

# 2. Install dependencies if necessary
if to_install:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '--quiet'] + list(to_install))

# =====================================================================
# AGENT CODE BELOW:
# =====================================================================
import pandas as pd
import numpy as np
from io import StringIO
import sys
# Load data from Excel file
df = pd.read_excel('/data/metrics_pi_m.xlsx')
# Calculate mean of numeric columns
mean_values = df.select_dtypes(include=[np.number]).mean()
# Print brief summary of results
print(mean_values)
# Redirect stdout to capture output
stdout, stderr = sys.stdout, sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()
try:
    # Execute code here
    mean_values = df.select_dtypes(include=[np.number]).mean()
    print(mean_values)
except Exception as e:
    print(str(e))
finally:
    # Restore original stdout and stderr
    sys.stdout = stdout
    sys.stderr = stderr
