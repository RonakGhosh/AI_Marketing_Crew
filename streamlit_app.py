import os
from datetime import datetime
from pathlib import Path
import streamlit as st

# ---------- Paths ----------
BASE_DIR = Path(__file__).parent.resolve()
DRAFTS_DIR = BASE_DIR / "resources" / "drafts"
BLOGS_DIR = DRAFTS_DIR / "blogs"
POSTS_DIR = DRAFTS_DIR / "posts"
REELS_DIR = DRAFTS_DIR / "reels"
for p in [DRAFTS_DIR, BLOGS_DIR, POSTS_DIR, REELS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="AI Marketing Crew (Fast & Lean)", page_icon="✨", layout="wide")

# ---------- Header ----------
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:1.8rem;">⚡</span>
        <h1 style="margin:0;">AI Marketing Crew — Fast & Cost-Efficient</h1>
    </div>
    <p style="margin-top:-8px;color:#6b7280;">
        Lean prompts, small outputs, optional web tools, and caching.
    </p>
    <hr/>
    """,
    unsafe_allow_html=True
)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("🔐 Keys & Settings")
    google_api_key = st.text_input("Google API Key (Gemini)", type="password", placeholder="Paste your key")
    serper_api_key = st.text_input("Serper API Key (optional)", type="password", placeholder="Optional")
    mode = st.selectbox("Run Mode", ["Lite (fastest, cheapest)", "Standard", "Deep (web tools)"], index=0,
                        help="Lite: strategy + calendar. Standard: + posts + reels + blogs. Deep: enables web tools (Serper/Scrape).")

    st.divider()
    st.caption("📄 Optional uploads (PDF/MD/TXT) for context")
    uploads = st.file_uploader("Upload files", type=["pdf", "md", "txt"], accept_multiple_files=True)
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

# ---------- Campaign Form ----------
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
            value="Automates repetitive Excel tasks with AI, saving time and reducing errors.",
            height=120
        )
        current_date = datetime.now().strftime("%Y-%m-%d")

    run_btn = st.button("🚀 Run Marketing Crew", use_container_width=True)

# ---------- Helpers ----------
@st.cache_resource(show_spinner=False)
def load_crew_class():
    from crew import TheMarketingCrew
    return TheMarketingCrew

def read_text_file(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(errors="replace")
        except Exception:
            return ""

def render_folder(folder: Path, empty_msg: str, collapsed=True):
    items = sorted([p for p in folder.glob("**/*") if p.is_file()])
    if not items:
        st.warning(empty_msg)
        return
    for p in items:
        with st.expander(f"📄 {p.relative_to(BASE_DIR)}", expanded=not collapsed):
            content = read_text_file(p)
            # show small preview to save UI time
            preview = content if len(content) < 2000 else content[:2000] + "\n...\n[truncated]"
            if p.suffix.lower() in [".md", ".txt"]:
                st.code(preview, language="markdown")
            else:
                st.code(preview)
            with open(p, "rb") as fh:
                st.download_button(
                    "⬇️ Download",
                    data=fh.read(),
                    file_name=p.name,
                    mime="text/plain" if p.suffix.lower() in [".md", ".txt"] else "application/octet-stream",
                    use_container_width=True,
                    key=f"download_{p}"   # ✅ unique key
                )

def list_generated_files():
    files = []
    for folder in [DRAFTS_DIR, BLOGS_DIR, POSTS_DIR, REELS_DIR]:
        for p in folder.glob("**/*"):
            if p.is_file():
                files.append(p)
    return sorted(files)

# ---------- Main Action ----------
if run_btn:
    if not google_api_key:
        st.error("Please enter your Google API key in the sidebar.")
        st.stop()

    # Ensure both env vars are set for CrewAI/LiteLLM + LangChain
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ["GEMINI_API_KEY"] = google_api_key

    # Only set SERPER when Deep mode & key provided
    if mode == "Deep (web tools)" and serper_api_key:
        os.environ["SERPER_API_KEY"] = serper_api_key
    else:
        # clear to avoid slow web calls accidentally
        os.environ.pop("SERPER_API_KEY", None)

    TheMarketingCrew = load_crew_class()
    crew = TheMarketingCrew()
    full_crew = crew.marketingcrew()

    # Reduce work based on mode (fewer tasks = fewer tokens)
    # We control by slicing the crew.tasks in-place:
    if mode == "Lite (fastest, cheapest)":
        # Strategy + calendar only
        full_crew.tasks = [
            crew.prepare_marketing_strategy(),
            crew.create_content_calendar(),
        ]
    elif mode == "Standard":
        # Everything except web-heavy research step
        full_crew.tasks = [
            crew.prepare_marketing_strategy(),
            crew.create_content_calendar(),
            crew.prepare_post_drafts(),
            crew.prepare_scripts_for_reels(),
            crew.content_research_for_blogs(),
            crew.draft_blogs(),
            crew.seo_optimization(),
        ]
    else:
        # Deep includes research first (will use web tools if key present)
        full_crew.tasks = [
            crew.market_research(),
            crew.prepare_marketing_strategy(),
            crew.create_content_calendar(),
            crew.prepare_post_drafts(),
            crew.prepare_scripts_for_reels(),
            crew.content_research_for_blogs(),
            crew.draft_blogs(),
            crew.seo_optimization(),
        ]

    inputs = {
        "product_name": product_name.strip(),
        "target_audience": target_audience.strip(),
        "product_description": product_description.strip(),
        "budget": budget.strip(),
        "current_date": current_date
    }

    with st.spinner("Running compact workflow… ⏱️"):
        try:
            result = full_crew.kickoff(inputs=inputs)
            st.success("Crew run complete ✅")
        except Exception as e:
            st.exception(e)
            st.stop()

    st.subheader("📦 Results")
    tabs = st.tabs(["Overview", "Drafts", "Blogs", "Social Posts", "Reels", "All Files"])

    with tabs[0]:
        st.markdown("**Final Result (from CrewAI):**")
        # Avoid huge UI renders; show small preview
        res_str = str(result)
        st.code(res_str if len(res_str) < 2000 else res_str[:2000] + "\n...\n[truncated]", language="markdown")
        st.info("Files are saved under `resources/drafts/…`. Use the tabs below to preview & download.")

    with tabs[1]:
        render_folder(DRAFTS_DIR, "No general drafts found yet.", collapsed=True)
    with tabs[2]:
        render_folder(BLOGS_DIR, "No blogs generated yet.", collapsed=True)
    with tabs[3]:
        render_folder(POSTS_DIR, "No social post drafts generated yet.", collapsed=True)
    with tabs[4]:
        render_folder(REELS_DIR, "No reels scripts generated yet.", collapsed=True)
    with tabs[5]:
        files = list_generated_files()
        if not files:
            st.warning("No files generated yet.")
        else:
            for p in files:
                with st.expander(f"📄 {p.relative_to(BASE_DIR)}", expanded=False):
                    st.code(read_text_file(p)[:2000] + ("\n...\n[truncated]" if p.stat().st_size > 2000 else ""))
                    with open(p, "rb") as fh:
                        st.download_button(
                            "⬇️ Download",
                            data=fh.read(),
                            file_name=p.name,
                            mime="text/plain" if p.suffix.lower() in [".md", ".txt"] else "application/octet-stream",
                            use_container_width=True,
                            key=f"download_all_{p}"   # ✅ unique key
                        )
else:
    st.info("Fill in campaign details, paste your Google API key, choose a mode, then click **Run Marketing Crew**.")
