from pathlib import Path

root = Path.cwd()
source = (root/'evaluation/phase2_inference.py').read_text(encoding='utf-8')
replacements = {
    'Pure, unratified Cho Phase II paired calculations.': 'Pure, unadopted 51-target Cho candidate; numerical results only.',
    '1,040-cell': '1,020-cell',
    '1,040 cells': '1,020 cells',
    'ChoPairedCalculations': 'Cho51PairedCalculations',
    'range(1, 53)': 'range(2, 53)',
    'calculate_cho_paired_inference': 'calculate_51_target_paired_inference',
    'len(expected) != 52 or len(set(expected)) != 52': 'len(expected) != 51 or len(set(expected)) != 51',
    'all 52 distinct canonical Cho subjects': 'exactly subject_02..subject_52 (51 distinct subjects)',
    'len(paired_differences) != 52': 'len(paired_differences) != 51',
    'exactly 52 paired differences': 'exactly 51 paired differences',
    'sum(differences, Fraction()) / 52': 'sum(differences, Fraction()) / 51',
    'for value in differences), Fraction()) / 51': 'for value in differences), Fraction()) / 50',
    'zero_count == 52': 'zero_count == 51',
    'sample_variance / 52': 'sample_variance / 51',
    'subject_count=52': 'subject_count=51',
    'subjects=52': 'subjects=51',
}
for old,new in replacements.items():
    assert old in source, old
    source = source.replace(old,new)
destination = root/'docs/phase2/cho_51_target_analysis_candidate/paired_inference.py'
with destination.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(source)
print(str(destination))
