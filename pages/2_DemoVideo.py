import streamlit as st

st.set_page_config(page_title="Demo • CodeOrigin", page_icon="🎥", layout="wide")

c1, c2, c3, c4 = st.columns(4)
with c1: st.page_link("1_Home.py", label="Home", icon="🏠")
with c2: st.page_link("pages/2_DemoVideo.py", label="Demo", icon="🎥")
with c3: st.page_link("pages/4_CommitAnalysis.py", label="CodeOrigin", icon="🔍")
with c4: st.page_link("pages/3_Info.py", label="About Us", icon="👥")


st.subheader("Demo Video")
st.video("https://www.youtube.com/watch?v=-UGFq6jAlZg")