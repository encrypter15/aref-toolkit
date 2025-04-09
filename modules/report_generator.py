import json
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate(target, results, args):
    formats = ["json"]
    if args.verbose:
        formats.extend(["csv", "html", "pdf"])

    # JSON
    report = {"target": target, "recon": results}
    with open(f"reports/{target}_report.json", "w") as f:
        json.dump(report, f, indent=2)

    if "csv" in formats:
        with open(f"reports/{target}_report.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Section", "Data"])
            for key, value in results.items():
                writer.writerow([key, json.dumps(value)])

    if "html" in formats:
        with open(f"reports/{target}_report.html", "w") as f:
            f.write(f"<html><body><h1>{target} Report</h1><pre>{json.dumps(results, indent=2)}</pre></body></html>")

    if "pdf" in formats:
        doc = SimpleDocTemplate(f"reports/{target}_report.pdf", pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph(f"Report for {target}", styles["Title"]), Spacer(1, 12)]
        story.append(Paragraph(json.dumps(results, indent=2), styles["Normal"]))
        doc.build(story)

    print(f"[+] Report saved to reports/{target}_report.{'|'.join(formats)}")
