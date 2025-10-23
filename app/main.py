#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# main.py

"""
Systems Engineering & Assurance Program - Stations Alliance North
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Tuple


class IntegrationRoadmap:
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

        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, json_file)

        with open(json_path, "r") as f:
            self.data = json.load(f)

        self.status_colors = {
            "completed": "#2ecc71",
            "in_progress": "#3498db",
            "planned": "#95a5a6",
            "delayed": "#e74c3c",
        }

    def parse_date(self, date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%d")

    def get_all_portions(self) -> List[Tuple[str, str]]:
        """Get list of all (station, portion) tuples"""
        portions = []
        for station, station_data in self.data.items():
            # Skip non-station entries like $schema
            if station.startswith("$") or not isinstance(station_data, dict):
                continue
            for portion in station_data.keys():
                portions.append((station, portion))
        return portions

    def query_status_by_station(self, station: str) -> Dict:
        """Get status summary for a specific station"""
        # Skip non-station entries like $schema
        if station.startswith("$") or station not in self.data:
            return {"error": f"Station {station} not found"}

        station_data = self.data[station]
        if not isinstance(station_data, dict):
            return {"error": f"Station {station} not found"}

        summary = {"station": station, "portions": {}, "overall_progress": 0}

        total_stages = 0
        completed_stages = 0

        for portion, portion_data in station_data.items():
            portion_info = {"stages": [], "progress": 0}

            for stage in portion_data["stages"]:
                portion_info["stages"].append(
                    {
                        "name": stage["name"],
                        "status": stage["status"],
                        "start": stage["start"],
                        "end": stage["end"],
                    }
                )
                total_stages += 1
                if stage["status"] == "completed":
                    completed_stages += 1

            portion_progress = sum(
                1 for s in portion_data["stages"] if s["status"] == "completed"
            )
            portion_info["progress"] = (
                (portion_progress / len(portion_data["stages"]) * 100)
                if portion_data["stages"]
                else 0
            )
            summary["portions"][portion] = portion_info

        summary["overall_progress"] = (
            (completed_stages / total_stages * 100) if total_stages > 0 else 0
        )
        return summary

    def query_milestones_by_date_range(
        self, start_date: str, end_date: str
    ) -> List[Dict]:
        """Get all milestones within a date range"""
        start = self.parse_date(start_date)
        end = self.parse_date(end_date)

        milestones = []
        for station, station_data in self.data.items():
            # Skip non-station entries like $schema
            if station.startswith("$") or not isinstance(station_data, dict):
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    for milestone in stage["milestones"]:
                        milestone_date = self.parse_date(milestone["date"])
                        if start <= milestone_date <= end:
                            milestones.append(
                                {
                                    "station": station,
                                    "portion": portion,
                                    "stage": stage["name"],
                                    "milestone": milestone["name"],
                                    "date": milestone["date"],
                                    "status": milestone["status"],
                                }
                            )

        return sorted(milestones, key=lambda x: x["date"])

    def check_delays(self, reference_date: str | None = None) -> List[Dict]:
        """Check for stages that should be completed but aren't"""
        if reference_date is None:
            ref_date = datetime.now()
        else:
            ref_date = self.parse_date(reference_date)

        delays = []
        for station, station_data in self.data.items():
            # Skip non-station entries like $schema
            if station.startswith("$") or not isinstance(station_data, dict):
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    end_date = self.parse_date(stage["end"])
                    if end_date < ref_date and stage["status"] != "completed":
                        delays.append(
                            {
                                "station": station,
                                "portion": portion,
                                "stage": stage["name"],
                                "planned_end": stage["end"],
                                "current_status": stage["status"],
                                "days_overdue": (ref_date - end_date).days,
                            }
                        )

        return sorted(delays, key=lambda x: x["days_overdue"], reverse=True)

    def get_critical_path(self) -> List[Dict]:
        """Identify stages on the critical path (longest duration)"""
        critical_items = []
        for station, station_data in self.data.items():
            # Skip non-station entries like $schema
            if station.startswith("$") or not isinstance(station_data, dict):
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    start = self.parse_date(stage["start"])
                    end = self.parse_date(stage["end"])
                    duration = (end - start).days
                    critical_items.append(
                        {
                            "station": station,
                            "portion": portion,
                            "stage": stage["name"],
                            "duration_days": duration,
                            "start": stage["start"],
                            "end": stage["end"],
                            "status": stage["status"],
                        }
                    )

        return sorted(critical_items, key=lambda x: x["duration_days"], reverse=True)

    def visualize_roadmap(self, figsize=(16, 10), save_path=None):
        """Create a Gantt chart visualization of the roadmap"""
        fig, ax = plt.subplots(figsize=figsize)

        # Prepare data
        y_pos = 0
        y_labels = []
        y_positions = []

        # Find overall date range
        all_dates = []
        for station, station_data in self.data.items():
            # Skip non-station entries like $schema
            if station.startswith("$") or not isinstance(station_data, dict):
                continue
            for portion, portion_data in station_data.items():
                for stage in portion_data["stages"]:
                    all_dates.append(self.parse_date(stage["start"]))
                    all_dates.append(self.parse_date(stage["end"]))

        min_date = min(all_dates)
        max_date = max(all_dates)

        # Plot each station/portion/stage
        for station, station_data in self.data.items():
            # Skip non-station entries like $schema
            if station.startswith("$") or not isinstance(station_data, dict):
                continue
            # Add station header
            y_labels.append(f"[{station}]")
            y_positions.append(y_pos)
            y_pos += 1

            for portion, portion_data in station_data.items():
                # Add portion label
                y_labels.append(f"  {portion}")
                y_positions.append(y_pos)

                # Plot stages
                for stage in portion_data["stages"]:
                    start = self.parse_date(stage["start"])
                    end = self.parse_date(stage["end"])
                    duration = (end - start).days

                    # Draw stage bar
                    color = self.status_colors.get(stage["status"], "#95a5a6")
                    ax.barh(
                        y_pos,
                        duration,
                        left=(start - min_date).days,
                        height=0.5,
                        color=color,
                        alpha=0.8,
                        edgecolor="black",
                        linewidth=0.5,
                    )

                    # Add stage label
                    mid_point = (start - min_date).days + duration / 2
                    ax.text(
                        mid_point,
                        y_pos,
                        stage["name"],
                        ha="center",
                        va="center",
                        fontsize=8,
                        fontweight="bold",
                    )

                    # Plot milestones
                    for milestone in stage["milestones"]:
                        milestone_date = self.parse_date(milestone["date"])
                        milestone_pos = (milestone_date - min_date).days
                        ax.plot(
                            milestone_pos,
                            y_pos,
                            "D",
                            color="red",
                            markersize=8,
                            markeredgecolor="darkred",
                            markeredgewidth=1.5,
                            zorder=5,
                        )
                        ax.text(
                            milestone_pos,
                            y_pos + 0.3,
                            milestone["name"],
                            rotation=45,
                            ha="left",
                            fontsize=7,
                            style="italic",
                        )

                y_pos += 1

            y_pos += 0.5  # Extra space between stations

        # Formatting
        ax.set_yticks(y_positions)
        ax.set_yticklabels(y_labels, fontsize=9)
        # ax.set_xlabel("Timeline", fontsize=12, fontweight="semibold")
        ax.set_title(
            "Systems Engineering & Assurance Program - Stations Alliance North",
            fontsize=12,
            # fontweight="semibold",
            pad=20,
        )

        # X-axis formatting
        total_days = (max_date - min_date).days
        num_ticks = min(12, total_days // 30 + 1)
        tick_positions = [i * total_days / num_ticks for i in range(num_ticks + 1)]
        tick_dates = [min_date + timedelta(days=int(pos)) for pos in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(
            [d.strftime("%Y-%m-%d") for d in tick_dates], rotation=45, ha="right"
        )

        # Add current date tracker line
        today = datetime.now()
        if min_date <= today <= max_date:
            today_pos = (today - min_date).days
            ax.axvline(
                x=today_pos,
                color="red",
                linewidth=2,
                linestyle="-",
                alpha=0.7,
                zorder=10,
                label="Today",
            )
            # Add "TODAY" label at the top
            # ax.text(
            #     today_pos,
            #     -0.5,
            #     "TODAY",
            #     ha="center",
            #     va="bottom",
            #     fontsize=10,
            #     fontweight="bold",
            #     color="red",
            #     bbox=dict(
            #         boxstyle="round,pad=0.3",
            #         facecolor="yellow",
            #         edgecolor="red",
            #         alpha=0.8,
            #     ),
            # )

        # Legend
        legend_elements = [
            mpatches.Patch(color=self.status_colors["completed"], label="Completed"),
            mpatches.Patch(
                color=self.status_colors["in_progress"], label="In Progress"
            ),
            mpatches.Patch(color=self.status_colors["planned"], label="Planned"),
            Line2D(
                [0],
                [0],
                marker="D",
                color="w",
                markerfacecolor="red",
                markersize=8,
                label="Milestone",
            ),
        ]
        ax.legend(handles=legend_elements, loc="upper right", fontsize=9)

        ax.grid(axis="x", alpha=0.3, linestyle="--")
        ax.invert_yaxis()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Roadmap saved to {save_path}")

        return fig

# Main Function
def main():
    # Initialize roadmap with JSON file
    roadmap = IntegrationRoadmap("data/data.json")

    print("=" * 80)
    print("INTEGRATION ROADMAP - QUERY EXAMPLES")
    print("=" * 80)

    # Query 1: Status by station
    print("\n1. Box Hill Station Status:")
    print("-" * 40)
    status = roadmap.query_status_by_station("Box Hill Station")
    print(f"Overall Progress: {status['overall_progress']:.1f}%")
    for portion, info in status["portions"].items():
        print(f"\n  {portion}: {info['progress']:.1f}%")
        for stage in info["stages"]:
            print(
                f"    - {stage['name']}: {stage['status']} ({stage['start']} to {stage['end']})"
            )

    # Query 2: Milestones in date range
    print("\n\n2. Milestones (Q2 2024):")
    print("-" * 40)
    milestones = roadmap.query_milestones_by_date_range("2024-04-01", "2024-06-30")
    for m in milestones:
        print(
            f"  {m['date']}: {m['milestone']} - {m['station']}/{m['portion']} [{m['status']}]"
        )

    # Query 3: Check for delays
    print("\n\n3. Delays Check (as of today):")
    print("-" * 40)
    delays = roadmap.check_delays()
    if delays:
        for delay in delays[:5]:  # Show top 5 delays
            print(f"  ⚠ {delay['station']} - {delay['portion']} - {delay['stage']}")
            print(
                f"    Planned End: {delay['planned_end']}, Status: {delay['current_status']}"
            )
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
    print("\n\n5. Creating Visualisation...")
    print("-" * 40)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S Systems Engineering & Assurance Program - Stations Alliance North.png")
    fig = roadmap.visualize_roadmap(save_path=filename)
    print("✓ Visualisation complete!")
    print(f"\nFile created - {filename}")
    print("\nTo update the roadmap, edit the data.json File and rerun this Script.")

# Entry Point
if __name__ == "__main__":
    main()
