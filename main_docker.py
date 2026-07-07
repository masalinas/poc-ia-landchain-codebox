import os
import re
import docker

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent

# Initialize the Docker client (looks for your local running Docker Desktop/Daemon)
docker_client = docker.from_env()

def extract_code(raw: str) -> str:
    raw = raw.strip()

    # Match a fenced code block with optional language tag
    match = re.search(r"```(?:python)?\s*\n?(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()

    return raw  # no fence present, return as-is

@tool
def docker_code_box(code: str) -> str:
    # """Executes Python code safely inside an isolated Docker container (CodeBox) 
    # and returns the stdout/stderr. Use this for computations or data processing."""
    """Executes Python code safely inside an isolated Docker container (CodeBox) 
    and returns the stdout/stderr. Use this for computations, file reading, or data processing.
    
    Any files you want to analyze (like Excel/CSV files) are located in the '/data' directory.
    """    
    clean_code = extract_code(code)
    
    # Define where your local files are located on the computer
    host_data_dir = "/Users/miguel/git/poc-ia-landchain-codebox/data"
    temp_script_name = "agent_script.py"
    host_script_path = os.path.join(host_data_dir, temp_script_name)

    # We inject the auto-installation directly into the file before the agent code.
    # We use triple single quotes to avoid any formatting conflicts.
    full_script_content = f'''import re, subprocess, sys

# 1. Scan the file itself to determine which libraries the agent requires.
with open(__file__, 'r', encoding='utf-8') as f:
    code_content = f.read()

# We look for all import lines
imports = set(re.findall(r'^(?:import|from)\\s+([a-zA-Z0-9_]+)', code_content, re.M))
std_libs = {{'sys', 'os', 're', 'math', 'json', 'datetime', 'io', 'collections', 'time', 'subprocess'}}
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
{clean_code}
'''

    # 2. Escribir el script del agente en el volumen local
    with open(host_script_path, "w", encoding="utf-8") as f:
        f.write(full_script_content)

    try:
        container_output = docker_client.containers.run(
            image="python:3.11-slim",
            command=["python3", f"/data/{temp_script_name}"],           
            mem_limit="512m",            
            remove=True,
            stderr=True,
            volumes={
                host_data_dir: {
                    'bind': '/data',
                    'mode': 'ro' # Read-Only for safety
                } 
            }            
        )

        return f"Execution Success:\n{container_output.decode('utf-8')}"
    
    except docker.errors.ContainerError as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else str(e)
        return f"Execution Error (Code Failed):\n{stderr}"
    except docker.errors.APIError as e:
        return f"System Error: Docker API failed. Details: {str(e)}"
    except Exception as e:
        return f"System Error: Could not execute code. Details: {str(e)}"

# 1. Local Model via Ollama
llm = ChatOllama(model="hf.co/unsloth/Llama-3.2-3B-Instruct-GGUF:latest", temperature=0)

# 2. Tools
tools = [docker_code_box]

# 3. Build and Run the Agent
agent_executor = create_agent(
    llm,
    tools,
    system_prompt="You are a helpful assistant. Use the docker_code_box tool for any computation."
)

# 4. Test it out!
#instruction = "What is the result of 2**10 multiplied by 5? Use the docker code box"
instruction = "Read the Excel file located at /data/metrics_pi_m.xlsx using pandas. Calculate the mean of all the numeric columns and print a brief summary of the results."
print(f"Usuario: {instruction}\n")

# The agent enters the loop: think -> call tool -> read result -> respond
inputs = {"messages": [("user", instruction)]}
response = agent_executor.invoke(inputs)

print(f"Agent: {response['messages'][-1].content}")