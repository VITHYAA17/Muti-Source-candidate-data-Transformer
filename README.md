
WHAT THIS PROJECT DOES:
----------------------
This project takes resume and candidate data from 6 different sources (like LinkedIn, GitHub, Excel/CSV files, ATS databases, Resumes, and Recruiter Notes), cleans up formatting, joins duplicate profiles together, and creates one unified profile per person.

It also computes a "Confidence Score" to show how much we can trust each detail, and logs a "Provenance Table" showing exactly where each field came from.


FOLDER STRUCTURE:
-----------------
* input/            <-- Put your raw CSV, JSON, and text resume files here.
* output/           <-- Where the final matched JSON results are saved.
* config/           <-- Where you control which fields to display in output.
* src/              <-- The Python code (parsers, merging, trust scores, UI server).
* tests/            <-- Test scripts to verify the code is working.


HOW TO SET UP:
--------------
1. Open your terminal in the "candidate-transformer" folder.
2. Install the required tools:
   pip install -r requirements.txt


HOW TO RUN AND SEE RESULTS:
---------------------------
1. Run the main ETL Pipeline:
   python src/main.py
   (This reads files from 'input/', merges duplicates, and writes the JSON outputs to the 'output/' folder).

2. Run the Interactive Web Browser Dashboard:
   python src/ui_server.py
   (Then, open http://localhost:8000 in your browser to click buttons, search, and view candidates).

3. Run the Automated Code Tests:
   python -m unittest discover -s tests -p "test_*.py"

4. Build the One-Page Design PDF:
   python generate_pdf.py
======================================================
