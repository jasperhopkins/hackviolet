import streamlit as st

st.set_page_config(page_title="Demo • CodeOrigin", page_icon="🎥", layout="wide", initial_sidebar_state="collapsed")

# ===================== NAV =====================
st.markdown("""
<style>
.nav-wrap { display:flex; justify-content:center; gap:14px; margin:18px 0 24px; }
.nav-wrap .stButton>button{
  background:rgba(255,255,255,0.12);
  color:#FFFFFF;
  border:1px solid rgba(255,255,255,0.25);
  border-radius:18px;
  padding:10px 22px;
  font-weight:700;
  font-size:16px;
  box-shadow:0 3px 6px rgba(0,0,0,.15);
  transition:.15s ease;
}
.nav-wrap .stButton>button:hover{
  background:rgba(255,255,255,0.18);
  transform:translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1], gap="small")
with c1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("1_Home.py")
with c2:
    if st.button("🎥 Demo", use_container_width=True):
        st.switch_page("pages/2_DemoVideo.py")
with c3:
    if st.button("🔍 CodeOrigin", use_container_width=True):
        st.switch_page("pages/4_CommitAnalysis.py")
with c4:
    if st.button("👥 Contributors", use_container_width=True):
        st.switch_page("pages/5_ContributorProfiles.py")
with c5:
    if st.button("ℹ️ About Us", use_container_width=True):
        st.switch_page("pages/3_Info.py")
st.markdown('</div>', unsafe_allow_html=True)

st.subheader("Demo Video")
st.video("https://youtu.be/6ioqGIbIa2Q")

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