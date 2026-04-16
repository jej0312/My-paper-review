# src/main.py

from src.collectors.arxiv import collect_arxiv
from src.collectors.iclr_openreview import collect_iclr
from src.collectors.neurips_proceedings import collect_neurips
from src.analyze.aggregate_month import build_monthly_reports

def collect_daily():
    papers = []
    papers += collect_arxiv()
    papers += collect_iclr()
    papers += collect_neurips()

    # normalize
    # deduplicate
    # classify
    # summarize
    # save

def build_monthly_report():
    # load previous month papers
    # aggregate by category
    # extract top themes
    # compare with prior month
    # write markdown
    # optionally publish notion/email
    pass