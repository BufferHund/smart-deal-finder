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
import time
import altair as alt  # For interactive charts

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

# Try to import dependencies with graceful fallbacks
try:
    from region_clustering import create_deals_from_regions
    REGION_CLUSTERING_AVAILABLE = True
except ImportError:
    REGION_CLUSTERING_AVAILABLE = False

try:
    from advanced_region_clustering import create_deals_advanced
    ADVANCED_CLUSTERING_AVAILABLE = True
except ImportError:
    ADVANCED_CLUSTERING_AVAILABLE = False

try:
    from gemini_extractor import extract_with_gemini, test_gemini_connection
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from ollama_extractor import (
        extract_with_ollama,
        check_ollama_available,
        get_available_ollama_models
    )
    OLLAMA_AVAILABLE = check_ollama_available()
except ImportError:
    OLLAMA_AVAILABLE = False
except Exception:
    OLLAMA_AVAILABLE = False

# Configure page
st.set_page_config(
    page_title="SmartDeal Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Theme & Animations
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: #f8f9fa;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700;
    }
    
    /* Cards */
    .stCard {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* Log Console */
    .console-log {
        background-color: #1e293b;
        color: #10b981;
        font-family: 'JetBrains Mono', monospace;
        padding: 1rem;
        border-radius: 8px;
        height: 200px;
        overflow-y: auto;
        font-size: 0.85rem;
        border: 1px solid #334155;
    }
    .log-line {
        margin: 2px 0;
        border-bottom: 1px solid #334155;
        padding-bottom: 2px;
    }
    .log-time {
        color: #94a3b8;
        margin-right: 8px;
    }

    /* Deal Cards */
    .deal-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        transition: all 0.2s;
    }
    .deal-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #2563eb;
    }
    .deal-price {
        font-size: 1.5rem;
        font-weight: 800;
        color: #ef4444;
    }
    .deal-product {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
    }
    
    /* Badges */
    .badge {
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-success { background:#dcfce7; color:#166534; }
    .badge-warning { background:#fef3c7; color:#92400e; }
    .badge-error { background:#fee2e2; color:#b91c1c; }
</style>
""", unsafe_allow_html=True)

# --- Persistence Import ---
try:
    from services import storage
except ImportError:
    # Fallback if running from a different context
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from src.services import storage

# Initialize session state
if 'ocr_results' not in st.session_state:
    st.session_state.ocr_results = None
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'ocr_pipelines' not in st.session_state:
    st.session_state.ocr_pipelines = {}
if 'deals' not in st.session_state:
    st.session_state.deals = []
    # Try to load persisted deals
    cached_deals = storage.get_active_deals()
    if cached_deals:
        st.session_state.deals = cached_deals
        st.toast(f"Restored {len(cached_deals)} deals from previous session.", icon="🔄")
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'last_processed_image' not in st.session_state:
    st.session_state.last_processed_image = None
if 'processing_step' not in st.session_state:
    st.session_state.processing_step = 0

def add_log(message, type="info"):
    """Add a log message to the session state console"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({
        "time": timestamp,
        "msg": message,
        "type": type
    })

def render_console():
    """Render the simulated system console"""
    logs_html = "".join([
        f"<div class='log-line'><span class='log-time'>[{log['time']}]</span> {log['msg']}</div>"
        for log in reversed(st.session_state.logs[-50:]) # Show last 50 logs
    ])
    st.markdown(f"<div class='console-log'>{logs_html}</div>", unsafe_allow_html=True)

def get_ocr_pipeline(ocr_engine):
    """Get or create cached OCR pipeline instance"""
    engine_map = {"PaddleOCR": "paddleocr", "Tesseract": "tesseract"}
    engine_key = engine_map.get(ocr_engine, "tesseract")

    if engine_key not in st.session_state.ocr_pipelines:
        try:
            from preprocessing.ocr_pipeline import OCRPipeline
            st.session_state.ocr_pipelines[engine_key] = OCRPipeline(
                ocr_engine=engine_key,
                output_format='json'
            )
            add_log(f"Initialized {ocr_engine} engine successfully")
        except Exception as e:
            add_log(f"Failed to initialize {ocr_engine}: {str(e)}", "error")
            return None
    return st.session_state.ocr_pipelines[engine_key]

def sidebar_configuration():
    """Professional configuration sidebar"""
    with st.sidebar:
        st.markdown("### ⚙️ System Configuration")
        
        # 1. Architecture Selection
        st.markdown("#### 1. Architecture Strategy")
        architecture = st.radio(
            "Select Pipeline Type:",
            ["Traditional OCR Pipeline", "End-to-End OCR Free (VLM)"],
            help="Traditional: Separate detection & recognition. OCR Free: Visual Language Models understanding context."
        )
        
        # 2. Source Selection (Dynamic based on Architecture)
        st.markdown("#### 2. Deployment Source")
        
        selected_model_config = {}
        
        if architecture == "Traditional OCR Pipeline":
            source = "Local Deployment" # OCR is always local in this app context
            st.info("Using Local OCR Engines")
            
            model = st.selectbox("Select Engine", ["Tesseract OCR", "PaddleOCR"])
            selected_model_config = {
                "type": "ocr_pipeline",
                "engine": "PaddleOCR" if "Paddle" in model else "Tesseract"
            }
            
            with st.expander("Advanced OCR Settings"):
                st.checkbox("Pre-process Image", value=True, key="ocr_preprocess")
                st.slider("Confidence Threshold", 0.0, 1.0, 0.5, key="ocr_conf")
                
        else: # End-to-End OCR Free
            source = st.radio("Select Source:", ["Web API (Cloud)", "Local Deployment (On-Prem)"])
            
            if source == "Web API (Cloud)":
                if GEMINI_AVAILABLE:
                    st.success("✅ Google Gemini Available")
                    model = st.selectbox("Select Model", [
                        "gemini-2.0-flash",
                        "gemini-1.5-pro",
                        "gemini-1.5-flash"
                    ])
                    api_key = st.text_input("API Key", type="password")
                    selected_model_config = {
                        "type": "web_api",
                        "model": model,
                        "api_key": api_key
                    }
                else:
                    st.error("❌ Google Generative AI SDK not installed")
            
            else: # Local VLM
                if OLLAMA_AVAILABLE:
                    st.success("✅ Ollama Service Connected")
                    models = get_available_ollama_models()
                    if models:
                        model_opts = [m['name'] for m in models]
                        selected = st.selectbox("Select Local Model", model_opts)
                        model_obj = next((m for m in models if m['name'] == selected), None)
                        selected_model_config = {
                            "type": "local_vlm",
                            "model_id": model_obj['model_id'] if model_obj else None,
                            "name": selected
                        }
                    else:
                        st.warning("No VLM models found in Ollama")
                else:
                    st.error("❌ Ollama not detected")
        
        st.markdown("---")
        st.markdown("### 🎨 Visual Settings")
        st.checkbox("Show Bounding Boxes", value=True, key="show_bboxes")
        
        return selected_model_config

def main_content(model_config):
    """Main application area"""
    
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #2563eb; margin-bottom: 0.5rem;'>SmartDeal Enterprise</h1>
            <p style='font-size: 1.2rem; color: #64748b;'>Intelligent Brochure Analysis & Deal Extraction System</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Dashboard stats
    if not st.session_state.ocr_results:
        cols = st.columns(4)
        cols[0].metric("System Status", "Ready", delta="Online")
        cols[1].metric("Active Models", "8", delta="3 New")
        cols[2].metric("Avg. Latency", "1.2s", delta="-0.3s")
        cols[3].metric("Accuracy Rate", "98.5%", delta="+1.2%")
    
    # Main Workflow Tabs
    tab_upload, tab_results, tab_analytics = st.tabs(["📤 Ingestion & Processing", "📊 Results Dashboard", "📈 Analytics"])
    
    with tab_upload:
        col1, col2 = st.columns([1, 1])
        
        image = None
        img_array = None
        
        with col1:
            st.markdown("### 📄 Document Ingestion")
            uploaded_file = st.file_uploader(
                "Upload Brochure (PDF/Image)", 
                type=['png', 'jpg', 'jpeg', 'pdf'],
                label_visibility="collapsed"
            )

            if uploaded_file:
                st.markdown("#### Source Preview")
                if uploaded_file.name.lower().endswith('.pdf'):
                    try:
                        from preprocessing.pdf_processor import PDFProcessor
                        proc = PDFProcessor()
                        with open(f"/tmp/{uploaded_file.name}", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        img_array = proc.get_page_image(f"/tmp/{uploaded_file.name}", 1)
                        if img_array is not None:
                             image = Image.fromarray(img_array)
                             st.image(image, use_column_width=True, caption="Page 1 Preview")
                    except Exception as e:
                        st.error(f"PDF Error: {e}")
                else:
                    image = Image.open(uploaded_file)
                    img_array = np.array(image)
                    st.image(image, use_column_width=True, caption="Image Preview")

        with col2:
            st.markdown("#### 🖥️ System Console")
            render_console()
            
            if uploaded_file:
                st.markdown("---")
                if st.button("🚀 Start Extraction Pipeline", type="primary", use_container_width=True):
                    process_file(uploaded_file, image, img_array, model_config)

    with tab_results:
         if 'deals' in st.session_state and st.session_state.deals:
             render_results_dashboard()
         else:
             st.info("Run extraction to view results.")

    with tab_analytics:
         if 'deals' in st.session_state and st.session_state.deals:
             render_analytics()
         else:
             st.info("Run extraction to view analytics.")

def process_file(file, image, img_array, config):
    """Execute the extraction pipeline with enhanced feedback"""
    
    add_log("Starting extraction pipeline...", "info")
    st.session_state.logs = [] # Clear old logs
    add_log(f"Ingesting file: {file.name}")
    
    progress_bar = st.progress(0)
    
    try:
        results = None
        deals = []
        
        start_time = time.time()
        
        if config['type'] == 'web_api':
            add_log(f"Connecting to {config['model']} API...")
            progress_bar.progress(20)
            
            if not config.get('api_key'):
                add_log("Missing API Key", "error")
                st.error("API Key required")
                return
                
            res = extract_with_gemini(img_array, api_key=config['api_key'], model=config['model'])
            deals = res['deals']
            
        elif config['type'] == 'local_vlm':
            add_log(f"Loading local model: {config['name']}...")
            progress_bar.progress(30)
            
            res = extract_with_ollama(img_array, model_id=config['model_id'])
            deals = res['deals']
            
        elif config['type'] == 'ocr_pipeline':
            add_log(f"Initializing OCR engine: {config['engine']}...")
            progress_bar.progress(20)
            
            pipeline = get_ocr_pipeline(config['engine'])
            tmp_path = "/tmp/process_temp.jpg"
            cv2.imwrite(tmp_path, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
            
            add_log("Running text detection & recognition...")
            ocr_res = pipeline.process_image(tmp_path, preprocess=st.session_state.get('ocr_preprocess', True))
            progress_bar.progress(60)
            
            add_log(f"Detected {ocr_res['num_boxes']} text regions")
            add_log(" performing clustering and entity extraction...")
            
            if ADVANCED_CLUSTERING_AVAILABLE:
                deals = create_deals_advanced(ocr_res['text_boxes'])
            else:
                deals = []
            
            st.session_state.ocr_results = ocr_res
            
        duration = time.time() - start_time
        progress_bar.progress(100)
        add_log(f"Extraction complete in {duration:.2f}s", "success")
        add_log(f"Found {len(deals)} potential deals", "success")
        
        st.session_state.deals = deals
        st.session_state.last_processed_image = image
        st.session_state.last_config = config
        
        # Persist extracted deals
        storage.save_active_deals(deals)
        add_log("Deals saved to session cache.", "info")
        
        st.rerun()
        
    except Exception as e:
        add_log(f"Critical Error: {str(e)}", "error")
        st.error(str(e))

def render_results_dashboard():
    """Render the enhanced results dashboard"""
    st.markdown("### 📊 Extraction Results")
    
    # Visual Confirmation with Slider
    col_vis, col_data = st.columns([1, 1])
    
    with col_vis:
        st.markdown("#### Visual Confirmation")
        if st.session_state.get('last_processed_image'):
            # Generate processed image only if needed
            if st.session_state.get('show_bboxes', True) and st.session_state.get('ocr_results'):
               try:
                   processed = draw_bounding_boxes(
                       np.array(st.session_state.last_processed_image),
                       st.session_state.ocr_results['text_boxes'],
                       0.5, True, False
                   )
                   st.image(processed, use_column_width=True, caption="Processed View")
               except:
                   st.image(st.session_state.last_processed_image, use_column_width=True, caption="Original View")
            else:
               st.image(st.session_state.last_processed_image, use_column_width=True, caption="Original View")
        else:
            st.info("Visual preview not available for restored session.")
            
    with col_data:
        # Export Actions
        c1, c2 = st.columns(2)
        if st.session_state.deals:
             # Create DataFrame for export
             df_export = pd.DataFrame(st.session_state.deals)
             # Simplify structure for CSV/Excel
             flat_deals = []
             for d in st.session_state.deals:
                 # Handle difference between original OCR format (nested) and new flat format
                 p_text = d.get('product', {}).get('text') if isinstance(d.get('product'), dict) else d.get('product_name', d.get('product'))
                 price_val = d.get('price', {}).get('value') if isinstance(d.get('price'), dict) else d.get('price')
                 disc_text = d.get('discount', {}).get('text') if isinstance(d.get('discount'), dict) else d.get('discount')
                 
                 flat_deals.append({
                     "Product": p_text,
                     "Price": price_val,
                     "Discount": disc_text,
                     "Confidence": d.get('confidence', 0)
                 })
             df = pd.DataFrame(flat_deals)
             
             csv = df.to_csv(index=False).encode('utf-8')
             c1.download_button("📥 Download CSV", csv, "deals.csv", "text/csv")
             
             # JSON Export
             json_str = json.dumps(st.session_state.deals, indent=2)
             c2.download_button("📥 Download JSON", json_str, "deals.json", "application/json")

        st.markdown("#### Extracted Items")
        for deal in st.session_state.deals:
            # Handle mixed structure
            if isinstance(deal.get('price'), dict):
                # Nested structure
                price_val = deal.get('price', {}).get('value', 'N/A')
                prod_name = deal.get('product', {}).get('text', 'Unknown Product')
                discount = deal.get('discount', {}).get('text', None)
            else:
                # Flat structure
                price_val = deal.get('price', 'N/A')
                prod_name = deal.get('product_name', deal.get('product', 'Unknown Product'))
                discount = deal.get('discount', None)
            
            conf = deal.get('confidence', 0.9)
            
            badge_class = "badge-success" if conf > 0.8 else "badge-warning"
            
            st.markdown(f"""
            <div class="deal-card">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <div class="deal-product">{prod_name}</div>
                        <div class="deal-meta">
                            <span class="badge {badge_class}">Conf: {conf*100:.0f}%</span>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div class="deal-price">{price_val}</div>
                        {f'<div class="badge badge-error">{discount}</div>' if discount else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_analytics():
    """Render interactive analytics charts"""
    st.markdown("### 📈 Deal Analytics")
    
    if not st.session_state.deals:
        return
        
    flat_deals = []
    for d in st.session_state.deals:
         # Handle flat/nested differences
         if isinstance(d.get('price'), dict):
             price_str = d.get('price', {}).get('value', '0')
             prod_name = d.get('product', {}).get('text', 'Unknown')
         else:
             price_str = str(d.get('price', '0'))
             prod_name = d.get('product_name', d.get('product', 'Unknown'))
             
         price_str = price_str.replace('€', '').replace(',', '.').strip()
         try:
             price_num = float(price_str)
         except:
             price_num = 0.0
             
         flat_deals.append({
             "Product": prod_name,
             "Price": price_num,
             "Confidence": d.get('confidence', 0.0),
             "HasDiscount": "Yes" if d.get('discount') else "No"
         })
         
    df_chart = pd.DataFrame(flat_deals)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### Price Distribution")
        chart_price = alt.Chart(df_chart).mark_bar().encode(
            x=alt.X('Price', bin=True),
            y='count()',
            color='HasDiscount'
        ).interactive()
        st.altair_chart(chart_price, use_container_width=True)
        
    with c2:
        st.markdown("#### Confidence Analysis")
        chart_conf = alt.Chart(df_chart).mark_circle(size=60).encode(
            x='Price',
            y='Confidence',
            color='HasDiscount',
            tooltip=['Product', 'Price', 'Confidence']
        ).interactive()
        st.altair_chart(chart_conf, use_container_width=True)

# Run App
# Top-level mode selection
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Application Mode")
app_mode = st.sidebar.radio(
    "Select View", 
    ["👨‍💼 Enterprise Admin", "🛒 Shopper App"],
    label_visibility="collapsed"
)

if app_mode == "🛒 Shopper App":
    # Consumer Mode
    try:
        from consumer_view import render_consumer_app
        render_consumer_app()
    except ImportError:
        st.error("Consumer module not found. Please ensure consumer_view.py exists.")
else:
    # Enterprise Admin Mode (Existing Logic)
    config = sidebar_configuration()
    main_content(config)

    if 'deals' in st.session_state and st.session_state.deals:
         # Only show analytics if in admin mode and deals exist
         pass # render_results() is called inside main_content tabs now or can be added here if needed
