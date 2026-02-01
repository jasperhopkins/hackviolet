import streamlit as st

st.set_page_config(page_title="Demo • CodeOrigin", page_icon="🎥", layout="wide")

c1, c2, c3, c4 = st.columns(4)
with c1: st.page_link("1_Home.py", label="Home", icon="🏠")
with c2: st.page_link("pages/2_DemoVideo.py", label="Demo", icon="🎥")
with c3: st.page_link("pages/4_CommitAnalysis.py", label="CodeOrigin", icon="🔍")
with c4: st.page_link("pages/3_Info.py", label="About Us", icon="👥")


st.subheader("Demo Video")
st.video("https://www.youtube.com/watch?v=-UGFq6jAlZg")

st.markdown("""
<style>
.repo-box {
    max-width: 720px;
    margin: 24px auto 0;
    padding: 18px 22px;
    background-color: #A882DD;
    border-radius: 18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25);
    text-align: center;
}
.repo-box h3 {
    margin: 0 0 8px;
    color: #564592;
}
.repo-box a {
    color: #E0EFde;
    font-weight: 600;
    text-decoration: none;
}
.repo-box a:hover {
    text-decoration: underline;
}
</style>

<div class="repo-box">
    <h3>GitHub Repository</h3>
    <a href="https://github.com/jasperhopkins/hackviolet" target="_blank">
        https://github.com/jasperhopkins/hackviolet
    </a>
</div>
""", unsafe_allow_html=True)