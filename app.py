import json
import streamlit as st
from openai import OpenAI
from string import Template
from config import Config
from parsers import parse_vacancy, parse_resume
import html
import re

prompt_path = "prompt.txt"
system_prompt_path = "system_prompt.txt"


def print_numbered_list(list_items):
    for i, item in enumerate(list_items):
        st.write(f"{i+1}. {item}")

# Read prompts from JSON file
def load_prompts(file_path='prompt.json'):
    with open(file_path, 'r') as file:
        prompts = json.load(file)
    return prompts['system_prompt'], Template(prompts['user_prompt_template'])

SYSTEM_PROMPT, USER_PROMPT_TEMPLATE = load_prompts()
if st.secrets["OPENAI_API_KEY"]:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    OPENAI_API_KEY = Config.OPENAI_API_KEY

client = OpenAI(
    # Replace with your OpenAI API key or use environment variable
    api_key=OPENAI_API_KEY#Config.OPENAI_API_KEY
)

def on_vacancy_url():
    url = st.session_state.job_url
    if url:
        vacancy = parse_vacancy(url)
        st.session_state.job_description = vacancy
    else:
        st.session_state.job_description = ""

def on_resume_url():
    url = st.session_state.cv_url
    if url:
        resume = parse_resume(url)
        st.session_state.resume = resume
    else:
        st.session_state.resume = ""

def score_resume(vacancy, resume):
    # Fill the template with the provided vacancy and resume
    user_prompt = USER_PROMPT_TEMPLATE.substitute(vacancy=vacancy, resume=resume)

    stream = client.chat.completions.create(
        model="gpt-4o-mini",  # or another suitable model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        stream=True,
        max_tokens=1000,
        temperature=0
    )
    
    return stream

def scrollable_markdown(content, height=200):
    content = content.replace('`', '\\`')
    markdown_html = f"""
    <div style="height: {height}px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; background-color: #f0f0f0;">
        <div id="content"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/2.0.3/marked.min.js"></script>
    <script>
        document.getElementById('content').innerHTML = marked.parse(`{content}`);
    </script>
    """
    st.components.v1.html(markdown_html, height=height+30)


def html_escape(text):
    return html.escape(text).replace('\n', '&#10;')

def extract_section(content, tag):
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def parse_analysis(content):
    # Extract the content inside the outermost <analysis> tags
    full_analysis = extract_section(content, "analysis")
    
    # If there's no <analysis> tag, treat the entire content as analysis
    if not full_analysis:
        full_analysis = content

    # Extract justification and score from within the full analysis
    justification = extract_section(full_analysis, "justification")
    score = extract_section(full_analysis, "matching_score")

    # Remove justification and score from the analysis text
    analysis = re.sub(r'<justification>.*?</justification>', '', full_analysis, flags=re.DOTALL)
    analysis = re.sub(r'<matching_score>.*?</matching_score>', '', analysis, flags=re.DOTALL)
    
    # Trim any leading/trailing whitespace
    analysis = analysis.strip()

    # Handle special cases
    if not analysis and justification:
        # SCENARIO 1: If analysis is empty but justification exists, keep them separate
        pass
    elif analysis and not justification:
        # SCENARIO 3 & 4: If justification is empty/absent, keep all text in analysis
        analysis = full_analysis

    return analysis, justification, score

def scrollable_stream_output(height=400):
    stream_container = st.empty()
    analysis_header = st.empty()
    analysis_container = st.empty()
    justification_header = st.empty()
    justification_container = st.empty()
    score_container = st.empty()
    stream_content = ""
    
    def update_stream(content):
        nonlocal stream_content
        stream_content += content
        analysis, justification, score = parse_analysis(stream_content)
        
        if analysis:
            analysis_header.markdown("## Analysis", help="Detailed analysis of the job description and resume")
            analysis_container.markdown(f"""
            <div style="height: {height}px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; background-color: #f0f0f0; color: #333;">
                <pre style="white-space: pre-wrap; word-wrap: break-word;">{html_escape(analysis)}</pre>
            </div>
            """, unsafe_allow_html=True)
        else:
            analysis_header.empty()
            analysis_container.empty()
        
        if justification:
            justification_header.markdown("## Justification", help="Explanation for the matching score")
            justification_container.markdown(f"""
            <div style="height: 200px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; background-color: #f0f0f0; color: #333;">
                <pre style="white-space: pre-wrap; word-wrap: break-word;">{html_escape(justification)}</pre>
            </div>
            """, unsafe_allow_html=True)
        else:
            justification_header.empty()
            justification_container.empty()
        
        if score:
            score_container.markdown(f"## Matching Score: {score}", help="Overall match between the job description and resume")
        else:
            score_container.empty()
    
    return update_stream



st.title("Resume Scoring Application")
# Add your Streamlit code here
activities_list = ['Identify the key requirements, skills, and qualifications mentioned in the job posting',
                    'Identify the candidate\'s qualifications, skills, and experience',
                    'Evaluate how well the candidate\'s qualifications match the job requirements',
                    'Score the candidate\'s overall performance on the job',
                    'Justify our score']
st.write("Welcome to the resume scoring application!")
st.write("What we do:")
print_numbered_list(activities_list)

if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'resume' not in st.session_state:
    st.session_state.resume = ""

st.write("Let us start!")
job_description_url = st.text_area("Enter your vacancy url:", height=20, key="job_url", on_change=on_vacancy_url)
resume_url = st.text_area("Enter your resume url:", height=20, key="cv_url", on_change=on_resume_url)
st.write('Job description:')
scrollable_markdown(st.session_state.job_description)
st.write('Resume:')
scrollable_markdown(st.session_state.resume)
#job_description = st.text_area("Enter your vacancy description here:", st.session_state.job_description, height=200)
#resume = st.text_area("Enter your CV here:", height=200)
if st.button("Check match"):
    with st.spinner("Scoring..."):
        scoring_stream = score_resume(st.session_state.job_description, st.session_state.resume)
        update_stream = scrollable_stream_output()
        for chunk in scoring_stream:
            if chunk.choices[0].delta.content is not None:
                update_stream(chunk.choices[0].delta.content)