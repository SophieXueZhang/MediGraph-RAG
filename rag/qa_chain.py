# TODO: LangChain RetrievalQA + Neo4j knowledge graph query
import os
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from langchain.chains import RetrievalQA
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

from neo4j import GraphDatabase
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalQASystem:
    """
    Medical Question Answering System using RAG
    """
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        # Neo4j connection
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        
        # LangChain components
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=self.openai_api_key
        )
        
        self.vector_store = None
        self.qa_chain = None
        
        # Custom prompt for medical QA
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful medical information assistant. Use the following medical knowledge to answer the question. 

IMPORTANT DISCLAIMERS:
- This information is for educational purposes only
- Always consult healthcare professionals for medical advice
- Do not use this for self-diagnosis or treatment decisions

Medical Knowledge Context:
{context}

Question: {question}

Answer: Provide a clear, accurate answer based on the medical knowledge provided. If the information is incomplete or you're unsure, state that clearly and recommend consulting a healthcare professional.
"""
        )
    
    def _extract_documents_from_neo4j(self) -> List[Document]:
        """
        Extract documents from Neo4j knowledge graph
        """
        documents = []
        
        with self.driver.session() as session:
            # Extract drug information
            drug_query = """
            MATCH (d:Drug)
            OPTIONAL MATCH (d)-[:TREATS]->(disease:Disease)
            OPTIONAL MATCH (d)-[:CAUSES]->(symptom:Symptom)
            RETURN d.name as drug_name, d.description as description,
                   collect(DISTINCT disease.name) as treats,
                   collect(DISTINCT symptom.name) as side_effects
            LIMIT 1000
            """
            
            result = session.run(drug_query)
            for record in result:
                drug_name = record['drug_name']
                description = record['description'] or ""
                treats = [t for t in record['treats'] if t]
                side_effects = [s for s in record['side_effects'] if s]
                
                text = f"Drug: {drug_name}. "
                if description:
                    text += f"Description: {description}. "
                if treats:
                    text += f"Treats: {', '.join(treats)}. "
                if side_effects:
                    text += f"Side effects: {', '.join(side_effects)}. "
                
                doc = Document(
                    page_content=text,
                    metadata={
                        'type': 'drug',
                        'name': drug_name,
                        'treats': treats,
                        'side_effects': side_effects
                    }
                )
                documents.append(doc)
            
            # Extract disease information
            disease_query = """
            MATCH (disease:Disease)
            OPTIONAL MATCH (drug:Drug)-[:TREATS]->(disease)
            OPTIONAL MATCH (disease)-[:HAS_SYMPTOM]->(symptom:Symptom)
            RETURN disease.name as disease_name, disease.description as description,
                   collect(DISTINCT drug.name) as treatments,
                   collect(DISTINCT symptom.name) as symptoms
            LIMIT 1000
            """
            
            result = session.run(disease_query)
            for record in result:
                disease_name = record['disease_name']
                description = record['description'] or ""
                treatments = [t for t in record['treatments'] if t]
                symptoms = [s for s in record['symptoms'] if s]
                
                text = f"Disease: {disease_name}. "
                if description:
                    text += f"Description: {description}. "
                if treatments:
                    text += f"Treatments: {', '.join(treatments)}. "
                if symptoms:
                    text += f"Symptoms: {', '.join(symptoms)}. "
                
                doc = Document(
                    page_content=text,
                    metadata={
                        'type': 'disease',
                        'name': disease_name,
                        'treatments': treatments,
                        'symptoms': symptoms
                    }
                )
                documents.append(doc)
        
        logger.info(f"Extracted {len(documents)} documents from Neo4j")
        return documents
    
    def initialize(self, documents_file: str = None):
        """
        Initialize the QA system
        """
        logger.info("Initializing Medical QA System...")
        
        # Extract documents from Neo4j
        documents = self._extract_documents_from_neo4j()
        
        if not documents:
            raise ValueError("No documents found in Neo4j database")
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        split_docs = text_splitter.split_documents(documents)
        
        # Create vector store
        self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
        logger.info(f"Built vector store with {len(split_docs)} document chunks")
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={
                "prompt": self.prompt_template
            },
            return_source_documents=True
        )
        
        logger.info("Medical QA System initialized successfully")
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a medical question
        
        Args:
            question: Medical question
            
        Returns:
            Dictionary with answer and source documents
        """
        if not self.qa_chain:
            raise ValueError("QA system not initialized. Call initialize() first.")
        
        logger.info(f"Processing question: {question}")
        
        # Get response from QA chain
        response = self.qa_chain({"query": question})
        
        # Format source documents
        source_documents = []
        for doc in response.get('source_documents', []):
            source_documents.append({
                'content': doc.page_content,
                'metadata': doc.metadata
            })
        
        result = {
            'answer': response['result'],
            'source_documents': source_documents,
            'question': question
        }
        
        logger.info(f"Generated answer with {len(source_documents)} sources")
        return result
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        """
        stats = {
            'neo4j_connected': False,
            'vector_store_ready': self.vector_store is not None,
            'qa_chain_ready': self.qa_chain is not None,
            'total_nodes': 0,
            'total_documents': 0
        }
        
        # Check Neo4j connection
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                record = result.single()
                if record:
                    stats['total_nodes'] = record['count']
                    stats['neo4j_connected'] = True
        except Exception as e:
            logger.warning(f"Failed to get Neo4j stats: {e}")
        
        # Get vector store info
        if self.vector_store:
            stats['total_documents'] = self.vector_store.index.ntotal
        
        return stats

def main():
    """
    Test the Medical QA System
    """
    import time
    
    qa_system = MedicalQASystem()
    
    print("Initializing system...")
    start_time = time.time()
    qa_system.initialize()
    init_time = time.time() - start_time
    print(f"Initialization completed in {init_time:.2f} seconds")
    
    # Test questions
    test_questions = [
        "What is metformin used for?",
        "What are the side effects of ibuprofen?",
        "How is diabetes treated?",
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        start_time = time.time()
        response = qa_system.ask(question)
        response_time = time.time() - start_time
        
        print(f"Answer: {response['answer']}")
        print(f"Sources: {len(response['source_documents'])}")
        print(f"Response time: {response_time:.2f} seconds")
        print("-" * 50)

if __name__ == "__main__":
    main() 