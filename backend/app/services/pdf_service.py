import io
import calendar
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from app.config import settings
from app.models import PayrollItem, Payslip

def num_to_words(number: float) -> str:
    """Convert number to Indian currency words format (Rupees & Paise)"""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", 
             "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", 
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    n = int(number)
    if n == 0:
        return "Zero Rupees Only"
        
    def convert_upto_999(num):
        out = ""
        if num >= 100:
            out += units[num // 100] + " Hundred "
            num %= 100
        if num >= 20:
            out += tens[num // 10] + " "
            num %= 10
        if num > 0:
            out += units[num] + " "
        return out.strip()

    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000
    remainder = n

    res = ""
    if crore > 0:
        res += convert_upto_999(crore) + " Crore "
    if lakh > 0:
        res += convert_upto_999(lakh) + " Lakh "
    if thousand > 0:
        res += convert_upto_999(thousand) + " Thousand "
    if remainder > 0:
        res += convert_upto_999(remainder) + " "

    res = res.strip() + " Rupees"
    
    paise = int(round((number - int(number)) * 100))
    if paise > 0:
        res += f" and {convert_upto_999(paise)} Paise"
        
    return res + " Only"

def generate_payslip_pdf(item: PayrollItem, payslip: Payslip) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    brand_blue = colors.HexColor("#0f3d64")
    dark_gray = colors.HexColor("#1e293b")
    light_blue = colors.HexColor("#f0f7ff")
    border_gray = colors.HexColor("#cbd5e1")
    text_muted = colors.HexColor("#64748b")
    
    company_style = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=brand_blue,
        alignment=TA_CENTER
    )
    sub_title_style = ParagraphStyle(
        'CompanySubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=text_muted,
        alignment=TA_CENTER
    )
    payslip_badge_style = ParagraphStyle(
        'PayslipBadge',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0359a1"),
        alignment=TA_CENTER
    )
    th_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#ffffff"),
    )
    th_right_style = ParagraphStyle(
        'TableHeaderRight',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#ffffff"),
        alignment=TA_RIGHT
    )
    cell_bold_style = ParagraphStyle(
        'CellBold',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=dark_gray,
    )
    cell_regular_style = ParagraphStyle(
        'CellRegular',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=dark_gray,
    )
    cell_right_style = ParagraphStyle(
        'CellRight',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=dark_gray,
        alignment=TA_RIGHT
    )
    cell_bold_right_style = ParagraphStyle(
        'CellBoldRight',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=dark_gray,
        alignment=TA_RIGHT
    )

    elements = []
    
    # 1. Header with Company Details
    elements.append(Paragraph(settings.COMPANY_NAME.upper(), company_style))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(f"{settings.COMPANY_ADDRESS}", sub_title_style))
    elements.append(Paragraph(f"Email: {settings.COMPANY_EMAIL} | Tel: {settings.COMPANY_PHONE} | CIN: {settings.COMPANY_CIN} | TAN: {settings.COMPANY_TAN}", sub_title_style))
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=2, spaceAfter=8))
    
    # 2. Payslip Month Title
    month_name = calendar.month_name[payslip.month]
    elements.append(Paragraph(f"PAYSLIP FOR THE MONTH OF {month_name.upper()} {payslip.year}", payslip_badge_style))
    elements.append(Spacer(1, 8))
    
    # 3. Employee Info Block (4 columns)
    emp = item.employee
    emp_info_data = [
        [
            Paragraph("<b>Employee ID:</b>", cell_regular_style), Paragraph(item.employee_code, cell_bold_style),
            Paragraph("<b>Payslip No:</b>", cell_regular_style), Paragraph(payslip.payslip_number, cell_bold_style)
        ],
        [
            Paragraph("<b>Employee Name:</b>", cell_regular_style), Paragraph(item.employee_name, cell_bold_style),
            Paragraph("<b>Designation:</b>", cell_regular_style), Paragraph(item.designation_name or "N/A", cell_regular_style)
        ],
        [
            Paragraph("<b>Department:</b>", cell_regular_style), Paragraph(item.department_name or "N/A", cell_regular_style),
            Paragraph("<b>Date of Joining:</b>", cell_regular_style), Paragraph(str(emp.date_of_joining) if emp and emp.date_of_joining else "N/A", cell_regular_style)
        ],
        [
            Paragraph("<b>Bank Name:</b>", cell_regular_style), Paragraph(item.bank_name or "N/A", cell_regular_style),
            Paragraph("<b>Bank Account No:</b>", cell_regular_style), Paragraph(item.bank_account_no or "N/A", cell_regular_style)
        ],
        [
            Paragraph("<b>PAN Number:</b>", cell_regular_style), Paragraph(item.pan_number or "N/A", cell_regular_style),
            Paragraph("<b>UAN / EPF No:</b>", cell_regular_style), Paragraph(emp.uan_number if emp and emp.uan_number else "N/A", cell_regular_style)
        ],
        [
            Paragraph("<b>Payment Mode:</b>", cell_regular_style), Paragraph((item.payment_method or "Bank Transfer").upper(), cell_regular_style),
            Paragraph("<b>Status:</b>", cell_regular_style), Paragraph("PAID", cell_bold_style)
        ]
    ]
    
    emp_table = Table(emp_info_data, colWidths=[90, 170, 90, 170])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_blue),
        ('BOX', (0, 0), (-1, -1), 0.5, border_gray),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 8))
    
    # 4. Attendance Summary Line
    att_data = [
        [
            Paragraph(f"<b>Total Working Days:</b> {int(item.total_working_days)}", cell_regular_style),
            Paragraph(f"<b>Present:</b> {int(item.present_days)}", cell_regular_style),
            Paragraph(f"<b>Paid Leave:</b> {int(item.paid_leave_days)}", cell_regular_style),
            Paragraph(f"<b>Unpaid Leave/Loss of Pay:</b> {int(item.unpaid_leave_days + item.absent_days)}", cell_regular_style),
            Paragraph(f"<b>Overtime Hours:</b> {item.overtime_hours:.1f} hrs", cell_regular_style)
        ]
    ]
    att_table = Table(att_data, colWidths=[105, 95, 95, 125, 100])
    att_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.5, border_gray),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(att_table)
    elements.append(Spacer(1, 10))
    
    # 5. Earnings & Deductions Dual Table
    earnings_rows = [
        ("Basic Salary", f"{item.basic_salary:,.2f}"),
        ("House Rent Allowance (HRA)", f"{item.hra:,.2f}"),
        ("Dearness Allowance (DA)", f"{item.da:,.2f}"),
        ("Conveyance Allowance", f"{item.conveyance_allowance:,.2f}"),
        ("Medical Allowance", f"{item.medical_allowance:,.2f}"),
        ("Special Allowance", f"{item.special_allowance:,.2f}"),
    ]
    if item.performance_bonus > 0:
        earnings_rows.append(("Performance Bonus", f"{item.performance_bonus:,.2f}"))
    if item.overtime_pay > 0:
        earnings_rows.append(("Overtime Pay", f"{item.overtime_pay:,.2f}"))
    if item.incentives > 0:
        earnings_rows.append(("Incentives", f"{item.incentives:,.2f}"))
    if item.other_earnings > 0:
        earnings_rows.append(("Other Allowances / Bonus", f"{item.other_earnings:,.2f}"))
        
    deductions_rows = []
    if item.epf_employee > 0 or emp and emp.epf_enabled:
        deductions_rows.append(("Employee EPF (12%)", f"{item.epf_employee:,.2f}"))
    if item.esi_employee > 0 or (emp and emp.esi_enabled):
        deductions_rows.append(("Employee ESI (0.75%)", f"{item.esi_employee:,.2f}"))
    if item.professional_tax > 0:
        deductions_rows.append(("Professional Tax (PT)", f"{item.professional_tax:,.2f}"))
    if item.tds > 0:
        deductions_rows.append(("Income Tax (TDS)", f"{item.tds:,.2f}"))
    if item.unpaid_leave_deduction > 0:
        deductions_rows.append(("Loss of Pay / Leave Deduction", f"{item.unpaid_leave_deduction:,.2f}"))
    if item.loan_advance_deduction > 0:
        deductions_rows.append(("Loan / Advance Deduction", f"{item.loan_advance_deduction:,.2f}"))
    if item.late_penalty_deduction > 0:
        deductions_rows.append(("Late Penalty", f"{item.late_penalty_deduction:,.2f}"))
    if item.other_deductions > 0:
        deductions_rows.append(("Other Deductions", f"{item.other_deductions:,.2f}"))
        
    # Pad rows to align heights
    max_len = max(len(earnings_rows), len(deductions_rows), 6)
    while len(earnings_rows) < max_len:
        earnings_rows.append(("", ""))
    while len(deductions_rows) < max_len:
        deductions_rows.append(("", ""))
        
    table_rows = [
        [
            Paragraph("EARNINGS", th_style), Paragraph("AMOUNT (INR)", th_right_style),
            Paragraph("DEDUCTIONS", th_style), Paragraph("AMOUNT (INR)", th_right_style)
        ]
    ]
    
    for i in range(max_len):
        e_name, e_val = earnings_rows[i]
        d_name, d_val = deductions_rows[i]
        table_rows.append([
            Paragraph(e_name, cell_regular_style), Paragraph(e_val, cell_right_style),
            Paragraph(d_name, cell_regular_style), Paragraph(d_val, cell_right_style)
        ])
        
    # Totals Row
    table_rows.append([
        Paragraph("<b>GROSS EARNINGS</b>", cell_bold_style), Paragraph(f"<b>Rs. {item.gross_salary:,.2f}</b>", cell_bold_right_style),
        Paragraph("<b>TOTAL DEDUCTIONS</b>", cell_bold_style), Paragraph(f"<b>Rs. {item.total_deductions:,.2f}</b>", cell_bold_right_style)
    ])
    
    salary_table = Table(table_rows, colWidths=[180, 80, 180, 80])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), brand_blue),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 0.5, border_gray),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 10))
    
    # 6. Net Salary Callout Box
    net_words = num_to_words(item.net_salary)
    net_box_data = [
        [
            Paragraph(f"<font size=11 color='#074c84'><b>NET TAKE HOME SALARY:</b></font> <font size=13 color='#0270c7'><b>Rs. {item.net_salary:,.2f}</b></font><br/><font size=8.5 color='#475569'><b>Amount in Words:</b> {net_words}</font>", cell_regular_style)
        ]
    ]
    net_table = Table(net_box_data, colWidths=[520])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_blue),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0270c7")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 15))
    
    # 7. Employer Contributions Note & Signatures
    employer_notes = f"Employer PF Contribution: Rs. {item.epf_employer:,.2f} | Employer ESI Contribution: Rs. {item.esi_employer:,.2f}"
    elements.append(Paragraph(f"<font size=8 color='#64748b'>{employer_notes}</font>", cell_regular_style))
    elements.append(Spacer(1, 20))
    
    sign_data = [
        [
            Paragraph("<b>Employee Signature</b><br/><br/>_______________________", cell_regular_style),
            Paragraph("<b>Authorized Signatory</b><br/>Apex Technologies Pvt Ltd<br/>_______________________", cell_right_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(sign_table)
    elements.append(Spacer(1, 10))
    
    # 8. Disclaimer
    disclaimer = "Note: This payslip is electronically generated by PayPulse Payroll System. For inquiries, contact HR/Payroll team at payroll@apextechglobal.com."
    elements.append(Paragraph(disclaimer, sub_title_style))
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
