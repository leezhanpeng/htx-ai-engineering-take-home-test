
import os
import streamlit as st
import requests
import json

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="HTX AI Engineering Take Home Test",
    layout="wide"
)

st.title("HTX AI Engineering Take Home Test")

tab1, tab2 = st.tabs(["Field Extraction", "Multi-Agent Analysis"])

with tab1:
    st.header("Field Extraction")
    pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="extraction_pdf")

    if "fields_to_extract" not in st.session_state:
        st.session_state.fields_to_extract = [
            {"pages": "5", "description": "Amount of Corporate Income Tax in 2023", "output_type": "float"},
            {"pages": "5", "description": "YOY percentage difference of Corp Income Tax in 2023", "output_type": "float"},
            {"pages": "20", "description": "Total amount of top ups in 2024", "output_type": "float"},
            {"pages": "5-6", "description": "List of taxes mentioned in section Operating Revenue", "output_type": "list[str]"},
            {"pages": "8", "description": "Latest Actual Fiscal Position in billions", "output_type": "float"},
            {"pages": "1", "description": "The document's distribution date", "output_type": "str"},
            {"pages": "36", "description": "The date relating to estate duty", "output_type": "str"}
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

            response = requests.post(f"{API_BASE_URL}/extract", files=files, data=data)
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

with tab2:
    st.header("Multi-Agent Budget Analysis")

    pdf_file_ma = st.file_uploader("Upload PDF", type=["pdf"], key="multi_agent_pdf")

    query = st.text_area(
        "Your question:",
        value="What are the key government revenue streams, and how will the Budget for the Future Energy Fund be supported?",
        height=80,
        key="multi_agent_query"
    )

    if "analysis_running" not in st.session_state:
        st.session_state.analysis_running = False

    if st.button("Run Analysis", disabled=(pdf_file_ma is None or not query.strip() or st.session_state.analysis_running), type="primary", use_container_width=True):
        st.session_state.analysis_running = True
        pdf_file_ma.seek(0)
        files = {"file": (pdf_file_ma.name, pdf_file_ma.read(), "application/pdf")}
        data = {"query": query}

        log_expander_placeholder = st.empty()
        logs = []

        response = requests.post(
            f"{API_BASE_URL}/multi-agent-query",
            files=files,
            data=data,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        response.raise_for_status()

        result = {"final_answer": "", "revenue_findings": None, "expenditure_findings": None}

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    update = json.loads(line[6:])
                    update_type = update.get("type")

                    if update_type == "routing":
                        logs.append(("Supervisor", "Routing query...", "info"))
                        with log_expander_placeholder.container():
                            with st.expander("Execution Log", expanded=True):
                                for step, message, status in logs:
                                    col1, col2 = st.columns([1, 4])
                                    col1.markdown(f"**{step}**")
                                    if status == "info":
                                        col2.markdown(f":blue[{message}]")
                                    elif status == "success":
                                        col2.markdown(f":green[{message}]")
                        logs[-1] = ("Supervisor", f"Routed to: {update.get('decision', 'agents')}", "success")

                    elif update_type == "revenue_analysis":
                        logs.append(("Revenue Agent", "Analyzing...", "info"))
                        with log_expander_placeholder.container():
                            with st.expander("Execution Log", expanded=True):
                                for step, message, status in logs:
                                    col1, col2 = st.columns([1, 4])
                                    col1.markdown(f"**{step}**")
                                    if status == "info":
                                        col2.markdown(f":blue[{message}]")
                                    elif status == "success":
                                        col2.markdown(f":green[{message}]")
                        num_streams = update.get('num_streams', 0)
                        confidence_level = update.get('confidence_level', 'N/A')
                        logs[-1] = ("Revenue Agent", f"Found {num_streams} revenue streams (confidence: {confidence_level})", "success")
                        result["revenue_findings"] = update.get("findings", {})

                    elif update_type == "expenditure_analysis":
                        logs.append(("Expenditure Agent", "Analyzing...", "info"))
                        with log_expander_placeholder.container():
                            with st.expander("Execution Log", expanded=True):
                                for step, message, status in logs:
                                    col1, col2 = st.columns([1, 4])
                                    col1.markdown(f"**{step}**")
                                    if status == "info":
                                        col2.markdown(f":blue[{message}]")
                                    elif status == "success":
                                        col2.markdown(f":green[{message}]")
                        num_items = update.get('num_items', 0)
                        confidence_level = update.get('confidence_level', 'N/A')
                        logs[-1] = ("Expenditure Agent", f"Found {num_items} expenditure items (confidence: {confidence_level})", "success")
                        result["expenditure_findings"] = update.get("findings", {})

                    elif update_type == "synthesis":
                        logs.append(("Supervisor", "Synthesizing response...", "info"))
                        with log_expander_placeholder.container():
                            with st.expander("Execution Log", expanded=True):
                                for step, message, status in logs:
                                    col1, col2 = st.columns([1, 4])
                                    col1.markdown(f"**{step}**")
                                    if status == "info":
                                        col2.markdown(f":blue[{message}]")
                                    elif status == "success":
                                        col2.markdown(f":green[{message}]")

                    elif update_type == "final_result":
                        logs[-1] = ("Supervisor", "Synthesis complete", "success")
                        with log_expander_placeholder.container():
                            with st.expander("Execution Log", expanded=False):
                                for step, message, status in logs:
                                    col1, col2 = st.columns([1, 4])
                                    col1.markdown(f"**{step}**")
                                    if status == "info":
                                        col2.markdown(f":blue[{message}]")
                                    elif status == "success":
                                        col2.markdown(f":green[{message}]")
                        result["final_answer"] = update.get("final_answer", "")
                        result["revenue_findings"] = update.get("revenue_findings")
                        result["expenditure_findings"] = update.get("expenditure_findings")

                    elif update_type == "complete":
                        break

                    elif update_type == "error":
                        st.error(f"Error: {update.get('message', 'Unknown error')}")
                        break

        st.session_state.analysis_running = False

        st.markdown("#### Answer")
        st.markdown(result["final_answer"])

        if result["revenue_findings"] or result["expenditure_findings"]:
            st.divider()
            tab1, tab2 = st.tabs(["Revenue", "Expenditure"])

            with tab1:
                if result["revenue_findings"]:
                    findings = result["revenue_findings"]

                    col_a, col_b = st.columns([1, 3])
                    col_a.metric("Confidence", findings.get('confidence_level', 'N/A'))
                    if findings.get("total_revenue"):
                        total = findings["total_revenue"]
                        col_b.metric("Total Revenue", f"{total.get('amount', 'N/A')} {total.get('unit', '')}")

                    if findings.get('confidence_explanation'):
                        st.write(findings['confidence_explanation'])

                    if findings.get("revenue_streams"):
                        st.divider()
                        for i, stream in enumerate(findings["revenue_streams"], 1):
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            col1.write(f"{i}. {stream['category']}")
                            if stream.get("amount"):
                                col2.write(f"{stream['amount']} {stream.get('unit', '')}")
                            if stream.get("year"):
                                col3.write(stream['year'])
                            if stream.get("page"):
                                col4.write(f"p.{stream['page']}")
                else:
                    st.info("Not analyzed")

            with tab2:
                if result["expenditure_findings"]:
                    findings = result["expenditure_findings"]

                    col_a, col_b = st.columns([1, 3])
                    col_a.metric("Confidence", findings.get('confidence_level', 'N/A'))
                    if findings.get("total_expenditure"):
                        total = findings["total_expenditure"]
                        col_b.metric("Total Expenditure", f"{total.get('amount', 'N/A')} {total.get('unit', '')}")

                    if findings.get('confidence_explanation'):
                        st.write(findings['confidence_explanation'])

                    if findings.get("expenditure_items"):
                        st.divider()
                        for i, item in enumerate(findings["expenditure_items"], 1):
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            col1.write(f"{i}. {item['category']}")
                            if item.get("amount"):
                                col2.write(f"{item['amount']} {item.get('unit', '')}")
                            if item.get("year"):
                                col3.write(item['year'])
                            if item.get("page"):
                                col4.write(f"p.{item['page']}")
                            if item.get("purpose"):
                                col1.caption(f"Purpose: {item['purpose']}")
                else:
                    st.info("Not analyzed")
