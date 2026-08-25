
# **Project Evals Champion: 4-Hour Local Harness Bootcamp**

**Objective:** Build local scaffolding for advanced evaluation paradigms: SDK Evals, Multimedia (Actor-Critic), ADK (Trajectory), and Antigravity (Artifact/State). **Environment:** Local Python IDE, Vertex AI SDK, Application Default Credentials (`gcloud auth application-default login`).

## 🗓️ Tomorrow's Agenda

* **08:00 \- 09:00 | Hour 1: SDK Evals.** Automating Pointwise metrics over a dataset.  
* **09:00 \- 10:00 | Hour 2: Multimedia "Actor-Critic" Loop.** Building a self-correcting image generator.  
* **10:00 \- 11:00 | Hour 3: ADK Trajectory Evals.** Evaluating *how* an agent thinks (tool use), not just what it says.  
* **11:00 \- 12:00 | Hour 4: Antigravity / Workspace Evals.** Evaluating artifacts and side-effects (e.g., did the code it wrote actually execute?).

&nbsp;

---

## 🤖 The SPECS (Feed these directly to your local Gemini Assistant)

### **📝 Spec 1: SDK Evals (Feed at 08:00)**

**Context:** I want to build a local Python evaluation harness using the Google Cloud `vertexai.evaluation` SDK. I am moving away from manual vibe-checks and need a script to mathematically score a dataset. **Task:** Write a complete, runnable Python script that does the following:

&nbsp;

1. Initializes Vertex AI. Instruct the user to set their `PROJECT_ID` and `LOCATION`.  
2. Creates a mock Pandas DataFrame with columns: `prompt`, `response`, and `reference`. Include 3 rows of example data representing a text summarization task (one great response, one hallucinated response, one unsafe response).  
3. Configures an `EvalTask`. Use standard metrics suitable for this dataset: `fluency`, `safety`, and `rouge_l`.  
4. Executes the evaluation task on the DataFrame using `gemini-1.5-pro` as the judge.  
5. Prints the summarized evaluation results and the detailed row-by-row metrics to the terminal in a clean tabular format.

### **📝 Spec 2: Multimedia Actor-Critic Loop (Feed at 09:00)**

**Context:** You cannot use simple math (like BLEU/ROUGE) to grade an image. I want to build a self-correcting image generation loop locally using Python, where an "Actor" generates an image, and a "Critic" (Gemini Vision) grades it and fixes the prompt. **Task:** Write a Python script using the Vertex AI SDK that does the following:

&nbsp;

1. **The Actor:** Create a function that takes a text prompt and generates an image using the Imagen 3 model, saving it locally as `iteration_{n}.jpg`.  
2. **The Critic:** Create a function that passes the generated image AND the original prompt to `gemini-1.5-pro`. The system prompt must instruct Gemini to act as a strict art critic and output a structured JSON response. **CRITICAL:** Use `response_schema` or `response_mime_type="application/json"` to force the JSON.  
* The JSON must contain: `score` (int 1-10), `missing_elements` (list of strings), and `improved_prompt` (string \- rewritten to fix the missing elements).  
3. **The Loop:** Write a `while` loop (max 3 iterations). Start with the prompt: *"A hyper-realistic photo of exactly three red apples resting on a rustic wooden table."* Generate the image, run the Critic, print the JSON critique to the console, and if the score is \< 9, use the `improved_prompt` for the next iteration.

### **📝 Spec 3: ADK Trajectory Evals (Feed at 10:00)**

**Context:** I am preparing to evaluate agent trajectories using concepts from Google's Agent Development Kit (ADK). Standard text evals fail here; we must evaluate the "trajectory" (the sequence of tools the agent decided to use). **Task:** Write a Python script that mathematically grades an agent's execution path without using an LLM to grade it.

&nbsp;

1. Create a mock JSON variable representing a successful agent trajectory: `{"task": "Find the capital of France and email it to bob@example.com", "steps": [{"action": "search", "input": "capital of France", "result": "Paris"}, {"action": "send_email", "to": "bob@example.com", "body": "The capital is Paris"}]}`  
2. Create a second mock JSON variable representing a failing trajectory (e.g., the agent emails *before* searching, or hallucinates the city).  
3. Write an `evaluate_trajectory(trajectory_json)` function in pure Python that iterates through the steps. It should return `True` ONLY IF:  
* A "search" action occurs *before* a "send\_email" action in the list.  
* The `result` string from the search is present in the `body` string of the email.  
4. Run the function on both JSON payloads and print the results cleanly.

### **📝 Spec 4: Antigravity Workspace Evals (Feed at 11:00)**

**Context:** In Antigravity (Google's agent workspace platform), agents modify files and write code. You ignore the chat window and evaluate the actual artifacts and side-effects. **Task:** Write a Python testing harness using `pytest` that verifies a side-effect on the local file system.

&nbsp;

1. **Setup:** In a pytest fixture, create a temporary directory called `./workspace/`.  
2. **Mock Agent Action:** Write a mock function `run_agent()` that simulates an agent. This function should write a file named `calculator.py` into the `./workspace/` directory containing a simple `def add(a, b): return a + b` function.  
3. **The Eval (Test 1 \- Artifact Check):** Write a test that asserts `./workspace/calculator.py` exists on disk.  
4. **The Eval (Test 2 \- Side-Effect Check):** Write a test that dynamically imports `calculator.py` from the workspace, executes `calculator.add(5, 5)`, and asserts that the result equals `10`.  
5. **Teardown:** Ensure the workspace is deleted after the tests run.

&nbsp;

---

### **🚀 Pre-flight Checklist for Tomorrow:**

1. Make sure your local Python environment (e.g., `venv` or `conda`) is active.  
2. Run `pip install google-cloud-aiplatform pytest pandas`.  
3. Run `gcloud auth application-default login` so your local machine is ready to talk to GCP.

&nbsp;

Have a great build session tomorrow\! Let me know when you kick this off and if you hit any roadblocks parsing the JSON in Hour 2\.

&nbsp;

