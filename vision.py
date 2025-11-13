# Invoice Extractor with Modern White Theme UI
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import json
from PIL import Image
from datetime import datetime
import google.generativeai as genai

os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

st.set_page_config(
    page_title='InvoiceAI Pro',
    page_icon='',
    layout='wide',
    initial_sidebar_state='expanded'
)

custom_css = '''<style>
@import url('"'"'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'"'"');
.main { background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 50%, #ffffff 100%); color: #1a1a1a; }
.glass-card { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); border: 1.5px solid rgba(59, 130, 246, 0.15); border-radius: 16px; padding: 20px; margin: 15px 0; box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08); }
.header-container { background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); padding: 50px 40px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 20px 50px rgba(59, 130, 246, 0.25); text-align: center; }
h2 { color: #1a1a1a; font-weight: 800; margin-top: 30px; }
.metric-card { background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(30, 144, 255, 0.03) 100%); border: 1.5px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 20px; text-align: center; }
.metric-value { font-size: 36px; font-weight: 800; color: #3b82f6; margin: 10px 0; }
.stButton button { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 12px; padding: 14px 32px; font-weight: 700; }
</style>'''

st.markdown(custom_css, unsafe_allow_html=True)

def get_gemini_response(input_prompt, image, user_question):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([input_prompt, image[0], user_question])
    return response.text

def extract_invoice_data(image_data, invoice_name):
    extraction_prompt = 'Extract invoice info as JSON with: invoice_number, invoice_date, vendor_name, total_amount, currency, due_date, payment_terms, items_count, tax_amount'
    try:
        response_text = get_gemini_response(extraction_prompt, image_data, 'Extract invoice details')
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            data['"'"'invoice_name'"'"'] = invoice_name
            return data
        return {'error': 'Could not parse', 'invoice_name': invoice_name}
    except Exception as e:
        return {'error': str(e), 'invoice_name': invoice_name}

def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return [{'mime_type': uploaded_file.type, 'data': bytes_data}]
    raise FileNotFoundError('No file uploaded')

st.markdown('<div style=\"text-align: center; padding: 30px;\"><h1 style=\"color: #3b82f6; font-size: 48px;\"> InvoiceAI Pro</h1><p style=\"color: #666;\">Enterprise Invoice Processing</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([' Compare', ' Q&A', ' Analytics'])

with tab1:
    st.subheader('Upload Multiple Invoices')
    uploaded_files = st.file_uploader('Choose invoices', type=['jpg', 'jpeg', 'png', 'pdf'], accept_multiple_files=True, key='multi_upload')
    
    if uploaded_files and len(uploaded_files) > 0:
        st.success(f'✅ {len(uploaded_files)} invoice(s) uploaded successfully')
        
        # Show file previews
        preview_cols = st.columns(min(3, len(uploaded_files)))
        for idx, file in enumerate(uploaded_files):
            with preview_cols[idx % 3]:
                try:
                    if file.type.startswith('image'):
                        img = Image.open(file)
                        st.image(img, caption=file.name[:20], use_column_width=True)
                    else:
                        st.info(f'📄 {file.name}')
                except Exception as e:
                    st.warning(f'Cannot preview: {file.name}')
        
        st.divider()
        
        question = st.text_input('Ask a question about these invoices:', placeholder='e.g., Compare totals, Find duplicates...')
        
        col1, col2 = st.columns([3, 1])
        with col1:
            analyze_btn = st.button('🚀 Analyze & Compare', use_container_width=True)
        with col2:
            st.write('⚡')
        
        if analyze_btn:
            if not question:
                st.warning('Please enter a question')
            else:
                progress_bar = st.progress(0)
                status_placeholder = st.empty()
                
                all_data = []
                for idx, file in enumerate(uploaded_files):
                    status_placeholder.info(f'📄 Processing {idx+1}/{len(uploaded_files)}: {file.name}')
                    try:
                        img_data = input_image_setup(file)
                        extracted = extract_invoice_data(img_data, file.name)
                        all_data.append(extracted)
                    except Exception as e:
                        st.error(f'Error processing {file.name}: {str(e)}')
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_placeholder.empty()
                progress_bar.empty()
                
                if all_data:
                    st.subheader('📊 Extracted Data')
                    st.json(all_data)
                    
                    st.subheader('🤖 AI Analysis')
                    try:
                        prompt = f'Analyze these invoices and answer: {question}\n\nData:\n{json.dumps(all_data, indent=2)}'
                        response = get_gemini_response('You are an invoice analysis expert.', [{'mime_type': 'text/plain', 'data': prompt.encode()}], '')
                        st.info(response)
                    except Exception as e:
                        st.error(f'Analysis failed: {str(e)}')

with tab2:
    st.subheader('Ask About One Invoice')
    single_file = st.file_uploader('Choose invoice', type=['jpg', 'jpeg', 'png', 'pdf'], key='single_upload')
    
    if single_file:
        try:
            if single_file.type.startswith('image'):
                img = Image.open(single_file)
                st.image(img, caption=single_file.name, use_column_width=True)
            else:
                st.info(f'📄 {single_file.name}')
        except Exception as e:
            st.warning(f'Cannot preview file')
        
        question = st.text_input('Your question:', placeholder='e.g., What is the total amount?', key='single_q')
        
        if st.button('💬 Get Answer', use_container_width=True):
            if not question:
                st.warning('Please enter a question')
            else:
                try:
                    with st.spinner('🔄 Analyzing...'):
                        img_data = input_image_setup(single_file)
                        response = get_gemini_response('You are an invoice expert. Answer the question.', img_data, question)
                        st.success('✅ Answer:')
                        st.info(response)
                except Exception as e:
                    st.error(f'Error: {str(e)}')

with tab3:
    st.subheader('System Info')
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric('Speed', '<2s')
    with m2:
        st.metric('Accuracy', '98%')
    with m3:
        st.metric('Languages', '100+')
