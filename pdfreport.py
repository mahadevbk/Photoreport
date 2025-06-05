

import streamlit as st
from fpdf import FPDF
from PIL import Image
import tempfile
import os
import datetime

st.set_page_config(layout="wide")
st.title("\U0001F4F8 Multi-page PDF Photo Report Creator")

if "pages" not in st.session_state:
    st.session_state.pages = []

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# Sidebar: Project Info
st.sidebar.header("Project Info")
project_name = st.sidebar.text_input("Project Name")
username = st.sidebar.text_input("Your Name")
report_date = st.sidebar.date_input("Report Date", value=datetime.date.today())

st.markdown("---")
st.subheader("➕ Add New Page")

new_images = st.file_uploader("Upload 1 to 4 images", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="uploader")
new_title = st.text_input("Photo Set Title", key="title_input")
new_description = st.text_area("Photo Description (room for ~10 lines)", height=200, key="desc_input")

if st.button("Add Page", key="add_button"):
    if not (1 <= len(new_images) <= 4):
        st.warning("Please upload between 1 and 4 images.")
    elif not new_description.strip():
        st.warning("Please enter a description.")
    else:
        st.session_state.pages.append({
            "images": new_images,
            "title": new_title,
            "description": new_description
        })
        st.success("Page added!")
        st.session_state.edit_index = None

# --- Thumbnail Preview Section ---
st.markdown("---")
st.subheader("\U0001F5BC️ Current Pages")

to_delete = None
for i, page in enumerate(st.session_state.pages):
    cols = st.columns([1, 4, 1])
    with cols[1]:
        st.image(page["images"][0], width=200, caption=page["title"])
    with cols[2]:
        if st.button("📝 Edit", key=f"edit_{i}"):
            st.session_state.edit_index = i
        if st.button("❌ Delete", key=f"delete_{i}"):
            to_delete = i

    if st.session_state.edit_index == i:
        st.markdown(f"### ✏️ Editing Page {i+1}")
        edit_title = st.text_input("Edit Title", value=page["title"], key=f"edit_title_{i}")
        edit_description = st.text_area("Edit Description", value=page["description"], height=200, key=f"edit_desc_{i}")
        edit_images = st.file_uploader("Replace Images (Optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"edit_images_{i}")
        if st.button("💾 Save Changes", key=f"save_{i}"):
            st.session_state.pages[i]["title"] = edit_title
            st.session_state.pages[i]["description"] = edit_description
            if edit_images:
                st.session_state.pages[i]["images"] = edit_images
            st.session_state.edit_index = None
            st.success("Page updated.")
        if st.button("❎ Cancel", key=f"cancel_{i}"):
            st.session_state.edit_index = None

if to_delete is not None:
    st.session_state.pages.pop(to_delete)
    st.success("Page deleted.")

# --- PDF Generator ---
def generate_pdf(pages, project_name, username, report_date):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)

    for page_num, page in enumerate(pages, start=1):
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, project_name, ln=1, align='C')

        collage_width = 127
        collage_height = 90
        full_width = 190
        x_offset = (210 - collage_width) // 2
        y_offset = 25
        gap = 5

        # Grey background for image section - full width
        pdf.set_fill_color(220, 220, 220)
        pdf.rect(10, y_offset - 5, full_width, collage_height + 10, 'F')

        num_images = len(page["images"])
        rows = 2 if num_images > 2 else 1
        cols = 2 if num_images > 1 else 1
        img_w = (collage_width - gap * (cols - 1)) / cols
        img_h = (collage_height - gap * (rows - 1)) / rows

        for i, img_file in enumerate(page["images"]):
            img = Image.open(img_file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                img.save(tmp_file.name, format="JPEG")
                col = i % cols
                row = i // cols
                x = x_offset + (img_w + gap) * col
                y = y_offset + (img_h + gap) * row

                img_width_px, img_height_px = img.size
                img_aspect = img_width_px / img_height_px
                box_aspect = img_w / img_h

                if img_aspect > box_aspect:
                    draw_w = img_w
                    draw_h = img_w / img_aspect
                else:
                    draw_h = img_h
                    draw_w = img_h * img_aspect

                draw_x = x + (img_w - draw_w) / 2
                draw_y = y + (img_h - draw_h) / 2

                pdf.image(tmp_file.name, x=draw_x, y=draw_y, w=draw_w, h=draw_h)
                temp_img_path = tmp_file.name

            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

        desc_y = y_offset + collage_height + 10

        # Title (Image Subject) with white background
        pdf.set_xy(10, desc_y)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 10, f" Subject: {page['title']}", ln=1, fill=True)

        # Grey background for description block
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, "Description:", ln=1, fill=True)

        pdf.set_font("Arial", size=12)
        lines = page["description"].splitlines()
        while len(lines) < 10:
            lines.append("")

        for line in lines:
            pdf.cell(190, 10, txt=line, ln=1, fill=True)

        # Footer
        pdf.set_y(-30)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, f"Created by: {username}", ln=1)
        pdf.cell(0, 10, f"Date: {report_date}", ln=1)

        # Page number
        pdf.set_y(-10)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Page {page_num}", align="C")

    return pdf.output(dest='S').encode('latin1')

# Generate PDF
if st.session_state.pages:
    st.markdown("---")
    st.subheader("\U0001F4C4 Generate Photo Report")
    if st.button("Generate PDF"):
        if not project_name.strip() or not username.strip():
            st.warning("Please fill in all project information.")
        else:
            pdf_bytes = generate_pdf(st.session_state.pages, project_name, username, report_date)
            st.download_button(
                label="\U0001F4E5 Download Photo Report PDF",
                data=pdf_bytes,
                file_name=f"{project_name.replace(' ', '_')}_Photo_Report.pdf",
                mime="application/pdf"
            )
# ------------------ FOOTER -------------------
st.markdown("---")
st.markdown("Dev's PDF Editor | Code on https://github.com/mahadevbk/pdfeditor ")
st.info("Built with ❤️ using [Streamlit](https://streamlit.io/) — free and open source. [Other Scripts by dev](https://devs-scripts.streamlit.app/) on Streamlit.")
