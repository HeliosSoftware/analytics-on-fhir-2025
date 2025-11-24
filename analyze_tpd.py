"""
Tests Pending at Discharge - Analysis and Visualization
Analytics on FHIR 2025 Conference Demo
"""

import json
import glob
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pysof import ViewDefinitionRunner
from datetime import datetime

def load_fhir_data(data_dir='test-data'):
    """Load all FHIR bundles from directory"""
    fhir_bundles = []
    for file_path in glob.glob(f'{data_dir}/*.json'):
        with open(file_path, 'r') as f:
            fhir_bundles.append(json.load(f))
    return fhir_bundles

def load_view_definition(file_path):
    """Load a ViewDefinition from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    print("=" * 60)
    print("Tests Pending at Discharge - Analysis")
    print("=" * 60)

    # Load FHIR data
    print("\n1. Loading FHIR test data...")
    fhir_data = load_fhir_data()
    print(f"   Loaded {len(fhir_data)} FHIR bundles")

    # Load ViewDefinitions
    print("\n2. Loading ViewDefinitions...")
    dr_view = load_view_definition('DiagnosticReportAtDischargeView.json')
    enc_view = load_view_definition('EncounterPendingLabCountView.json')
    print("   ✓ DiagnosticReportAtDischargeView")
    print("   ✓ EncounterPendingLabCountView")

    # Execute ViewDefinitions
    print("\n3. Running SQL on FHIR transformations...")
    runner = ViewDefinitionRunner()

    dr_results = runner.run(dr_view, fhir_data)
    dr_df = pd.DataFrame(dr_results)
    print(f"   ✓ Found {len(dr_df)} pending diagnostic reports")

    enc_results = runner.run(enc_view, fhir_data)
    enc_df = pd.DataFrame(enc_results)
    print(f"   ✓ Analyzed {len(enc_df)} encounters")

    # Calculate summary statistics
    print("\n4. Summary Statistics")
    print("   " + "-" * 50)

    encounters_with_pending = len(enc_df[enc_df['pending_lab_count'] > 0])
    pending_rate = (encounters_with_pending / len(enc_df) * 100) if len(enc_df) > 0 else 0

    print(f"   Total encounters: {len(enc_df)}")
    print(f"   Encounters with pending labs: {encounters_with_pending}")
    print(f"   Pending lab rate: {pending_rate:.1f}%")
    print(f"   Total pending lab reports: {len(dr_df)}")

    if len(dr_df) > 0:
        print(f"\n   Report Status Breakdown:")
        status_counts = dr_df['report_status'].value_counts()
        for status, count in status_counts.items():
            print(f"     - {status}: {count}")

    if len(enc_df) > 0 and 'pending_lab_count' in enc_df.columns:
        avg_pending = enc_df['pending_lab_count'].mean()
        max_pending = enc_df['pending_lab_count'].max()
        print(f"\n   Average pending labs per encounter: {avg_pending:.2f}")
        print(f"   Maximum pending labs (single encounter): {max_pending}")

    # Create visualizations
    print("\n5. Generating visualizations...")

    # Visualization 1: Pending Lab Status Distribution
    if len(dr_df) > 0:
        fig1 = px.bar(
            dr_df['report_status'].value_counts().reset_index(),
            x='report_status',
            y='count',
            title='Pending Lab Reports by Status',
            labels={'report_status': 'Report Status', 'count': 'Number of Reports'},
            color='report_status',
            color_discrete_map={
                'registered': '#ff7f0e',
                'partial': '#2ca02c',
                'preliminary': '#1f77b4'
            }
        )
        fig1.update_layout(showlegend=False, height=500)
        fig1.write_html('viz_1_status_distribution.html')
        print("   ✓ Created viz_1_status_distribution.html")

    # Visualization 2: Pending Lab Count Distribution
    if len(enc_df) > 0 and 'pending_lab_count' in enc_df.columns:
        fig2 = px.histogram(
            enc_df,
            x='pending_lab_count',
            nbins=20,
            title='Distribution of Pending Lab Counts per Encounter',
            labels={'pending_lab_count': 'Number of Pending Labs', 'count': 'Number of Encounters'},
            color_discrete_sequence=['#1f77b4']
        )
        fig2.update_layout(height=500, showlegend=False)
        fig2.write_html('viz_2_count_distribution.html')
        print("   ✓ Created viz_2_count_distribution.html")

    # Visualization 3: Time Series Analysis
    if len(dr_df) > 0 and 'hospital_discharge_time' in dr_df.columns:
        dr_df['hospital_discharge_time'] = pd.to_datetime(dr_df['hospital_discharge_time'])
        dr_df['discharge_date'] = dr_df['hospital_discharge_time'].dt.date

        daily_counts = dr_df.groupby('discharge_date').size().reset_index(name='count')
        daily_counts['discharge_date'] = pd.to_datetime(daily_counts['discharge_date'])

        fig3 = px.line(
            daily_counts,
            x='discharge_date',
            y='count',
            title='Pending Labs at Discharge - Daily Trend',
            labels={'discharge_date': 'Discharge Date', 'count': 'Number of Pending Labs'},
            markers=True
        )
        fig3.update_traces(line_color='#d62728', marker=dict(size=8))
        fig3.update_layout(height=500)
        fig3.write_html('viz_3_daily_trend.html')
        print("   ✓ Created viz_3_daily_trend.html")

    # Visualization 4: Combined Dashboard
    if len(dr_df) > 0 and len(enc_df) > 0:
        fig4 = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Status Distribution',
                'Pending Count per Encounter',
                'Key Metrics',
                'Top Encounters by Pending Labs'
            ),
            specs=[
                [{"type": "bar"}, {"type": "histogram"}],
                [{"type": "indicator"}, {"type": "bar"}]
            ]
        )

        # Status distribution
        status_counts = dr_df['report_status'].value_counts()
        fig4.add_trace(
            go.Bar(x=status_counts.index, y=status_counts.values, name='Status'),
            row=1, col=1
        )

        # Pending count histogram
        fig4.add_trace(
            go.Histogram(x=enc_df['pending_lab_count'], name='Count Distribution'),
            row=1, col=2
        )

        # Key metric indicator
        fig4.add_trace(
            go.Indicator(
                mode="number+delta",
                value=pending_rate,
                title={'text': "Encounters with<br>Pending Labs (%)"},
                delta={'reference': 20, 'relative': False},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=1
        )

        # Top encounters
        top_encounters = enc_df.nlargest(10, 'pending_lab_count')
        fig4.add_trace(
            go.Bar(
                x=top_encounters['encounter_id'],
                y=top_encounters['pending_lab_count'],
                name='Top Encounters'
            ),
            row=2, col=2
        )

        fig4.update_layout(
            height=800,
            showlegend=False,
            title_text="Tests Pending at Discharge - Executive Dashboard"
        )
        fig4.write_html('viz_4_dashboard.html')
        print("   ✓ Created viz_4_dashboard.html")

    # Export data
    print("\n6. Exporting data files...")
    dr_df.to_csv('analysis_diagnostic_reports.csv', index=False)
    enc_df.to_csv('analysis_encounters.csv', index=False)
    print("   ✓ analysis_diagnostic_reports.csv")
    print("   ✓ analysis_encounters.csv")

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print("\nOpen the HTML files in your browser to view visualizations:")
    print("  - viz_1_status_distribution.html")
    print("  - viz_2_count_distribution.html")
    print("  - viz_3_daily_trend.html")
    print("  - viz_4_dashboard.html")

if __name__ == '__main__':
    main()
