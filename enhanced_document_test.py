#!/usr/bin/env python3
import sys
import os
import asyncio
from datetime import datetime
import json
import base64
import re
import uuid
import matplotlib.pyplot as plt
import io
from PIL import Image
import numpy as np

# Add the backend directory to the path so we can import the modules
sys.path.append('/app/backend')

# Import the modules to test
from enhanced_document_system import DocumentQualityGate, ProfessionalDocumentFormatter, ChartGenerator

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def record_test_result(test_name, passed, details=None):
    """Record a test result"""
    result = "PASSED" if passed else "FAILED"
    print(f"Test Result: {result}")
    
    test_result = {
        "name": test_name,
        "result": result,
        "details": details
    }
    
    test_results["tests"].append(test_result)
    
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    return passed

def print_summary():
    """Print a summary of all test results"""
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {test_results['passed']} passed, {test_results['failed']} failed")
    print("="*80)
    
    for i, test in enumerate(test_results["tests"], 1):
        result_symbol = "✅" if test["result"] == "PASSED" else "❌"
        print(f"{i}. {result_symbol} {test['name']}")
    
    print("="*80)
    overall_result = "PASSED" if test_results["failed"] == 0 else "FAILED"
    print(f"OVERALL RESULT: {overall_result}")
    print("="*80)

async def test_document_quality_gate():
    """Test the document quality gate system"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT QUALITY GATE SYSTEM")
    print("="*80)
    
    quality_gate = DocumentQualityGate()
    
    # Test 1: Early conversation (1-2 rounds) should not trigger document creation
    print("\nTest 1: Early conversation (1-2 rounds) should not trigger document creation")
    
    early_conversation = """
    Alex: I think we should consider updating our budget allocation for the next quarter.
    Mark: That's an interesting idea. What specific changes are you thinking about?
    """
    
    early_result = await quality_gate.should_create_document(
        early_conversation, 
        conversation_round=2,
        last_document_round=0,
        agents=[]
    )
    
    print(f"Quality gate decision: {early_result['should_create']}")
    print(f"Reason: {early_result['reason']}")
    
    early_test_passed = not early_result['should_create']
    if early_test_passed:
        print("✅ Quality gate correctly blocked document creation for early conversation")
    else:
        print("❌ Quality gate incorrectly allowed document creation for early conversation")
    
    record_test_result("Early conversation blocking", early_test_passed, early_result)
    
    # Test 2: Conversation with depth but no consensus should not trigger document creation
    print("\nTest 2: Conversation with depth but no consensus should not trigger document creation")
    
    no_consensus_conversation = """
    Alex: I think we should consider updating our budget allocation for the next quarter.
    Mark: That's an interesting idea. What specific changes are you thinking about?
    Alex: I believe we should allocate more resources to marketing and less to R&D.
    Mark: I'm not sure I agree. R&D is critical for our long-term success.
    Alex: But marketing could help us increase short-term revenue.
    Mark: Let's continue this discussion next week when we have more data.
    """
    
    no_consensus_result = await quality_gate.should_create_document(
        no_consensus_conversation, 
        conversation_round=6,
        last_document_round=0,
        agents=[]
    )
    
    print(f"Quality gate decision: {no_consensus_result['should_create']}")
    print(f"Reason: {no_consensus_result['reason']}")
    
    no_consensus_test_passed = not no_consensus_result['should_create']
    if no_consensus_test_passed:
        print("✅ Quality gate correctly blocked document creation for conversation without consensus")
    else:
        print("❌ Quality gate incorrectly allowed document creation for conversation without consensus")
    
    record_test_result("No consensus blocking", no_consensus_test_passed, no_consensus_result)
    
    # Test 3: Conversation with depth and consensus should trigger document creation
    print("\nTest 3: Conversation with depth and consensus should trigger document creation")
    
    consensus_conversation = """
    Alex: I think we should consider updating our budget allocation for the next quarter.
    Mark: That's an interesting idea. What specific changes are you thinking about?
    Alex: I believe we should allocate more resources to marketing and less to R&D.
    Mark: I see your point, but I'm concerned about reducing R&D funding.
    Alex: What if we reduce R&D by only 5% and increase marketing by 10%?
    Mark: That could work. We'd still maintain most of our R&D initiatives.
    Diego: I agree with this approach. The 5% reduction won't significantly impact our R&D roadmap.
    Alex: Great! After thorough discussion, we need to create a budget document with these specific timeline milestones and resource requirements.
    Mark: Yes, let's formalize our decision in a comprehensive budget allocation document.
    """
    
    consensus_result = await quality_gate.should_create_document(
        consensus_conversation, 
        conversation_round=9,
        last_document_round=0,
        agents=[]
    )
    
    print(f"Quality gate decision: {consensus_result['should_create']}")
    print(f"Reason: {consensus_result['reason']}")
    
    consensus_test_passed = consensus_result['should_create']
    if consensus_test_passed:
        print("✅ Quality gate correctly allowed document creation for conversation with consensus")
    else:
        print("❌ Quality gate incorrectly blocked document creation for conversation with consensus")
    
    record_test_result("Consensus approval", consensus_test_passed, consensus_result)
    
    # Test 4: Cooldown period should prevent immediate document creation
    print("\nTest 4: Cooldown period should prevent immediate document creation")
    
    cooldown_result = await quality_gate.should_create_document(
        consensus_conversation, 
        conversation_round=11,
        last_document_round=9,
        agents=[]
    )
    
    print(f"Quality gate decision: {cooldown_result['should_create']}")
    print(f"Reason: {cooldown_result['reason']}")
    
    cooldown_test_passed = not cooldown_result['should_create']
    if cooldown_test_passed:
        print("✅ Quality gate correctly enforced cooldown period")
    else:
        print("❌ Quality gate failed to enforce cooldown period")
    
    record_test_result("Cooldown period enforcement", cooldown_test_passed, cooldown_result)
    
    # Print summary
    print("\nDOCUMENT QUALITY GATE SUMMARY:")
    
    tests_passed = sum([early_test_passed, no_consensus_test_passed, consensus_test_passed, cooldown_test_passed])
    print(f"{tests_passed}/4 quality gate tests passed")
    
    overall_passed = tests_passed == 4
    if overall_passed:
        print("✅ Document quality gate system is working correctly")
    else:
        print("❌ Document quality gate system has issues")
    
    return overall_passed

def test_chart_generation():
    """Test the chart generation system"""
    print("\n" + "="*80)
    print("TESTING CHART GENERATION")
    print("="*80)
    
    chart_generator = ChartGenerator()
    
    # Test 1: Pie chart generation
    print("\nTest 1: Pie chart generation")
    
    budget_data = {
        "Research": 1500000,
        "Development": 2000000,
        "Marketing": 1000000,
        "Operations": 800000,
        "Administration": 500000
    }
    
    try:
        pie_chart = chart_generator.create_pie_chart(budget_data, "Budget Allocation")
        
        pie_chart_passed = pie_chart and len(pie_chart) > 1000
        if pie_chart_passed:
            print(f"✅ Pie chart generated successfully (Base64 length: {len(pie_chart)})")
            # Save a sample of the chart to verify it's valid
            sample_path = "/tmp/sample_pie_chart.png"
            with open(sample_path, "wb") as f:
                f.write(base64.b64decode(pie_chart))
            print(f"Sample pie chart saved to {sample_path}")
        else:
            print("❌ Failed to generate pie chart or output too small")
        
        record_test_result("Pie chart generation", pie_chart_passed, {"base64_length": len(pie_chart) if pie_chart else 0})
    except Exception as e:
        print(f"❌ Error generating pie chart: {e}")
        record_test_result("Pie chart generation", False, {"error": str(e)})
        pie_chart_passed = False
    
    # Test 2: Bar chart generation
    print("\nTest 2: Bar chart generation")
    
    risk_data = {
        "Market Risk": 7,
        "Technical Risk": 5,
        "Regulatory Risk": 6,
        "Operational Risk": 4,
        "Competitive Risk": 8
    }
    
    try:
        bar_chart = chart_generator.create_bar_chart(risk_data, "Risk Assessment", "Risk Categories", "Impact Level")
        
        bar_chart_passed = bar_chart and len(bar_chart) > 1000
        if bar_chart_passed:
            print(f"✅ Bar chart generated successfully (Base64 length: {len(bar_chart)})")
            # Save a sample of the chart to verify it's valid
            sample_path = "/tmp/sample_bar_chart.png"
            with open(sample_path, "wb") as f:
                f.write(base64.b64decode(bar_chart))
            print(f"Sample bar chart saved to {sample_path}")
        else:
            print("❌ Failed to generate bar chart or output too small")
        
        record_test_result("Bar chart generation", bar_chart_passed, {"base64_length": len(bar_chart) if bar_chart else 0})
    except Exception as e:
        print(f"❌ Error generating bar chart: {e}")
        record_test_result("Bar chart generation", False, {"error": str(e)})
        bar_chart_passed = False
    
    # Test 3: Timeline chart generation
    print("\nTest 3: Timeline chart generation")
    
    timeline_data = [
        {"date": "Month 1-2", "label": "Feasibility Study"},
        {"date": "Month 3-6", "label": "Technology Selection"},
        {"date": "Month 7-12", "label": "Pilot Implementation"},
        {"date": "Month 13-18", "label": "Scale Testing"},
        {"date": "Month 19-24", "label": "Full Deployment"}
    ]
    
    try:
        timeline_chart = chart_generator.create_timeline_chart(timeline_data, "Project Timeline")
        
        timeline_chart_passed = timeline_chart and len(timeline_chart) > 1000
        if timeline_chart_passed:
            print(f"✅ Timeline chart generated successfully (Base64 length: {len(timeline_chart)})")
            # Save a sample of the chart to verify it's valid
            sample_path = "/tmp/sample_timeline_chart.png"
            with open(sample_path, "wb") as f:
                f.write(base64.b64decode(timeline_chart))
            print(f"Sample timeline chart saved to {sample_path}")
        else:
            print("❌ Failed to generate timeline chart or output too small")
        
        record_test_result("Timeline chart generation", timeline_chart_passed, {"base64_length": len(timeline_chart) if timeline_chart else 0})
    except Exception as e:
        print(f"❌ Error generating timeline chart: {e}")
        record_test_result("Timeline chart generation", False, {"error": str(e)})
        timeline_chart_passed = False
    
    # Print summary
    print("\nCHART GENERATION SUMMARY:")
    
    tests_passed = sum([pie_chart_passed, bar_chart_passed, timeline_chart_passed])
    print(f"{tests_passed}/3 chart generation tests passed")
    
    overall_passed = tests_passed == 3
    if overall_passed:
        print("✅ Chart generation system is working correctly")
    else:
        print("❌ Chart generation system has issues")
    
    return overall_passed

def test_professional_document_formatting():
    """Test the professional document formatting system"""
    print("\n" + "="*80)
    print("TESTING PROFESSIONAL DOCUMENT FORMATTING")
    print("="*80)
    
    formatter = ProfessionalDocumentFormatter()
    
    # Test 1: Basic document formatting
    print("\nTest 1: Basic document formatting")
    
    basic_content = """# Project Implementation Plan

## Executive Summary
This document outlines the implementation plan for our new product launch.

## Timeline
- Phase 1: Research and Planning (Q1)
- Phase 2: Development (Q2)
- Phase 3: Testing (Q3)
- Phase 4: Launch (Q4)

## Budget Allocation
- Research: $50,000
- Development: $200,000
- Marketing: $100,000
- Operations: $75,000

## Risk Assessment
1. Market competition
2. Technical challenges
3. Resource constraints
4. Regulatory issues
"""
    
    try:
        formatted_doc = formatter.format_document(
            basic_content,
            "Project Implementation Plan",
            ["Alex Chen", "Mark Castellano"],
            "implementation",
            "The team discussed the implementation plan for the new product launch, including timeline, budget, and risks."
        )
        
        # Save the formatted document to a file for inspection
        with open("/tmp/formatted_doc.html", "w") as f:
            f.write(formatted_doc)
        print(f"Formatted document saved to /tmp/formatted_doc.html")
        
        # Check if the formatted document contains HTML structure
        has_html_structure = "<!DOCTYPE html>" in formatted_doc and "</html>" in formatted_doc
        if has_html_structure:
            print("✅ Document has proper HTML structure")
        else:
            print("❌ Document is missing proper HTML structure")
        
        # Check if the formatted document contains styling
        has_css_styling = "<style>" in formatted_doc and "</style>" in formatted_doc
        if has_css_styling:
            print("✅ Document has CSS styling")
        else:
            print("❌ Document is missing CSS styling")
        
        # Check if the formatted document contains the title
        has_title = "Project Implementation Plan" in formatted_doc
        if has_title:
            print("✅ Document contains the correct title")
        else:
            print("❌ Document is missing the correct title")
        
        # Check if the formatted document contains the authors
        has_authors = "Alex Chen" in formatted_doc and "Mark Castellano" in formatted_doc
        if has_authors:
            print("✅ Document contains the correct authors")
        else:
            print("❌ Document is missing the correct authors")
        
        basic_formatting_passed = has_html_structure and has_css_styling and has_title and has_authors
        record_test_result("Basic document formatting", basic_formatting_passed, {
            "has_html_structure": has_html_structure,
            "has_css_styling": has_css_styling,
            "has_title": has_title,
            "has_authors": has_authors
        })
    except Exception as e:
        print(f"❌ Error formatting basic document: {e}")
        record_test_result("Basic document formatting", False, {"error": str(e)})
        basic_formatting_passed = False
    
    # Test 2: Document with charts
    print("\nTest 2: Document with charts")
    
    chart_content = """# Budget Analysis

## Executive Summary
This document analyzes our budget allocation for the upcoming fiscal year.

## Budget Breakdown
- Research: $1,500,000
- Development: $2,000,000
- Marketing: $1,000,000
- Operations: $800,000
- Administration: $500,000

## Timeline
- Q1: Planning and resource allocation
- Q2: Initial implementation
- Q3: Mid-year review and adjustments
- Q4: Final evaluation and planning for next year

## Risk Assessment
1. Market volatility (High)
2. Resource constraints (Medium)
3. Competitive pressure (High)
4. Regulatory changes (Low)
5. Technical challenges (Medium)
"""
    
    try:
        chart_doc = formatter.format_document(
            chart_content,
            "Annual Budget Analysis",
            ["Finance Team", "Executive Committee"],
            "budget",
            "The team discussed the budget allocation for the upcoming fiscal year, including breakdown by department, timeline, and risk assessment."
        )
        
        # Save the formatted document to a file for inspection
        with open("/tmp/chart_doc.html", "w") as f:
            f.write(chart_doc)
        print(f"Chart document saved to /tmp/chart_doc.html")
        
        # Check if the formatted document contains base64 images (charts)
        has_charts = "data:image/png;base64," in chart_doc
        if has_charts:
            print("✅ Document contains embedded charts")
        else:
            print("❌ Document is missing embedded charts")
        
        # Check if the formatted document contains chart containers
        has_chart_containers = "chart-container" in chart_doc
        if has_chart_containers:
            print("✅ Document has proper chart containers")
        else:
            print("❌ Document is missing chart containers")
        
        chart_formatting_passed = has_charts and has_chart_containers
        record_test_result("Document with charts", chart_formatting_passed, {
            "has_charts": has_charts,
            "has_chart_containers": has_chart_containers
        })
    except Exception as e:
        print(f"❌ Error formatting document with charts: {e}")
        record_test_result("Document with charts", False, {"error": str(e)})
        chart_formatting_passed = False
    
    # Print summary
    print("\nPROFESSIONAL DOCUMENT FORMATTING SUMMARY:")
    
    tests_passed = sum([basic_formatting_passed, chart_formatting_passed])
    print(f"{tests_passed}/2 document formatting tests passed")
    
    overall_passed = tests_passed == 2
    if overall_passed:
        print("✅ Professional document formatting system is working correctly")
    else:
        print("❌ Professional document formatting system has issues")
    
    return overall_passed

async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TESTING ENHANCED DOCUMENT GENERATION SYSTEM")
    print("="*80)
    
    # Test the document quality gate system
    quality_gate_success = await test_document_quality_gate()
    
    # Test the chart generation system
    chart_success = test_chart_generation()
    
    # Test the professional document formatting system
    formatting_success = test_professional_document_formatting()
    
    # Print summary of all tests
    print_summary()
    
    print("\n" + "="*80)
    print("ENHANCED DOCUMENT GENERATION SYSTEM ASSESSMENT")
    print("="*80)
    
    if quality_gate_success:
        print("✅ Document quality gate system is working correctly")
        print("✅ Early conversations (1-2 rounds) don't trigger document creation")
        print("✅ Only conversations with depth and consensus create documents")
        print("✅ Cooldown period between document creations is enforced")
    else:
        print("❌ Document quality gate system has issues")
    
    if chart_success:
        print("✅ Chart generation system is working correctly")
        print("✅ System can generate pie charts for budget allocation")
        print("✅ System can generate bar charts for risk assessment")
        print("✅ System can generate timeline charts for project milestones")
    else:
        print("❌ Chart generation system has issues")
    
    if formatting_success:
        print("✅ Professional document formatting system is working correctly")
        print("✅ Documents have proper HTML structure with CSS styling")
        print("✅ Documents include proper headers, sections, and metadata")
        print("✅ Charts are embedded in documents where appropriate")
    else:
        print("❌ Professional document formatting system has issues")
    
    print("="*80)
    
    return quality_gate_success and chart_success and formatting_success

if __name__ == "__main__":
    asyncio.run(main())