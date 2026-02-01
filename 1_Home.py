import streamlit as st

st.set_page_config(page_title="CodeOrigin", page_icon="🏠", layout="wide")

# ===================== NAV (buttons + switch_page) =====================
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1,1,1,1], gap="small")
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
    if st.button("👥 About Us", use_container_width=True):
        st.switch_page("pages/3_Info.py")
st.markdown('</div>', unsafe_allow_html=True)

# ===================== PAGE STYLES =====================
st.markdown("""
<style>
body { background:#564592; color:#F2F0FA; }

.hero{
  position:relative;
  width:100%;
  max-width:1100px;
  height:300px;
  margin:0 auto 40px;
  border-radius:20px;
  background:#A882DD;
  display:flex;
  align-items:center;
  justify-content:center;
  flex-direction:column;
  text-align:center;
  box-shadow:0 6px 20px rgba(0,0,0,.35);
}

.hero img{
  width:300px;
  margin:0;
  filter:drop-shadow(0 10px 28px rgba(0,0,0,.55));
}

.hero p{
  font-size:20px;
  color:#E6E3F5;
  font-style:italic;
}

.info-row{
  display:flex;
  justify-content:center;
  gap:22px;
  flex-wrap:wrap;
  margin-top:40px;
}

.info-box{
  width:260px;
  background:rgba(255,255,255,0.12);
  color:#FFFFFF;
  border-radius:18px;
  box-shadow:0 4px 10px rgba(0,0,0,.25);
  padding:18px;
  text-align:center;
  transition:.2s ease;
}

.info-box:hover{
  background:rgba(255,255,255,0.18);
  transform:translateY(-3px);
}

.info-box h3{
  margin-bottom:8px;
  color:#FFFFFF;
}

.info-box p{
  margin:0;
  font-size:.95rem;
  color:#E6E3F5;
}
</style>
""", unsafe_allow_html=True)

# ===================== HERO =====================
st.markdown("""
<div class="hero">
  <img src="https://raw.githubusercontent.com/jasperhopkins/hackviolet/refs/heads/main/CodeOriginLogo.png" style="width:850px;">
</div>
""", unsafe_allow_html=True)

# ===================== INFO BOXES =====================
st.markdown("""
<div class="info-row">
  <div class="info-box">
    <h3>🔎 Commit Analysis</h3>
    <p>Who changed what, when, and where.</p>
  </div>

  <div class="info-box">
    <h3>🧬 Style Drift</h3>
    <p>Spot sudden authorship shifts.</p>
  </div>

  <div class="info-box">
    <h3>🤖 AI Insights</h3>
    <p>LLM-powered explanations.</p>
  </div>
</div>
""", unsafe_allow_html=True)