import streamlit as st

st.set_page_config(page_title="About Us • CodeOrigin", page_icon="👥", layout="wide")

c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.page_link("1_Home.py", label="Home", icon="🏠")
with c2: st.page_link("pages/2_DemoVideo.py", label="Demo", icon="🎥")
with c3: st.page_link("pages/3_Info.py", label="About Us", icon="👥")
with c4: st.page_link("pages/4_CommitAnalysis.py", label="CodeOrigin", icon="🔍")
with c5: st.page_link("pages/5_RepoLink.py", label = "Repository Link", icon="⚙")