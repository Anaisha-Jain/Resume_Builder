import json
import os
import streamlit as st
from google import genai

# --- Page Setup ---
st.set_page_config(
    page_title="Interactive AI Resume Builder", page_icon="📄", layout="wide"
)

st.title("📄 Interactive AI Resume Builder (LaTeX)")
st.caption(
    "Add your background piece-by-piece, let AI polish your experience, and generate a custom-tailored LaTeX resume."
)

# --- Initialize Session State for Master Data ---
if "master_data" not in st.session_state:
    st.session_state.master_data = {
        "education": {},
        "skills_list": [],
        "categorized_skills": "",
        "experiences": [],
        "projects": [],
    }

# --- Retrieve API Key ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

# --- Sidebar: Configuration & Backup/Restore ---
with st.sidebar:
    st.header("⚙️ Configuration")
    if api_key:
        st.success("🔒 API Key Active")
    else:
        api_key = st.text_input("Gemini API Key", type="password")

    st.divider()
    st.header("💾 Backup & Restore")
    st.caption("Save your full profile as a JSON file or restore a previous session.")

    # Export Profile JSON
    profile_json_str = json.dumps(st.session_state.master_data, indent=2)
    st.download_button(
        label="📥 Export Profile Backup (.json)",
        data=profile_json_str,
        file_name="my_master_profile.json",
        mime="application/json",
        use_container_width=True,
    )

    # Import Profile JSON
    uploaded_json = st.file_uploader(
        "📤 Restore Profile Backup (.json)", type="json"
    )
    if uploaded_json is not None:
        try:
            loaded_data = json.load(uploaded_json)
            st.session_state.master_data = loaded_data
            st.success("Profile restored!")
            st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON file: {e}")

client = genai.Client(api_key=api_key) if api_key else None

# --- Main Navigation Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎓 Education",
    "🛠️ Skills",
    "💼 Experience",
    "🚀 Projects",
    "⚡ Generate Resume",
])

# ==========================================
# TAB 1: EDUCATION
# ==========================================
with tab1:
    st.header("Education Details")
    edu = st.session_state.master_data.get("education", {})

    col1, col2 = st.columns(2)
    with col1:
        uni = st.text_input(
            "University / Institution",
            value=edu.get("university", ""),
            placeholder="e.g., University of Waterloo",
        )
        degree = st.text_input(
            "Degree / Major",
            value=edu.get("degree", ""),
            placeholder="e.g., B.A.Sc. Nanotechnology Engineering",
        )
    with col2:
        dates = st.text_input(
            "Attendance / Graduation Dates",
            value=edu.get("dates", ""),
            placeholder="e.g., Sep 2025 -- Apr 2030",
        )
        loc = st.text_input(
            "Location",
            value=edu.get("location", ""),
            placeholder="e.g., Waterloo, ON",
        )

    st.session_state.master_data["education"] = {
        "university": uni,
        "degree": degree,
        "dates": dates,
        "location": loc,
    }

# ==========================================
# TAB 2: SKILLS (Tag Input + Auto-Clearing)
# ==========================================
with tab2:
    st.header("Master Skills Inventory")
    st.caption(
        "Type in skills individually or comma-separated. Gemini will organize and categorize them for you."
    )

    current_skills = st.session_state.master_data.get("skills_list", [])

    # Skill addition form using st.form for clean state reset
    with st.form(key="add_skill_form", clear_on_submit=True):
        col_input, col_btn = st.columns([4, 1])
        with col_input:
            new_skill_input = st.text_input(
                "Add Skill(s):",
                placeholder="e.g., Python, SolidWorks, React, Machine Learning",
            )
        with col_btn:
            st.write(" ")
            st.write(" ")
            submit_skill = st.form_submit_button("➕ Add Skill", use_container_width=True)

        if submit_skill and new_skill_input.strip():
            added_items = [
                s.strip()
                for s in new_skill_input.split(",")
                if s.strip() and s.strip() not in current_skills
            ]
            current_skills.extend(added_items)
            st.session_state.master_data["skills_list"] = current_skills
            st.rerun()

    # Display current skill tags
    if current_skills:
        st.markdown("**Your Skill Tags:**")
        st.write(", ".join([f"`{s}`" for s in current_skills]))

        col_cat, col_clear = st.columns([3, 1])
        with col_cat:
            if st.button("✨ Auto-Categorize Skills with AI"):
                if not client:
                    st.error("Please provide a Gemini API Key in the sidebar.")
                else:
                    with st.spinner("Categorizing skills..."):
                        cat_prompt = f"""
Given this list of skills: {', '.join(current_skills)}
Group them into 3-5 clean categories suitable for a technical resume (e.g., Programming Languages, Frameworks & Tools, Hardware, Lab Protocols).
Format output as:
Category Name: skill1, skill2, skill3
"""
                        res = client.models.generate_content(
                            model="gemini-2.5-flash", contents=cat_prompt
                        )
                        st.session_state.master_data["categorized_skills"] = (
                            res.text.strip()
                        )
                        st.success("Skills categorized successfully!")

        with col_clear:
            if st.button("🗑️ Clear All Skills"):
                st.session_state.master_data["skills_list"] = []
                st.session_state.master_data["categorized_skills"] = ""
                st.rerun()

    st.divider()
    cat_skills = st.text_area(
        "Categorized Skills Preview (Used in Final Resume Output)",
        value=st.session_state.master_data.get("categorized_skills", ""),
        height=150,
        help="You can manually tweak the AI-generated categories here if desired.",
    )
    st.session_state.master_data["categorized_skills"] = cat_skills

# ==========================================
# TAB 3: EXPERIENCE (Add + Auto-Clear + Polish)
# ==========================================
with tab3:
    st.header("Work & Leadership Experience")

    with st.expander("➕ Add New Experience", expanded=True):
        with st.form(key="add_experience_form", clear_on_submit=True):
            e_title = st.text_input(
                "Role / Job Title*",
                placeholder="e.g., Electrical Lead or Research Assistant",
            )
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                e_org = st.text_input(
                    "Company / Organization*", placeholder="e.g., Acme Tech"
                )
                e_dates = st.text_input(
                    "Dates*", placeholder="e.g., May 2024 -- Aug 2024"
                )
            with col_e2:
                e_loc = st.text_input(
                    "Location", placeholder="e.g., San Francisco, CA"
                )

            e_desc = st.text_area(
                "Raw Notes / Description*",
                placeholder="Enter rough details of what you did. E.g.: 'I built fast APIs using Python, fixed database bugs, and helped the team build authentication system.'",
                height=120,
            )

            submit_exp = st.form_submit_button("💾 Save Experience Entry")

            if submit_exp:
                if e_title and e_org and e_desc:
                    new_exp = {
                        "title": e_title,
                        "org": e_org,
                        "dates": e_dates,
                        "location": e_loc,
                        "bullets": [
                            b.strip("- ")
                            for b in e_desc.split("\n")
                            if b.strip()
                        ],
                    }
                    st.session_state.master_data["experiences"].append(new_exp)
                    st.success(f"Added '{e_title}'!")
                    st.rerun()
                else:
                    st.warning("Please fill in Title, Organization, and Description.")

    st.divider()
    st.subheader("Your Saved Experiences")
    experiences = st.session_state.master_data.get("experiences", [])

    for idx, exp in enumerate(experiences):
        with st.container(border=True):
            st.markdown(
                f"### {exp['title']} @ {exp['org']} ({exp.get('dates', '')})"
            )
            st.caption(f"📍 {exp.get('location', 'N/A')}")

            for bullet in exp.get("bullets", []):
                st.markdown(f"• {bullet}")

            col_pol, col_del = st.columns([4, 1])

            if col_pol.button(
                f"✨ Polish Bullets with AI", key=f"pol_exp_{idx}"
            ):
                if not client:
                    st.error("Please add a Gemini API Key in the sidebar.")
                else:
                    with st.spinner("Fluffing and polishing bullet points..."):
                        polish_prompt = f"""
Transform these raw experience notes into 3 high-impact, professional resume bullet points.
Role: {exp['title']} at {exp['org']}
Raw Notes: {exp['bullets']}

Rules:
- Start with strong action verbs.
- Make them sound technical, professional, and impactful.
- Keep each bullet point clear and concise.
Return ONLY the polished bullet points as a bulleted list (starting with '- ').
"""
                        pol_res = client.models.generate_content(
                            model="gemini-2.5-flash", contents=polish_prompt
                        )
                        new_bullets = [
                            line.strip("- ")
                            for line in pol_res.text.strip().split("\n")
                            if line.strip()
                        ]
                        st.session_state.master_data["experiences"][idx][
                            "bullets"
                        ] = new_bullets
                        st.rerun()

            if col_del.button(f"🗑️ Delete", key=f"del_exp_{idx}"):
                st.session_state.master_data["experiences"].pop(idx)
                st.rerun()

# ==========================================
# TAB 4: PROJECTS (Add + Auto-Clear + Polish)
# ==========================================
with tab4:
    st.header("Projects Database")

    with st.expander("➕ Add New Project", expanded=True):
        with st.form(key="add_project_form", clear_on_submit=True):
            p_title = st.text_input(
                "Project Name*", placeholder="e.g., Tidal Health Platform"
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_tech = st.text_input(
                    "Tech Stack / Tools*",
                    placeholder="e.g., Python, Streamlit, PyTorch",
                )
            with col_p2:
                p_dates = st.text_input("Date / Year*", placeholder="e.g., Nov 2025")

            p_desc = st.text_area(
                "Raw Project Details*",
                placeholder="e.g.: 'Made a web app at a hackathon that tracks user health data and gives AI summaries. Won best data viz award.'",
                height=120,
            )

            submit_proj = st.form_submit_button("💾 Save Project Entry")

            if submit_proj:
                if p_title and p_desc:
                    new_proj = {
                        "title": p_title,
                        "tech": p_tech,
                        "dates": p_dates,
                        "bullets": [
                            b.strip("- ")
                            for b in p_desc.split("\n")
                            if b.strip()
                        ],
                    }
                    st.session_state.master_data["projects"].append(new_proj)
                    st.success(f"Added project '{p_title}'!")
                    st.rerun()
                else:
                    st.warning("Please fill in Project Name and Details.")

    st.divider()
    st.subheader("Your Saved Projects")
    projects = st.session_state.master_data.get("projects", [])

    for idx, proj in enumerate(projects):
        with st.container(border=True):
            st.markdown(
                f"### {proj['title']} | *{proj.get('tech', '')}* ({proj.get('dates', '')})"
            )

            for bullet in proj.get("bullets", []):
                st.markdown(f"• {bullet}")

            col_ppol, col_pdel = st.columns([4, 1])

            if col_ppol.button(
                f"✨ Polish Project Bullets with AI", key=f"pol_proj_{idx}"
            ):
                if not client:
                    st.error("Please add a Gemini API Key in the sidebar.")
                else:
                    with st.spinner("Polishing project bullets..."):
                        proj_prompt = f"""
Transform these raw project notes into 2-3 strong resume bullet points highlighting technical execution and impact.
Project: {proj['title']} using {proj.get('tech')}
Raw Notes: {proj['bullets']}

Return ONLY the polished bullet points as a bulleted list (starting with '- ').
"""
                        proj_res = client.models.generate_content(
                            model="gemini-2.5-flash", contents=proj_prompt
                        )
                        new_proj_bullets = [
                            line.strip("- ")
                            for line in proj_res.text.strip().split("\n")
                            if line.strip()
                        ]
                        st.session_state.master_data["projects"][idx][
                            "bullets"
                        ] = new_proj_bullets
                        st.rerun()

            if col_pdel.button(f"🗑️ Delete", key=f"del_proj_{idx}"):
                st.session_state.master_data["projects"].pop(idx)
                st.rerun()

# ==========================================
# TAB 5: GENERATE RESUME
# ==========================================
with tab5:
    st.header("Generate Tailored LaTeX Resume")

    jd_input = st.text_area(
        "Paste Target Job Description (JD) Here:",
        height=200,
        placeholder="Paste full job requirements and responsibilities...",
    )

    latex_template = r"""\documentclass[letterpaper,10.5pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\raggedbottom
\raggedright

\titleformat{\section}{\vspace{-4pt}\scshape\raggedright\large}{}{0em}{}[\titlerule \vspace{-5pt}]

\newcommand{\resumeItem}[1]{\item\small{#1 \vspace{-2pt}}}
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\begin{document}

\begin{center}
    {\Huge \scshape [Your Name]} \\ \vspace{4pt}
    \small +1(000)000-0000 $|$ \href{mailto:email@example.com}{email@example.com} $|$ \href{https://linkedin.com}{LinkedIn} $|$ \href{https://github.com}{GitHub}
\end{center}

\section{Education}
  \begin{itemize}[leftmargin=0.15in, label={}]
    \resumeSubheading{{{UNIVERSITY}}}{{{EDU_DATES}}}{{{DEGREE}}}{{{EDU_LOCATION}}}
  \end{itemize}

\section{Technical Skills}
{{TECHNICAL_SKILLS}}

\section{Experience}
{{EXPERIENCE}}

\section{Projects}
{{PROJECTS}}

\end{document}
"""

    if st.button("🚀 Generate Tailored LaTeX Resume", type="primary"):
        if not api_key:
            st.error("Please enter a Gemini API Key in the sidebar.")
        elif not jd_input.strip():
            st.warning("Please paste a Job Description first.")
        else:
            with st.spinner("Filtering & formatting relevant items for JD..."):
                master_dump = st.session_state.master_data

                gen_prompt = f"""
You are an expert technical recruiter and resume writer.

Analyze the user's master profile and select/adapt content that best matches the Target Job Description.

MASTER PROFILE DATA:
{json.dumps(master_dump, indent=2)}

TARGET JOB DESCRIPTION:
"{jd_input}"

INSTRUCTIONS:
1. Select ONLY the most relevant skills, experiences, and projects that align with the requirements in the Job Description.
2. Adapt bullet points lightly to incorporate relevant ATS keywords from the JD (never invent false facts).
3. Output exact LaTeX syntax formatted for the following macros:
   - TECHNICAL_SKILLS: Standard formatted LaTeX itemize or formatted text lines.
   - EXPERIENCE: `\\begin{{itemize}}[leftmargin=0.15in, label={{}}]` wrapping `\\resumeSubheading{{Role/Title}}{{Dates}}{{Company/Org}}{{Location}}`, followed by `\\begin{{itemize}} \\resumeItem{{...}} \\end{{itemize}}`.
   - PROJECTS: `\\begin{{itemize}}[leftmargin=0.15in, label={{}}]` wrapping `\\resumeProjectHeading{{\\textbf{{Title}} $|$ \\emph{{TechStack}}}}{{Dates}}`, followed by `\\begin{{itemize}} \\resumeItem{{...}} \\end{{itemize}}`.

Return the output as a JSON object with these exact keys:
{{
  "TECHNICAL_SKILLS": "...LaTeX code...",
  "EXPERIENCE": "...LaTeX code...",
  "PROJECTS": "...LaTeX code..."
}}
"""
                try:
                    res = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=gen_prompt,
                        config={"response_mime_type": "application/json"},
                    )
                    out = json.loads(res.text)

                    edu_data = master_dump.get("education", {})
                    final_tex = latex_template
                    final_tex = final_tex.replace(
                        "{{UNIVERSITY}}", edu_data.get("university", "")
                    )
                    final_tex = final_tex.replace(
                        "{{DEGREE}}", edu_data.get("degree", "")
                    )
                    final_tex = final_tex.replace(
                        "{{EDU_DATES}}", edu_data.get("dates", "")
                    )
                    final_tex = final_tex.replace(
                        "{{EDU_LOCATION}}", edu_data.get("location", "")
                    )
                    final_tex = final_tex.replace(
                        "{{TECHNICAL_SKILLS}}", out.get("TECHNICAL_SKILLS", "")
                    )
                    final_tex = final_tex.replace(
                        "{{EXPERIENCE}}", out.get("EXPERIENCE", "")
                    )
                    final_tex = final_tex.replace(
                        "{{PROJECTS}}", out.get("PROJECTS", "")
                    )

                    st.success("Resume successfully generated!")
                    st.code(final_tex, language="latex")
                    st.download_button(
                        "📥 Download .tex File for Overleaf",
                        data=final_tex,
                        file_name="tailored_resume.tex",
                        mime="text/x-tex",
                    )
                except Exception as e:
                    st.error(f"Generation error: {e}")