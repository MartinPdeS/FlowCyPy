from dataclasses import dataclass, field
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Frame, PageTemplate, Spacer, Paragraph, Image
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
from pathlib import Path
import shutil


def df2table(df):
    paragraphs = [[Paragraph(col) for col in df.columns]] + df.values.tolist()
    style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.lightgrey, colors.white])
    ]

    return Table(paragraphs, hAlign='LEFT', style=style)


@dataclass
class Report:
    flow_cell: object
    scatterer: object
    analyzer: object
    output_filename: str = "flow_report.pdf"
    title_color: object = field(default=colors.darkblue)
    header_color: object = field(default=colors.darkgreen)
    footer_color: object = field(default=colors.gray)
    str_format: str = field(default='.2~P')

    # Page size constants
    width: float = field(default=A4[0], init=False)
    height: float = field(default=A4[1], init=False)

    temporary_folder = Path('./temporary_')

    def add_background(self, canvas, doc):
        """Adds a background color to every page."""
        canvas.saveState()
        canvas.setFillColorRGB(0.95, 0.95, 0.95)  # Light grey background
        canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)  # Fill the entire page
        canvas.restoreState()
        self.add_watermark(canvas, doc)

    def add_footer(self, canvas, doc):
        """Adds a footer with page number to every page."""
        canvas.saveState()
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.setFillColor(self.footer_color)
        canvas.drawString(1 * inch, 0.75 * inch, "Flow Cytometry Report")
        canvas.drawRightString(A4[0] - inch, 0.75 * inch, f"Page {doc.page}")
        canvas.restoreState()

    def get_header(self):
        """Returns a Paragraph for the report header."""
        style = getSampleStyleSheet()['Title']
        style.textColor = self.title_color
        return Paragraph("Flow Cytometry Simulation Report", style)

    def get_flow_cell_section(self):
        """Returns a Paragraph or Table for the FlowCell section."""
        style = getSampleStyleSheet()['Heading2']

        table_data = [['Attribute', 'Value']]
        table_data += self.flow_cell.get_properties()

        table = Table(table_data, hAlign='LEFT')
        table.setStyle(self.get_table_style())

        return Paragraph("Section 1: FlowCell Parameters", style), table

    def get_image_from(self, plot_function: object, figure_size, scale: float = 1, align: str = 'RIGHT') -> Image:
        # Generate and save plot image for the scatterer distribution
        plot_filename = self.temporary_folder / f"{id(plot_function)}.png"
        plot_function(show=False, figure_size=figure_size)
        plt.savefig(plot_filename)
        plt.close()

        # Create an image object to include in the PDF
        image = Image(
            filename=plot_filename,
            hAlign=align,
            height=figure_size[1] * scale * inch,
            width=figure_size[0] * scale * inch
        )

        return image

    def get_scatterer_section(self):
        """Returns a Table for the scatterer distribution section."""
        style = getSampleStyleSheet()['Heading2']

        df = self.scatterer.populations[0].dataframe.pint.dequantify().reset_index().describe(percentiles=[])
        df = df[['Time']]
        print(df)

        table = df2table(df)

        # df = self.scatterer.dataframe#.reset_index()
        # _report = df.pint.dequantify().describe(percentiles=[])
        # print(_report)
        # import pandas as pd
        # report = pd.DataFrame()
        # report['Attribute'] = _report['index']
        # report['Index'] = _report['Index']
        # report['Time'] = _report['Time']
        # print(report)

        # table = df2table(report)

        table.setStyle(self.get_table_style())

        self.get_image_from(self.scatterer.plot, figure_size=(8, 8), scale=0.5)

        # combined_table = Table([[table, image]], hAlign='LEFT')
        combined_table = Table([[table]], hAlign='LEFT')

        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align both the table and image at the top
        ]))

        return Paragraph("Section 2: Scatterer populations", style), combined_table

    def get_detector_section(self):
        """Returns a Table for the detector properties."""
        style = getSampleStyleSheet()['Heading2']
        detector_0, detector_1 = self.analyzer.cytometer.detectors
        properties_0 = detector_0.get_properties()
        properties_1 = detector_1.get_properties()

        # Create table data
        table_data = [['Attribute', f'Detector {detector_0.name}', f'Detector {detector_1.name}']]
        table_data += [[p0[0], p0[1], p1[1]] for p0, p1 in zip(properties_0, properties_1)]

        # Create and return the table
        table = Table(table_data, hAlign='LEFT')
        table.setStyle(self.get_table_style())

        image_0 = self.get_image_from(detector_0.plot, align='CENTER', figure_size=(6, 3))
        image_1 = self.get_image_from(detector_1.plot, align='CENTER', figure_size=(6, 3))

        return Paragraph("Section 3: Detectors parameters", style), table, image_0, image_1

    def get_analyzer_section(self) -> None:
        """Adds a section displaying analyzer properties."""
        style = getSampleStyleSheet()['Heading2']

        image = self.get_image_from(self.analyzer.plot_peak, align='CENTER', figure_size=(7, 6), scale=1)

        return Paragraph("Section 4: Peak Analyzer parameters", style), image

    def get_table_style(self) -> TableStyle:
        """Returns a consistent table style."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

    def add_watermark(self, canvas, doc):
        """Adds a semi-transparent watermark to the current page."""
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 50)
        canvas.setFillColorRGB(0.9, 0.9, 0.9)  # Light grey color for watermark
        canvas.setFillAlpha(0.3)  # Transparency level (0.0 fully transparent, 1.0 fully opaque)

        # Position the watermark in the center of the page
        width, height = A4
        canvas.translate(width / 2, height / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "FLOWCYPY REPORT")  # Watermark text

        canvas.restoreState()

    def generate_report(self):
        """Generates the PDF report, applying a background to every page."""
        # Use SimpleDocTemplate from Platypus

        if self.temporary_folder.exists():
            shutil.rmtree(self.temporary_folder)

        self.temporary_folder.mkdir()

        doc = SimpleDocTemplate(
            self.output_filename,
            pagesize=A4,
            showBoundary=1,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=1.5 * inch
        )

        spacer = Spacer(1, 0.2 * inch)

        story = [
            self.get_header(), spacer,
            *self.get_flow_cell_section(), spacer,
            *self.get_scatterer_section(), spacer,
            *self.get_detector_section(), spacer,
            *self.get_analyzer_section()
        ]

        # Create a page template with the background and header/footer functions
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='normal'
        )

        template = PageTemplate(
            id='background',
            frames=frame,
            onPage=self.add_background,
            onPageEnd=self.add_footer,
        )

        doc.addPageTemplates([template])

        # Build the PDF
        doc.build(story)
        print(f"PDF report saved as {self.output_filename}")

        shutil.rmtree(self.temporary_folder)
