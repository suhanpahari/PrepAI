import random
import subprocess
import speech_recognition as sr
from text2speach import speak_input  # Assuming this is a custom module
import platform
from llm_add import llm  # Assuming this is a custom module
from langchain_core.prompts import PromptTemplate
from datetime import datetime

# Function to get random question (unchanged)
def get_random_question(filename="question.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            questions = [q.strip() for q in file.readlines() if q.strip()]
        return random.choice(questions) if questions else None
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None

# Speech recognition function (unchanged)
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now.")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print("Processing speech...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return "No response"
        except sr.UnknownValueError:
            print("Could not understand the response.")
            return "Unclear response"
        except sr.RequestError:
            print("Speech recognition service error.")
            return "Error in recognition"

# Eye and face tracking functions (unchanged)
def start_eye_tracking():
    try:
        if platform.system() == "Windows":
            return subprocess.Popen(["start", "cmd", "/c", "python", "eye.py"], shell=True)
        elif platform.system() == "Darwin":
            return subprocess.Popen(["open", "-a", "Terminal", "python", "eye.py"])
        elif platform.system() == "Linux":
            return subprocess.Popen(["gnome-terminal", "--", "python", "eye.py"])
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"Error starting eye tracking: {e}")
        return None

def start_face_tracking():
    try:
        if platform.system() == "Windows":
            return subprocess.Popen(["start", "cmd", "/c", "python", "face.py"], shell=True)
        elif platform.system() == "Darwin":
            return subprocess.Popen(["open", "-a", "Terminal", "python", "face.py"])
        elif platform.system() == "Linux":
            return subprocess.Popen(["gnome-terminal", "--", "python", "face.py"])
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"Error starting face tracking: {e}")
        return None

# Generate evaluation response (unchanged)
def generate_currect_response(question, response):
    template = '''
    You are a question helper. You must check the response against the answer.
    
    If the answer is completely wrong, reply with a correct answer starting with 0.
    If the answer is correct, start with 1 (no need to reply further).
    If the answer is partially correct, start with 0.5 and provide a modified reply.

    Question: {question}
    Response: {response}

    Max word limit: 100.
    '''
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    try:
        response = chain.invoke(input={"question": question, "response": response})
        return response.content
    except Exception as e:
        print(f"Error generating disaster response: {e}")
        return "Error processing response"

# New function to generate LaTeX report
def generate_latex_report(candidate_name, participant_id, test_data):
    current_date = datetime.now().strftime("%B %d, %Y")
    
    latex_content = r'''\documentclass[a4paper,12pt]{article}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{array}
\usepackage{float}
\usepackage{wrapfig}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{booktabs}
\usepackage{fontawesome}
\usepackage{fancyhdr}
\usepackage{draftwatermark}

\geometry{margin=1in, headsep=1.5cm}
\SetWatermarkText{PrepAI}
\SetWatermarkScale{1.2}
\SetWatermarkColor{lightgray!30}

\definecolor{prepai-blue}{RGB}{255,20,147}
\definecolor{prepai-gray}{RGB}{200, 200, 200}

\titleformat{\section}
  {\normalfont\Large\bfseries\color{prepai-blue}}
  {\thesection}{1em}{}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\includegraphics[width=2cm]{PrepAI.jpg}}
\fancyhead[R]{\textbf{\color{prepai-blue} Interview Report}}
\fancyfoot[L]{\textbf{\color{prepai-blue} PrepAI} \\ \textit{Innovating Assessments}}
\fancyfoot[R]{\textbf{\color{prepai-blue} Page \thepage}}

\newcommand{\sectionline}{\noindent\rule{\linewidth}{1pt}}

\begin{document}

\begin{center}
    \textbf{\LARGE\color{prepai-blue} Interview Report}\\[1em]
    \textbf{Candidate Name:} ''' + candidate_name + r'''\\
    \textbf{Participant ID:} ''' + participant_id + r'''\\
    \textbf{Date:} ''' + current_date + r'''\\
\end{center}

\sectionline

\section*{Interview Questions and Answers}
\begin{enumerate}
'''
    
    # Add questions, answers, and evaluations
    for i, (question, answer, eval_response) in enumerate(test_data, 1):
        # Parse evaluation response
        if eval_response.startswith("0 "):
            correct_answer = eval_response[2:]
            eval_text = "0"
        elif eval_response.startswith("1"):
            correct_answer = ""
            eval_text = "1"
        elif eval_response.startswith("0.5 "):
            correct_answer = eval_response[4:]
            eval_text = "0.5"
        else:
            correct_answer = "Evaluation error"
            eval_text = "N/A"
        
        latex_content += r'''\item 
    \begin{minipage}{0.7\textwidth}
        \textbf{Question ''' + str(i) + r''':} ''' + question + r''' \\
        \textbf{Candidate's Answer:} ''' + answer + r''' \\
        \textbf{Correct Answer:} ''' + correct_answer + r'''
    \end{minipage}
    \hfill
    \begin{minipage}{0.28\textwidth}
        \begin{flushright}
            \small Score: ''' + eval_text + r'''
        \end{flushright}
    \end{minipage}
'''

    # Final remarks (basic scoring logic as an example)
    scores = [float(t[2].split()[0]) if t[2].startswith(("0 ", "1", "0.5 ")) else 0 for t in test_data]
    avg_score = sum(scores) / len(scores) if scores else 0
    performance = "Satisfactory" if avg_score >= 0.5 else "Needs Improvement"
    recommendation = "Recommended for further training" if avg_score < 1 else "Ready for role"

    latex_content += r'''\end{enumerate}

\sectionline

\newpage
\section*{Final Remarks}
\begin{itemize}
    \item \textbf{\faUser\ Performance:} ''' + performance + r'''
    \item \textbf{\faGraduationCap\ Recommendation:} ''' + recommendation + r'''
\end{itemize}

\vspace{2em}
\noindent\textbf{Interviewer Name:} Automated System \\
\textbf{Signature:} \makebox[3cm]{\hrulefill} \\
\textbf{Date:} ''' + current_date + r'''

\end{document}
'''

    # Write to file
    with open("interview_report.tex", "w", encoding="utf-8") as f:
        f.write(latex_content)

    # Compile LaTeX to PDF
    try:
        subprocess.run(["pdflatex", "interview_report.tex"], check=True)
        print("Report generated: interview_report.pdf")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling LaTeX: {e}")
    except FileNotFoundError:
        print("pdflatex not found. Please install a LaTeX distribution (e.g., TeX Live or MiKTeX).")

# Modified main function
def main():
    name = input("Enter your name: ")
    participant_id = input("Enter your ID: ")

    start = input("Start? (y/n): ").strip().lower()
    if start != "y":
        print("Exiting...")
        return

    print("Starting eye and face tracking in new windows...")
    eye_tracking_process = start_eye_tracking()
    face_tracking_process = start_face_tracking()

    test_data = []  # Store (question, answer, evaluation) tuples

    try:
        for i in range(5):
            print(f"\nQuestion {i + 1}:")
            
            question = get_random_question()
            if not question:
                print("No questions available. Exiting.")
                break

            print(question)
            speak_input(question)

            ready = input("Ready to answer? (y/n): ").strip().lower()
            if ready != "y":
                print("Skipping question...")
                continue

            answer = recognize_speech()
            print(f"Answer {i + 1}: {answer}")

            eval_response = generate_currect_response(question, answer)
            print("Evaluation:", eval_response)

            test_data.append((question, answer, eval_response))

    except KeyboardInterrupt:
        print("\nSession interrupted by user.")

    finally:
        print("\nStopping tracking processes...")
        if eye_tracking_process:
            eye_tracking_process.terminate()
        if face_tracking_process:
            face_tracking_process.terminate()
        
        if eye_tracking_process:
            eye_tracking_process.wait()
        if face_tracking_process:
            face_tracking_process.wait()
        
        # Generate the report
        if test_data:
            generate_latex_report(name, participant_id, test_data)
        else:
            print("No data collected for the report.")

        print("Session completed.")

if __name__ == "__main__":
    main()