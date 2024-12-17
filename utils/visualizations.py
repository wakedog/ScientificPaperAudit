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
