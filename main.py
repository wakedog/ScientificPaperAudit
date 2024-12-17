import streamlit as st
import pandas as pd
from utils.paper_fetcher import PaperFetcher
from utils.ai_analyzer import PaperAnalyzer
from utils.visualizations import Visualizer
import time

# Page configuration
st.set_page_config(
    page_title="Scientific Paper Analysis Platform",
    page_icon="📚",
    layout="wide"
)

# Load custom CSS
with open("styles/custom.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize components
paper_fetcher = PaperFetcher()
analyzer = PaperAnalyzer()
visualizer = Visualizer()

# Header
st.markdown("<h1 class='main-header'>Scientific Paper Analysis Platform</h1>", unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("Analysis Controls")
    paper_count = st.slider("Number of papers to analyze", 10, 1000, 100)
    analyze_button = st.button("Start Analysis")

# Main content
if analyze_button:
    # Create analysis pipeline
    with st.spinner("Fetching papers..."):
        papers = paper_fetcher.fetch_random_papers(paper_count)
        papers_df = paper_fetcher.create_dataframe(papers)
        
    with st.spinner("Analyzing papers..."):
        analysis_results = analyzer.analyze_batch(papers)
        
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Papers Analyzed", len(papers))
    with col2:
        avg_issues = analysis_results[[col for col in analysis_results.columns if 'issues' in col]].mean().mean()
        st.metric("Average Issues per Paper", f"{avg_issues:.2f}")
    with col3:
        avg_confidence = analysis_results[[col for col in analysis_results.columns if 'confidence' in col]].mean().mean()
        st.metric("Average Confidence Score", f"{avg_confidence:.1f}%")

    # Visualizations
    st.subheader("Analysis Results")
    
    # Error distribution
    st.plotly_chart(
        visualizer.create_error_distribution(analysis_results),
        use_container_width=True
    )
    
    # Confidence heatmap
    st.plotly_chart(
        visualizer.create_confidence_heatmap(analysis_results),
        use_container_width=True
    )
    
    # Timeline view
    st.plotly_chart(
        visualizer.create_timeline_view(analysis_results),
        use_container_width=True
    )
    
    # Detailed results table
    st.subheader("Detailed Results")
    st.dataframe(
        analysis_results.style.background_gradient(subset=[col for col in analysis_results.columns if 'confidence' in col])
    )
    
    # Export functionality
    csv = analysis_results.to_csv(index=False)
    st.download_button(
        label="Download Results CSV",
        data=csv,
        file_name="paper_analysis_results.csv",
        mime="text/csv"
    )
else:
    st.info("Click 'Start Analysis' to begin analyzing scientific papers.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Scientific Paper Analysis Platform | Powered by AI
    </div>
    """,
    unsafe_allow_html=True
)
