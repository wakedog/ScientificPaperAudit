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
