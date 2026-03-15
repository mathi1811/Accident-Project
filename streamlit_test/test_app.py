import streamlit as st

st.title("Minimal Streamlit Form Test")
with st.form("test_form"):
    name = st.text_input("Your name")
    submitted = st.form_submit_button("Submit")
    st.write(f"Form rendered. Submit value: {submitted}")
if submitted:
    st.success(f"Hello, {name}!")
