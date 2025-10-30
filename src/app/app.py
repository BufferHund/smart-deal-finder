"""Streamlit web application for brochure information extraction"""

import streamlit as st
import sys
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image
import io

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure page
st.set_page_config(
    page_title="SmartDeal - Brochure Analyzer",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🛒 SmartDeal: Supermarket Brochure Analyzer")
st.markdown("""
Upload a supermarket brochure image or PDF to extract deal information including:
- Product names
- Prices
- Discounts
- Special offers
""")

# Sidebar
st.sidebar.header("Settings")

# OCR Engine selection
ocr_engine = st.sidebar.selectbox(
    "OCR Engine",
    ["PaddleOCR", "Tesseract", "EasyOCR"],
    help="Select the OCR engine to use for text extraction"
)

# Preprocessing option
use_preprocessing = st.sidebar.checkbox(
    "Enable Image Preprocessing",
    value=True,
    help="Apply image enhancement for better OCR results"
)

# Confidence threshold
confidence_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="Minimum confidence for text detection"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
**SmartDeal** is an intelligent system for extracting structured deal information
from supermarket brochures using computer vision and NLP techniques.

**Team:** Liyang, Zhaokun
**Project:** Seminar Project (8 weeks)
""")

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload & Extract", "📊 Analysis", "ℹ️ Info"])

with tab1:
    st.header("Upload Brochure")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a brochure image or PDF",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Upload a supermarket brochure in image or PDF format"
    )

    if uploaded_file is not None:
        # Display uploaded file info
        st.success(f"File uploaded: {uploaded_file.name}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Original Image")

            # Display image
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)

                # Convert to numpy array for processing
                img_array = np.array(image)
            else:
                st.info("PDF processing will be implemented in later versions")
                img_array = None

        with col2:
            st.subheader("Extracted Information")

            if img_array is not None:
                # Process button
                if st.button("🔍 Extract Information", type="primary"):
                    with st.spinner("Processing image with OCR..."):
                        try:
                            # Placeholder for actual OCR processing
                            # This will be implemented when OCR pipeline is integrated
                            st.info("OCR processing will be integrated in the next phase")

                            # Mock data for demonstration
                            extracted_data = {
                                "products": [
                                    {
                                        "name": "Apfel",
                                        "price": "1.99",
                                        "unit": "kg",
                                        "discount": "20%"
                                    },
                                    {
                                        "name": "Milch",
                                        "price": "0.89",
                                        "unit": "L",
                                        "discount": None
                                    }
                                ]
                            }

                            # Display extracted data
                            st.json(extracted_data)

                            # Download button for JSON
                            json_str = json.dumps(extracted_data, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="📥 Download JSON",
                                data=json_str,
                                file_name="extracted_deals.json",
                                mime="application/json"
                            )

                        except Exception as e:
                            st.error(f"Error processing image: {str(e)}")
            else:
                st.warning("Please upload an image to extract information")

with tab2:
    st.header("Deal Analysis")

    st.info("Analysis features will be implemented in Week 6-7")

    st.markdown("""
    **Planned Features:**
    - Price comparison across supermarkets
    - Discount percentage analysis
    - Product category breakdown
    - Best deals recommendation
    - Price trends over time
    """)

    # Placeholder chart
    st.markdown("### Sample Visualization")
    st.line_chart({"Aldi": [1.99, 1.89, 1.79], "Lidl": [2.09, 1.99, 1.89]})

with tab3:
    st.header("Project Information")

    st.markdown("""
    ## Problem Description
    Supermarket brochures contain valuable information about weekly discounts, product offers,
    and price changes. However, these brochures are usually published as unstructured images
    or PDFs, which makes it difficult for customers to extract and analyze deals.

    ## Methodology
    1. **OCR & Layout Analysis**: Text detection and recognition
    2. **Information Extraction**: Entity recognition using layout-aware transformers
    3. **Fine-tuning**: PEFT on collected data

    ## Main Challenges
    - Data format variation (PDF, images, scanned copies)
    - Layout variability (different retailer designs)
    - OCR noise (distorted fonts and symbols)
    - Entity alignment (linking visual blocks with semantic fields)
    - Limited labeled data

    ## Technologies Used
    - **OCR**: PaddleOCR, Tesseract, EasyOCR
    - **ML Models**: LayoutLMv3, Donut, TrOCR
    - **Fine-tuning**: PEFT, LoRA
    - **Web Framework**: Streamlit
    - **Computer Vision**: OpenCV, PIL

    ## Project Timeline
    This is an 8-week project covering:
    1. Data collection & preprocessing (Week 1-3)
    2. Model selection & training (Week 4-5)
    3. Evaluation & refinement (Week 6)
    4. Application development (Week 7-8)
    """)

    # Display team info
    st.markdown("---")
    st.markdown("### Team")
    st.markdown("**Liyang** and **Zhaokun**")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'>Made with ❤️ using Streamlit</div>",
    unsafe_allow_html=True
)
