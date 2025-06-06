import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional
from datetime import datetime


class DashboardComponents:
    """Collection of reusable dashboard components"""
    
    @staticmethod
    def render_status_badge(status: str, message: str = "") -> str:
        """Render a status badge with appropriate styling"""
        status_styles = {
            'PASS': {'color': '#28a745', 'icon': '✅', 'label': 'PASS'},
            'WARNING': {'color': '#ffc107', 'icon': '⚠️', 'label': 'WARNING'},
            'FAIL': {'color': '#dc3545', 'icon': '❌', 'label': 'FAIL'},
            'ERROR': {'color': '#6c757d', 'icon': '🔧', 'label': 'ERROR'}
        }
        
        style = status_styles.get(status.upper(), status_styles['ERROR'])
        
        badge_html = f"""
        <span style="
            background-color: {style['color']};
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        ">
            {style['icon']} {style['label']}
        </span>
        """
        
        if message:
            badge_html += f"<span style='margin-left: 8px;'>{message}</span>"
        
        return badge_html
    
    @staticmethod
    def render_metric_card(title: str, value: Any, delta: Optional[Any] = None, 
                          status: Optional[str] = None, help_text: Optional[str] = None):
        """Render a metric card with optional status and delta"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if delta is not None:
                st.metric(
                    label=title,
                    value=value,
                    delta=delta,
                    help=help_text
                )
            else:
                st.metric(
                    label=title,
                    value=value,
                    help=help_text
                )
        
        with col2:
            if status:
                st.markdown(
                    DashboardComponents.render_status_badge(status),
                    unsafe_allow_html=True
                )
    
    @staticmethod
    def render_summary_cards(summary_data: Dict[str, Any], cols: int = 4):
        """Render a row of summary metric cards"""
        columns = st.columns(cols)
        
        for i, (key, data) in enumerate(summary_data.items()):
            with columns[i % cols]:
                if isinstance(data, dict):
                    value = data.get('value', 'N/A')
                    delta = data.get('delta')
                    status = data.get('status')
                    help_text = data.get('help')
                    
                    DashboardComponents.render_metric_card(
                        title=key,
                        value=value,
                        delta=delta,
                        status=status,
                        help_text=help_text
                    )
                else:
                    st.metric(label=key, value=data)
    
    @staticmethod
    def render_quality_score_gauge(score: float, title: str = "Quality Score"):
        """Render a quality score gauge chart"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 20}},
            delta={'reference': 90, 'relative': True},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': 'lightgray'},
                    {'range': [50, 80], 'color': 'yellow'},
                    {'range': [80, 95], 'color': 'lightgreen'},
                    {'range': [95, 100], 'color': 'green'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            font={'color': "darkblue", 'family': "Arial"}
        )
        
        return fig
    
    @staticmethod
    def render_status_distribution_pie(status_counts: Dict[str, int], title: str = "Check Status Distribution"):
        """Render a pie chart showing distribution of check statuses"""
        if not status_counts or sum(status_counts.values()) == 0:
            st.warning("No status data available for visualization")
            return None
        
        labels = list(status_counts.keys())
        values = list(status_counts.values())
        
        colors = {
            'PASS': '#28a745',
            'WARNING': '#ffc107',
            'FAIL': '#dc3545',
            'ERROR': '#6c757d'
        }
        
        color_sequence = [colors.get(label, '#6c757d') for label in labels]
        
        fig = px.pie(
            values=values,
            names=labels,
            title=title,
            color_discrete_sequence=color_sequence
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    @staticmethod
    def render_quality_trend_chart(trend_data: pd.DataFrame, x_col: str, y_col: str, 
                                 title: str = "Quality Trend Over Time"):
        """Render a line chart showing quality trends"""
        if trend_data.empty:
            st.warning("No trend data available for visualization")
            return None
        
        fig = px.line(
            trend_data,
            x=x_col,
            y=y_col,
            title=title,
            markers=True
        )
        
        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8)
        )
        
        fig.update_layout(
            height=400,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            hovermode='x unified'
        )
        
        # Add reference line at 90% if it's a percentage metric
        if 'percentage' in y_col.lower() or 'score' in y_col.lower():
            fig.add_hline(
                y=90,
                line_dash="dash",
                line_color="red",
                annotation_text="Target: 90%"
            )
        
        return fig
    
    @staticmethod
    def render_table_completeness_heatmap(completeness_data: List[Dict[str, Any]]):
        """Render a heatmap showing table completeness"""
        if not completeness_data:
            st.warning("No completeness data available for heatmap")
            return None
        
        df = pd.DataFrame(completeness_data)
        
        if 'table_name' not in df.columns or 'null_percentage' not in df.columns:
            st.warning("Invalid data structure for completeness heatmap")
            return None
        
        # Create a matrix for heatmap (single row with multiple columns)
        tables = df['table_name'].tolist()
        completeness_scores = (100 - df['null_percentage']).tolist()
        
        fig = go.Figure(data=go.Heatmap(
            z=[completeness_scores],
            x=tables,
            y=['Completeness %'],
            colorscale='RdYlGn',
            zmin=0,
            zmax=100,
            text=[[f"{score:.1f}%" for score in completeness_scores]],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate='<b>%{x}</b><br>Completeness: %{z:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title="Table Completeness Heatmap",
            xaxis_title="OMOP Tables",
            height=200,
            xaxis={'tickangle': 45}
        )
        
        return fig
    
    @staticmethod
    def render_expandable_details(title: str, data: Any, key: str):
        """Render expandable details section"""
        with st.expander(f"📋 {title}"):
            if isinstance(data, pd.DataFrame):
                if not data.empty:
                    st.dataframe(data, use_container_width=True, key=f"df_{key}")
                else:
                    st.info("No data available")
            elif isinstance(data, dict):
                st.json(data)
            elif isinstance(data, list):
                if data:
                    if isinstance(data[0], dict):
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True, key=f"list_{key}")
                    else:
                        for i, item in enumerate(data):
                            st.write(f"{i+1}. {item}")
                else:
                    st.info("No data available")
            else:
                st.write(data)
    
    @staticmethod
    def render_download_section(data: Any, filename_prefix: str):
        """Render download buttons for different formats"""
        if data is None:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if isinstance(data, pd.DataFrame):
                csv = data.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{filename_prefix}_{timestamp}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if isinstance(data, (pd.DataFrame, dict, list)):
                if isinstance(data, pd.DataFrame):
                    json_data = data.to_json(orient='records', indent=2)
                else:
                    import json
                    json_data = json.dumps(data, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"{filename_prefix}_{timestamp}.json",
                    mime="application/json"
                )
        
        with col3:
            # Excel download (requires openpyxl)
            if isinstance(data, pd.DataFrame):
                try:
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        data.to_excel(writer, index=False, sheet_name='Data')
                    
                    st.download_button(
                        label="📥 Download Excel",
                        data=buffer.getvalue(),
                        file_name=f"{filename_prefix}_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except ImportError:
                    st.info("Excel download requires openpyxl package")
    
    @staticmethod
    def render_progress_bar(current: int, total: int, label: str = "Progress"):
        """Render a progress bar with current/total information"""
        if total == 0:
            progress = 0
        else:
            progress = current / total
        
        st.progress(progress)
        st.caption(f"{label}: {current}/{total} ({progress:.1%})")
    
    @staticmethod
    def render_alert_box(alert_type: str, message: str, details: Optional[str] = None):
        """Render styled alert boxes"""
        alert_configs = {
            'success': {'icon': '✅', 'color': '#d4edda', 'border': '#c3e6cb'},
            'warning': {'icon': '⚠️', 'color': '#fff3cd', 'border': '#ffeaa7'},
            'error': {'icon': '❌', 'color': '#f8d7da', 'border': '#f5c6cb'},
            'info': {'icon': 'ℹ️', 'color': '#d1ecf1', 'border': '#bee5eb'}
        }
        
        config = alert_configs.get(alert_type, alert_configs['info'])
        
        alert_html = f"""
        <div style="
            background-color: {config['color']};
            border: 1px solid {config['border']};
            border-radius: 4px;
            padding: 12px;
            margin: 8px 0;
        ">
            <strong>{config['icon']} {message}</strong>
            {f'<br><small>{details}</small>' if details else ''}
        </div>
        """
        
        st.markdown(alert_html, unsafe_allow_html=True)


class QualityCheckRenderer:
    """Specialized renderer for quality check results"""
    
    @staticmethod
    def render_check_results(results: Dict[str, Any], check_type: str):
        """Render quality check results with appropriate visualizations"""
        st.subheader(f"📊 {check_type.title()} Results")
        
        if not results:
            st.warning(f"No {check_type} results available")
            return
        
        # Summary metrics
        summary = QualityCheckRenderer._extract_summary(results)
        if summary:
            DashboardComponents.render_summary_cards(summary)
        
        # Detailed results for each check
        for check_name, check_data in results.items():
            if isinstance(check_data, dict) and 'status' in check_data:
                QualityCheckRenderer._render_individual_check(check_name, check_data)
    
    @staticmethod
    def _extract_summary(results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract summary metrics from check results"""
        summary = {}
        
        total_checks = len(results)
        pass_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'PASS')
        fail_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'FAIL')
        warning_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'WARNING')
        error_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'ERROR')
        
        if total_checks > 0:
            pass_rate = (pass_count / total_checks) * 100
            
            summary = {
                'Total Checks': {'value': total_checks, 'status': 'PASS' if total_checks > 0 else 'ERROR'},
                'Passed': {'value': pass_count, 'status': 'PASS' if pass_count == total_checks else 'WARNING'},
                'Failed': {'value': fail_count, 'status': 'FAIL' if fail_count > 0 else 'PASS'},
                'Pass Rate': {'value': f"{pass_rate:.1f}%", 'status': 'PASS' if pass_rate >= 90 else 'WARNING' if pass_rate >= 70 else 'FAIL'}
            }
        
        return summary
    
    @staticmethod
    def _render_individual_check(check_name: str, check_data: Dict[str, Any]):
        """Render individual check results"""
        status = check_data.get('status', 'UNKNOWN')
        message = check_data.get('message', 'No message available')
        data = check_data.get('data', [])
        
        # Check header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{check_name.replace('_', ' ').title()}**")
        with col2:
            st.markdown(
                DashboardComponents.render_status_badge(status, message),
                unsafe_allow_html=True
            )
        
        # Show data if available
        if data:
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            elif isinstance(data, dict):
                st.json(data)
        
        # Show error if present
        if 'error' in check_data:
            st.error(f"Error: {check_data['error']}")
        
        st.divider()
