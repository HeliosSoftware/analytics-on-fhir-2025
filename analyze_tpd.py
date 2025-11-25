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
from pysof import run_view_definition
from datetime import datetime

def load_ndjson_resources(file_path):
    """Load FHIR resources from an NDJSON file"""
    resources = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                resources.append(json.loads(line))
    return resources

def load_view_definition(file_path):
    """Load a ViewDefinition from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    print("=" * 60)
    print("Tests Pending at Discharge - Analysis")
    print("=" * 60)

    # Define data paths
    fhir_dir = 'synthea/output/fhir'

    # Load FHIR data from NDJSON files
    print("\n1. Loading FHIR data from NDJSON files...")
    encounters = load_ndjson_resources(f'{fhir_dir}/Encounter.ndjson')
    observations = load_ndjson_resources(f'{fhir_dir}/Observation.ndjson')
    print(f"   Loaded {len(encounters)} encounters")
    print(f"   Loaded {len(observations)} observations")

    # Load ViewDefinitions
    print("\n2. Loading ViewDefinitions...")
    enc_view = load_view_definition('EncounterView.json')
    obs_view = load_view_definition('LabObservationView.json')
    print("   ✓ EncounterView")
    print("   ✓ LabObservationView")

    # Execute ViewDefinitions
    print("\n3. Running SQL on FHIR transformations...")

    # Create bundles from resources for pysof
    encounter_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": e} for e in encounters]
    }
    observation_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": o} for o in observations]
    }

    # Run Encounter view
    enc_result = run_view_definition(
        view=enc_view,
        bundle=encounter_bundle,
        format="json"
    )
    enc_df = pd.DataFrame(json.loads(enc_result)) if enc_result else pd.DataFrame()
    print(f"   ✓ Processed {len(enc_df)} encounters")

    # Run Observation view
    obs_result = run_view_definition(
        view=obs_view,
        bundle=observation_bundle,
        format="json"
    )
    obs_df = pd.DataFrame(json.loads(obs_result)) if obs_result else pd.DataFrame()
    print(f"   ✓ Processed {len(obs_df)} lab observations")

    # Calculate summary statistics
    print("\n4. Summary Statistics")
    print("   " + "-" * 50)

    # Calculate pending labs per encounter (labs without 'final' status at discharge time)
    if len(obs_df) > 0 and len(enc_df) > 0:
        # Count pending labs (not final) per encounter
        pending_obs = obs_df[obs_df['status'] != 'final'] if 'status' in obs_df.columns else obs_df

        # Count labs by encounter
        if 'encounter_id' in obs_df.columns:
            labs_per_encounter = obs_df.groupby('encounter_id').size().reset_index(name='lab_count')
            pending_per_encounter = pending_obs.groupby('encounter_id').size().reset_index(name='pending_lab_count')

            # Merge with encounters
            enc_df = enc_df.merge(pending_per_encounter, on='encounter_id', how='left')
            enc_df['pending_lab_count'] = enc_df['pending_lab_count'].fillna(0).astype(int)

            encounters_with_pending = len(enc_df[enc_df['pending_lab_count'] > 0])
        else:
            encounters_with_pending = 0
            enc_df['pending_lab_count'] = 0
    else:
        encounters_with_pending = 0
        if 'pending_lab_count' not in enc_df.columns:
            enc_df['pending_lab_count'] = 0

    pending_rate = (encounters_with_pending / len(enc_df) * 100) if len(enc_df) > 0 else 0

    print(f"   Total encounters: {len(enc_df)}")
    print(f"   Total lab observations: {len(obs_df)}")
    print(f"   Encounters with pending labs: {encounters_with_pending}")
    print(f"   Pending lab rate: {pending_rate:.1f}%")

    if len(obs_df) > 0 and 'status' in obs_df.columns:
        print(f"\n   Lab Observation Status Breakdown:")
        status_counts = obs_df['status'].value_counts()
        for status, count in status_counts.items():
            print(f"     - {status}: {count}")

    if len(enc_df) > 0 and 'pending_lab_count' in enc_df.columns:
        avg_pending = enc_df['pending_lab_count'].mean()
        max_pending = enc_df['pending_lab_count'].max()
        print(f"\n   Average pending labs per encounter: {avg_pending:.2f}")
        print(f"   Maximum pending labs (single encounter): {max_pending}")

    # Create visualizations
    print("\n5. Generating visualizations...")

    # Visualization 1: Lab Observation Status Distribution
    if len(obs_df) > 0 and 'status' in obs_df.columns:
        fig1 = px.bar(
            obs_df['status'].value_counts().reset_index(),
            x='status',
            y='count',
            title='Lab Observations by Status',
            labels={'status': 'Observation Status', 'count': 'Number of Observations'},
            color='status',
            color_discrete_map={
                'registered': '#ff7f0e',
                'preliminary': '#2ca02c',
                'final': '#1f77b4',
                'amended': '#9467bd'
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
    if len(enc_df) > 0 and 'end_time' in enc_df.columns:
        enc_df['end_time_dt'] = pd.to_datetime(enc_df['end_time'], errors='coerce', utc=True)
        enc_df['discharge_date'] = enc_df['end_time_dt'].dt.date

        # Filter to encounters with pending labs
        pending_encounters = enc_df[enc_df['pending_lab_count'] > 0]
        if len(pending_encounters) > 0:
            daily_counts = pending_encounters.groupby('discharge_date').size().reset_index(name='count')
            daily_counts['discharge_date'] = pd.to_datetime(daily_counts['discharge_date'])

            fig3 = px.line(
                daily_counts,
                x='discharge_date',
                y='count',
                title='Encounters with Pending Labs at Discharge - Daily Trend',
                labels={'discharge_date': 'Discharge Date', 'count': 'Number of Encounters'},
                markers=True
            )
            fig3.update_traces(line_color='#d62728', marker=dict(size=8))
            fig3.update_layout(height=500)
            fig3.write_html('viz_3_daily_trend.html')
            print("   ✓ Created viz_3_daily_trend.html")

    # Visualization 4: Combined Dashboard
    if len(obs_df) > 0 and len(enc_df) > 0:
        fig4 = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Lab Status Distribution',
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
        if 'status' in obs_df.columns:
            status_counts = obs_df['status'].value_counts()
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
    obs_df.to_csv('analysis_lab_observations.csv', index=False)
    enc_df.to_csv('analysis_encounters.csv', index=False)
    print("   ✓ analysis_lab_observations.csv")
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
