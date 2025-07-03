import streamlit as st
import sys
import os
import time

# Add the parent directory to the path to import qa_chain
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from rag.qa_chain import MedicalQASystem

# Nordic minimalist CSS styling
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Root styling */
    .stApp {
        background: #FFFFFF;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
    }
    
    /* Main container */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1.5rem 2rem;
    }
    
    /* Headers */
    .main-title {
        font-size: 2.5rem;
        font-weight: 300;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .subtitle {
        font-size: 1.1rem;
        font-weight: 300;
        color: #7F8C8D;
        text-align: center;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border: 1px solid #E8E8E8;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        font-size: 1rem;
        background: #FAFAFA;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #95A5A6;
        box-shadow: 0 0 0 3px rgba(149, 165, 166, 0.1);
        background: #FFFFFF;
    }
    
    /* Button styling */
    .stButton > button {
        background: #34495E;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 400;
        transition: all 0.2s ease;
        width: 100%;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        background: #2C3E50;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(52, 73, 94, 0.2);
    }
    
    /* Results container */
    .result-container {
        background: #F8F9FA;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid #E9ECEF;
    }
    
    .answer-text {
        font-size: 1.1rem;
        line-height: 1.7;
        color: #2C3E50;
        margin-bottom: 2rem;
    }
    
    /* Sources styling */
    .sources-title {
        font-size: 1rem;
        font-weight: 500;
        color: #34495E;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #E8E8E8;
    }
    
    .source-item {
        background: white;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        border: 1px solid #E8E8E8;
        font-size: 0.9rem;
        color: #5D6D7E;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .source-header {
        font-weight: 600;
        color: #34495E;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }
    
    /* Status indicators */
    .status-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .status-item {
        display: flex;
        align-items: center;
        margin: 0 1rem;
        font-size: 0.9rem;
        color: #7F8C8D;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-connected {
        background: #2ECC71;
    }
    
    .status-disconnected {
        background: #E74C3C;
    }
    
    /* Loading animation */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    .loading-text {
        color: #7F8C8D;
        font-size: 1rem;
        margin-left: 1rem;
    }
    
    /* Metrics */
    .stMetric {
        background: white;
        border: 1px solid #E8E8E8;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stMetric > div {
        color: #2C3E50;
    }
    
    /* Spacing adjustments */
    .element-container {
        margin-bottom: 1.5rem;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-container {
            padding: 1rem 1rem;
        }
        
        .main-title {
            font-size: 2rem;
        }
        
        .status-container {
            flex-direction: column;
        }
        
        .status-item {
            margin: 0.25rem 0;
        }
        
        .source-item {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'qa_system' not in st.session_state:
        st.session_state.qa_system = None
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    if 'initialization_attempted' not in st.session_state:
        st.session_state.initialization_attempted = False

def display_system_status():
    """Display system connection status"""
    if st.session_state.system_ready:
        neo4j_status = "Connected"
        openai_status = "API Ready"
        status_class = "status-connected"
    else:
        neo4j_status = "Disconnected"
        openai_status = "Not Ready"
        status_class = "status-disconnected"
    
    st.markdown(f"""
    <div class="status-container">
        <div class="status-item">
            <div class="status-dot {status_class}"></div>
            Neo4j: {neo4j_status}
        </div>
        <div class="status-item">
            <div class="status-dot {status_class}"></div>
            OpenAI: {openai_status}
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.cache_resource
def initialize_qa_system():
    """Initialize QA system with caching"""
    try:
        qa_system = MedicalQASystem()
        qa_system.initialize()  # Call initialize method
        return qa_system
    except Exception as e:
        st.error(f"System initialization failed: {str(e)}")
        return None

def main():
    # Initialize session state
    init_session_state()
    
    # Main layout
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-title">MediGraph</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Medical Knowledge Graph Q&A System</p>', unsafe_allow_html=True)
    
    # System status
    display_system_status()
    
    # Initialize system if not already done
    if not st.session_state.initialization_attempted:
        with st.spinner("Initializing system..."):
            st.session_state.qa_system = initialize_qa_system()
            st.session_state.system_ready = st.session_state.qa_system is not None
            st.session_state.initialization_attempted = True
        
        if st.session_state.system_ready:
            st.rerun()
    
    # Main interface
    if st.session_state.system_ready:
        # Question input
        st.markdown("### Please enter your medical question")
        question = st.text_input(
            "",
            placeholder="e.g., What medications can treat hypertension?",
            key="question_input"
        )
        
        # Submit button
        if st.button("Get Answer", key="submit_btn"):
            if question.strip():
                process_question(question)
            else:
                st.warning("Please enter a question")
        
        # Example questions
        st.markdown("---")
        st.markdown("#### Example Questions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Diabetes treatment methods", key="example1"):
                process_question("Diabetes treatment methods")
        
        with col2:
            if st.button("Hypertension medication guide", key="example2"):
                process_question("Hypertension medication guide")
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("Heart disease prevention", key="example3"):
                process_question("Heart disease prevention")
        
        with col4:
            if st.button("Common drug side effects", key="example4"):
                process_question("Common drug side effects")
    
    else:
        st.markdown("""
        <div class="result-container">
            <div class="answer-text">
                System is initializing, please wait...
                <br><br>
                If there's no response for a long time, please check:
                <br>• Neo4j database is running properly
                <br>• OpenAI API key is correctly configured
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Reinitialize", key="retry_init"):
            st.session_state.initialization_attempted = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def process_question(question):
    """Process the user's question and display results"""
    with st.spinner("Analyzing question..."):
        start_time = time.time()
        
        try:
            # Call ask method instead of answer_question
            result = st.session_state.qa_system.ask(question)
            processing_time = time.time() - start_time
            
            # Convert data format to match display_results expected format
            formatted_result = {
                'answer': result['answer'],
                'sources': [
                    {
                        'content': doc['content'],
                        'metadata': doc.get('metadata', {})
                    }
                    for doc in result['source_documents']
                ]
            }
            
            # Display results
            display_results(formatted_result, processing_time)
            
        except Exception as e:
            st.error(f"Error processing question: {str(e)}")

def display_results(result, processing_time):
    """Display the QA results in Nordic minimalist style"""
    st.markdown(f"""
    <div class="result-container">
        <div class="answer-text">
            {result['answer']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display sources title as markdown instead of HTML
    st.markdown(f"### 📚 Reference Sources ({len(result['sources'])} items)")
    
    # Display sources with more detail
    for i, source in enumerate(result['sources'], 1):
        content = source['content']
        metadata = source.get('metadata', {})
        
        # Increase display length to 500 characters
        if len(content) > 500:
            display_content = content[:500] + "..."
        else:
            display_content = content
        
        # Get metadata information
        source_type = metadata.get('type', 'Unknown Type')
        source_name = metadata.get('name', 'Unknown Source')
        
        st.markdown(f"""
        <div class="source-item">
            <div class="source-header">Reference {i} - {source_type}: {source_name}</div>
            {display_content}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Response Time", f"{processing_time:.2f}s")
    
    with col2:
        st.metric("Reference Sources", f"{len(result['sources'])} items")
    
    with col3:
        # Calculate simple confidence metric based on number of sources
        confidence = min(len(result['sources']) * 0.2, 1.0)
        st.metric("Confidence", f"{confidence:.1%}")

if __name__ == "__main__":
    main() 