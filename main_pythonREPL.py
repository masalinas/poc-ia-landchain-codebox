from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_experimental.utilities import PythonREPL

# 1. Creamos el "CodeBox" básico (REPL de Python)
python_repl = PythonREPL()

# 2. Definimos la herramienta que usará el modelo local
@tool
def code_box_interpreter(code: str) -> str:
    """Ejecuta código Python en un entorno aislado (CodeBox) y devuelve la salida. 
    Útil para cálculos complejos, algoritmos, lógica o manipulación de datos."""
    try:
        # Limpiamos posibles formatos de markdown que a veces los modelos locales añaden por error
        clean_code = code.strip().strip("```python").strip("```")
        result = python_repl.run(clean_code)
        return f"Resultado de la ejecución:\n{result}"
    except Exception as e:
        return f"Error al ejecutar el código: {str(e)}"

# 3. Inicializamos el modelo desde tu Ollama local
# Usamos un modelo con buen soporte de Tool Calling y temperature 0 para mayor precisión
llm = ChatOllama(
    model="hf.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF:latest", 
    temperature=0
)

tools = [code_box_interpreter]

# 4. Creamos el agente reactivo de LangGraph
agent_executor = create_agent(
    llm,
    tools
)

# 5. Ejecución de prueba
instruccion = "¿Cuál es el número primo número 150? Calcúlalo escribiendo un script en Python."
print(f"Usuario: {instruccion}\n")

# El agente entra en el bucle: piensa -> llama a la herramienta -> lee resultado -> responde
inputs = {"messages": [("user", instruccion)]}
response = agent_executor.invoke(inputs)

# Mostramos el mensaje final generado por tu Ollama local
print(f"Agente: {response['messages'][-1].content}")