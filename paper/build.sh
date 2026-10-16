#!/bin/sh
# Rebuild the paper: numbers -> figures -> equations -> markdown -> HTML -> PDF (run from the repository root)
set -e
${PYTHON:-python3} paper/paper_numbers.py && ${PYTHON:-python3} paper/paper_figures.py && ${PYTHON:-python3} paper/render_equations.py && ${PYTHON:-python3} paper/build_paper.py
cd paper
pandoc singapore_timing_paper_draft.md -o singapore_timing_paper_draft.html --standalone --css=paper_style.css --metadata pagetitle="The Ten-Year Echo in Singapore's COE Premium, and Why Housing Timing Signals Fail Out of Sample" --embed-resources
weasyprint singapore_timing_paper_draft.html singapore_timing_paper_draft.pdf --base-url .
