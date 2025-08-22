import os
from datetime import datetime
from pathlib import Path
import streamlit as st

# --- Paths for generated content ---
BASE_DIR = Path(__file__).parent.resolve()
DRAFTS_DIR = BASE_DIR / "resources" / "drafts"
BLOGS_DIR = DRAFTS_DIR / "blogs"
POSTS_DIR = DRAFTS_DIR / "posts"
REELS_DIR = DRAFTS_DIR / "reels"

# Ensure directories exist
for p in [DRAFTS_DIR, BLOGS_DIR, POSTS_DIR, REELS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="AI Marketing Crew (Gemini 1.5 Flash)",
    page_icon="✨",
    layout="wide"
)

# ------------------------------ UI: Header ------------------------------
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:1.8rem;">✨</span>
        <h1 style="margin:0;">AI Marketing Crew</h1>
    </div>
    <p style="margin-top:-8px;color:#6b7280;">
        Gemini 1.5 Flash + CrewAI — market research, weekly plan, posts, reels scripts, blogs & SEO in one click.
    </p>
    <hr/>
    """,
    unsafe_allow_html=True
)

# ------------------------------ Sidebar: Keys & Uploads ------------------------------
with st.sidebar:
    st.header("🔐 Keys & Inputs")

    google_api_key = st.text_input(
        "Google API Key (Gemini)",
        type="password",
        placeholder="Enter your Google API key"
    )

    # Optional: Serper key (if you plan to use SerperDevTool)
    serper_api_key = st.text_input(
        "Serper API Key (optional, for web search)",
        type="password",
        placeholder="Optional"
    )

    st.divider()
    st.caption("📄 Upload supporting files (PDF/MD/TXT) to assist research/content.")
    uploads = st.file_uploader(
        "Upload files",
        type=["pdf", "md", "txt"],
        accept_multiple_files=True
    )
    save_uploads_to = st.selectbox(
        "Save uploads under:",
        ["resources/drafts", "resources/drafts/blogs", "resources/drafts/posts", "resources/drafts/reels"],
        index=0
    )

    if uploads:
        base_target = BASE_DIR / save_uploads_to
        base_target.mkdir(parents=True, exist_ok=True)
        for f in uploads:
            (base_target / f.name).write_bytes(f.read())
        st.success(f"Uploaded {len(uploads)} file(s) to {save_uploads_to} ✅")

# ------------------------------ Campaign Form ------------------------------
with st.container():
    st.subheader("📋 Campaign Details")
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("Product Name", value="AI Powered Excel Automation Tool")
        target_audience = st.text_input("Target Audience", value="Small and Medium Enterprises (SMEs)")
        budget = st.text_input("Budget", value="₹50,000")
    with col2:
        product_description = st.text_area(
            "Product Description",
            value="A tool that automates repetitive tasks in Excel using AI, saving time and reducing errors.",
            height=120
        )
        current_date = datetime.now().strftime("%Y-%m-%d")

    run_btn = st.button("🚀 Run Marketing Crew", use_container_width=True)

# ------------------------------ Helpers ------------------------------
def run_marketing_crew(inputs: dict):
    """
    Imports crew only after setting env vars so the LLM picks up keys at import time.
    Returns the final result string (if any).
    """
    from crew import TheMarketingCrew
    crew = TheMarketingCrew()
    result = crew.marketingcrew().kickoff(inputs=inputs)
    return result

def read_text_file(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(errors="replace")
        except Exception:
            return ""

def render_folder(folder: Path, empty_msg: str):
    items = sorted([p for p in folder.glob("**/*") if p.is_file()])
    if not items:
        st.warning(empty_msg)
        return
    for p in items:
        with st.expander(f"📄 {p.relative_to(BASE_DIR)}"):
            content = read_text_file(p)
            if p.suffix.lower() in [".md", ".txt"]:
                st.markdown(content)
            else:
                st.code(content)
            with open(p, "rb") as fh:
                st.download_button(
                    "⬇️ Download",
                    data=fh.read(),
                    file_name=p.name,
                    mime="text/plain" if p.suffix.lower() in [".md", ".txt"] else "application/octet-stream",
                    use_container_width=True
                )

def list_generated_files():
    files = []
    for folder in [DRAFTS_DIR, BLOGS_DIR, POSTS_DIR, REELS_DIR]:
        for p in folder.glob("**/*"):
            if p.is_file():
                files.append(p)
    return sorted(files)

# ------------------------------ Main Action ------------------------------
if run_btn:
    if not google_api_key:
        st.error("Please enter your Google API key in the sidebar.")
        st.stop()

    os.environ["GOOGLE_API_KEY"] = google_api_key
    if serper_api_key:
        os.environ["SERPER_API_KEY"] = serper_api_key

    inputs = {
        "product_name": product_name.strip(),
        "target_audience": target_audience.strip(),
        "product_description": product_description.strip(),
        "budget": budget.strip(),
        "current_date": current_date
    }

    with st.spinner("Running Market Research and Strategy… this can take a minute ⏳"):
        try:
            result = run_marketing_crew(inputs)
            st.success("Crew run complete ✅")
        except Exception as e:
            st.exception(e)
            st.stop()

    st.subheader("📦 Results")
    tabs = st.tabs(["Overview", "Drafts", "Blogs", "Social Posts", "Reels", "All Files"])

    with tabs[0]:
        st.markdown("**Final Result (from CrewAI):**")
        st.write(result if result else "No top-level text returned by Crew; check generated files below.")
        st.info("Files are saved under `resources/drafts/…`. Use the tabs for previews & downloads.")

    with tabs[1]:
        render_folder(DRAFTS_DIR, "No general drafts found yet.")
    with tabs[2]:
        render_folder(BLOGS_DIR, "No blogs generated yet.")
    with tabs[3]:
        render_folder(POSTS_DIR, "No social post drafts generated yet.")
    with tabs[4]:
        render_folder(REELS_DIR, "No reels scripts generated yet.")
    with tabs[5]:
        files = list_generated_files()
        if not files:
            st.warning("No files generated yet.")
        else:
            for p in files:
                with st.expander(f"📄 {p.relative_to(BASE_DIR)}"):
                    st.code(read_text_file(p))
                    with open(p, "rb") as fh:
                        st.download_button(
                            "⬇️ Download",
                            data=fh.read(),
                            file_name=p.name,
                            mime="text/plain" if p.suffix.lower() in [".md", ".txt"] else "application/octet-stream",
                            use_container_width=True
                        )
else:
    st.info("Fill in campaign details, paste your Google API key, optionally upload files, then click **Run Marketing Crew**.")
