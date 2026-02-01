import streamlit as st

st.set_page_config(page_title="CodeOrigin", page_icon="🏠", layout="wide")

# ===================== NAV (buttons + switch_page) =====================
st.markdown("""
<style>
.nav-wrap { display:flex; justify-content:center; gap:14px; margin:18px 0 24px; }
.nav-wrap .stButton>button{
  border:0; border-radius:18px;
  padding:10px 22px; font-weight:700; font-size:16px;
  box-shadow:0 3px 6px rgba(0,0,0,.15);
  transition:.15s ease;
}
.nav-wrap .stButton>button:hover{ background:#DCCFB7; transform:translateY(-2px); }
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
    if st.button("👥 About Us", use_container_width=True):
        st.switch_page("pages/3_Info.py")
with c4:
    if st.button("🔍 CodeOrigin", use_container_width=True):
        st.switch_page("pages/4_CommitAnalysis.py")
with c5:
    if st.button("⚙ Repository Link", use_container_width=True):
        st.switch_page("pages/5_RepoLink.py")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<style>
.hero-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    margin: 12px 0 28px;
}

.logo-shadow img {
    width: 340px;                
    max-width: 90%;
    filter: drop-shadow(0 10px 28px rgba(0,0,0,0.45))
            drop-shadow(0 0 22px rgba(190,150,255,0.35)); 
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="logo-shadow">', unsafe_allow_html=True)
st.image("CodeOriginLogo.png", use_container_width=False)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)