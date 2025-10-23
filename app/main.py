#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# main.py

"""
Integration Roadmap for Railway Stations Project
Reads data from a separate JSON file: roadmap_data.json
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from typing import List, Dict, Tuple


class SystemsEngineeringandAssuranceProgram:
  
    def __init__(self, json_file: str):
        """
        Initialize roadmap with JSON file
        
        JSON structure:
        {
          "Station Name": {
            "Portion ID - Description": {
              "stages": [
                {
                  "name": "Stage Name",
                  "start": "YYYY-MM-DD",
                  "end": "YYYY-MM-DD",
                  "status": "completed|in_progress|planned|delayed",
                  "milestones": [
                    {
                      "name": "Milestone Name",
                      "date": "YYYY-MM-DD",
                      "status": "completed|in_progress|planned"
                    }
                  ]
                }
              ]
            }
          }
        }
        """
        with open(json_file, 'r') as f:
            self.data = json.load(f)
        
        self.status_colors = {
            'completed': '#2ecc71',
            'in_progress': '#3498db',
            'planned': '#95a5a6',
            'delayed': '#e74c3c'
        }
    
    def parse_date(self, date_str: str) -> datetime:
        """Convert date string to datetime object"""
        return datetime.strptime(date_str, "%Y-%m-%d")
    
    def get_all_portions(self) -> List[Tuple[str, str]]:
        """Get list of all (station, portion) tuples"""
        portions = []
        for station, station_data in self.data.items():
            if station == "$schema":  # Skip the schema property
                continue
            for portion in station_data.keys():
                portions.append((station, portion))
        return portions
    
    def query_status_by_station(self, station: str) -> Dict:
        """Get status summary for a specific station"""
        if station not in self.data or station == "$schema":
            return {"error": f"Station {station} not found"}
        
        summary = {
            "station": station,
            "portions": {},
            "overall_progress": 0
        }
        
        total_stages = 0
        completed_stages = 0
        
        for portion, portion_data in self.data[station].items():
            portion_info = {
                "stages": [],
                "progress": 0
            }
            
            for stage in portion_data["stages"]:
                portion_info["stages"].append({
                    "name": stage["name"],
                    "status": stage["status"],
                    "start": stage["start"],
                    "end": stage["end"]
                })
                total_stages += 1
                if stage["status"] == "completed":
                    completed_stages += 1
            
            portion_progress = sum(1 for s in portion_data["stages"] if s["status"] == "completed")
            portion_info["progress"] = (portion_progress / len(portion_data["stages"]) * 100) if portion_data["stages"] else 0
            summary["portions"][portion] = portion_info
        
        summary["overall_progress"] = (completed_stages / total_stages * 100) if total_stages > 0 else 0
        return summary
    
    def query_milestones_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get all milestones within a date range"""
        start = self.parse_date(start_date)
        end = self.parse_date(end_date)
        
        milestones = []
        for station, station_data in self.data.items():
            if station == "$schema":  # Skip the schema property
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    for milestone in stage["milestones"]:
                        milestone_date = self.parse_date(milestone["date"])
                        if start <= milestone_date <= end:
                            milestones.append({
                                "station": station,
                                "portion": portion,
                                "stage": stage["name"],
                                "milestone": milestone["name"],
                                "date": milestone["date"],
                                "status": milestone["status"]
                            })
        
        return sorted(milestones, key=lambda x: x["date"])
    
    def check_delays(self, reference_date: str | None = None) -> List[Dict]:
        """Check for stages that should be completed but aren't"""
        if reference_date is None:
            ref_date = datetime.now()
        else:
            ref_date = self.parse_date(reference_date)
        
        delays = []
        for station, station_data in self.data.items():
            if station == "$schema":  # Skip the schema property
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    end_date = self.parse_date(stage["end"])
                    if end_date < ref_date and stage["status"] != "completed":
                        delays.append({
                            "station": station,
                            "portion": portion,
                            "stage": stage["name"],
                            "planned_end": stage["end"],
                            "current_status": stage["status"],
                            "days_overdue": (ref_date - end_date).days
                        })
        
        return sorted(delays, key=lambda x: x["days_overdue"], reverse=True)
    
    def get_critical_path(self) -> List[Dict]:
        """Identify stages on the critical path (longest duration)"""
        critical_items = []
        for station, station_data in self.data.items():
            if station == "$schema":  # Skip the schema property
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    start = self.parse_date(stage["start"])
                    end = self.parse_date(stage["end"])
                    duration = (end - start).days
                    critical_items.append({
                        "station": station,
                        "portion": portion,
                        "stage": stage["name"],
                        "duration_days": duration,
                        "start": stage["start"],
                        "end": stage["end"],
                        "status": stage["status"]
                    })
        
        return sorted(critical_items, key=lambda x: x["duration_days"], reverse=True)
    
    def visualize_roadmap(self, figsize=(16, 10), save_path=None):
        """Create an interactive Gantt chart visualization of the roadmap using Plotly"""
        
        # Prepare data for plotly - group stages by portion
        gantt_data = []
        milestone_data = []
        y_labels = []
        y_pos = 0
        
        # Find overall date range
        all_dates = []
        for station, station_data in self.data.items():
            if station == "$schema":  # Skip the schema property
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    all_dates.append(self.parse_date(stage["start"]))
                    all_dates.append(self.parse_date(stage["end"]))
        
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        # Build data structure similar to original matplotlib approach
        for station, station_data in self.data.items():
            if station == "$schema":  # Skip the schema property
                continue
            
            # Add station header (but don't plot it, just for spacing)
            y_labels.append(f"[{station}]")
            y_pos += 1
            
            for portion, portion_data in station_data.items():
                # Add portion label
                portion_label = f"  {portion}"
                y_labels.append(portion_label)
                
                # All stages for this portion go on the same y_pos
                for stage in portion_data["stages"]:
                    gantt_data.append({
                        'Task': portion_label,
                        'Start': stage['start'],
                        'Finish': stage['end'],
                        'Status': stage['status'],
                        'Station': station,
                        'Portion': portion,
                        'Stage': stage['name'],
                        'y_pos': y_pos
                    })
                    
                    # Add milestones for this stage
                    for milestone in stage["milestones"]:
                        milestone_data.append({
                            'name': milestone['name'],
                            'date': milestone['date'],
                            'status': milestone['status'],
                            'task': portion_label,
                            'station': station,
                            'portion': portion,
                            'stage': stage['name'],
                            'y_pos': y_pos
                        })
                
                y_pos += 1
            
            y_pos += 0.5  # Extra space between stations
        
        # Create Gantt chart
        fig = go.Figure()
        
        # Track which statuses we've added to legend
        legend_statuses = set()
        
        # Add bars for each stage
        for task in gantt_data:
            start_date = datetime.strptime(task['Start'], '%Y-%m-%d')
            end_date = datetime.strptime(task['Finish'], '%Y-%m-%d')
            color = self.status_colors.get(task['Status'], '#95a5a6')
            
            # Calculate bar height (smaller to fit multiple stages)
            bar_height = 0.3
            y_center = task['y_pos']
            
            show_legend = task['Status'] not in legend_statuses
            if show_legend:
                legend_statuses.add(task['Status'])
            
            fig.add_trace(go.Scatter(
                x=[start_date, end_date, end_date, start_date, start_date],
                y=[y_center-bar_height/2, y_center-bar_height/2, y_center+bar_height/2, y_center+bar_height/2, y_center-bar_height/2],
                fill="toself",
                fillcolor=color,
                line=dict(color='black', width=1),
                mode='lines',
                name=task['Status'],
                legendgroup=task['Status'],
                showlegend=show_legend,
                hovertemplate=(
                    f"<b>{task['Stage']}</b><br>"
                    f"Portion: {task['Portion']}<br>"
                    f"Station: {task['Station']}<br>"
                    f"Status: {task['Status']}<br>"
                    f"Start: {task['Start']}<br>"
                    f"End: {task['Finish']}<br>"
                    f"Duration: {(end_date - start_date).days} days<br>"
                    "<extra></extra>"
                )
            ))
            
            # Add stage name text in the middle of the bar
            mid_date = start_date + (end_date - start_date) / 2
            fig.add_trace(go.Scatter(
                x=[mid_date],
                y=[y_center],
                mode='text',
                text=[task['Stage']],
                textfont=dict(size=9, color='white' if task['Status'] in ['completed', 'in_progress'] else 'black'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add milestones as markers
        if milestone_data:
            milestone_x = []
            milestone_y = []
            milestone_text = []
            milestone_hover = []
            
            for milestone in milestone_data:
                milestone_date = datetime.strptime(milestone['date'], '%Y-%m-%d')
                milestone_x.append(milestone_date)
                milestone_y.append(milestone['y_pos'])
                milestone_text.append(milestone['name'])
                milestone_hover.append(
                    f"<b>{milestone['name']}</b><br>"
                    f"Date: {milestone['date']}<br>"
                    f"Status: {milestone['status']}<br>"
                    f"Stage: {milestone['stage']}<br>"
                    f"Portion: {milestone['portion']}"
                )
            
            fig.add_trace(go.Scatter(
                x=milestone_x,
                y=milestone_y,
                mode='markers+text',
                marker=dict(
                    symbol='diamond',
                    size=10,
                    color='red',
                    line=dict(color='darkred', width=2)
                ),
                text=milestone_text,
                textposition="top center",
                textfont=dict(size=8, color='red'),
                name="Milestones",
                hovertemplate=milestone_hover,
                showlegend=True
            ))
        
        # Add today's date line
        today = datetime.now()
        if min_date <= today <= max_date:
            fig.add_shape(
                type="line",
                x0=today, x1=today,
                y0=0.5, y1=len(y_labels)+0.5,
                line=dict(color="red", width=3, dash="solid"),
            )
            fig.add_annotation(
                x=today,
                y=0.2,
                text="TODAY",
                showarrow=False,
                font=dict(color="red", size=12, family="Arial Black"),
                bgcolor="yellow",
                bordercolor="red",
                borderwidth=2
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Systems Engineering & Assurance Program - Stations Alliance North',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'family': 'Arial Black'}
            },
            xaxis=dict(
                title="Timeline",
                type='date',
                tickformat='%Y-%m-%d',
                tickangle=45,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1
            ),
            yaxis=dict(
                title="Tasks",
                tickmode='array',
                tickvals=list(range(1, len(y_labels)+1)),
                ticktext=y_labels,
                autorange="reversed",
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1
            ),
            height=max(600, len(y_labels) * 50 + 200),
            width=1200,
            hovermode='closest',
            template='plotly_white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Save the figure
        if save_path:
            # Save as HTML for interactivity
            html_path = save_path.replace('.png', '.html') if save_path.endswith('.png') else save_path + '.html'
            fig.write_html(html_path)
            print(f"Interactive Program saved to {html_path}")
            
            # Also save as PNG
            png_path = save_path.replace('.html', '.png') if save_path.endswith('.html') else save_path + '.png'
            try:
                fig.write_image(png_path, width=1200, height=max(600, len(y_labels) * 50 + 200))
                print(f"Static Program saved to {png_path}")
            except Exception as e:
                print(f"Note: Could not save PNG file: {e}")
        
        # Don't automatically show in non-interactive environments
        # fig.show()  # Commented out to prevent hanging in some environments
        
        return fig


def main():
    """Demo the roadmap functionality"""
    # Initialize roadmap with JSON file
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'data', 'data.json')
    roadmap = SystemsEngineeringandAssuranceProgram(data_path)
    
    print("=" * 80)
    print("SYSTEMS ENGINEERING & ASSURANCE PROGRAM - QUERY EXAMPLES")
    print("=" * 80)
    
    # Query 1: Status by station
    # print("\n1. Station A Status:")
    # print("-" * 40)
    # status = roadmap.query_status_by_station("Station A")
    # print(f"Overall Progress: {status['overall_progress']:.1f}%")
    # for portion, info in status['portions'].items():
    #     print(f"\n  {portion}: {info['progress']:.1f}%")
    #     for stage in info['stages']:
    #         print(f"    - {stage['name']}: {stage['status']} ({stage['start']} to {stage['end']})")
    
    # Query 2: Milestones in date range
    print("\n\n2. Milestones (Q2 2024):")
    print("-" * 40)
    milestones = roadmap.query_milestones_by_date_range("2024-04-01", "2024-06-30")
    for m in milestones:
        print(f"  {m['date']}: {m['milestone']} - {m['station']}/{m['portion']} [{m['status']}]")
    
    # Query 3: Check for delays
    print("\n\n3. Delays Check (as of today):")
    print("-" * 40)
    delays = roadmap.check_delays()
    if delays:
        for delay in delays[:5]:  # Show top 5 delays
            print(f"  ⚠ {delay['station']} - {delay['portion']} - {delay['stage']}")
            print(f"    Planned End: {delay['planned_end']}, Status: {delay['current_status']}")
            print(f"    Days Overdue: {delay['days_overdue']}")
    else:
        print("  ✓ No delays detected!")
    
    # Query 4: Critical path
    print("\n\n4. Critical Path (Longest Duration Stages):")
    print("-" * 40)
    critical = roadmap.get_critical_path()[:5]  # Top 5
    for i, item in enumerate(critical, 1):
        print(f"  {i}. {item['stage']} - {item['station']}/{item['portion']}")
        print(f"     Duration: {item['duration_days']} days, Status: {item['status']}")
    
    # Create visualization
    print("\n\n5. Creating Visualization...")
    print("-" * 40)
    fig = roadmap.visualize_roadmap(save_path='sea_program')
    print("✓ Visualization complete!")
    print("\nFiles created:")
    print("  - sea_program.html (Interactive Gantt chart)")
    print("  - sea_program.png (Static Gantt chart)")
    print("\nTo update the roadmap, edit: data/data.json")


if __name__ == "__main__":
    main()
