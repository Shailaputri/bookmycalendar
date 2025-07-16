import streamlit as st
from datetime import datetime, date
import pytz
import re
import os
import pdfkit
from google_auth import get_calendar_service
from calendar_utils import get_available_slots, create_appointment

# Constants
TIMEZONE = 'Asia/Kolkata'
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
import os

# Dynamically build the correct path
img_path = os.path.join("static", "gpay_qr.png")
# GPAY_QR_CODE = st.image(img_path, width=200)

def validate_email(email):
    """Validate email format using regex"""
    return re.match(EMAIL_REGEX, email) is not None

# def generate_pdf(html_content, filename):
#     """Generate PDF from HTML content"""
#     try:
#         pdfkit.from_string(html_content, filename)
#         return True
#     except Exception as e:
#         st.error(f"PDF generation failed: {e}")
#         return False

# Alternative using WeasyPrint (pure Python)
# from weasyprint import HTML
# def generate_pdf(html_content, filename):
#     try:
#         HTML(string=html_content).write_pdf(filename)
#         return True
#     except Exception as e:
#         st.error(f"PDF generation failed: {e}")
#         return False

from xhtml2pdf import pisa
import io

def generate_pdf(html_content, filename):
    """Generate PDF using xhtml2pdf"""
    try:
        result = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html_content), dest=result)
        with open(filename, "wb") as f:
            f.write(result.getvalue())
        return True
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        return False

def get_reference_id(email):
    """Generate a consistent reference ID from email"""
    return f"APPT-{abs(hash(email)) % 1000000:06d}"  # 6-digit numeric ID

def main():
    st.title('Appointment Booking with Payment')
    
    # Initialize session state
    if 'payment_verified' not in st.session_state:
        st.session_state.payment_verified = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    try:
        service = get_calendar_service()
    except Exception as e:
        st.error(f"🔐 Authentication failed: {e}")
        return

    # Step 1: Date selection
    selected_date = st.date_input("Select date", min_value=date.today())
    available_slots = get_available_slots(service, selected_date)
    slot_options = [s.strftime("%I:%M %p") for s in available_slots]
    selected_time = st.selectbox("Select time", slot_options)

    # Step 2: User details
    with st.form("user_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        
        if st.form_submit_button("Continue to Payment"):
            if not name:
                st.error("Please enter your name")
            elif not validate_email(email):
                st.error("Please enter a valid email address")
            else:
                st.session_state.user_data = {
                    "name": name,
                    "email": email,
                    "date": selected_date,
                    "time": selected_time,
                    "reference_id": get_reference_id(email)
                }
                st.rerun()

    # Step 3: Payment verification
    if st.session_state.user_data:
        st.divider()
        st.subheader("Complete Payment (₹500)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(img_path, width=200)
            st.write(f"Reference: {st.session_state.user_data['reference_id']}")

        with col2:
            with st.form("payment_form"):
                transaction_id = st.text_input("Transaction ID (starts with 'GPT')", 
                                             placeholder="GPT123456789")
                
                if st.form_submit_button("Verify Payment"):
                    if transaction_id.startswith("GPT") and len(transaction_id) == 12:
                        st.session_state.payment_verified = True
                        st.success("Payment verified!")
                        st.rerun()
                    else:
                        st.error("Invalid Transaction ID. Must be 12 characters starting with 'GPT'")

    # Step 4: Booking confirmation
    if st.session_state.get('payment_verified', False):
        try:
            selected_slot = next(
                s for s in available_slots 
                if s.strftime("%I:%M %p") == st.session_state.user_data["time"]
            )
            
            # Create calendar event
            event = create_appointment(
                service,
                selected_slot,
                st.session_state.user_data["name"],
                st.session_state.user_data["email"]
            )
            
            # Generate PDF
            pdf_content = f"""
            <h1>Appointment Confirmation</h1>
            <p><strong>Name:</strong> {st.session_state.user_data["name"]}</p>
            <p><strong>Date:</strong> {st.session_state.user_data["date"].strftime('%Y-%m-%d')}</p>
            <p><strong>Time:</strong> {st.session_state.user_data["time"]}</p>
            <p><strong>Reference ID:</strong> {st.session_state.user_data["reference_id"]}</p>
            """
            pdf_filename = f"booking_{st.session_state.user_data['reference_id']}.pdf"
            
            if generate_pdf(pdf_content, pdf_filename):
                with open(pdf_filename, "rb") as f:
                    st.success("🎉 Booking confirmed!")
                    st.download_button(
                        "Download Receipt",
                        data=f,
                        file_name=pdf_filename,
                        mime="application/pdf"
                    )
                
                # Clean up
                if os.path.exists(pdf_filename):
                    os.remove(pdf_filename)
                
                # Reset flow
                st.session_state.clear()
                
        except Exception as e:
            st.error(f"❌ Booking failed: {str(e)}")
            st.session_state.payment_verified = False

if __name__ == '__main__':
    main()