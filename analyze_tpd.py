"""
Tests Pending at Discharge - Analysis and Visualization
Analytics on FHIR 2025 Conference Demo
"""

import json
import glob
import pandas as pd
import plotly.express as px
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

    # Define culture lab LOINC codes
    CULTURE_CODES = {'600-7', '630-4', '43409-2', '6463-4'}

    # Calculate pending labs per encounter (labs issued after discharge)
    if len(obs_df) > 0 and len(enc_df) > 0:
        # Fix encounter_id mismatch: strip "Encounter/" prefix from observations
        if 'encounter_id' in obs_df.columns:
            obs_df['encounter_id'] = obs_df['encounter_id'].str.replace('Encounter/', '', regex=False)

        # Filter to only inpatient (TPD) encounters for analysis
        tpd_encounters = enc_df[enc_df['encounter_class'] == 'IMP'].copy()
        print(f"   TPD (inpatient) encounters: {len(tpd_encounters)}")

        # Merge observations with TPD encounters
        # Use start_time as "discharge" reference (in this model, delays are measured from encounter start)
        obs_with_enc = obs_df.merge(
            tpd_encounters[['encounter_id', 'start_time', 'end_time']],
            on='encounter_id',
            how='inner'
        )

        # Convert timestamps for comparison
        obs_with_enc['issued_dt'] = pd.to_datetime(obs_with_enc['issued_time'], errors='coerce', utc=True)
        obs_with_enc['start_dt'] = pd.to_datetime(obs_with_enc['start_time'], errors='coerce', utc=True)

        # Calculate days from encounter start (represents delay until lab result available)
        obs_with_enc['days_post_discharge'] = (
            (obs_with_enc['issued_dt'] - obs_with_enc['start_dt']).dt.total_seconds() / 86400
        )

        # Classify as Culture vs Other
        obs_with_enc['is_culture'] = obs_with_enc['lab_code'].isin(CULTURE_CODES)

        # All labs from TPD encounters are "pending" (they have delays)
        obs_with_enc['is_pending'] = obs_with_enc['days_post_discharge'] > 0

        # Count pending labs per encounter
        pending_per_encounter = obs_with_enc[obs_with_enc['is_pending']].groupby('encounter_id').size().reset_index(name='pending_lab_count')

        # Merge with encounters
        enc_df = enc_df.merge(pending_per_encounter, on='encounter_id', how='left')
        enc_df['pending_lab_count'] = enc_df['pending_lab_count'].fillna(0).astype(int)

        encounters_with_pending = len(enc_df[enc_df['pending_lab_count'] > 0])
        total_pending_labs = obs_with_enc['is_pending'].sum()
        total_cultures = obs_with_enc['is_culture'].sum()
        total_other = len(obs_with_enc) - total_cultures
    else:
        encounters_with_pending = 0
        total_pending_labs = 0
        total_cultures = 0
        total_other = 0
        if 'pending_lab_count' not in enc_df.columns:
            enc_df['pending_lab_count'] = 0

    pending_rate = (encounters_with_pending / len(tpd_encounters) * 100) if len(tpd_encounters) > 0 else 0

    print(f"   Total encounters: {len(enc_df)}")
    print(f"   Total lab observations: {len(obs_df)}")
    print(f"   Labs from TPD encounters: {len(obs_with_enc) if 'obs_with_enc' in dir() else 0}")
    print(f"   - Cultures: {total_cultures}")
    print(f"   - Other: {total_other}")
    print(f"   Encounters with pending labs: {encounters_with_pending}")
    print(f"   Pending lab rate: {pending_rate:.1f}%")

    if len(enc_df) > 0 and 'pending_lab_count' in enc_df.columns:
        tpd_with_pending = enc_df[enc_df['pending_lab_count'] > 0]
        if len(tpd_with_pending) > 0:
            avg_pending = tpd_with_pending['pending_lab_count'].mean()
            max_pending = tpd_with_pending['pending_lab_count'].max()
            print(f"\n   Average pending labs per TPD encounter: {avg_pending:.2f}")
            print(f"   Maximum pending labs (single encounter): {max_pending}")

    # Create visualization
    print("\n5. Generating visualization...")

    if len(obs_df) > 0 and 'obs_with_enc' in dir() and len(obs_with_enc) > 0:
        # Filter to pending labs only
        pending_labs = obs_with_enc[obs_with_enc['is_pending']].copy()

        if len(pending_labs) > 0:
            # Assign to day buckets like the reference image
            def assign_bucket(days):
                if days <= 1:
                    return '0-1'
                elif days <= 2:
                    return '1-2'
                elif days <= 3:
                    return '2-3'
                elif days <= 4:
                    return '3-4'
                elif days <= 6:
                    return '4-6'
                elif days <= 10:
                    return '6-10'
                else:
                    return '10+'

            pending_labs['bucket'] = pending_labs['days_post_discharge'].apply(assign_bucket)
            pending_labs['lab_type'] = pending_labs['is_culture'].map({True: 'Cultures', False: 'Other'})

            # Aggregate by bucket and lab type
            bucket_data = pending_labs.groupby(['bucket', 'lab_type']).size().reset_index(name='count')

            # Ensure proper bucket ordering
            bucket_order = ['0-1', '1-2', '2-3', '3-4', '4-6', '6-10', '10+']
            bucket_data['bucket'] = pd.Categorical(bucket_data['bucket'], categories=bucket_order, ordered=True)
            bucket_data = bucket_data.sort_values('bucket')

            # Create stacked bar chart like reference image
            fig = px.bar(
                bucket_data,
                x='bucket',
                y='count',
                color='lab_type',
                title='Results after Discharge',
                labels={
                    'bucket': 'Days post-discharge',
                    'count': 'Volume',
                    'lab_type': ''
                },
                color_discrete_map={
                    'Cultures': '#1f4e79',  # Dark blue
                    'Other': '#5b9bd5'      # Light blue
                },
                category_orders={'bucket': bucket_order}
            )
            fig.update_layout(
                height=500,
                barmode='stack',
                legend=dict(
                    orientation='h',
                    yanchor='top',
                    y=0.98,
                    xanchor='right',
                    x=0.98
                ),
                font=dict(size=14),
                margin=dict(b=80)
            )
            fig.write_html('tests_pending_by_day.html')
            print("   ✓ Created tests_pending_by_day.html")

            # Print distribution summary
            print("\n   Distribution by bucket:")
            total = len(pending_labs)
            for bucket in bucket_order:
                bucket_total = len(pending_labs[pending_labs['bucket'] == bucket])
                cultures = len(pending_labs[(pending_labs['bucket'] == bucket) & (pending_labs['is_culture'])])
                other = bucket_total - cultures
                pct = bucket_total / total * 100 if total > 0 else 0
                cult_pct = cultures / bucket_total * 100 if bucket_total > 0 else 0
                print(f"   {bucket:5s}: {bucket_total:4d} ({pct:5.1f}%) - Cultures: {cultures:4d} ({cult_pct:4.1f}%), Other: {other:4d}")
        else:
            print("   No pending labs found")

    # Export data
    print("\n6. Exporting data files...")
    obs_df.to_csv('analysis_lab_observations.csv', index=False)
    enc_df.to_csv('analysis_encounters.csv', index=False)
    print("   ✓ analysis_lab_observations.csv")
    print("   ✓ analysis_encounters.csv")

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print("\nOpen tests_pending_by_day.html in your browser to view the visualization.")

if __name__ == '__main__':
    main()
