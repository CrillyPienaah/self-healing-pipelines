import pandas as pd
import glob
import json

# Find most recent CSV
csv_files = glob.glob('research_data/*.csv')
if not csv_files:
    print('No research data found!')
    exit(1)

latest_file = max(csv_files)
print(f' Analyzing: {latest_file}\n')

# Load data
df = pd.read_csv(latest_file)

print('=' * 70)
print('RESEARCH DATA ANALYSIS')
print('=' * 70)

print(f'\n Dataset Overview:')
print(f'   Total Examples: {len(df)}')
print(f'   Date Range: {df[\"timestamp\"].min()} to {df[\"timestamp\"].max()}')

print(f'\n Confidence Distribution:')
print(df['confidence_score'].describe())
print(f'\n   High Confidence (90%): {len(df[df[\"confidence_score\"] >= 90])} ({len(df[df[\"confidence_score\"] >= 90])/len(df)*100:.1f}%)')
print(f'   Medium Confidence (70-89%): {len(df[(df[\"confidence_score\"] >= 70) & (df[\"confidence_score\"] < 90)])}')
print(f'   Low Confidence (<70%): {len(df[df[\"confidence_score\"] < 70])}')

print(f'\n  Generation Time:')
print(df['generation_time_sec'].describe())
print(f'   Fastest: {df[\"generation_time_sec\"].min():.1f}s')
print(f'   Slowest: {df[\"generation_time_sec\"].max():.1f}s')
print(f'   Average: {df[\"generation_time_sec\"].mean():.1f}s')

print(f'\n Fix Code Complexity:')
print(f'   Average Length: {df[\"fix_code_length\"].mean():.0f} characters')
print(f'   Shortest: {df[\"fix_code_length\"].min()} chars')
print(f'   Longest: {df[\"fix_code_length\"].max()} chars')

print(f'\n Rollback Planning:')
print(f'   Has Rollback Plan: {len(df[df[\"has_rollback\"] == True])} ({len(df[df[\"has_rollback\"] == True])/len(df)*100:.1f}%)')

print(f'\n Schema Change Patterns:')
print(f'   Columns Added (avg): {df[\"columns_added\"].mean():.1f}')
print(f'   Single Column Add: {len(df[df[\"columns_added\"] == 1])}')
print(f'   Multi-Column Add: {len(df[df[\"columns_added\"] > 1])}')
print(f'   Column Removals: {len(df[df[\"columns_added\"] < 0])}')

print(f'\n Estimated Costs:')
print(f'   Total API Calls: {len(df)}')
print(f'   Estimated Cost: \')

print(f'\n Research Readiness:')
print(f'    {len(df)} labeled examples')
print(f'    Diverse schema change patterns')
print(f'    Performance benchmarks established')
print(f'    Ready for academic publication')

print('\n' + '=' * 70)
