import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle

# ---------- Grade System ----------
def get_grade(avg):
    if avg >= 90: return "A+"
    elif avg >= 80: return "A"
    elif avg >= 70: return "B"
    elif avg >= 60: return "C"
    elif avg >= 50: return "D"
    else: return "F"

# ---------- PDF Report Card Generator ----------
def generate_interactive_pdf_report(df, school_name, school_address, logo_path=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    logo_height = 1 * inch

    for index, row in df.iterrows():
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawCentredString(width / 2.0, height - margin, school_name)
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2.0, height - margin - 20, school_address)
        c.drawCentredString(width / 2.0, height - margin - 40, "Student Report Card")

        if logo_path is not None:
            try:
                c.drawImage(logo_path, margin, height - logo_height - 20, width=logo_height, height=logo_height)
            except:
                pass  # Skip if logo fails

        name = row['Name']
        average = row['Average']
        grade = get_grade(average)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, height - 120, f"Student Name: {name}")
        c.drawString(margin, height - 140, f"Average Marks: {average:.2f}")
        c.drawString(margin, height - 160, f"Grade: {grade}")

        subjects = df.columns[1:-1]
        data = [["Subject", "Marks"]] + [[subj, row[subj]] for subj in subjects]

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#5DADE2")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ]))
        table.wrapOn(c, width, height)
        table.drawOn(c, margin, height - 300)

        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.grey)
        c.drawString(margin, 30, "Generated by Student Marks Analyzer")

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# ---------- Streamlit UI ----------
st.set_page_config(page_title="🎓 Student Marks Analyzer", layout="wide")
st.markdown("<h1 style='color:#2C3E50;'>🎓 Student Marks Analyzer with PDF Report Cards</h1>", unsafe_allow_html=True)

lang = st.sidebar.radio("🌐 Select Language / भाषा चुनें:", ["English", "Hindi"])

# Optional: School Info
st.sidebar.markdown("🏫 **School Information**")
school_name = st.sidebar.text_input("School Name", "Green Valley Public School")
school_address = st.sidebar.text_input("School Address", "Sector 10, Mohali")

# Optional Logo Upload
logo_file = st.sidebar.file_uploader("Upload School Logo (Optional)", type=["png", "jpg", "jpeg"])
logo_path = None
if logo_file:
    logo_path = f"./temp_logo.{logo_file.type.split('/')[-1]}"
    with open(logo_path, "wb") as f:
        f.write(logo_file.read())

upload_option = st.sidebar.radio("📂 Choose Input Method:", ["Upload CSV", "Manual Input"])

if upload_option == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("📄 Upload CSV file (Name, Subjects, Marks)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
else:
    st.sidebar.write("📝 Enter student data manually")
    names = st.sidebar.text_area("Student names (comma separated)", "Alice, Bob")
    subjects = st.sidebar.text_area("Subjects (comma separated)", "Math, English, Science")
    
    if names and subjects:
        names_list = [n.strip() for n in names.split(",")]
        subjects_list = [s.strip() for s in subjects.split(",")]

        data = []
        for name in names_list:
            row = [name]
            for subject in subjects_list:
                val = st.sidebar.number_input(f"{name}'s marks in {subject}", min_value=0, max_value=100, step=1, key=f"{name}_{subject}")
                row.append(val)
            data.append(row)
        
        cols = ["Name"] + subjects_list
        df = pd.DataFrame(data, columns=cols)

# ---------- Analysis & Report ----------
if 'df' in locals() or 'df' in globals():
    df['Average'] = df.iloc[:, 1:].mean(axis=1)

    st.subheader("📊 Student Data")
    st.dataframe(df)

    st.subheader("📘 Average Marks per Student")
    st.bar_chart(df.set_index("Name")["Average"])

    st.subheader("📈 Average Marks per Subject")
    avg_marks = df.iloc[:, 1:-1].mean().sort_values(ascending=False)
    st.bar_chart(avg_marks)

    st.subheader("🔥 Subject-wise Performance Heatmap")
    fig, ax = plt.subplots()
    sns.heatmap(df.set_index("Name").iloc[:, :-1], annot=True, cmap="YlGnBu", ax=ax)
    st.pyplot(fig)

    st.subheader("🏷️ Grade Legend")
    st.markdown("""
    - **A+**: 90 and above  
    - **A**: 80 - 89  
    - **B**: 70 - 79  
    - **C**: 60 - 69  
    - **D**: 50 - 59  
    - **F**: Below 50  
    """)

    # PDF Generation for All
    st.subheader("📄 Download Combined PDF Report Cards")
    pdf_buffer = generate_interactive_pdf_report(df, school_name, school_address, logo_path)
    st.download_button("📥 Download All Report Cards PDF", data=pdf_buffer, file_name="student_report_cards.pdf", mime="application/pdf")

    # Optionally, Individual Download
    st.subheader("🧍 Download Individual Report")
    selected_student = st.selectbox("Select Student", df["Name"])
    student_df = df[df["Name"] == selected_student]
    student_pdf = generate_interactive_pdf_report(student_df, school_name, school_address, logo_path)
    st.download_button("📄 Download Individual Report Card", data=student_pdf, file_name=f"{selected_student}_report_card.pdf", mime="application/pdf")

else:
    st.warning("Please upload data or enter manually.")

