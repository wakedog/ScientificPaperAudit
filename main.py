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

# Initialize session state
if 'selected_paper_index' not in st.session_state:
    st.session_state.selected_paper_index = None

# Header
st.markdown("<h1 class='main-header'>Scientific Paper Analysis Platform</h1>", unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("Analysis Controls")
    
    # Search functionality
    search_topic = st.text_input("Search Topic", 
                                placeholder="Enter a topic to search for specific papers...")
    paper_count = st.slider("Number of papers to analyze", 10, 1000, 100)
    
    st.subheader("Filters")
    min_confidence = st.slider("Minimum Confidence Score", 0, 100, 50)
    error_threshold = st.slider("Minimum Issues to Highlight", 0, 10, 3)
    
    selected_categories = st.multiselect(
        "Filter Error Categories",
        analyzer.error_categories,
        default=analyzer.error_categories
    )
    
    analyze_button = st.button("Start Analysis")

# Main content
if analyze_button:
    # Create analysis pipeline
    with st.spinner("Fetching papers..."):
        papers = paper_fetcher.fetch_papers(paper_count, topic=search_topic)
        papers_df = paper_fetcher.create_dataframe(papers)
        
    with st.spinner("Analyzing papers..."):
        analysis_results = analyzer.analyze_batch(papers)
        # Add categories from original papers dataframe
        analysis_results['categories'] = papers_df['categories']
            
    # Filter data based on user selections
    filtered_results = analysis_results.copy()
    
    # Apply confidence filter
    confidence_cols = [col for col in filtered_results.columns if 'confidence' in col]
    confidence_mask = filtered_results[confidence_cols].mean(axis=1) >= min_confidence
    filtered_results = filtered_results[confidence_mask]
    
    # Apply category filters
    selected_cols = []
    for category in selected_categories:
        selected_cols.extend([
            col for col in filtered_results.columns 
            if category.lower().replace(' ', '_') in col.lower()
        ])
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Papers", len(papers))
    with col2:
        st.metric("Filtered Papers", len(filtered_results))
    with col3:
        avg_issues = filtered_results[[col for col in filtered_results.columns if 'issues' in col]].mean().mean()
        st.metric("Avg Issues/Paper", f"{avg_issues:.2f}")
    with col4:
        high_risk_papers = len(filtered_results[
            filtered_results[[col for col in filtered_results.columns if 'issues' in col]].sum(axis=1) >= error_threshold
        ])
        st.metric("High Risk Papers", high_risk_papers)

    # Visualizations
    st.subheader("Analysis Results")
    
    # Get pattern analysis
    patterns = analyzer.aggregate_patterns(analysis_results)
    
    # Display pattern insights
    st.markdown("### Key Pattern Insights")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Trend Analysis")
        for category, trend in patterns['temporal_patterns']['trend_direction'].items():
            trend_icon = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
            st.write(f"{trend_icon} {category}: {trend.title()}")
    
    with col2:
        st.markdown("#### Strong Correlations")
        for category, correlations in patterns['error_correlations'].items():
            if correlations:
                corr_text = ", ".join([f"{cat} ({corr:+.2f})" for cat, corr in correlations.items()])
                st.write(f"🔗 {category} correlates with: {corr_text}")
    
    # Create tabs for different visualization categories
    viz_tabs = st.tabs(["Error Analysis", "Paper Relationships", "Trends", "Categories"])
    
    with viz_tabs[0]:
        st.markdown("### Error Analysis")
        # Error distribution
        st.plotly_chart(
            visualizer.create_error_distribution(analysis_results),
            use_container_width=True
        )
        
        # Correlation heatmap
        st.plotly_chart(
            visualizer.create_correlation_heatmap(analysis_results),
            use_container_width=True
        )
        
        # Confidence heatmap
        st.plotly_chart(
            visualizer.create_confidence_heatmap(analysis_results),
            use_container_width=True
        )
    
    with viz_tabs[1]:
        st.markdown("### Paper Relationships")
        # Paper similarity network
        st.plotly_chart(
            visualizer.create_paper_similarity_network(analysis_results),
            use_container_width=True
        )
    
    with viz_tabs[2]:
        st.markdown("### Temporal Analysis")
        # Enhanced timeline view
        st.plotly_chart(
            visualizer.create_timeline_view(analysis_results),
            use_container_width=True
        )
        
        # Trend analysis
        st.plotly_chart(
            visualizer.create_trend_analysis(analysis_results),
            use_container_width=True
        )
    
    with viz_tabs[3]:
        st.markdown("### Category Distribution")
        # Topic distribution
        st.plotly_chart(
            visualizer.create_topic_distribution(analysis_results),
            use_container_width=True
        )
    
    # Detailed results table
    st.subheader("Detailed Results")
    
    # Prepare display dataframe
    display_df = analysis_results.copy()
    # Add paper URLs to display dataframe
    display_df['url'] = papers_df['url'].apply(lambda x: x if isinstance(x, str) else '')
    
    # Ensure URLs are valid
    display_df['url'] = display_df['url'].apply(
        lambda x: x if x.startswith('http') else f'https://arxiv.org/abs/{x.split("/")[-1]}' if x else ''
    )
    
    # Configure columns for better display
    column_config = {
        "title": st.column_config.TextColumn(
            "Paper Title",
            help="Title of the research paper",
            width="large"
        ),
        "published": st.column_config.DatetimeColumn(
            "Publication Date",
            format="DD/MM/YYYY",
            width="medium"
        ),
        "url": st.column_config.LinkColumn(
            "Paper Link",
            help="Click to view the original paper",
            validate="^https?://.*",
            max_chars=None,
            display_text="View Paper ↗",
            width="small"
        )
    }
    
    # Configure confidence and issues columns
    for category in analyzer.error_categories:
        conf_col = f"{category}_confidence"
        issues_col = f"{category}_issues"
        
        column_config[conf_col] = st.column_config.NumberColumn(
            f"{category} Confidence",
            help=f"Confidence score for {category}",
            format="%.1f%%"
        )
        column_config[issues_col] = st.column_config.NumberColumn(
            f"{category} Issues",
            help=f"Number of issues found in {category}"
        )
    
    # Add detailed error analysis section
    st.subheader("Detailed Error Analysis")
    st.info("Click on a paper in the table below to see detailed error analysis")

    # Display the dataframe with configured columns and handle selection
    selection = st.data_editor(
        display_df,
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
        num_rows="dynamic",
        key="paper_analysis_table",
        disabled=True,
        column_order=["title", "published", "url"] + [col for col in display_df.columns if col not in ["title", "published", "url"]],
        height=400,
        on_change=lambda: None,  # Add empty on_change to enable selection
    )

    # Handle paper selection using selected_rows
    if st.session_state.paper_analysis_table["selected_rows"]:
        selected_index = st.session_state.paper_analysis_table["selected_rows"][0]
        selected_paper_title = display_df.iloc[selected_index]["title"]
        selected_paper = next((p for p in papers if p['title'] == selected_paper_title), None)
        
        if selected_paper:
            st.session_state.selected_paper_index = papers.index(selected_paper)
    
    # Display detailed error analysis for selected paper
    if st.session_state.selected_paper_index is not None:
        selected_paper = papers[st.session_state.selected_paper_index]
        analysis = analyzer.analyze_paper(selected_paper)
        
        for category in analyzer.error_categories:
            if category in analysis:
                with st.expander(f"{category} Analysis"):
                    issues = analysis[category].get('issues', [])
                    if isinstance(issues, list) and issues:
                        for idx, issue in enumerate(issues, 1):
                            severity_color = {
                                'high': 'red',
                                'medium': 'orange',
                                'low': 'blue'
                            }.get(issue.get('severity', 'low'), 'gray')
                            
                            st.markdown(f"""
                            ##### Issue {idx}
                            **Location:** {issue.get('location', 'Not specified')}  
                            **Severity:** :{severity_color}[●] {issue.get('severity', 'Not specified')}
                            
                            **Description:**  
                            {issue.get('description', 'No description available')}
                            
                            **Context:**  
                            > {issue.get('context', 'No context available')}
                            
                            **Suggestion:**  
                            {issue.get('suggestion', 'No suggestion available')}
                            """)
                            st.divider()
                    else:
                        st.write("No specific issues found in this category.")
    
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