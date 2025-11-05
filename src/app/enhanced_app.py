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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add directories to path
app_dir = Path(__file__).parent
src_dir = app_dir.parent
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(app_dir))

# Import custom modules (from same directory)
import utils
from utils import (
    draw_bounding_boxes,
    extract_entities,
    entities_to_dataframe,
    create_deals_from_entities,
    export_to_json,
    export_to_csv
)

# Try to import region-based clustering (requires sklearn)
try:
    from region_clustering import create_deals_from_regions
    REGION_CLUSTERING_AVAILABLE = True
except ImportError:
    REGION_CLUSTERING_AVAILABLE = False
    logger.warning("Region clustering not available (sklearn not installed)")

# Try to import advanced region clustering (requires sklearn + scipy)
try:
    from advanced_region_clustering import create_deals_advanced
    ADVANCED_CLUSTERING_AVAILABLE = True
except ImportError:
    ADVANCED_CLUSTERING_AVAILABLE = False
    if REGION_CLUSTERING_AVAILABLE:
        logger.warning("Advanced clustering not available (scipy not installed)")

# Try to import Gemini extractor
try:
    from gemini_extractor import extract_with_gemini, test_gemini_connection, get_available_models
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini integration not available (google-generativeai not installed)")

# Try to import open-source VLM extractor
try:
    from opensource_vlm_extractor import (
        extract_with_opensource_vlm,
        test_model_availability,
        get_available_models as get_vlm_models
    )
    VLM_AVAILABLE = True
except ImportError:
    VLM_AVAILABLE = False
    logger.warning("Open-source VLM not available (transformers/torch not installed)")

# Try to import VLM model manager
try:
    from vlm_model_manager import (
        get_available_vlm_models,
        check_model_downloaded,
        download_model,
        delete_model,
        get_model_info,
        get_all_cached_models,
        clean_all_models
    )
    VLM_MANAGER_AVAILABLE = True
except ImportError:
    VLM_MANAGER_AVAILABLE = False
    logger.warning("VLM model manager not available")

# Try to import Ollama extractor
try:
    from ollama_extractor import (
        extract_with_ollama,
        check_ollama_available,
        get_available_ollama_models,
        check_model_downloaded as check_ollama_model_downloaded,
        pull_model as pull_ollama_model,
        delete_model as delete_ollama_model
    )
    OLLAMA_AVAILABLE = check_ollama_available()
    logger.info(f"Ollama integration loaded. Available: {OLLAMA_AVAILABLE}")
except ImportError as e:
    OLLAMA_AVAILABLE = False
    logger.warning(f"Ollama integration not available (import error): {e}")
except Exception as e:
    OLLAMA_AVAILABLE = False
    logger.warning(f"Ollama integration not available (error): {e}")

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
# Cache OCR pipelines to avoid reinitialization
if 'ocr_pipelines' not in st.session_state:
    st.session_state.ocr_pipelines = {}


def get_ocr_pipeline(ocr_engine):
    """Get or create cached OCR pipeline instance"""
    engine_map = {
        "PaddleOCR": "paddleocr",
        "Tesseract": "tesseract",
        "EasyOCR": "easyocr"
    }

    engine_key = engine_map[ocr_engine]

    # Check if pipeline already exists in cache
    if engine_key not in st.session_state.ocr_pipelines:
        try:
            from preprocessing.ocr_pipeline import OCRPipeline
            st.session_state.ocr_pipelines[engine_key] = OCRPipeline(
                ocr_engine=engine_key,
                output_format='json'
            )
            logger.info(f"Created new {ocr_engine} pipeline instance")
        except Exception as e:
            logger.error(f"Failed to initialize {ocr_engine}: {str(e)}")
            raise

    return st.session_state.ocr_pipelines[engine_key]


def process_with_ocr(image_array, ocr_engine, use_preprocessing, confidence_threshold):
    """Process image with selected OCR engine"""
    try:
        # Get cached pipeline instance
        pipeline = get_ocr_pipeline(ocr_engine)

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
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        raise  # Don't use mock data, raise the error so we can see what's wrong


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
st.title("SmartDeal")
st.markdown("Automatic extraction of product deals from supermarket brochures")

# Sidebar
with st.sidebar:
    st.header("Settings")

    # Extraction Method Selection
    st.subheader("Method")

    extraction_methods = []
    # Order: Gemini -> OCR -> Ollama
    if GEMINI_AVAILABLE:
        extraction_methods.append("Gemini AI")
    extraction_methods.append("OCR")
    if OLLAMA_AVAILABLE:
        extraction_methods.append("Ollama VLM")

    extraction_method = st.radio("Choose extraction method", extraction_methods, index=0)

    use_gemini = extraction_method == "Gemini AI"
    use_ollama = extraction_method == "Ollama VLM"

    # Gemini Configuration
    if use_gemini:
        st.markdown("---")
        st.subheader("Gemini Configuration")

        gemini_api_key = st.text_input("API Key", type="password", placeholder="Enter your Gemini API key")

        if gemini_api_key:
            # Test connection
            if st.button("Test Connection"):
                with st.spinner("Testing..."):
                    if test_gemini_connection(gemini_api_key):
                        st.success("API key is valid")
                    else:
                        st.error("Invalid API key")

            # Model selection
            gemini_model = st.selectbox(
                "Model",
                [
                    "gemini-2.5-pro",
                    "gemini-2.5-flash",
                    "gemini-2.5-flash-lite",
                    "gemini-2.0-flash-exp",
                    "gemini-1.5-pro",
                    "gemini-1.5-flash"
                ]
            )
        else:
            st.warning("Please enter your API key")
            st.caption("Get a free API key at: https://aistudio.google.com/apikey")

    elif not GEMINI_AVAILABLE:
        st.info("Install: pip install google-generativeai")


    # Ollama VLM Configuration
    if use_ollama:
        st.markdown("---")
        st.subheader("Ollama Configuration")

        if OLLAMA_AVAILABLE:
            # Get available models
            ollama_models = get_available_ollama_models()

            # Model selection
            model_options = [f"{m['name']} - {m['description']}" for m in ollama_models]

            selected_ollama_idx = st.selectbox(
                "Model",
                range(len(model_options)),
                format_func=lambda i: model_options[i]
            )

            selected_ollama_model = ollama_models[selected_ollama_idx]
            ollama_model_id = selected_ollama_model['model_id']

            # Check if model is downloaded
            if selected_ollama_model['downloaded']:
                st.success("Model ready")
            else:
                st.info(f"Will download on first use ({selected_ollama_model['size']})")

        else:
            st.error("Ollama not available")
            st.code("brew install ollama && pip install ollama")
    elif not OLLAMA_AVAILABLE:
        if use_ollama:
            st.info("Install: brew install ollama && pip install ollama")

    # OCR Settings (only if not using Gemini or Ollama)
    if not use_gemini and not use_ollama:
        st.markdown("---")
        st.subheader("OCR Settings")
        ocr_engine = st.selectbox("Engine", ["Tesseract", "EasyOCR"])
    else:
        ocr_engine = None

    # Preprocessing option
    use_preprocessing = st.checkbox("Image Preprocessing", value=True)

    # Confidence threshold
    confidence_threshold = st.slider("Confidence", 0.0, 1.0, 0.5, 0.05)

    # Deal extraction method (hidden for Gemini/Ollama)
    if not use_gemini and not use_ollama:
        st.markdown("---")
        st.subheader("Deal Extraction")

        if ADVANCED_CLUSTERING_AVAILABLE:
            extraction_method = st.radio("Method", ["Advanced", "Region-based", "Distance-based"])
            use_advanced_clustering = extraction_method == "Advanced"
            use_region_clustering = extraction_method == "Region-based"
        elif REGION_CLUSTERING_AVAILABLE:
            extraction_method = st.radio("Method", ["Region-based", "Distance-based"])
            use_advanced_clustering = False
            use_region_clustering = extraction_method == "Region-based"
        else:
            use_advanced_clustering = False
            use_region_clustering = False
    else:
        use_advanced_clustering = False
        use_region_clustering = False

    # Display options
    st.markdown("---")
    st.subheader("Display")

    show_bboxes = st.checkbox("Bounding Boxes", value=True)
    show_text = st.checkbox("Text Labels", value=True)
    show_confidence = st.checkbox("Confidence", value=False)
    show_debug = st.checkbox("Debug Info", value=False)

    st.markdown("---")
    st.markdown("### Statistics")

    if st.session_state.ocr_results:
        st.metric("Text Boxes", st.session_state.ocr_results['num_boxes'])

        if st.session_state.entities:
            total_entities = sum(len(v) for v in st.session_state.entities.values())
            st.metric("Entities", total_entities)

        if st.session_state.deals:
            st.metric("Deals", len(st.session_state.deals))

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Upload", "Data", "Analysis", "History"])

# Tab 1: Upload & Process
with tab1:
    st.subheader("Upload Brochure")

    uploaded_file = st.file_uploader(
        "Choose a brochure image or PDF",
        type=['png', 'jpg', 'jpeg', 'pdf']
    )

    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.success(f"File: {uploaded_file.name}")
        with col2:
            st.info(f"Size: {uploaded_file.size / 1024:.1f} KB")
        with col3:
            if st.button("Reset"):
                st.session_state.ocr_results = None
                st.session_state.processed_image = None
                st.session_state.entities = None
                st.session_state.deals = None
                st.session_state.pdf_page_count = None
                st.session_state.selected_page = None
                st.rerun()

        # Check if PDF
        is_pdf = uploaded_file.name.lower().endswith('.pdf')

        if is_pdf:
            # Handle PDF file
            st.info("PDF file detected")

            # Save PDF temporarily
            temp_pdf_path = f"/tmp/{uploaded_file.name}"
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Get page count
            if 'pdf_page_count' not in st.session_state or st.session_state.pdf_page_count is None:
                try:
                    from preprocessing.pdf_processor import PDFProcessor
                    pdf_processor = PDFProcessor()
                    page_count = pdf_processor.get_page_count(temp_pdf_path)
                    st.session_state.pdf_page_count = page_count
                except Exception as e:
                    st.error(f"Error reading PDF: {str(e)}")
                    st.info("Make sure pypdfium2 is installed: pip install pypdfium2")
                    page_count = 0

            page_count = st.session_state.pdf_page_count

            if page_count > 0:
                st.success(f"PDF has {page_count} page(s)")

                # Page selection
                if page_count > 1:
                    selected_page = st.slider(
                        "Select page to process",
                        min_value=1,
                        max_value=page_count,
                        value=1,
                        help="Choose which page of the PDF to process"
                    )
                else:
                    selected_page = 1

                st.session_state.selected_page = selected_page

                # Convert PDF page to image
                try:
                    from preprocessing.pdf_processor import PDFProcessor
                    pdf_processor = PDFProcessor()
                    img_array = pdf_processor.get_page_image(temp_pdf_path, selected_page)

                    if img_array is not None:
                        image = Image.fromarray(img_array)
                    else:
                        st.error("Failed to convert PDF page to image")
                        image = None
                        img_array = None

                except Exception as e:
                    st.error(f"Error converting PDF: {str(e)}")
                    st.info("Try installing: pip install pypdfium2")
                    image = None
                    img_array = None
            else:
                image = None
                img_array = None

        else:
            # Handle image file
            image = Image.open(uploaded_file)
            img_array = np.array(image)

        # Display images side by side
        if image is not None and img_array is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📸 Original Image")
                if is_pdf and page_count > 1:
                    st.caption(f"Page {selected_page} of {page_count}")
                st.image(image, use_column_width=True)

            with col2:
                st.subheader("Processed Result")

                # Process button
                if use_gemini:
                    button_label = "Extract with Gemini AI"
                    button_disabled = not gemini_api_key
                elif use_ollama:
                    button_label = f"Extract with {selected_ollama_model['name']}"
                    button_disabled = not OLLAMA_AVAILABLE
                else:
                    button_label = "Extract Information"
                    button_disabled = False

                if st.button(button_label, type="primary", use_container_width=True, disabled=button_disabled):
                    if use_gemini:
                        # Gemini AI extraction
                        with st.spinner(f"Processing with {gemini_model}..."):
                            try:
                                result = extract_with_gemini(
                                    img_array,
                                    api_key=gemini_api_key,
                                    model=gemini_model,
                                    language="German"
                                )

                                # Store results
                                deals = result['deals']
                                st.session_state.deals = deals
                                st.session_state.ocr_results = {
                                    'num_boxes': 0,
                                    'text_boxes': [],
                                    'source': 'gemini'
                                }
                                st.session_state.entities = {
                                    'products': [],
                                    'prices': [],
                                    'discounts': [],
                                    'units': [],
                                    'dates': [],
                                    'other': []
                                }
                                st.session_state.processed_image = None

                                st.success(f"Gemini extracted {len(deals)} deals!")

                            except Exception as e:
                                st.error(f"Gemini extraction failed: {str(e)}")
                                import traceback
                                st.error(f"Details: {traceback.format_exc()}")

                    elif use_ollama:
                        # Ollama VLM extraction
                        spinner_text = f"🦙 Processing with {selected_ollama_model['name']}..."
                        if not selected_ollama_model['downloaded']:
                            spinner_text += " (First use: downloading model...)"

                        with st.spinner(spinner_text):
                            try:
                                result = extract_with_ollama(
                                    img_array,
                                    model_id=ollama_model_id,
                                    language="German"
                                )

                                # Store results
                                deals = result['deals']
                                st.session_state.deals = deals
                                st.session_state.ocr_results = {
                                    'num_boxes': 0,
                                    'text_boxes': [],
                                    'source': 'ollama'
                                }
                                st.session_state.entities = {
                                    'products': [],
                                    'prices': [],
                                    'discounts': [],
                                    'units': [],
                                    'dates': [],
                                    'other': []
                                }
                                st.session_state.processed_image = None

                                # Success message
                                st.success(f"{selected_ollama_model['name']} successfully extracted {len(deals)} products!")
                                if len(deals) > 0:
                                    st.info(f"Estimated accuracy: ~90% | Method: Ollama VLM (Local AI)")

                            except Exception as e:
                                st.error(f"Ollama extraction failed: {str(e)}")
                                st.warning("Suggestion: Try switching to another model, or use Gemini AI / Advanced OCR")
                                import traceback
                                st.error(f"Details: {traceback.format_exc()}")

                    else:
                        # Traditional OCR extraction
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

                            # Create deals using selected method
                            if use_advanced_clustering and ADVANCED_CLUSTERING_AVAILABLE:
                                # Best method: Advanced region-based with smart heuristics
                                deals = create_deals_advanced(ocr_results['text_boxes'])
                            elif use_region_clustering and REGION_CLUSTERING_AVAILABLE:
                                # Good method: Region-based clustering
                                deals = create_deals_from_regions(
                                    ocr_results['text_boxes'],
                                    eps=120,  # Distance threshold for clustering
                                    min_samples=2  # Minimum boxes per region
                                )
                            else:
                                # Old method: Distance-based matching
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

                        st.success("Processing complete!")
                        st.rerun()

                # Display processed image
                if st.session_state.processed_image is not None:
                    st.image(st.session_state.processed_image, use_column_width=True)
                elif st.session_state.ocr_results is not None and not show_bboxes:
                    st.image(image, use_column_width=True)
                else:
                    st.info("Click 'Extract Information' to start")
        else:
            st.warning("Unable to load image. Please try a different file.")

# Tab 2: Extracted Data
with tab2:
    st.subheader("Extracted Data")

    if st.session_state.ocr_results is None:
        st.info("Upload and process an image first")
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

        # Debug information
        if show_debug and st.session_state.ocr_results:
            with st.expander("Debug: All OCR Text (Raw Output)", expanded=False):
                st.markdown("**All text boxes detected by OCR:**")
                debug_data = []
                for i, box in enumerate(st.session_state.ocr_results.get('text_boxes', [])[:50], 1):
                    debug_data.append({
                        '#': i,
                        'Text': box['text'],
                        'Confidence': f"{box['confidence']:.2f}",
                        'Length': len(box['text']),
                        'Has €': '€' in box['text'],
                        'Has %': '%' in box['text'],
                        'Has digits': any(c.isdigit() for c in box['text'])
                    })

                df_debug = pd.DataFrame(debug_data)
                st.dataframe(df_debug, use_column_width=True, hide_index=True)

                st.markdown("**Tip:** Look for price-like text that has € symbol or decimals")
                st.markdown("**If prices are missing:**")
                st.markdown("- Check if € symbol is recognized correctly")
                st.markdown("- Look for decimal numbers (e.g., 1.99, 2,50)")
                st.markdown("- Price patterns may need adjustment")

        st.markdown("---")

        # Entity breakdown
        if st.session_state.entities:
            st.subheader("Entities by Type")

            # Create tabs for each entity type
            entity_tabs = st.tabs([
                "Products",
                "Prices",
                "Discounts",
                "Units",
                "Dates",
                "All Data"
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
    st.subheader("Identified Deals")

    if st.session_state.deals is None:
        st.info("Process an image first")
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
                        if deal.get('price'):
                            st.markdown(f"**€{deal['price']}**")
                        else:
                            st.markdown("_Not detected_")

                    with col3:
                        st.markdown("**Discount**")
                        if deal.get('discount'):
                            st.markdown(f"**{deal['discount']}**")
                        else:
                            st.markdown("_No discount_")

                    if deal.get('unit'):
                        st.markdown(f"Unit: {deal['unit']}")

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
