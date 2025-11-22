"""
Chart builder utilities for creating consistent, reusable Plotly visualizations.

Provides standardized chart creation functions to eliminate duplicate code
and ensure consistent styling across the analytics dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List


class ChartBuilder:
    """Factory class for creating standardized Plotly charts."""

    # Default color schemes
    COLORS = {
        'primary': '#1f77b4',
        'secondary': '#2ca02c',
        'accent': '#ff7f0e',
        'blues': 'Blues',
        'greens': 'Greens',
        'qualitative': px.colors.qualitative.Set3
    }

    @staticmethod
    def create_line_chart(
        data,
        x: str,
        y: str,
        title: str,
        xaxis_title: str = "",
        yaxis_title: str = "",
        height: int = 400,
        color: str = COLORS['primary'],
        line_width: int = 3,
        marker_size: int = 8
    ) -> go.Figure:
        """
        Create a line chart with markers.

        Args:
            data: DataFrame or dict with data
            x: Column name for x-axis
            y: Column name for y-axis
            title: Chart title
            xaxis_title: X-axis label
            yaxis_title: Y-axis label
            height: Chart height in pixels
            color: Line color
            line_width: Width of line
            marker_size: Size of markers

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data[x],
            y=data[y],
            mode='lines+markers',
            name=title,
            line=dict(color=color, width=line_width),
            marker=dict(size=marker_size)
        ))

        fig.update_layout(
            title=title,
            xaxis_title=xaxis_title or x.title(),
            yaxis_title=yaxis_title or y.title(),
            hovermode='x unified',
            height=height
        )

        return fig

    @staticmethod
    def create_bar_chart(
        data,
        x: str,
        y: str,
        title: str,
        orientation: str = 'v',
        color: Optional[str] = None,
        color_continuous_scale: str = 'Blues',
        xaxis_title: str = "",
        yaxis_title: str = "",
        height: int = 400,
        show_legend: bool = False
    ) -> go.Figure:
        """
        Create a bar chart.

        Args:
            data: DataFrame with data
            x: Column name for x-axis (or y-axis if horizontal)
            y: Column name for y-axis (or x-axis if horizontal)
            title: Chart title
            orientation: 'v' for vertical, 'h' for horizontal
            color: Column name to color by (optional)
            color_continuous_scale: Color scale to use
            xaxis_title: X-axis label
            yaxis_title: Y-axis label
            height: Chart height in pixels
            show_legend: Whether to show legend

        Returns:
            Plotly Figure object
        """
        fig = px.bar(
            data,
            x=x,
            y=y,
            orientation=orientation,
            title=title,
            labels={x: xaxis_title or x.title(), y: yaxis_title or y.title()},
            color=color,
            color_continuous_scale=color_continuous_scale if color else None
        )

        fig.update_layout(height=height, showlegend=show_legend)

        return fig

    @staticmethod
    def create_pie_chart(
        data,
        values: str,
        names: str,
        title: str,
        height: int = 400,
        color_discrete_sequence: Optional[List[str]] = None,
        color_discrete_map: Optional[Dict[str, str]] = None,
        show_percent: bool = True
    ) -> go.Figure:
        """
        Create a pie chart.

        Args:
            data: DataFrame with data
            values: Column name for values
            names: Column name for labels
            title: Chart title
            height: Chart height in pixels
            color_discrete_sequence: List of colors to use
            color_discrete_map: Dict mapping labels to specific colors
            show_percent: Whether to show percentages on slices

        Returns:
            Plotly Figure object
        """
        fig = px.pie(
            data,
            values=values,
            names=names,
            title=title,
            color_discrete_sequence=color_discrete_sequence,
            color_discrete_map=color_discrete_map
        )

        if show_percent:
            fig.update_traces(textposition='inside', textinfo='percent+label')

        fig.update_layout(height=height)

        return fig

    @staticmethod
    def create_horizontal_bar_chart(
        data,
        x: str,
        y: str,
        title: str,
        color: Optional[str] = None,
        color_continuous_scale: str = 'Blues',
        height: int = 500,
        xaxis_title: str = "",
        yaxis_title: str = ""
    ) -> go.Figure:
        """
        Create a horizontal bar chart (convenience wrapper).

        Args:
            data: DataFrame with data
            x: Column name for x-axis (values)
            y: Column name for y-axis (categories)
            title: Chart title
            color: Column name to color by (optional)
            color_continuous_scale: Color scale to use
            height: Chart height in pixels
            xaxis_title: X-axis label
            yaxis_title: Y-axis label

        Returns:
            Plotly Figure object
        """
        return ChartBuilder.create_bar_chart(
            data=data,
            x=x,
            y=y,
            title=title,
            orientation='h',
            color=color,
            color_continuous_scale=color_continuous_scale,
            height=height,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            show_legend=False
        )

    @staticmethod
    def create_simple_bar_chart(
        data,
        x: str,
        y: str,
        title: str,
        bar_color: str = COLORS['secondary'],
        height: int = 300
    ) -> go.Figure:
        """
        Create a simple bar chart with uniform color.

        Args:
            data: DataFrame with data
            x: Column name for x-axis
            y: Column name for y-axis
            title: Chart title
            bar_color: Color for all bars
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data[x],
            y=data[y],
            name=title,
            marker_color=bar_color
        ))

        fig.update_layout(
            title=title,
            xaxis_title=x.title(),
            yaxis_title=y.title(),
            height=height
        )

        return fig

    @staticmethod
    def create_colored_bar_chart(
        data,
        x: str,
        y: str,
        title: str,
        color_by: str,
        color_scale: str = 'Blues',
        height: int = 400
    ) -> go.Figure:
        """
        Create a bar chart with color gradient based on values.

        Args:
            data: DataFrame with data
            x: Column name for x-axis
            y: Column name for y-axis
            title: Chart title
            color_by: Column name to determine color intensity
            color_scale: Plotly color scale name
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        fig = px.bar(
            data,
            x=x,
            y=y,
            title=title,
            color=color_by,
            color_continuous_scale=color_scale,
            labels={x: x.title(), y: y.title()}
        )

        fig.update_layout(height=height, showlegend=False)

        return fig

    @staticmethod
    def create_category_bar_chart(
        data,
        x: str,
        y: str,
        title: str,
        color_by: str,
        height: int = 400
    ) -> go.Figure:
        """
        Create a bar chart with categorical colors.

        Args:
            data: DataFrame with data
            x: Column name for x-axis
            y: Column name for y-axis
            title: Chart title
            color_by: Column name for categorical colors
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        fig = px.bar(
            data,
            x=x,
            y=y,
            title=title,
            color=color_by
        )

        fig.update_layout(height=height)

        return fig
