import streamlit as st
import pandas as pd
from recommendation import recommend_assessments

st.set_page_config(page_title="SHL Assessment Recommender", layout="wide")

st.title("SHL Assessment Recommendation System")
st.write("Enter a job description or query (or paste a URL) to get relevant SHL assessment recommendations.")

query_input = st.text_area("Job Description / Query / URL", height=150)

if st.button("Get Recommendations"):
    if not query_input.strip():
        st.error("Please enter a job description, query, or URL.")
    else:
        with st.spinner("Finding recommendations..."):
            try:
                results = recommend_assessments(query_input, top_k=10)
                if not results:
                    st.warning("No recommendations found. Please refine your query.")
                else:
                    # Prepare DataFrame
                    for r in results:
                        r["Assessment"] = f"[{r['name']}]({r['url']})"
                        r["Duration (min)"] = r.pop("duration_minutes", None)
                        r["Remote"] = r.pop("remote")
                        r["Adaptive (IRT)"] = r.pop("adaptive")
                        r["Test Type"] = r.pop("test_type")
                        # remove url & name fields
                        r.pop("url", None)
                        r.pop("name", None)
                    df = pd.DataFrame(results)
                    st.markdown(df.to_markdown(index=False), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")