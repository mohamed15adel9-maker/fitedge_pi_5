# Choose the backend: "llama_cpp" on the laptop, "ollama" on the Pi.
BACKEND = "llama_cpp"      # <-- change to "ollama" on the Pi

# ---------------- llama-cpp-python backend (laptop) ----------------
if BACKEND == "llama_cpp":
    from llama_cpp import Llama
    from pathlib import Path

    MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models" / "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
)
    _llm = Llama(model_path=str(MODEL_PATH), n_ctx=4096,verbose = False)

    def think(messages):
        try:
            response = _llm.create_chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=256,
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error in think: {e}")
            return "Sorry, I couldn't process that request."

# ---------------- Ollama backend (Pi) ----------------
elif BACKEND == "ollama":
    import ollama

    MODEL = "llama3.2:3b"   # match what you pulled on the Pi

    def think(messages):
        try:
            response = ollama.chat(
                model=MODEL,
                messages=messages,
                options={"temperature": 0.3, "num_predict": 256},
            )
            return response["message"]["content"].strip()
        except Exception as e:
            print(f"Error in think: {e}")
            return "Sorry, I couldn't process that request."