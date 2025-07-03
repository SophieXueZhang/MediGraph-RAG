// TODO: Define Drug, Disease, Symptom nodes and relationships
// Medical Knowledge Graph Schema for Neo4j

// ========================================
// NODE CONSTRAINTS AND INDEXES
// ========================================

// Drug nodes
CREATE CONSTRAINT drug_id_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.id IS UNIQUE;
CREATE INDEX drug_name_index IF NOT EXISTS FOR (d:Drug) ON (d.name);
CREATE INDEX drug_generic_index IF NOT EXISTS FOR (d:Drug) ON (d.generic_name);

// Disease nodes  
CREATE CONSTRAINT disease_id_unique IF NOT EXISTS FOR (d:Disease) REQUIRE d.id IS UNIQUE;
CREATE INDEX disease_name_index IF NOT EXISTS FOR (d:Disease) ON (d.name);

// Symptom nodes
CREATE CONSTRAINT symptom_id_unique IF NOT EXISTS FOR (s:Symptom) REQUIRE s.id IS UNIQUE;
CREATE INDEX symptom_name_index IF NOT EXISTS FOR (s:Symptom) ON (s.name);

// Chemical/Compound nodes (for active ingredients)
CREATE CONSTRAINT chemical_id_unique IF NOT EXISTS FOR (c:Chemical) REQUIRE c.id IS UNIQUE;
CREATE INDEX chemical_name_index IF NOT EXISTS FOR (c:Chemical) ON (c.name);

// ========================================
// NODE PROPERTIES SCHEMA
// ========================================

// Drug node properties:
// - id: unique identifier
// - name: brand/trade name
// - generic_name: generic drug name
// - active_ingredients: list of active compounds
// - drug_class: therapeutic class
// - dosage_forms: available forms (tablet, injection, etc.)
// - fda_approved: boolean
// - description: drug description

// Disease node properties:
// - id: unique identifier  
// - name: disease name
// - synonyms: alternative names
// - category: disease category
// - icd_codes: ICD classification codes
// - description: disease description

// Symptom node properties:
// - id: unique identifier
// - name: symptom name
// - severity: mild/moderate/severe
// - body_system: affected body system
// - description: symptom description

// Chemical node properties:
// - id: unique identifier
// - name: chemical name
// - molecular_formula: chemical formula
// - cas_number: CAS registry number
// - umls_id: UMLS concept identifier

// ========================================
// RELATIONSHIP TYPES AND PROPERTIES
// ========================================

// Drug-Disease relationships
// (:Drug)-[:TREATS]->(:Disease)
// Properties: efficacy, dosage, duration, confidence

// (:Drug)-[:INDICATED_FOR]->(:Disease) 
// Properties: indication_type, approval_status, confidence

// (:Drug)-[:CONTRAINDICATED_FOR]->(:Disease)
// Properties: contraindication_type, severity, confidence

// Drug-Symptom relationships  
// (:Drug)-[:CAUSES]->(:Symptom)
// Properties: frequency, severity, onset_time, confidence

// (:Drug)-[:ALLEVIATES]->(:Symptom)
// Properties: effectiveness, time_to_relief, confidence

// Disease-Symptom relationships
// (:Disease)-[:HAS_SYMPTOM]->(:Symptom)
// Properties: frequency, severity, stage, confidence

// (:Disease)-[:PRESENTS_AS]->(:Symptom)
// Properties: presentation_type, likelihood, confidence

// Drug-Drug interactions
// (:Drug)-[:INTERACTS_WITH]->(:Drug)
// Properties: interaction_type, severity, mechanism, confidence

// Drug-Chemical relationships
// (:Drug)-[:CONTAINS]->(:Chemical)
// Properties: concentration, role (active/inactive), confidence

// ========================================
// SAMPLE DATA CREATION (for testing)
// ========================================

// Create sample Drug nodes
MERGE (metformin:Drug {
    id: "drug_001",
    name: "Metformin",
    generic_name: "metformin hydrochloride", 
    drug_class: "Antidiabetic",
    fda_approved: true,
    description: "Oral antidiabetic medication used to treat type 2 diabetes"
});

MERGE (ibuprofen:Drug {
    id: "drug_002", 
    name: "Ibuprofen",
    generic_name: "ibuprofen",
    drug_class: "NSAID",
    fda_approved: true,
    description: "Nonsteroidal anti-inflammatory drug used for pain relief"
});

// Create sample Disease nodes
MERGE (diabetes:Disease {
    id: "disease_001",
    name: "Type 2 Diabetes",
    category: "Endocrine Disorder",
    icd_codes: ["E11"],
    description: "Chronic condition affecting blood sugar regulation"
});

MERGE (hypertension:Disease {
    id: "disease_002",
    name: "Hypertension", 
    category: "Cardiovascular Disease",
    icd_codes: ["I10"],
    description: "High blood pressure condition"
});

// Create sample Symptom nodes
MERGE (nausea:Symptom {
    id: "symptom_001",
    name: "Nausea",
    body_system: "Gastrointestinal",
    description: "Feeling of sickness and urge to vomit"
});

MERGE (headache:Symptom {
    id: "symptom_002",
    name: "Headache",
    body_system: "Neurological", 
    description: "Pain in head or neck region"
});

// Create sample relationships
MERGE (metformin)-[:TREATS {
    efficacy: "high",
    confidence: 0.95,
    source: "FDA_label"
}]->(diabetes);

MERGE (metformin)-[:CAUSES {
    frequency: "common",
    severity: "mild",
    confidence: 0.8,
    source: "clinical_trials"
}]->(nausea);

MERGE (diabetes)-[:HAS_SYMPTOM {
    frequency: "common",
    stage: "early",
    confidence: 0.9
}]->(headache);

MERGE (ibuprofen)-[:ALLEVIATES {
    effectiveness: "high",
    time_to_relief: "30-60 minutes",
    confidence: 0.85
}]->(headache);

// ========================================
// USEFUL QUERIES FOR TESTING
// ========================================

// Find all drugs that treat a specific disease
// MATCH (d:Drug)-[:TREATS]->(disease:Disease {name: "Type 2 Diabetes"})
// RETURN d.name, d.description;

// Find side effects of a drug
// MATCH (drug:Drug {name: "Metformin"})-[:CAUSES]->(s:Symptom)
// RETURN s.name, s.description;

// Find drug interactions
// MATCH (d1:Drug)-[r:INTERACTS_WITH]->(d2:Drug)
// RETURN d1.name, r.interaction_type, d2.name;

// Find alternative treatments for a disease  
// MATCH (d:Drug)-[:TREATS]->(disease:Disease {name: "Type 2 Diabetes"})
// RETURN d.name, d.drug_class
// ORDER BY d.name; 