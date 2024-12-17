import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import networkx as nx

class Visualizer:
    def __init__(self):
        self.colors = {
            'background': '#FAFAFA',
            'navy': '#000080',
            'highlight1': '#FF4B4B',
            'highlight2': '#1F77B4',
            'highlight3': '#2CA02C'
        }

    def create_error_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create enhanced error distribution visualization with hover data and patterns."""
        error_counts = df[[col for col in df.columns if 'issues' in col]].sum()
        confidence_avgs = df[[col for col in df.columns if 'confidence' in col]].mean()
        severity_levels = []
        
        # Calculate severity levels
        for cat in error_counts.index:
            avg_issues = error_counts[cat]
            avg_conf = confidence_avgs[cat.replace('_issues', '_confidence')]
            if avg_issues > error_counts.mean() and avg_conf < confidence_avgs.mean():
                severity = 'High Risk'
            elif avg_issues > error_counts.mean() or avg_conf < confidence_avgs.mean():
                severity = 'Moderate Risk'
            else:
                severity = 'Low Risk'
            severity_levels.append(severity)
        
        # Create hover text with enhanced information
        hover_text = [
            f"Category: {cat.replace('_issues', '')}<br>" +
            f"Total Issues: {issues}<br>" +
            f"Avg Confidence: {conf:.1f}%<br>" +
            f"Risk Level: {sev}"
            for cat, issues, conf, sev in zip(
                error_counts.index,
                error_counts.values,
                confidence_avgs.values,
                severity_levels
            )
        ]
        
        # Color mapping based on severity
        color_map = {
            'High Risk': self.colors['highlight1'],
            'Moderate Risk': '#FFA500',  # Orange
            'Low Risk': self.colors['navy']
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=error_counts.index,
                y=error_counts.values,
                marker_color=[color_map[sev] for sev in severity_levels],
                hovertext=hover_text,
                hoverinfo='text',
                text=severity_levels,
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title={
                'text': "Distribution of Errors Across Categories",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Error Category",
            yaxis_title="Number of Issues",
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        return fig

    def create_confidence_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create enhanced confidence score heatmap with temporal patterns."""
        confidence_cols = [col for col in df.columns if 'confidence' in col]
        
        # Group by time periods for temporal analysis
        df['month'] = pd.to_datetime(df['published']).dt.strftime('%Y-%m')
        temporal_confidence = df.groupby('month')[confidence_cols].mean().tail(6)  # Last 6 months
        
        # Create enhanced heatmap
        fig = go.Figure(data=go.Heatmap(
            z=temporal_confidence.values,
            x=[col.replace('_confidence', '') for col in confidence_cols],
            y=temporal_confidence.index,
            colorscale='RdYlBu',
            showscale=True,
            hoverongaps=False,
            hovertemplate='Category: %{x}<br>Period: %{y}<br>Confidence: %{z:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': "Confidence Score Trends by Category",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Category",
            yaxis_title="Time Period",
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        return fig

    def create_timeline_view(self, df: pd.DataFrame) -> go.Figure:
        """Create enhanced timeline view with trend analysis."""
        # Calculate moving averages for smoother trends
        window_size = 7
        df = df.sort_values('published')
        df['total_issues'] = df[[col for col in df.columns if 'issues' in col]].sum(axis=1)
        df['ma_issues'] = df['total_issues'].rolling(window=window_size).mean()
        
        # Create main scatter plot
        fig = go.Figure()
        
        # Add individual points
        fig.add_trace(go.Scatter(
            x=df['published'],
            y=df['total_issues'],
            mode='markers',
            name='Individual Papers',
            marker=dict(
                size=8,
                color=df['total_issues'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Issue Count")
            ),
            hovertemplate="<br>".join([
                "Title: %{customdata[0]}",
                "Date: %{x}",
                "Issues: %{y}",
                "<extra></extra>"
            ]),
            customdata=df[['title']]
        ))
        
        # Add trend line
        fig.add_trace(go.Scatter(
            x=df['published'],
            y=df['ma_issues'],
            mode='lines',
            name=f'{window_size}-Day Moving Average',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title={
                'text': "Temporal Analysis of Paper Issues",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Publication Date",
            yaxis_title="Number of Issues",
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            hovermode='closest',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )
        
        return fig
        
    def create_correlation_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create correlation heatmap between different error categories."""
        # Extract issues columns
        issues_cols = [col for col in df.columns if 'issues' in col]
        correlation_matrix = df[issues_cols].corr()
        
        # Create annotation text
        annotations = []
        for i, row in enumerate(correlation_matrix.values):
            for j, value in enumerate(row):
                annotations.append(
                    dict(
                        x=correlation_matrix.columns[j],
                        y=correlation_matrix.index[i],
                        text=f"{value:.2f}",
                        font=dict(color='white' if abs(value) > 0.4 else 'black'),
                        showarrow=False
                    )
                )
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu',
            zmid=0,
            showscale=True,
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title={
                'text': "Error Category Correlations",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Error Category",
            yaxis_title="Error Category",
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            annotations=annotations
        )
        
        return fig
        
    def create_paper_similarity_network(self, df: pd.DataFrame) -> go.Figure:
        """Create interactive paper similarity network visualization."""
        # Calculate similarity scores between papers based on their error patterns
        error_cols = [col for col in df.columns if 'issues' in col]
        
        # Ensure we have numeric data
        numeric_df = df[error_cols].fillna(0).astype(float)
        
        # Initialize similarity matrix with zeros
        n_papers = len(numeric_df)
        similarity_matrix = np.zeros((n_papers, n_papers))
        
        # Calculate similarities
        for i in range(n_papers):
            for j in range(n_papers):
                if i != j:
                    paper1 = numeric_df.iloc[i].values
                    paper2 = numeric_df.iloc[j].values
                    # Avoid division by zero
                    norm1 = np.linalg.norm(paper1)
                    norm2 = np.linalg.norm(paper2)
                    if norm1 > 0 and norm2 > 0:
                        similarity_matrix[i, j] = np.dot(paper1, paper2) / (norm1 * norm2)
        
        # Convert to pandas DataFrame for networkx
        similarity_df = pd.DataFrame(
            similarity_matrix,
            index=numeric_df.index,
            columns=numeric_df.index
        )
        
        # Create network layout
        G = nx.from_numpy_array(similarity_matrix)
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Create edges (connections between similar papers)
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # Create nodes (papers)
        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Error Count',
                    xanchor='left',
                    titleside='right'
                )
            ),
            text=df['title'],
            textposition="top center"
        )
        
        # Color nodes by total error count
        node_colors = df[error_cols].sum(axis=1)
        node_trace.marker.color = node_colors
        
        # Create the figure
        fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                         title='Paper Similarity Network',
                         showlegend=False,
                         hovermode='closest',
                         margin=dict(b=20,l=5,r=5,t=40),
                         plot_bgcolor=self.colors['background'],
                         paper_bgcolor=self.colors['background'],
                         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                     )
        
        return fig
        
    def create_topic_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create topic distribution visualization using categories."""
        try:
            if 'categories' not in df.columns:
                # Create a basic figure with a message when no categories are available
                fig = go.Figure()
                fig.add_annotation(
                    text="No category data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=20)
                )
                return fig

            # Extract categories and count papers per category
            categories = []
            for cats in df['categories'].fillna([]):
                if isinstance(cats, (list, tuple)):
                    categories.extend(cats)
                elif isinstance(cats, str):
                    categories.append(cats)
                    
            if not categories:
                fig = go.Figure()
                fig.add_annotation(
                    text="No categories found in the data",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=20)
                )
                return fig
                
            category_counts = pd.Series(categories).value_counts()
            
            # Create sunburst chart
            fig = go.Figure(go.Sunburst(
                labels=category_counts.index,
                parents=[""] * len(category_counts),
                values=category_counts.values,
                branchvalues="total",
            ))
        
        fig.update_layout(
            title={
                'text': "Distribution of Papers by Category",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            width=800,
            height=800,
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background']
        )
        
        return fig
        
    def create_trend_analysis(self, df: pd.DataFrame) -> go.Figure:
        """Create trend analysis visualization showing patterns over time."""
        # Prepare time series data
        df['date'] = pd.to_datetime(df['published'])
        df.set_index('date', inplace=True)
        df_resampled = df[[col for col in df.columns if 'issues' in col]].resample('W').mean()
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add traces for each error category
        for col in df_resampled.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_resampled.index,
                    y=df_resampled[col],
                    name=col.replace('_issues', ''),
                    mode='lines+markers'
                ),
                secondary_y=False
            )
        
        # Calculate and add trend line
        for col in df_resampled.columns:
            z = np.polyfit(range(len(df_resampled.index)), df_resampled[col], 1)
            p = np.poly1d(z)
            fig.add_trace(
                go.Scatter(
                    x=df_resampled.index,
                    y=p(range(len(df_resampled.index))),
                    name=f"{col.replace('_issues', '')} trend",
                    line=dict(dash='dash'),
                    opacity=0.5
                ),
                secondary_y=False
            )
        
        fig.update_layout(
            title={
                'text': "Error Trends Over Time",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Date",
            yaxis_title="Number of Issues",
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            hovermode='x unified'
        )
        
        return fig
