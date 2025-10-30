"""Enhanced Streamlit web application for brochure information extraction"""

import streamlit as st
import sys
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime
import io

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import custom modules
from app.utils import (
    draw_bounding_boxes,
    extract_entities,
    entities_to_dataframe,
    create_deals_from_entities,
    export_to_json,
    export_to_csv
)

# Configure page
st.set_page_config(
    page_title="SmartDeal - Brochure Analyzer",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .deal-card {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ocr_results' not in st.session_state:
    st.session_state.ocr_results = None
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'entities' not in st.session_state:
    st.session_state.entities = None
if 'deals' not in st.session_state:
    st.session_state.deals = None
if 'history' not in st.session_state:
    st.session_state.history = []


def process_with_ocr(image_array, ocr_engine, use_preprocessing, confidence_threshold):
    """Process image with selected OCR engine"""
    try:
        # Import OCR pipeline
        from preprocessing.ocr_pipeline import OCRPipeline

        # Initialize pipeline
        engine_map = {
            "PaddleOCR": "paddleocr",
            "Tesseract": "tesseract",
            "EasyOCR": "easyocr"
        }

        pipeline = OCRPipeline(
            ocr_engine=engine_map[ocr_engine],
            output_format='json'
        )

        # Save temp image
        temp_path = "/tmp/temp_brochure.jpg"
        cv2.imwrite(temp_path, cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR))

        # Process
        result = pipeline.process_image(temp_path, preprocess=use_preprocessing)

        # Filter by confidence
        filtered_boxes = [
            box for box in result['text_boxes']
            if box['confidence'] >= confidence_threshold
        ]

        result['text_boxes'] = filtered_boxes
        result['num_boxes'] = len(filtered_boxes)

        return result

    except Exception as e:
        st.error(f"OCR processing error: {str(e)}")
        st.info("Using mock data for demonstration. Install OCR libraries for real processing.")

        # Return mock data
        return create_mock_ocr_results(image_array.shape)


def create_mock_ocr_results(image_shape):
    """Create mock OCR results for demonstration"""
    height, width = image_shape[:2]

    mock_boxes = [
        {
            'text': 'Äpfel',
            'confidence': 0.95,
            'bbox': {'x_min': int(width*0.1), 'y_min': int(height*0.2),
                    'x_max': int(width*0.3), 'y_max': int(height*0.25)}
        },
        {
            'text': '1.99 €',
            'confidence': 0.92,
            'bbox': {'x_min': int(width*0.1), 'y_min': int(height*0.27),
                    'x_max': int(width*0.2), 'y_max': int(height*0.30)}
        },
        {
            'text': '-20%',
            'confidence': 0.88,
            'bbox': {'x_min': int(width*0.25), 'y_min': int(height*0.27),
                    'x_max': int(width*0.30), 'y_max': int(height*0.30)}
        },
        {
            'text': 'Milch',
            'confidence': 0.94,
            'bbox': {'x_min': int(width*0.5), 'y_min': int(height*0.2),
                    'x_max': int(width*0.7), 'y_max': int(height*0.25)}
        },
        {
            'text': '0.89 €',
            'confidence': 0.91,
            'bbox': {'x_min': int(width*0.5), 'y_min': int(height*0.27),
                    'x_max': int(width*0.6), 'y_max': int(height*0.30)}
        },
        {
            'text': '1 L',
            'confidence': 0.87,
            'bbox': {'x_min': int(width*0.65), 'y_min': int(height*0.27),
                    'x_max': int(width*0.7), 'y_max': int(height*0.30)}
        },
        {
            'text': 'Brot',
            'confidence': 0.93,
            'bbox': {'x_min': int(width*0.1), 'y_min': int(height*0.5),
                    'x_max': int(width*0.3), 'y_max': int(height*0.55)}
        },
        {
            'text': '2.49 €',
            'confidence': 0.90,
            'bbox': {'x_min': int(width*0.1), 'y_min': int(height*0.57),
                    'x_max': int(width*0.2), 'y_max': int(height*0.60)}
        }
    ]

    return {
        'image_path': 'mock',
        'ocr_engine': 'mock',
        'text_boxes': mock_boxes,
        'num_boxes': len(mock_boxes)
    }


# Header
st.title("🛒 SmartDeal: Supermarket Brochure Analyzer")
st.markdown("Upload a supermarket brochure to extract structured deal information automatically")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # OCR Engine selection
    ocr_engine = st.selectbox(
        "OCR Engine",
        ["PaddleOCR", "Tesseract", "EasyOCR"],
        help="Select the OCR engine to use for text extraction"
    )

    # Preprocessing option
    use_preprocessing = st.checkbox(
        "Enable Image Preprocessing",
        value=True,
        help="Apply image enhancement for better OCR results"
    )

    # Confidence threshold
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Minimum confidence for text detection"
    )

    # Display options
    st.markdown("---")
    st.subheader("Display Options")

    show_bboxes = st.checkbox("Show Bounding Boxes", value=True)
    show_text = st.checkbox("Show Text Labels", value=True)
    show_confidence = st.checkbox("Show Confidence Scores", value=False)

    st.markdown("---")
    st.markdown("### 📊 Statistics")

    if st.session_state.ocr_results:
        st.metric("Text Boxes", st.session_state.ocr_results['num_boxes'])

        if st.session_state.entities:
            total_entities = sum(len(v) for v in st.session_state.entities.values())
            st.metric("Entities Found", total_entities)

        if st.session_state.deals:
            st.metric("Deals Identified", len(st.session_state.deals))

    st.markdown("---")
    st.markdown("### About")
    st.info("""
**SmartDeal** - Intelligent brochure analysis

**Team:** Liyang, Zhaokun
**Project:** 8-week Seminar
    """)

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload & Process",
    "🔍 Extracted Data",
    "📊 Deals Analysis",
    "📚 History"
])

# Tab 1: Upload & Process
with tab1:
    st.header("Upload Brochure")

    uploaded_file = st.file_uploader(
        "Choose a brochure image",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a supermarket brochure image"
    )

    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.success(f"✓ File: {uploaded_file.name}")
        with col2:
            st.info(f"📦 Size: {uploaded_file.size / 1024:.1f} KB")
        with col3:
            if st.button("🔄 Reset"):
                st.session_state.ocr_results = None
                st.session_state.processed_image = None
                st.session_state.entities = None
                st.session_state.deals = None
                st.rerun()

        # Load image
        image = Image.open(uploaded_file)
        img_array = np.array(image)

        # Display images side by side
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📸 Original Image")
            st.image(image, use_container_width=True)

        with col2:
            st.subheader("🎯 Processed Result")

            # Process button
            if st.button("🔍 Extract Information", type="primary", use_container_width=True):
                with st.spinner(f"Processing with {ocr_engine}..."):
                    # Process OCR
                    ocr_results = process_with_ocr(
                        img_array,
                        ocr_engine,
                        use_preprocessing,
                        confidence_threshold
                    )

                    st.session_state.ocr_results = ocr_results

                    # Extract entities
                    entities = extract_entities(ocr_results['text_boxes'])
                    st.session_state.entities = entities

                    # Create deals
                    deals = create_deals_from_entities(entities)
                    st.session_state.deals = deals

                    # Create processed image
                    if show_bboxes:
                        processed = draw_bounding_boxes(
                            img_array.copy(),
                            ocr_results['text_boxes'],
                            confidence_threshold,
                            show_text,
                            show_confidence
                        )
                        st.session_state.processed_image = processed

                    # Add to history
                    st.session_state.history.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'filename': uploaded_file.name,
                        'ocr_engine': ocr_engine,
                        'num_boxes': ocr_results['num_boxes'],
                        'num_deals': len(deals)
                    })

                    st.success("✓ Processing complete!")
                    st.rerun()

            # Display processed image
            if st.session_state.processed_image is not None:
                st.image(st.session_state.processed_image, use_container_width=True)
            elif st.session_state.ocr_results is not None and not show_bboxes:
                st.image(image, use_container_width=True)
            else:
                st.info("👆 Click 'Extract Information' to start processing")

# Tab 2: Extracted Data
with tab2:
    st.header("Extracted Data")

    if st.session_state.ocr_results is None:
        st.info("📝 Upload and process an image first to see extracted data")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Text Boxes",
                st.session_state.ocr_results['num_boxes'],
                help="Total number of text regions detected"
            )

        with col2:
            if st.session_state.entities:
                num_products = len(st.session_state.entities.get('products', []))
                st.metric("Products", num_products)

        with col3:
            if st.session_state.entities:
                num_prices = len(st.session_state.entities.get('prices', []))
                st.metric("Prices", num_prices)

        with col4:
            if st.session_state.entities:
                num_discounts = len(st.session_state.entities.get('discounts', []))
                st.metric("Discounts", num_discounts)

        st.markdown("---")

        # Entity breakdown
        if st.session_state.entities:
            st.subheader("📋 Entities by Type")

            # Create tabs for each entity type
            entity_tabs = st.tabs([
                "🏷️ Products",
                "💰 Prices",
                "📉 Discounts",
                "📏 Units",
                "📅 Dates",
                "📄 All Data"
            ])

            entity_types = ['products', 'prices', 'discounts', 'units', 'dates']

            for i, entity_type in enumerate(entity_types):
                with entity_tabs[i]:
                    entities_list = st.session_state.entities.get(entity_type, [])

                    if entities_list:
                        # Display as DataFrame
                        df_data = []
                        for entity in entities_list:
                            row = {
                                'Text': entity['text'],
                                'Confidence': f"{entity['confidence']:.2%}"
                            }
                            if 'value' in entity:
                                row['Value'] = entity['value']
                            if 'quantity' in entity:
                                row['Quantity'] = entity['quantity']
                            if 'unit' in entity:
                                row['Unit'] = entity['unit']

                            df_data.append(row)

                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Download button
                        csv = export_to_csv(df)
                        st.download_button(
                            f"📥 Download {entity_type.capitalize()}",
                            csv,
                            f"{entity_type}.csv",
                            "text/csv",
                            key=f"download_{entity_type}"
                        )
                    else:
                        st.info(f"No {entity_type} detected")

            # All data tab
            with entity_tabs[5]:
                df = entities_to_dataframe(st.session_state.entities)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Export options
                col1, col2 = st.columns(2)

                with col1:
                    csv = export_to_csv(df)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        "all_entities.csv",
                        "text/csv"
                    )

                with col2:
                    json_data = export_to_json(st.session_state.entities)
                    st.download_button(
                        "📥 Download JSON",
                        json_data,
                        "all_entities.json",
                        "application/json"
                    )

# Tab 3: Deals Analysis
with tab3:
    st.header("Identified Deals")

    if st.session_state.deals is None:
        st.info("🎯 Process an image first to see identified deals")
    else:
        if len(st.session_state.deals) == 0:
            st.warning("No deals could be automatically identified. Try adjusting the confidence threshold.")
        else:
            st.success(f"Found {len(st.session_state.deals)} potential deals!")

            # Display deals as cards
            for i, deal in enumerate(st.session_state.deals):
                with st.expander(f"🛍️ Deal {i+1}: {deal['product_name']}", expanded=True):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("**Product**")
                        st.markdown(f"**{deal['product_name']}**")

                    with col2:
                        st.markdown("**Price**")
                        if deal['price']:
                            st.markdown(f"**€{deal['price']}**")
                        else:
                            st.markdown("_Not detected_")

                    with col3:
                        st.markdown("**Discount**")
                        if deal['discount']:
                            st.markdown(f"**{deal['discount']}%**")
                        else:
                            st.markdown("_No discount_")

                    if deal.get('unit'):
                        st.markdown(f"📦 Unit: {deal['unit']}")

            # Export deals
            st.markdown("---")
            st.subheader("Export Deals")

            col1, col2 = st.columns(2)

            with col1:
                # Create DataFrame for deals
                deals_data = []
                for deal in st.session_state.deals:
                    deals_data.append({
                        'Product': deal['product_name'],
                        'Price': deal.get('price', 'N/A'),
                        'Discount': deal.get('discount', 'N/A'),
                        'Unit': deal.get('unit', 'N/A')
                    })

                df_deals = pd.DataFrame(deals_data)
                csv_deals = export_to_csv(df_deals)

                st.download_button(
                    "📥 Download Deals (CSV)",
                    csv_deals,
                    "deals.csv",
                    "text/csv"
                )

            with col2:
                json_deals = export_to_json(st.session_state.deals)
                st.download_button(
                    "📥 Download Deals (JSON)",
                    json_deals,
                    "deals.json",
                    "application/json"
                )

# Tab 4: History
with tab4:
    st.header("Processing History")

    if len(st.session_state.history) == 0:
        st.info("📜 No processing history yet")
    else:
        st.success(f"Total processed files: {len(st.session_state.history)}")

        # Display history as table
        df_history = pd.DataFrame(st.session_state.history)
        st.dataframe(df_history, use_container_width=True, hide_index=True)

        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>SmartDeal v1.0 | Made with Streamlit</div>",
    unsafe_allow_html=True
)
