# TODO: Batch import data to Neo4j
import json
import pandas as pd
from neo4j import GraphDatabase
import logging
from typing import List, Dict, Any
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jIngestor:
    """
    Data ingestion class for loading medical knowledge graph into Neo4j
    """
    
    def __init__(self, uri="bolt://localhost:7687", username="neo4j", password="password"):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j database URI
            username: Neo4j username  
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        logger.info(f"Connected to Neo4j at {uri}")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def execute_cypher_file(self, cypher_file: str):
        """
        Execute Cypher commands from file
        
        Args:
            cypher_file: Path to .cypher file
        """
        with open(cypher_file, 'r', encoding='utf-8') as f:
            cypher_content = f.read()
        
        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in cypher_content.split(';') if stmt.strip()]
        
        with self.driver.session() as session:
            for statement in statements:
                if statement and not statement.startswith('//'):
                    try:
                        result = session.run(statement)
                        logger.info(f"Executed: {statement[:50]}...")
                    except Exception as e:
                        logger.error(f"Error executing statement: {e}")
                        logger.error(f"Statement: {statement}")
    
    def clear_database(self):
        """Clear all nodes and relationships"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared all existing data")
    
    def create_drug_nodes(self, fda_data_file: str):
        """
        Create Drug nodes from FDA data
        
        Args:
            fda_data_file: Path to processed FDA JSONL file
        """
        logger.info(f"Creating Drug nodes from {fda_data_file}")
        
        with open(fda_data_file, 'r', encoding='utf-8') as f:
            fda_records = [json.loads(line) for line in f]
        
        drugs_created = 0
        
        with self.driver.session() as session:
            for record in fda_records:
                # Extract drug information
                drug_id = record.get('id', '')
                brand_names = record.get('product_name', [])
                generic_names = record.get('generic_name', [])
                active_ingredients = record.get('active_ingredient', [])
                
                if not drug_id:
                    continue
                
                # Use first brand name or generic name as primary name
                primary_name = (brand_names[0] if brand_names else 
                               generic_names[0] if generic_names else 
                               drug_id)
                
                # Create Drug node
                cypher = """
                MERGE (d:Drug {id: $drug_id})
                SET d.name = $name,
                    d.brand_names = $brand_names,
                    d.generic_names = $generic_names,
                    d.active_ingredients = $active_ingredients,
                    d.fda_approved = true,
                    d.created_at = datetime()
                """
                
                session.run(cypher, {
                    'drug_id': drug_id,
                    'name': primary_name,
                    'brand_names': brand_names,
                    'generic_names': generic_names, 
                    'active_ingredients': active_ingredients
                })
                
                drugs_created += 1
        
        logger.info(f"Created {drugs_created} Drug nodes")
    
    def create_entities_from_ner(self, entities_file: str):
        """
        Create Disease, Symptom, and Chemical nodes from NER results
        
        Args:
            entities_file: Path to NER entities JSONL file
        """
        logger.info(f"Creating entity nodes from {entities_file}")
        
        with open(entities_file, 'r', encoding='utf-8') as f:
            entity_records = [json.loads(line) for line in f]
        
        # Collect unique entities by type
        entities_by_type = {
            'DISEASE': set(),
            'SYMPTOM': set(), 
            'CHEMICAL': set()
        }
        
        for record in entity_records:
            for entity in record['entities']:
                entity_type = entity['label']
                entity_text = entity['text'].lower().strip()
                
                if entity_type in entities_by_type and len(entity_text) > 2:
                    entities_by_type[entity_type].add(entity_text)
        
        # Create nodes for each entity type
        with self.driver.session() as session:
            # Create Disease nodes
            for disease_name in entities_by_type['DISEASE']:
                cypher = """
                MERGE (d:Disease {name: $name})
                SET d.id = 'disease_' + replace(toLower($name), ' ', '_'),
                    d.created_at = datetime()
                """
                session.run(cypher, {'name': disease_name})
            
            # Create Symptom nodes
            for symptom_name in entities_by_type['SYMPTOM']:
                cypher = """
                MERGE (s:Symptom {name: $name})
                SET s.id = 'symptom_' + replace(toLower($name), ' ', '_'),
                    s.created_at = datetime()
                """
                session.run(cypher, {'name': symptom_name})
            
            # Create Chemical nodes
            for chemical_name in entities_by_type['CHEMICAL']:
                cypher = """
                MERGE (c:Chemical {name: $name})
                SET c.id = 'chemical_' + replace(toLower($name), ' ', '_'),
                    c.created_at = datetime()
                """
                session.run(cypher, {'name': chemical_name})
        
        logger.info(f"Created {len(entities_by_type['DISEASE'])} Disease nodes")
        logger.info(f"Created {len(entities_by_type['SYMPTOM'])} Symptom nodes") 
        logger.info(f"Created {len(entities_by_type['CHEMICAL'])} Chemical nodes")
    
    def create_relationships_from_triples(self, triples_file: str):
        """
        Create relationships from knowledge triples CSV
        
        Args:
            triples_file: Path to triples CSV file
        """
        logger.info(f"Creating relationships from {triples_file}")
        
        if not os.path.exists(triples_file):
            logger.warning(f"Triples file {triples_file} not found")
            return
        
        df = pd.read_csv(triples_file)
        logger.info(f"Processing {len(df)} triples")
        
        relationships_created = 0
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                subject = row['subject'].strip()
                predicate = row['predicate'].strip()
                obj = row['object'].strip()
                frequency = row.get('frequency', 1)
                
                # Map relation types to Cypher patterns
                if predicate == 'treats':
                    cypher = """
                    MATCH (d:Drug {name: $subject})
                    MATCH (disease:Disease {name: $object})
                    MERGE (d)-[r:TREATS]->(disease)
                    SET r.confidence = 0.7,
                        r.frequency = $frequency,
                        r.source = 'extracted'
                    """
                elif predicate == 'causes':
                    cypher = """
                    MATCH (d:Drug {name: $subject})
                    MATCH (s:Symptom {name: $object})
                    MERGE (d)-[r:CAUSES]->(s)
                    SET r.confidence = 0.6,
                        r.frequency = $frequency,
                        r.source = 'extracted'
                    """
                elif predicate == 'has_symptom':
                    cypher = """
                    MATCH (disease:Disease {name: $subject})
                    MATCH (s:Symptom {name: $object})
                    MERGE (disease)-[r:HAS_SYMPTOM]->(s)
                    SET r.confidence = 0.6,
                        r.frequency = $frequency,
                        r.source = 'extracted'
                    """
                elif predicate == 'interacts_with':
                    cypher = """
                    MATCH (d1:Drug {name: $subject})
                    MATCH (d2:Drug {name: $object})
                    MERGE (d1)-[r:INTERACTS_WITH]->(d2)
                    SET r.confidence = 0.7,
                        r.frequency = $frequency,
                        r.source = 'extracted'
                    """
                else:
                    # Generic relationship
                    cypher = f"""
                    MATCH (n1 {{name: $subject}})
                    MATCH (n2 {{name: $object}})
                    MERGE (n1)-[r:RELATED_TO]->(n2)
                    SET r.relation_type = $predicate,
                        r.confidence = 0.5,
                        r.frequency = $frequency,
                        r.source = 'extracted'
                    """
                
                try:
                    result = session.run(cypher, {
                        'subject': subject,
                        'object': obj,
                        'predicate': predicate,
                        'frequency': frequency
                    })
                    relationships_created += 1
                except Exception as e:
                    logger.warning(f"Error creating relationship {subject}-{predicate}->{obj}: {e}")
        
        logger.info(f"Created {relationships_created} relationships")
    
    def get_graph_stats(self) -> Dict[str, int]:
        """
        Get statistics about the knowledge graph
        
        Returns:
            Dictionary with node and relationship counts
        """
        with self.driver.session() as session:
            # Count nodes by type
            node_counts = {}
            for label in ['Drug', 'Disease', 'Symptom', 'Chemical']:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                node_counts[label] = result.single()['count']
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            relationship_count = result.single()['count']
            
            # Count relationship types
            result = session.run("""
                MATCH ()-[r]->() 
                RETURN type(r) as rel_type, count(r) as count 
                ORDER BY count DESC
            """)
            rel_types = {record['rel_type']: record['count'] for record in result}
            
            stats = {
                'nodes': node_counts,
                'total_relationships': relationship_count,
                'relationship_types': rel_types
            }
            
            logger.info(f"Graph statistics: {stats}")
            return stats

def main():
    """Main ingestion pipeline"""
    # Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    ingestor = Neo4jIngestor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    try:
        # Initialize schema
        schema_file = Path("graph/schema.cypher")
        if schema_file.exists():
            logger.info("Setting up database schema...")
            ingestor.execute_cypher_file(str(schema_file))
        
        # Data file paths - use unified data if available, fallback to FDA-only
        fda_file = Path("data/processed/fda_processed.jsonl")
        
        # Check for unified data first
        unified_entities = Path("data/processed/all_entities.jsonl")
        unified_triples = Path("data/processed/unified_triples.csv")
        
        entities_file = unified_entities if unified_entities.exists() else Path("data/processed/fda_processed_entities.jsonl")
        triples_file = unified_triples if unified_triples.exists() else Path("data/processed/fda_processed_triples.csv")
        
        # Clear existing data (optional - comment out for incremental loading)
        # ingestor.clear_database()
        
        # Load FDA drug data
        if fda_file.exists():
            ingestor.create_drug_nodes(str(fda_file))
        else:
            logger.warning(f"FDA data file {fda_file} not found")
        
        # Load extracted entities
        if entities_file.exists():
            ingestor.create_entities_from_ner(str(entities_file))
        else:
            logger.warning(f"Entities file {entities_file} not found")
        
        # Load relationships
        if triples_file.exists():
            ingestor.create_relationships_from_triples(str(triples_file))
        else:
            logger.warning(f"Triples file {triples_file} not found")
        
        # Print final statistics
        ingestor.get_graph_stats()
        
    finally:
        ingestor.close()

if __name__ == "__main__":
    main() 