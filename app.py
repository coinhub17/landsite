import streamlit as st
import hashlib, uuid, datetime, io
from fpdf import FPDF
from PIL import Image

# ---------- CONFIG ----------
ADMIN_PASSWORD = "KVN_ADMIN_SECRET"

# ---------- MEMORY ----------
if "cert_store" not in st.session_state:
    st.session_state.cert_store = {}

if "last_cert_id" not in st.session_state:
    st.session_state.last_cert_id = None

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

# ---------- HASH ----------
def hash_file(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

# ---------- PDF ----------
def generate_pdf(cert, image_bytes=None):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Kerio Valley IP Protection Certificate", ln=True, align="C")
    pdf.ln(10)

    # Insert image (if image file)
    if image_bytes:
        img = Image.open(io.BytesIO(image_bytes))
        img_path = "temp.png"
        img.save(img_path)

        # Add image
        pdf.image(img_path, x=30, y=50, w=150)

        # Overlay text (simulate watermark)
        pdf.set_xy(30, 120)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(150, 150, 150)  # grey (watermark feel)

        pdf.multi_cell(150, 6,
            f"SHA256:\n{cert['file_hash']}\n\nTimestamp:\n{cert['timestamp']}"
        )

    else:
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 8, "No preview available for this file type.")

    pdf.ln(10)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 8,
        "This certificate confirms the existence of the file at the given timestamp.\n"
        "Verification is done by re-uploading the original file and matching its SHA256 hash."
    )

    return pdf.output(dest='S').encode('latin1')

# ---------- UI ----------
st.title("Kerio Valley IP Protection System")

# ---------- UPLOAD ----------
st.header("Upload File")

file = st.file_uploader("Upload file")

if file:
    content = file.read()
    file_hash = hash_file(content)

    cert_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    st.session_state.cert_store[cert_id] = {
        "id": cert_id,
        "file_hash": file_hash,
        "timestamp": timestamp,
        "filename": file.name,
        "file_bytes": content
    }

    st.session_state.last_cert_id = cert_id

    st.success("File recorded successfully")
    st.write("Certificate ID:", cert_id)
    st.write("Hash:", file_hash)

# ---------- VERIFY ----------
st.header("Verify File")

verify_file = st.file_uploader("Re-upload file to verify", key="verify")

if verify_file:
    verify_bytes = verify_file.read()
    verify_hash = hash_file(verify_bytes)

    found = False

    for cert in st.session_state.cert_store.values():
        if cert["file_hash"] == verify_hash:
            st.success("✅ File Verified Successfully")
            st.write("Certificate ID:", cert["id"])
            st.write("Timestamp:", cert["timestamp"])
            found = True
            break

    if not found:
        st.error("❌ File Not Verified")

# ---------- ADMIN ----------
st.divider()
st.subheader("Admin Access")

password = st.text_input("Admin Password", type="password")

if password == ADMIN_PASSWORD:
    st.session_state.admin_mode = True
    st.success("Admin mode enabled")

# ---------- DOWNLOAD ----------
if st.session_state.admin_mode and st.session_state.last_cert_id:
    cert = st.session_state.cert_store.get(st.session_state.last_cert_id)

    if cert:
        image_bytes = None

        try:
            Image.open(io.BytesIO(cert["file_bytes"]))
            image_bytes = cert["file_bytes"]
        except:
            pass

        pdf = generate_pdf(cert, image_bytes)

        st.download_button(
            "Download Certificate",
            data=pdf,
            file_name=f"KVN_{cert['id']}.pdf",
            mime="application/pdf"
        )