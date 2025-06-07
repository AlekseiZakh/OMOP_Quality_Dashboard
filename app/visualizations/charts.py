import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st
import logging


class OMOPCharts:
    """Specialized charts for OMOP data visualization"""
    
    @staticmethod
    def create_completeness_bar_chart(completeness_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a bar chart showing completeness percentages by table"""
        if not completeness_data:
            return OMOPCharts._create_empty_chart("No completeness data available")
        
        try:
            df = pd.DataFrame(completeness_data)
            
            # Calculate completeness percentage (100 - null_percentage)
            df['completeness_percentage'] = 100 - df.get('null_percentage', 0)
            
            # Color coding based on completeness
            colors = []
            for comp in df['completeness_percentage']:
                if comp >= 95:
                    colors.append('#28a745')  # Green
                elif comp >= 80:
                    colors.append('#ffc107')  # Yellow
                else:
                    colors.append('#dc3545')  # Red
            
            fig = go.Figure(data=[
                go.Bar(
                    x=df['table_name'],
                    y=df['completeness_percentage'],
                    marker_color=colors,
                    text=[f"{comp:.1f}%" for comp in df['completeness_percentage']],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Completeness: %{y:.1f}%<br>Total Rows: %{customdata}<extra></extra>',
                    customdata=df.get('total_rows', 0)
                )
            ])
            
            fig.update_layout(
                title="Data Completeness by Table",
                xaxis_title="OMOP Tables",
                yaxis_title="Completeness Percentage (%)",
                yaxis=dict(range=[0, 105]),
                height=500,
                showlegend=False
            )
            
            fig.update_xaxes(tickangle=45)
            
            # Add reference lines
            fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="Excellent (95%)")
            fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Good (80%)")
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating completeness bar chart: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_temporal_issues_chart(temporal_data: Dict[str, Any]) -> go.Figure:
        """Create a chart showing temporal consistency issues"""
        try:
            # Extract data for different temporal issues
            chart_data = []
            
            if 'future_dates' in temporal_data:
                future_data = temporal_data['future_dates'].get('data', [])
                for item in future_data:
                    if item.get('future_count', 0) > 0:
                        chart_data.append({
                            'issue_type': f"Future dates in {item['table']}",
                            'count': item['future_count'],
                            'category': 'Future Dates'
                        })
            
            if 'events_after_death' in temporal_data:
                death_data = temporal_data['events_after_death'].get('data', [])
                for item in death_data:
                    if item.get('events_after_death', 0) > 0:
                        chart_data.append({
                            'issue_type': f"{item['event_type']} after death",
                            'count': item['events_after_death'],
                            'category': 'Events After Death'
                        })
            
            if not chart_data:
                return OMOPCharts._create_empty_chart("No temporal issues found")
            
            df = pd.DataFrame(chart_data)
            
            fig = px.bar(
                df,
                x='issue_type',
                y='count',
                color='category',
                title="Temporal Consistency Issues",
                labels={'count': 'Number of Issues', 'issue_type': 'Issue Type'},
                color_discrete_map={
                    'Future Dates': '#ff6b6b',
                    'Events After Death': '#4ecdc4'
                }
            )
            
            fig.update_layout(
                height=400,
                xaxis_tickangle=45,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating temporal issues chart: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_concept_mapping_sunburst(mapping_data: Dict[str, Any]) -> go.Figure:
        """Create a sunburst chart showing concept mapping quality by domain"""
        try:
            if 'unmapped_concepts' not in mapping_data or not mapping_data['unmapped_concepts'].get('data'):
                return OMOPCharts._create_empty_chart("No concept mapping data available")
            
            data = mapping_data['unmapped_concepts']['data']
            
            # Prepare data for sunburst
            ids = []
            labels = []
            parents = []
            values = []
            colors = []
            
            # Root
            ids.append("root")
            labels.append("All Concepts")
            parents.append("")
            values.append(sum(item['total_records'] for item in data))
            colors.append(0.5)
            
            # Domains
            for item in data:
                domain = item['domain']
                total = item['total_records']
                unmapped = item['unmapped_count']
                mapped = total - unmapped
                
                # Domain node
                domain_id = f"domain_{domain}"
                ids.append(domain_id)
                labels.append(f"{domain}<br>{total:,} total")
                parents.append("root")
                values.append(total)
                colors.append(0.3)
                
                # Mapped concepts
                if mapped > 0:
                    ids.append(f"mapped_{domain}")
                    labels.append(f"Mapped<br>{mapped:,}")
                    parents.append(domain_id)
                    values.append(mapped)
                    colors.append(1.0)  # Green
                
                # Unmapped concepts
                if unmapped > 0:
                    ids.append(f"unmapped_{domain}")
                    labels.append(f"Unmapped<br>{unmapped:,}")
                    parents.append(domain_id)
                    values.append(unmapped)
                    colors.append(0.0)  # Red
            
            fig = go.Figure(go.Sunburst(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",
                hovertemplate='<b>%{label}</b><br>Count: %{value:,}<extra></extra>',
                marker=dict(
                    colorscale='RdYlGn',
                    cmid=0.5,
                    color=colors
                )
            ))
            
            fig.update_layout(
                title="Concept Mapping Quality by Domain",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating concept mapping sunburst: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_vocabulary_treemap(vocab_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a treemap showing vocabulary usage"""
        try:
            if not vocab_data:
                return OMOPCharts._create_empty_chart("No vocabulary data available")
            
            df = pd.DataFrame(vocab_data)
            
            # Calculate total usage for each vocabulary
            df['total_usage'] = (df.get('condition_usage', 0) + 
                               df.get('drug_usage', 0) + 
                               df.get('procedure_usage', 0))
            
            # Filter out vocabularies with no usage
            df = df[df['total_usage'] > 0].copy()
            
            if df.empty:
                return OMOPCharts._create_empty_chart("No vocabulary usage data available")
            
            # Sort by usage and take top 20
            df = df.nlargest(20, 'total_usage')
            
            fig = go.Figure(go.Treemap(
                labels=df['vocabulary_name'],
                values=df['total_usage'],
                parents=[""] * len(df),
                text=[f"{name}<br>{usage:,} uses<br>{concepts:,} concepts" 
                      for name, usage, concepts in zip(df['vocabulary_name'], df['total_usage'], df.get('unique_concepts', 0))],
                textinfo="text",
                hovertemplate='<b>%{label}</b><br>Total Usage: %{value:,}<br>Unique Concepts: %{customdata:,}<extra></extra>',
                customdata=df.get('unique_concepts', 0),
                marker=dict(
                    colorscale='Viridis',
                    colorbar=dict(title="Usage Count")
                )
            ))
            
            fig.update_layout(
                title="Vocabulary Usage Distribution",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating vocabulary treemap: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_measurement_outliers_scatter(outlier_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a scatter plot showing measurement outliers"""
        try:
            if not outlier_data:
                return OMOPCharts._create_empty_chart("No measurement outlier data available")
            
            df = pd.DataFrame(outlier_data)
            
            # Filter measurements that have outlier status
            df = df[df.get('outlier_status', '') == 'OUTLIER'].copy()
            
            if df.empty:
                return OMOPCharts._create_empty_chart("No measurement outliers found")
            
            fig = go.Figure()
            
            for _, row in df.iterrows():
                concept_name = row.get('concept_name', 'Unknown')
                min_val = row.get('min_value', 0)
                max_val = row.get('max_value', 0)
                avg_val = row.get('avg_value', 0)
                count = row.get('measurement_count', 0)
                
                # Add scatter point for each measurement type
                fig.add_trace(go.Scatter(
                    x=[concept_name],
                    y=[avg_val],
                    mode='markers',
                    marker=dict(
                        size=min(max(count/100, 10), 50),  # Size based on count
                        color='red',
                        opacity=0.7,
                        line=dict(width=2, color='darkred')
                    ),
                    name=concept_name,
                    text=f"Min: {min_val}<br>Max: {max_val}<br>Avg: {avg_val:.2f}<br>Count: {count:,}",
                    hovertemplate='<b>%{x}</b><br>Average: %{y:.2f}<br>%{text}<extra></extra>',
                    showlegend=False
                ))
                
                # Add error bars for min/max range
                fig.add_trace(go.Scatter(
                    x=[concept_name, concept_name],
                    y=[min_val, max_val],
                    mode='lines',
                    line=dict(color='red', width=2),
                    name=f"{concept_name} Range",
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            fig.update_layout(
                title="Measurement Value Outliers",
                xaxis_title="Measurement Type",
                yaxis_title="Value",
                height=500,
                xaxis_tickangle=45
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating measurement outliers scatter: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_data_density_timeline(density_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a timeline showing data density by year"""
        try:
            if not density_data:
                return OMOPCharts._create_empty_chart("No data density information available")
            
            df = pd.DataFrame(density_data)
            
            if 'year' not in df.columns or 'total_conditions' not in df.columns:
                return OMOPCharts._create_empty_chart("Invalid data structure for timeline")
            
            # Sort by year
            df = df.sort_values('year')
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Total Conditions by Year', 'Unique Patients by Year'),
                vertical_spacing=0.1
            )
            
            # Conditions timeline
            fig.add_trace(
                go.Scatter(
                    x=df['year'],
                    y=df['total_conditions'],
                    mode='lines+markers',
                    name='Total Conditions',
                    line=dict(color='blue', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>Year: %{x}</b><br>Conditions: %{y:,}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Patients timeline
            if 'unique_patients' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['year'],
                        y=df['unique_patients'],
                        mode='lines+markers',
                        name='Unique Patients',
                        line=dict(color='green', width=3),
                        marker=dict(size=8),
                        hovertemplate='<b>Year: %{x}</b><br>Patients: %{y:,}<extra></extra>'
                    ),
                    row=2, col=1
                )
            
            fig.update_layout(
                title="Data Density Over Time",
                height=600,
                showlegend=True
            )
            
            fig.update_xaxes(title_text="Year")
            fig.update_yaxes(title_text="Count", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=2, col=1)
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating data density timeline: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_foreign_key_violations_chart(fk_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a chart showing foreign key violations"""
        try:
            if not fk_data:
                return OMOPCharts._create_empty_chart("No foreign key violations found")
            
            # Filter out relationships with no violations
            violations = [item for item in fk_data if item.get('violations', 0) > 0]
            
            if not violations:
                return OMOPCharts._create_empty_chart("No foreign key violations found")
            
            df = pd.DataFrame(violations)
            
            fig = px.bar(
                df,
                x='relationship',
                y='violations',
                title="Foreign Key Violations by Relationship",
                labels={'violations': 'Number of Violations', 'relationship': 'Table Relationship'},
                color='violations',
                color_continuous_scale='Reds'
            )
            
            fig.update_layout(
                height=400,
                xaxis_tickangle=45,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating foreign key violations chart: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_age_distribution_histogram(age_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a histogram showing age distribution"""
        try:
            if not age_data:
                return OMOPCharts._create_empty_chart("No age distribution data available")
            
            df = pd.DataFrame(age_data)
            
            if 'age_group' not in df.columns or 'count' not in df.columns:
                return OMOPCharts._create_empty_chart("Invalid age distribution data")
            
            # Sort age groups in logical order
            age_order = ['Under 18', '18-30', '31-50', '51-70', 'Over 70', 'Unknown']
            df['age_group'] = pd.Categorical(df['age_group'], categories=age_order, ordered=True)
            df = df.sort_values('age_group')
            
            fig = px.bar(
                df,
                x='age_group',
                y='count',
                title="Patient Age Distribution",
                labels={'count': 'Number of Patients', 'age_group': 'Age Group'},
                color='percentage',
                color_continuous_scale='Blues',
                text='percentage'
            )
            
            fig.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside'
            )
            
            fig.update_layout(
                height=400,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating age distribution histogram: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_visit_duration_box_plot(visit_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a box plot showing visit duration distribution"""
        try:
            if not visit_data:
                return OMOPCharts._create_empty_chart("No visit duration data available")
            
            df = pd.DataFrame(visit_data)
            
            required_cols = ['visit_type', 'avg_duration_days', 'min_duration_days', 'max_duration_days']
            if not all(col in df.columns for col in required_cols):
                return OMOPCharts._create_empty_chart("Invalid visit duration data structure")
            
            # Filter out visits with problematic durations
            df = df[
                (df['min_duration_days'] >= 0) & 
                (df['max_duration_days'] <= 365) &
                (df.get('visit_count', 0) > 10)  # Only include visit types with substantial data
            ].copy()
            
            if df.empty:
                return OMOPCharts._create_empty_chart("No valid visit duration data after filtering")
            
            fig = go.Figure()
            
            for _, row in df.iterrows():
                visit_type = row['visit_type']
                
                # Create a box plot for each visit type
                # Note: This is simplified - in reality you'd want the raw data points
                fig.add_trace(go.Box(
                    y=[row['min_duration_days'], 
                       row['avg_duration_days'] - (row['avg_duration_days'] - row['min_duration_days'])/2,
                       row['avg_duration_days'], 
                       row['avg_duration_days'] + (row['max_duration_days'] - row['avg_duration_days'])/2,
                       row['max_duration_days']],
                    name=visit_type,
                    boxmean='sd',
                    hovertemplate=f'<b>{visit_type}</b><br>Duration: %{{y}} days<extra></extra>'
                ))
            
            fig.update_layout(
                title="Visit Duration Distribution by Visit Type",
                yaxis_title="Duration (Days)",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating visit duration box plot: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_quality_summary_radar(quality_scores: Dict[str, float]) -> go.Figure:
        """Create a radar chart showing overall quality scores"""
        try:
            if not quality_scores:
                return OMOPCharts._create_empty_chart("No quality scores available")
            
            categories = list(quality_scores.keys())
            values = list(quality_scores.values())
            
            # Close the radar chart
            categories += [categories[0]]
            values += [values[0]]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Quality Scores',
                line=dict(color='blue', width=2),
                marker=dict(color='blue', size=8)
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickvals=[20, 40, 60, 80, 100],
                        ticktext=['20%', '40%', '60%', '80%', '100%']
                    )
                ),
                title="Overall Quality Scores by Category",
                height=500,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating quality summary radar: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def create_unmapped_concepts_waterfall(unmapped_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a waterfall chart showing unmapped concepts by domain"""
        try:
            if not unmapped_data:
                return OMOPCharts._create_empty_chart("No unmapped concept data available")
            
            df = pd.DataFrame(unmapped_data)
            
            if 'domain' not in df.columns or 'unmapped_count' not in df.columns:
                return OMOPCharts._create_empty_chart("Invalid unmapped concept data")
            
            # Filter domains with unmapped concepts
            df = df[df['unmapped_count'] > 0].copy()
            
            if df.empty:
                return OMOPCharts._create_empty_chart("No unmapped concepts found")
            
            # Sort by unmapped count
            df = df.sort_values('unmapped_count', ascending=False)
            
            fig = go.Figure(go.Waterfall(
                name="Unmapped Concepts",
                orientation="v",
                measure=["relative"] * len(df),
                x=df['domain'],
                textposition="outside",
                text=[f"{count:,}" for count in df['unmapped_count']],
                y=df['unmapped_count'],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "#ff6b6b"}},
                totals={"marker": {"color": "#1f77b4"}}
            ))
            
            fig.update_layout(
                title="Unmapped Concepts by Domain",
                xaxis_title="Domain",
                yaxis_title="Number of Unmapped Concepts",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating unmapped concepts waterfall: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")
    
    @staticmethod
    def _create_empty_chart(message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            xanchor='center',
            yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        
        fig.update_layout(
            height=400,
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        
        return fig


class InteractiveCharts:
    """Interactive chart components with user controls"""
    
    @staticmethod
    def create_filterable_table_chart(data: List[Dict[str, Any]], 
                                    title: str = "Filterable Data") -> Tuple[go.Figure, Dict]:
        """Create a chart with interactive filters"""
        try:
            if not data:
                return OMOPCharts._create_empty_chart("No data available"), {}
            
            df = pd.DataFrame(data)
            
            # Create filter controls
            filters = {}
            
            # Get categorical columns for filtering
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if categorical_cols:
                st.sidebar.subheader("🔍 Filters")
                
                for col in categorical_cols[:3]:  # Limit to 3 filters to avoid clutter
                    unique_values = df[col].unique().tolist()
                    if len(unique_values) > 1 and len(unique_values) <= 20:  # Reasonable number of options
                        selected_values = st.sidebar.multiselect(
                            f"Filter by {col.replace('_', ' ').title()}",
                            options=unique_values,
                            default=unique_values,
                            key=f"filter_{col}"
                        )
                        filters[col] = selected_values
            
            # Apply filters
            filtered_df = df.copy()
            for col, values in filters.items():
                if values:  # Only apply filter if values are selected
                    filtered_df = filtered_df[filtered_df[col].isin(values)]
            
            # Create chart based on filtered data
            if len(filtered_df) == 0:
                return OMOPCharts._create_empty_chart("No data matches the selected filters"), filters
            
            # Simple bar chart of first numeric column
            numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols and categorical_cols:
                fig = px.bar(
                    filtered_df,
                    x=categorical_cols[0],
                    y=numeric_cols[0],
                    title=f"{title} (Filtered)",
                    height=400
                )
                fig.update_xaxes(tickangle=45)
            else:
                fig = OMOPCharts._create_empty_chart("Unable to create chart from available data")
            
            return fig, filters
            
        except Exception as e:
            logging.error(f"Error creating filterable chart: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart"), {}
    
    @staticmethod
    def create_time_series_chart(data: List[Dict[str, Any]], 
                               date_col: str, 
                               value_col: str,
                               title: str = "Time Series") -> go.Figure:
        """Create an interactive time series chart"""
        try:
            if not data:
                return OMOPCharts._create_empty_chart("No time series data available")
            
            df = pd.DataFrame(data)
            
            if date_col not in df.columns or value_col not in df.columns:
                return OMOPCharts._create_empty_chart(f"Required columns {date_col}, {value_col} not found")
            
            # Convert date column
            try:
                df[date_col] = pd.to_datetime(df[date_col])
            except:
                return OMOPCharts._create_empty_chart(f"Unable to parse dates in {date_col}")
            
            # Sort by date
            df = df.sort_values(date_col)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=df[value_col],
                mode='lines+markers',
                name=value_col.replace('_', ' ').title(),
                line=dict(width=3),
                marker=dict(size=6),
                hovertemplate='<b>Date:</b> %{x}<br><b>Value:</b> %{y:,.0f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title=value_col.replace('_', ' ').title(),
                height=400,
                hovermode='x unified'
            )
            
            # Add range selector
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1Y", step="year", stepmode="backward"),
                            dict(count=2, label="2Y", step="year", stepmode="backward"),
                            dict(count=5, label="5Y", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=True),
                    type="date"
                )
            )
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating time series chart: {e}")
            return OMOPCharts._create_empty_chart("Error creating chart")


# Export main classes
__all__ = [
    'OMOPCharts',
    'InteractiveCharts'
]
