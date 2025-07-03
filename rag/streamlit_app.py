import streamlit as st
import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import time
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag.qa_chain import MedicalQASystem

# Page configuration
st.set_page_config(
    page_title="Medical Knowledge Graph RAG System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e88e5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .answer-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .source-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'qa_system' not in st.session_state:
        st.session_state.qa_system = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'system_stats' not in st.session_state:
        st.session_state.system_stats = {}

@st.cache_resource
def load_qa_system():
    """Load QA system"""
    try:
        qa_system = MedicalQASystem()
        qa_system.initialize()
        return qa_system
    except Exception as e:
        st.error(f"Failed to initialize QA system: {e}")
        return None

def display_system_stats(stats: Dict[str, Any]):
    """Display system statistics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🔗 Neo4j Status</h3>
            <p style="font-size: 1.5rem;">{}</p>
        </div>
        """.format("✅ Connected" if stats.get('neo4j_connected', False) else "❌ Disconnected"), 
        unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Total Nodes</h3>
            <p style="font-size: 1.5rem;">{}</p>
        </div>
        """.format(stats.get('total_nodes', 0)), 
        unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🧠 Vector Store</h3>
            <p style="font-size: 1.5rem;">{}</p>
        </div>
        """.format("✅ Ready" if stats.get('vector_store_ready', False) else "❌ Not Ready"), 
        unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🤖 QA Chain</h3>
            <p style="font-size: 1.5rem;">{}</p>
        </div>
        """.format("✅ Ready" if stats.get('qa_chain_ready', False) else "❌ Not Ready"), 
        unsafe_allow_html=True)

def display_chat_history():
    """Display chat history"""
    if st.session_state.chat_history:
        st.markdown("### 💬 Chat History")
        for i, (question, answer, sources) in enumerate(reversed(st.session_state.chat_history[-5:])):
            with st.expander(f"Q{len(st.session_state.chat_history)-i}: {question[:100]}..."):
                st.markdown(f"**Question:** {question}")
                st.markdown(f"**Answer:** {answer}")
                if sources:
                    st.markdown(f"**Sources:** {len(sources)} documents")

def main():
    """Main application function"""
    init_session_state()
    
    # Page title
    st.markdown('<h1 class="main-header">🏥 Medical Knowledge Graph RAG System</h1>', 
                unsafe_allow_html=True)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🔧 System Configuration")
        
        # System initialization
        if st.button("🚀 Initialize System", type="primary"):
            with st.spinner("Initializing Medical QA System..."):
                st.session_state.qa_system = load_qa_system()
                if st.session_state.qa_system:
                    st.session_state.system_stats = st.session_state.qa_system.get_system_stats()
                    st.success("✅ System initialized successfully!")
                else:
                    st.error("❌ Failed to initialize system")
        
        # Display system status
        if st.session_state.qa_system:
            if st.button("📊 Refresh Stats"):
                st.session_state.system_stats = st.session_state.qa_system.get_system_stats()
            
            st.markdown("### 📈 System Statistics")
            stats = st.session_state.system_stats
            if stats:
                st.json(stats)
        
        # Chat history management
        st.markdown("### 🗂️ Chat Management")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.success("Chat history cleared!")
        
        # Display chat history
        display_chat_history()
    
    # Main content area
    if st.session_state.qa_system is None:
        st.info("👈 Please initialize the system first using the sidebar.")
        st.markdown("""
        ## 📋 System Features
        
        - **🧠 AI-Powered Medical QA**: Ask questions about medical conditions, treatments, and drug interactions
        - **📊 Knowledge Graph Integration**: Powered by Neo4j medical knowledge graph
        - **🔍 Source Attribution**: Every answer comes with source documents
        - **⚡ Real-time Processing**: Fast response times with optimized retrieval
        - **🔒 Safety First**: Educational information with medical disclaimers
        
        ## 🚀 Quick Start
        1. Click "Initialize System" in the sidebar
        2. Wait for the system to load (may take a few minutes first time)
        3. Ask your medical questions below
        4. Review answers and source documents
        """)
        return
    
    # Display system statistics
    if st.session_state.system_stats:
        display_system_stats(st.session_state.system_stats)
    
    # Q&A interface
    st.markdown("## 💬 Ask Medical Questions")
    
    # Example questions
    st.markdown("### 🎯 Try These Example Questions:")
    example_questions = [
        "What is metformin used for?",
        "What are the side effects of ibuprofen?",
        "How is diabetes treated?",
        "What are symptoms of hypertension?",
        "How does aspirin work?"
    ]
    
    cols = st.columns(len(example_questions))
    for i, (col, question) in enumerate(zip(cols, example_questions)):
        with col:
            if st.button(f"📝 {question}", key=f"example_{i}"):
                st.session_state.current_question = question
    
    # Question input
    question = st.text_input(
        "🔍 Enter your medical question:",
        value=st.session_state.get('current_question', ''),
        placeholder="e.g., What are the side effects of aspirin?",
        key="question_input"
    )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            include_sources = st.checkbox("📚 Show source documents", value=True)
            max_sources = st.slider("Maximum sources to show", 1, 10, 5)
        with col2:
            response_language = st.selectbox("🌐 Response language", ["Auto", "English"])
            show_metadata = st.checkbox("🔍 Show metadata", value=False)
    
    # Process question
    if question and (st.button("🚀 Ask Question", type="primary") or st.session_state.get('current_question')):
        if 'current_question' in st.session_state:
            del st.session_state.current_question
            
        with st.spinner("🔍 Searching knowledge base and generating answer..."):
            start_time = time.time()
            
            try:
                response = st.session_state.qa_system.ask(question)
                end_time = time.time()
                response_time = end_time - start_time
                
                # Display answer
                st.markdown(f"""
                <div class="answer-box">
                    <h3>🤖 Answer <span style="color: #666; font-size: 0.8rem;">(Response time: {response_time:.2f}s)</span></h3>
                    <p>{response['answer']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display sources
                if include_sources and response.get('source_documents'):
                    st.markdown(f"### 📚 Reference Sources ({len(response['source_documents'])} items)")
                    
                    for i, source in enumerate(response['source_documents'][:max_sources]):
                        st.markdown(f"""
                        <div class="source-box">
                            <h4>📄 Source {i+1}</h4>
                            <p><strong>Content:</strong> {source['content'][:300]}...</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if show_metadata and source.get('metadata'):
                            st.json(source['metadata'])
                
                # Add to chat history
                st.session_state.chat_history.append((
                    question, 
                    response['answer'], 
                    response.get('source_documents', [])
                ))
                
                # Display performance metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⏱️ Response Time", f"{response_time:.2f}s")
                with col2:
                    st.metric("📊 Sources Found", len(response.get('source_documents', [])))
                with col3:
                    st.metric("💬 Total Questions", len(st.session_state.chat_history))
                
            except Exception as e:
                st.error(f"❌ Error processing question: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>⚠️ <strong>Disclaimer:</strong> This system provides educational information only. 
        Always consult healthcare professionals for medical advice.</p>
        <p>🔬 Medical Knowledge Graph RAG System | Powered by OpenAI & Neo4j</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 