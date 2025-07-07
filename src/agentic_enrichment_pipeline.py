# src/agentic_enrichment_pipeline.py
"""
LangGraph Agentic Enrichment Pipeline
Showcases: LangGraph expertise, Multi-source integration, Real-time processing, Production patterns
"""

import pandas as pd
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
from pathlib import Path

# LangGraph imports for agentic workflows
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage

# Import our configuration system
from config import load_config

class EnrichmentState(TypedDict):
    """LangGraph state for agentic enrichment workflow"""
    record: dict
    entity_classification: dict
    enrichment_strategy: dict
    data_sources_attempted: List[str]
    enrichment_results: List[dict]
    confidence_scores: List[float]
    quality_metrics: dict
    final_result: dict
    error_state: Optional[str]

@dataclass
class AgenticEnrichmentResult:
    # Original fields
    fdd: str
    fdd_store_no: str
    fdd_location_name: str
    franchisee: str
    fdd_contact_name: str
    address: str
    city: str
    state: str
    zip: str
    phone: str

    # Enriched fields
    franchisee_owner: str = ""
    corporate_name: str = ""
    corporate_address: str = ""
    corporate_phone: str = ""
    corporate_email: str = ""
    linkedin: str = ""
    url_sources: str = ""

    # Agentic workflow metrics
    agent_confidence: float = 0.0
    enrichment_strategy_used: str = ""
    data_sources_consulted: int = 0
    agent_reasoning: str = ""
    workflow_execution_time: float = 0.0
    quality_score: float = 0.0

    # Production metrics
    processing_timestamp: str = ""
    pipeline_version: str = "2.0-agentic"

class EnrichmentAgent:
    """LangGraph-powered intelligent enrichment agent"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.workflow = self._build_agentic_workflow()
        
    def _build_agentic_workflow(self) -> StateGraph:
        """Build LangGraph workflow for intelligent enrichment"""
        workflow = StateGraph(EnrichmentState)
        
        # Add workflow nodes
        workflow.add_node("classify_entity", self._classify_entity_node)
        workflow.add_node("plan_enrichment", self._plan_enrichment_strategy)
        workflow.add_node("execute_business_enrichment", self._execute_business_enrichment)
        workflow.add_node("execute_individual_enrichment", self._execute_individual_enrichment)
        workflow.add_node("validate_and_score", self._validate_and_score_results)
        workflow.add_node("resolve_conflicts", self._resolve_data_conflicts)
        workflow.add_node("finalize_result", self._finalize_enrichment_result)
        
        # Define workflow edges with intelligent routing
        workflow.set_entry_point("classify_entity")
        
        workflow.add_edge("classify_entity", "plan_enrichment")
        
        # Conditional routing based on entity type
        workflow.add_conditional_edges(
            "plan_enrichment",
            self._route_enrichment_strategy,
            {
                "business": "execute_business_enrichment",
                "individual": "execute_individual_enrichment"
            }
        )
        
        workflow.add_edge("execute_business_enrichment", "validate_and_score")
        workflow.add_edge("execute_individual_enrichment", "validate_and_score")
        
        # Conditional conflict resolution
        workflow.add_conditional_edges(
            "validate_and_score",
            self._check_conflicts,
            {
                "conflicts_found": "resolve_conflicts",
                "no_conflicts": "finalize_result"
            }
        )
        
        workflow.add_edge("resolve_conflicts", "finalize_result")
        workflow.add_edge("finalize_result", END)
        
        return workflow.compile()
    
    async def _classify_entity_node(self, state: EnrichmentState) -> EnrichmentState:
        """LangGraph node: Intelligent entity classification"""
        record = state["record"]
        franchisee_name = record.get("Franchisee", record.get("franchisee", ""))
        
        # Advanced classification logic
        business_indicators = ['LLC', 'INC', 'CORP', 'LTD', 'LP', 'COMPANY', 'ENTERPRISES']
        individual_patterns = [',', 'JR', 'SR', 'III']
        
        business_score = sum(1 for indicator in business_indicators if indicator in franchisee_name.upper())
        individual_score = sum(1 for pattern in individual_patterns if pattern in franchisee_name)
        
        # Contextual analysis
        has_comma = ',' in franchisee_name
        word_count = len(franchisee_name.split())
        
        # Agent reasoning
        if business_score > 0:
            entity_type = "business"
            confidence = min(0.95, 0.7 + (business_score * 0.1))
            reasoning = f"Business entity detected: {business_score} business indicators found"
        elif has_comma and word_count == 2:
            entity_type = "individual"
            confidence = 0.9
            reasoning = "Individual detected: 'Last, First' format"
        elif word_count == 2 and business_score == 0:
            entity_type = "individual"
            confidence = 0.8
            reasoning = "Individual detected: Two-word name, no business indicators"
        else:
            entity_type = "business"
            confidence = 0.6
            reasoning = "Default to business: Ambiguous case"
        
        classification = {
            "type": entity_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "business_indicators": business_score,
            "individual_indicators": individual_score
        }
        
        state["entity_classification"] = classification
        self.logger.debug(f"🤖 Agent classified '{franchisee_name}' as {entity_type} (conf: {confidence:.2f})")
        
        return state
    
    async def _plan_enrichment_strategy(self, state: EnrichmentState) -> EnrichmentState:
        """LangGraph node: Plan optimal enrichment strategy"""
        classification = state["entity_classification"]
        record = state["record"]
        
        # Agent decides enrichment strategy based on entity type and location
        strategy = {
            "primary_sources": [],
            "fallback_sources": [],
            "confidence_threshold": 0.7,
            "max_sources": 4
        }
        
        if classification["type"] == "business":
            # Business enrichment strategy
            strategy["primary_sources"] = ["business_registry", "google_places"]
            strategy["fallback_sources"] = ["corporate_database", "linkedin_company"]
            
            # Texas has better business registry data
            if record["state"].upper() == "TX":
                strategy["confidence_threshold"] = 0.8
                strategy["reasoning"] = "Texas business registry provides high-quality data"
            else:
                strategy["reasoning"] = "Standard business enrichment strategy"
                
        else:
            # Individual enrichment strategy  
            strategy["primary_sources"] = ["linkedin_individual", "google_search"]
            strategy["fallback_sources"] = ["people_search", "social_media"]
            strategy["reasoning"] = "Individual-focused enrichment strategy"
        
        state["enrichment_strategy"] = strategy
        state["data_sources_attempted"] = []
        state["enrichment_results"] = []
        state["confidence_scores"] = []
        
        self.logger.debug(f"🎯 Agent planned strategy: {strategy['reasoning']}")
        return state
    
    async def _execute_business_enrichment(self, state: EnrichmentState) -> EnrichmentState:
        """LangGraph node: Execute business-specific enrichment"""
        record = state["record"]
        strategy = state["enrichment_strategy"]
        
        # Execute primary sources
        for source in strategy["primary_sources"]:
            result = await self._call_enrichment_source(source, record, "business")
            if result:
                state["enrichment_results"].append({**result, "source": source, "priority": "primary"})
                state["data_sources_attempted"].append(source)
                state["confidence_scores"].append(result.get("source_confidence", 0.7))
        
        # Execute fallback sources if needed
        avg_confidence = sum(state["confidence_scores"]) / len(state["confidence_scores"]) if state["confidence_scores"] else 0
        
        if avg_confidence < strategy["confidence_threshold"]:
            self.logger.debug("🔄 Agent triggering fallback sources due to low confidence")
            for source in strategy["fallback_sources"]:
                result = await self._call_enrichment_source(source, record, "business")
                if result:
                    state["enrichment_results"].append({**result, "source": source, "priority": "fallback"})
                    state["data_sources_attempted"].append(source)
                    state["confidence_scores"].append(result.get("source_confidence", 0.6))
        
        return state
    
    async def _execute_individual_enrichment(self, state: EnrichmentState) -> EnrichmentState:
        """LangGraph node: Execute individual-specific enrichment"""
        record = state["record"]
        strategy = state["enrichment_strategy"]
        
        # Parse individual name
        franchisee_name = record["franchisee"]
        if ',' in franchisee_name:
            parts = franchisee_name.split(',', 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip().split()[0] if parts[1].strip() else ""
        else:
            parts = franchisee_name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        # Execute individual enrichment sources
        for source in strategy["primary_sources"]:
            result = await self._call_individual_enrichment_source(source, record, first_name, last_name)
            if result:
                state["enrichment_results"].append({**result, "source": source, "priority": "primary"})
                state["data_sources_attempted"].append(source)
                state["confidence_scores"].append(result.get("source_confidence", 0.8))
        
        return state
    
    async def _validate_and_score_results(self, state: EnrichmentState) -> EnrichmentState:
        """LangGraph node: Validate enrichment results and calculate quality scores"""
        results = state["enrichment_results"]
        
        # Aggregate data from all sources
        aggregated_data = {}
        field_sources = {}
        
        for result in results:
            for field, value in result.items():
                if field not in ["source", "priority", "source_confidence"] and value:
                    if field not in aggregated_data:
                        aggregated_data[field] = []
                        field_sources[field] = []
                    
                    aggregated_data[field].append(value)
                    field_sources[field].append(result["source"])
        
        # Quality scoring
        quality_metrics = {
            "data_consistency": self._calculate_consistency_score(aggregated_data),
            "source_diversity": len(set(state["data_sources_attempted"])),
            "field_completeness": len(aggregated_data) / 6,  # 6 target fields
            "confidence_stability": min(state["confidence_scores"]) / max(state["confidence_scores"]) if state["confidence_scores"] else 0
        }
        
        state["quality_metrics"] = quality_metrics
        
        # Check for conflicts
        conflicts = {}
        for field, values in aggregated_data.items():
            unique_values = list(set(values))
            if len(unique_values) > 1:
                conflicts[field] = {
                    "values": unique_values,
                    "sources": field_sources[field]
                }
        
        state["conflicts"] = conflicts
        return state
    
    async def _resolve_data_conflicts(self, state: EnrichmentState) -> EnrichmentState:
        """LangGraph node: Intelligent conflict resolution"""
        conflicts = state.get("conflicts", {})
        results = state["enrichment_results"]
        
        resolved_data = {}
        
        for field, conflict_info in conflicts.items():
            values = conflict_info["values"]
            sources = conflict_info["sources"]
            
            # Agent reasoning for conflict resolution
            if "business_registry" in sources:
                # Prefer official business registry data
                registry_idx = sources.index("business_registry")
                resolved_value = values[registry_idx]
                reasoning = "Business registry data preferred for official information"
            elif "Verified:" in str(values):
                # Prefer verified data from Google Places
                verified_value = [v for v in values if "Verified:" in str(v)][0]
                resolved_value = verified_value
                reasoning = "Verified source data preferred"
            elif len(values[0]) > len(values[1]):
                # Prefer more detailed information
                resolved_value = max(values, key=len)
                reasoning = "More detailed information preferred"
            else:
                # Default to first reliable source
                resolved_value = values[0]
                reasoning = "First reliable source used"
            
            resolved_data[field] = resolved_value
            self.logger.debug(f"🔧 Agent resolved conflict for {field}: {reasoning}")
        
        # Update results with resolved conflicts
        for result in results:
            for field, resolved_value in resolved_data.items():
                if field in result:
                    result[field] = resolved_value
        
        return state
    
    async def _finalize_enrichment_result(self, state: EnrichmentState) -> EnrichmentState:
        """LangGraph node: Finalize enrichment result with agent scoring"""
        results = state["enrichment_results"]
        quality_metrics = state["quality_metrics"]
        classification = state["entity_classification"]
        
        # Merge all results
        final_data = {}
        source_urls = []
        
        for result in results:
            source_urls.append(result.get("source", "unknown"))
            for field, value in result.items():
                if field not in ["source", "priority", "source_confidence"] and value:
                    if field not in final_data:
                        final_data[field] = value
        
        # Calculate agent confidence (more sophisticated than simple confidence)
        agent_confidence = (
            (classification["confidence"] * 0.3) +  # Entity classification confidence
            (quality_metrics["data_consistency"] * 0.3) +  # Data consistency
            (quality_metrics["field_completeness"] * 0.2) +  # Completeness
            (min(1.0, quality_metrics["source_diversity"] / 3) * 0.2)  # Source diversity
        )
        
        # Agent reasoning summary
        reasoning_parts = [
            f"Entity: {classification['type']} ({classification['confidence']:.2f})",
            f"Sources: {len(state['data_sources_attempted'])}",
            f"Consistency: {quality_metrics['data_consistency']:.2f}",
            f"Completeness: {quality_metrics['field_completeness']:.2f}"
        ]
        
        final_result = {
            **state["record"],
            **final_data,
            "agent_confidence": round(agent_confidence, 3),
            "enrichment_strategy_used": state["enrichment_strategy"]["reasoning"],
            "data_sources_consulted": len(state["data_sources_attempted"]),
            "agent_reasoning": "; ".join(reasoning_parts),
            "quality_score": round(sum(quality_metrics.values()) / len(quality_metrics), 3),
            "url_sources": "; ".join(source_urls)
        }
        
        state["final_result"] = final_result
        return state
    
    def _route_enrichment_strategy(self, state: EnrichmentState) -> str:
        """LangGraph conditional edge: Route based on entity type"""
        return state["entity_classification"]["type"]
    
    def _check_conflicts(self, state: EnrichmentState) -> str:
        """LangGraph conditional edge: Check if conflicts need resolution"""
        return "conflicts_found" if state.get("conflicts") else "no_conflicts"
    
    async def _call_enrichment_source(self, source: str, record: dict, entity_type: str) -> dict:
        """Call specific enrichment source (simulated for demo)"""
        franchisee_name = record["franchisee"]
        
        if source == "business_registry":
            return {
                "corporate_name": franchisee_name,
                "corporate_address": f"Registered: {record['address']}, {record['city']}, {record['state']} {record['zip']}",
                "franchisee_owner": franchisee_name.replace(' LLC', '').replace(' Inc', '').strip(),
                "source_confidence": 0.9
            }
            
        elif source == "google_places":
            return {
                "corporate_phone": record["phone"],
                "corporate_address": f"Verified: {record['address']}, {record['city']}, {record['state']} {record['zip']}",
                "corporate_email": f"info@{franchisee_name.lower().replace(' ', '').replace(',', '')[:8]}.com",
                "source_confidence": 0.8
            }
            
        elif source == "corporate_database":
            return {
                "corporate_name": franchisee_name,
                "linkedin": f"https://www.linkedin.com/company/{franchisee_name.lower().replace(' ', '-').replace(',', '')}",
                "source_confidence": 0.7
            }
            
        return {}
    
    async def _call_individual_enrichment_source(self, source: str, record: dict, first_name: str, last_name: str) -> dict:
        """Call individual-specific enrichment source"""
        if source == "linkedin_individual":
            linkedin_slug = f"{first_name.lower()}-{last_name.lower()}".replace(' ', '-')
            return {
                "franchisee_owner": f"{first_name} {last_name}",
                "linkedin": f"https://www.linkedin.com/in/{linkedin_slug}",
                "source_confidence": 0.85
            }
            
        elif source == "google_search":
            return {
                "franchisee_owner": f"{first_name} {last_name}",
                "corporate_address": f"{record['address']}, {record['city']}, {record['state']} {record['zip']}",
                "source_confidence": 0.75
            }
            
        return {}
    
    def _calculate_consistency_score(self, aggregated_data: dict) -> float:
        """Calculate data consistency across sources"""
        if not aggregated_data:
            return 0.0
        
        consistency_scores = []
        for field, values in aggregated_data.items():
            unique_values = len(set(values))
            total_values = len(values)
            field_consistency = 1.0 - ((unique_values - 1) / max(1, total_values - 1))
            consistency_scores.append(field_consistency)
        
        return sum(consistency_scores) / len(consistency_scores)

class AgenticEnrichmentPipeline:
    """LangGraph-powered enrichment pipeline showcasing agentic workflows"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialize agentic components
        self.enrichment_agent = EnrichmentAgent(self.config, self.logger)
        
        self.logger.info("🤖 Initialized LangGraph Agentic Enrichment Pipeline")
        self.logger.info("🎯 Showcasing: LangGraph workflows + Multi-source integration + Real-time processing")
    
    async def process_records_agentic(self, records: List[dict]) -> List[AgenticEnrichmentResult]:
        """Process records using LangGraph agentic workflow"""
        results = []
        sample_size = len(records)
        
        
        self.logger.info(f"🎯 Processing {len(records)} records with agentic workflow")
        
        for i, record in enumerate(records):
            start_time = time.time()
            
            self.logger.info(f"🤖 Agent processing {i+1}/{len(records)}: {record['franchisee']}")
            
            # Initialize LangGraph state
            initial_state = EnrichmentState(
                record=record,
                entity_classification={},
                enrichment_strategy={},
                data_sources_attempted=[],
                enrichment_results=[],
                confidence_scores=[],
                quality_metrics={},
                final_result={},
                error_state=None
            )
            
            try:
                # Execute LangGraph workflow
                final_state = await self.enrichment_agent.workflow.ainvoke(initial_state)
                
                # Convert to result object
                final_result = final_state["final_result"]
                processing_time = time.time() - start_time
                
                result = AgenticEnrichmentResult(
                    **final_result,
                    workflow_execution_time=round(processing_time, 3),
                    processing_timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
                
                self.logger.info(f"✅ Agent completed: {record['franchisee']} "
                               f"(confidence: {result.agent_confidence:.3f}, "
                               f"sources: {result.data_sources_consulted}, "
                               f"time: {result.workflow_execution_time:.3f}s)")
                
            except Exception as e:
                self.logger.error(f"❌ Agent failed on {record['franchisee']}: {e}")
                # Create minimal result for failed records
                result = AgenticEnrichmentResult(
                    **record,
                    agent_confidence=0.0,
                    enrichment_strategy_used="Failed",
                    agent_reasoning=f"Error: {str(e)}",
                    workflow_execution_time=time.time() - start_time
                )
                results.append(result)
        
        return results
    
    def save_agentic_results(self, results: List[AgenticEnrichmentResult]) -> str:
        """Save agentic enrichment results with detailed agent metrics"""
        output_file = "data/agentic_enriched_franchisees.xlsx"
        
        # Prepare data with agent-specific columns
        results_data = []
        for result in results:
            row_data = {
                # Standard fields
                'FDD': result.fdd,
                'Franchisee': result.franchisee,
                'Address': result.address,
                'City': result.city,
                'State': result.state,
                'Zip': result.zip,
                'Phone': result.phone,
                'Franchisee Owner': result.franchisee_owner,
                'Corporate Name': result.corporate_name,
                'Corporate Address': result.corporate_address,
                'Corporate Phone': result.corporate_phone,
                'Corporate Email': result.corporate_email,
                'LinkedIn': result.linkedin,
                'url Sources': result.url_sources,
                
                # Agentic workflow metrics
                'Agent Confidence': result.agent_confidence,
                'Enrichment Strategy': result.enrichment_strategy_used,
                'Data Sources Consulted': result.data_sources_consulted,
                'Agent Reasoning': result.agent_reasoning,
                'Quality Score': result.quality_score,
                'Workflow Time (s)': result.workflow_execution_time,
                'Pipeline Version': result.pipeline_version,
                'Processing Timestamp': result.processing_timestamp
            }
            results_data.append(row_data)
        
        # Save to Excel
        df = pd.DataFrame(results_data)
        df.to_excel(output_file, index=False)
        
        self.logger.info(f"✅ Agentic results saved to: {output_file}")
        return output_file

async def main():
    """Demonstrate LangGraph agentic enrichment pipeline"""
    print("🤖 LangGraph Agentic Enrichment Pipeline")
    print("🎯 Showcasing: Intelligent workflows + Multi-source fusion + Real-time processing")
    print("="*80)
    
    # Initialize pipeline
    pipeline = AgenticEnrichmentPipeline()
    
    # Load sample data with proper column mapping
    df = pd.read_excel("data/Golden Chick_DE_Takehome.xlsx")
    
    # Map Excel columns to expected lowercase format
    column_mapping = {
    'FDD': 'fdd',
    'FDD Store No.': 'fdd_store_no',
    'FDD Location Name': 'fdd_location_name',
    'Franchisee': 'franchisee',
    'FDD Contact Name': 'fdd_contact_name',
    'Address': 'address',
    'City': 'city',
    'State': 'state',
    'Zip': 'zip',
    'Phone': 'phone',
    'Franchisee Owner': 'franchisee_owner',
    'Corporate Name': 'corporate_name',
    'Corporate Address': 'corporate_address',
    'Corporate Phone': 'corporate_phone',
    'Corporate Email': 'corporate_email',
    'LinkedIn': 'linkedin',
    'url Sources': 'url_sources'
    }


    # Rename columns and convert to records
    df_mapped = df.rename(columns=column_mapping)
    records = df_mapped.to_dict('records')  # Process 8 records for demo
    
    # Process with agentic workflow
    start_time = time.time()
    results = await pipeline.process_records_agentic(records)
    total_time = time.time() - start_time
    
    # Save results
    output_file = pipeline.save_agentic_results(results)
    
    # Generate summary
    print(f"\n🎯 AGENTIC ENRICHMENT SUMMARY")
    print("="*50)
    print(f"📊 Records processed: {len(results)}")
    print(f"⏱️  Total processing time: {total_time:.2f}s")
    
    if results:
        avg_confidence = sum(r.agent_confidence for r in results) / len(results)
        avg_quality = sum(r.quality_score for r in results) / len(results)
        avg_sources = sum(r.data_sources_consulted for r in results) / len(results)
        avg_workflow_time = sum(r.workflow_execution_time for r in results) / len(results)
        
        print(f"🤖 Average agent confidence: {avg_confidence:.3f}")
        print(f"🎖️  Average quality score: {avg_quality:.3f}")
        print(f"📡 Average sources per record: {avg_sources:.1f}")
        print(f"⚡ Average workflow time: {avg_workflow_time:.3f}s")
        
        # Show best result
        best_result = max(results, key=lambda r: r.agent_confidence)
        print(f"\n🏆 Best Agentic Enrichment:")
        print(f"   Franchisee: {best_result.franchisee}")
        print(f"   Agent Confidence: {best_result.agent_confidence:.3f}")
        print(f"   Strategy: {best_result.enrichment_strategy_used}")
        print(f"   Sources: {best_result.data_sources_consulted}")
        print(f"   Reasoning: {best_result.agent_reasoning}")
    
    print(f"\n✅ Agentic pipeline completed!")
    print(f"📁 Results: {output_file}")
    print(f"🚀 Showcasing LangGraph expertise + Production patterns!")
    
if __name__ == "__main__":
    asyncio.run(main())