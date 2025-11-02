import streamlit as st
import requests
import json

st.title("HTX AI Engineering Take Home Test")

pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if "fields_to_extract" not in st.session_state:
    st.session_state.fields_to_extract = [
        {"pages": "5", "description": "Amount of Corporate Income Tax in 2024", "output_type": "float"},
        {"pages": "5", "description": "YOY percentage difference of Corp Income Tax in 2024", "output_type": "float"},
        {"pages": "20", "description": "Total amount of top ups in 2024", "output_type": "float"},
        {"pages": "5-6", "description": "List of taxes mentioned in section Operating Revenue", "output_type": "list[str]"},
        {"pages": "8", "description": "Latest Actual Fiscal Position in billions", "output_type": "float"}
    ]

col_add, col_clear = st.columns([1, 1])
with col_add:
    if st.button("Add field", use_container_width=True):
        st.session_state.fields_to_extract.append({"pages": "", "description": "", "output_type": "str"})
with col_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.fields_to_extract = []

output_types = ["str", "int", "float", "list[str]", "list[int]", "list[float]"]

for i, field in enumerate(st.session_state.fields_to_extract):
    c1, c2, c3, c4 = st.columns([1, 3, 1, 0.5])
    field["pages"] = c1.text_input("Pages", field["pages"], key=f"pages_{i}")
    field["description"] = c2.text_area("Value to extract", field["description"], key=f"description_{i}", height=60)
    field["output_type"] = c3.selectbox("Type", output_types, index=output_types.index(field["output_type"]), key=f"output_type_{i}")
    with c4:
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        if st.button("✕", key=f"delete_{i}", use_container_width=True):
            st.session_state.fields_to_extract.pop(i)
            st.rerun()

if st.button("Extract", disabled=(pdf_file is None or len(st.session_state.fields_to_extract) == 0)):
    with st.spinner("Extracting..."):
        files = {"file": (pdf_file.name, pdf_file.read())}
        data = {"fields": json.dumps(st.session_state.fields_to_extract)}
        
        response = requests.post("http://localhost:8000/extract", files=files, data=data)
        results = response.json()
        
        for result in results["results"]:
            st.subheader(f"{result['description']}")
            st.write("**Original Text**")
            st.info(f"\"{result['original_text']}\"")
            st.write("**Value**")
            st.code(result['extracted'])
            if result['status'] is not None:
                st.write("**Status**")
                st.success(result['status'])
            st.write("**Reason**")
            st.info(result['reason'])
            st.divider()
