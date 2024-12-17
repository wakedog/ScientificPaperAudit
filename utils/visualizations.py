import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

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
        """Create error distribution visualization."""
        error_counts = df[[col for col in df.columns if 'issues' in col]].sum()
        
        fig = go.Figure(data=[
            go.Bar(
                x=error_counts.index,
                y=error_counts.values,
                marker_color=self.colors['navy']
            )
        ])
        
        fig.update_layout(
            title="Distribution of Errors Across Categories",
            xaxis_title="Error Category",
            yaxis_title="Number of Issues",
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background']
        )
        
        return fig

    def create_confidence_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create confidence score heatmap."""
        confidence_cols = [col for col in df.columns if 'confidence' in col]
        confidence_data = df[confidence_cols].mean()
        
        fig = go.Figure(data=go.Heatmap(
            z=[confidence_data.values],
            x=confidence_data.index,
            colorscale='RdYlBu',
            showscale=True
        ))
        
        fig.update_layout(
            title="Average Confidence Scores by Category",
            xaxis_title="Category",
            yaxis_showticklabels=False,
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background']
        )
        
        return fig

    def create_timeline_view(self, df: pd.DataFrame) -> go.Figure:
        """Create timeline of papers and their issues."""
        df['total_issues'] = df[[col for col in df.columns if 'issues' in col]].sum(axis=1)
        
        fig = px.scatter(
            df,
            x='published',
            y='total_issues',
            hover_data=['title'],
            color='total_issues',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            title="Issues Distribution Over Time",
            xaxis_title="Publication Date",
            yaxis_title="Total Issues Found",
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background']
        )
        
        return fig
