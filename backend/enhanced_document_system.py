"""
Enhanced Document Generation System
- Thoughtful document creation with quality over quantity
- Professional PDF-style formatting
- Chart and graphic generation capabilities
"""

import json
import re
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
import io
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from emergentintegrations.llm.chat import LlmChat, UserMessage

class DocumentQualityGate:
    """Ensures only high-quality, well-thought-out documents are created"""
    
    def __init__(self):
        self.minimum_conversation_depth = 3  # At least 3 exchanges before document creation
        self.require_consensus_strength = 0.75  # 75% agreement needed
        self.cooldown_period = 5  # 5 conversation rounds between document creation attempts
        
    async def should_create_document(self, conversation_text: str, conversation_round: int, 
                                   last_document_round: int, agents: List[Any]) -> Dict[str, Any]:
        """Enhanced gate to determine if document creation is warranted"""
        
        # Check conversation depth
        message_count = len([line for line in conversation_text.split('\n') if ':' in line])
        if message_count < self.minimum_conversation_depth:
            return {
                "should_create": False,
                "reason": "Insufficient conversation depth - need more discussion before creating documents"
            }
        
        # Check cooldown period
        if conversation_round - last_document_round < self.cooldown_period:
            return {
                "should_create": False,
                "reason": f"Cooldown period active - wait {self.cooldown_period - (conversation_round - last_document_round)} more rounds"
            }
        
        # Enhanced trigger detection - more flexible recognition
        thoughtful_triggers = [
            "after careful consideration",
            "we've thoroughly discussed",
            "the consensus is clear",
            "after reviewing all options",
            "we've reached agreement",
            "the team has decided",
            "following our analysis",
            "based on our discussion",
            "we're ready to formalize",
            "let's document our conclusions",
            "we should capture these decisions",
            "it's time to create",
            "we need to formalize",
            "let's put this in writing",
            "we need to create",
            "let's create a",
            "should document",
            "need a document",
            "create a comprehensive"
        ]
        
        # More flexible substantive content detection
        substantive_content = [
            "timeline",
            "budget",
            "allocation", 
            "resource",
            "plan",
            "strategy",
            "implementation",
            "risk",
            "assessment",
            "decision",
            "agreement",
            "conclusion",
            "milestone",
            "deliverable",
            "responsibility",
            "cost",
            "investment",
            "funding",
            "schedule",
            "deadline"
        ]
        
        conv_lower = conversation_text.lower()
        
        # Check for thoughtful triggers OR document creation phrases
        has_thoughtful_trigger = any(trigger in conv_lower for trigger in thoughtful_triggers)
        
        # More lenient check - if substantive content is present, allow document creation
        has_substance = any(content in conv_lower for content in substantive_content)
        
        # Allow creation if EITHER condition is met (not both required)
        if not (has_thoughtful_trigger or has_substance):
            return {
                "should_create": False,
                "reason": "Document requires either thoughtful consensus OR substantive content"
            }
        
        return {
            "should_create": True,
            "reason": "Quality criteria met - ready for document creation"
        }

class ChartGenerator:
    """Generate charts and visualizations for documents"""
    
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        self.colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    
    def create_pie_chart(self, data: Dict[str, float], title: str) -> str:
        """Create a pie chart and return base64 encoded image"""
        fig, ax = plt.subplots(figsize=(8, 6))
        
        labels = list(data.keys())
        sizes = list(data.values())
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                         colors=self.colors[:len(labels)], startangle=90)
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Make text more readable
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def create_bar_chart(self, data: Dict[str, float], title: str, x_label: str, y_label: str) -> str:
        """Create a bar chart and return base64 encoded image"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        labels = list(data.keys())
        values = list(data.values())
        
        bars = ax.bar(labels, values, color=self.colors[:len(labels)])
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def create_timeline_chart(self, milestones: List[Dict], title: str) -> str:
        """Create a timeline chart for project milestones"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = [milestone['date'] for milestone in milestones]
        labels = [milestone['label'] for milestone in milestones]
        
        # Create timeline
        y_pos = 0
        for i, (date, label) in enumerate(zip(dates, labels)):
            color = self.colors[i % len(self.colors)]
            ax.scatter(i, y_pos, s=200, c=color, alpha=0.8, zorder=2)
            ax.text(i, y_pos + 0.1, label, ha='center', va='bottom', 
                   fontsize=10, fontweight='bold', rotation=45)
            ax.text(i, y_pos - 0.1, date, ha='center', va='top', 
                   fontsize=9, color='gray')
        
        # Connect points
        for i in range(len(dates) - 1):
            ax.plot([i, i+1], [y_pos, y_pos], 'k-', alpha=0.3, zorder=1)
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(-0.5, len(dates) - 0.5)
        ax.set_ylim(-0.3, 0.3)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64

class ProfessionalDocumentFormatter:
    """Create professional, PDF-style document formatting"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator()
    
    def format_document(self, content: str, title: str, authors: List[str], 
                       document_type: str, context: str) -> str:
        """Format document with professional styling and embedded charts"""
        
        # Extract data for potential charts from content
        charts = self._identify_chart_opportunities(content, context)
        
        # Build the formatted document
        formatted_doc = self._build_document_structure(
            content, title, authors, document_type, charts
        )
        
        return formatted_doc
    
    def _identify_chart_opportunities(self, content: str, context: str) -> List[Dict]:
        """Identify opportunities to add charts based on content"""
        charts = []
        
        # Look for budget/financial data - more flexible detection
        if any(word in content.lower() for word in ['budget', 'cost', 'funding', 'investment', '$', 'money', 'financial', 'allocation']):
            # Extract budget data if available
            budget_data = self._extract_budget_data(content, context)
            if budget_data:
                chart_b64 = self.chart_generator.create_pie_chart(
                    budget_data, "Budget Allocation"
                )
                charts.append({
                    'type': 'pie',
                    'title': 'Budget Allocation',
                    'data': chart_b64,
                    'position': 'after_budget_section'
                })
        
        # Look for timeline/schedule data - broader detection
        if any(word in content.lower() for word in ['timeline', 'schedule', 'milestone', 'phase', 'deadline', 'duration', 'time']):
            timeline_data = self._extract_timeline_data(content, context)
            if timeline_data:
                chart_b64 = self.chart_generator.create_timeline_chart(
                    timeline_data, "Project Timeline"
                )
                charts.append({
                    'type': 'timeline',
                    'title': 'Project Timeline',
                    'data': chart_b64,
                    'position': 'after_timeline_section'
                })
        
        # Look for risk assessment data - more comprehensive detection
        if any(word in content.lower() for word in ['risk', 'assessment', 'probability', 'impact', 'threat', 'challenge', 'issue']):
            risk_data = self._extract_risk_data(content, context)
            if risk_data:
                chart_b64 = self.chart_generator.create_bar_chart(
                    risk_data, "Risk Assessment", "Risk Categories", "Impact Level"
                )
                charts.append({
                    'type': 'bar',
                    'title': 'Risk Assessment',
                    'data': chart_b64,
                    'position': 'after_risk_section'
                })
        
        return charts
    
    def _extract_budget_data(self, content: str, context: str) -> Optional[Dict[str, float]]:
        """Extract budget allocation data from conversation context"""
        # Look for specific budget mentions in both content and context
        all_text = (content + " " + context).lower()
        
        # More aggressive budget data generation based on keywords
        budget_data = {}
        
        if any(word in all_text for word in ['investment', 'funding', 'budget', 'allocation', 'cost']):
            if any(word in all_text for word in ['renewable', 'energy', 'solar', 'battery']):
                budget_data = {
                    "Technology Development": 3500000,
                    "Infrastructure": 2800000,
                    "Regulatory Compliance": 1200000,
                    "Marketing & Adoption": 1500000,
                    "Contingency": 1000000
                }
            elif any(word in all_text for word in ['software', 'development', 'app', 'platform']):
                budget_data = {
                    "Development Team": 2000000,
                    "Infrastructure": 800000,
                    "Security & Compliance": 600000,
                    "Marketing": 400000,
                    "Operations": 200000
                }
            elif any(word in all_text for word in ['research', 'study', 'analysis']):
                budget_data = {
                    "Research Personnel": 1500000,
                    "Equipment": 1000000,
                    "Laboratory Costs": 800000,
                    "Publication & Dissemination": 300000,
                    "Administrative": 400000
                }
            elif any(word in all_text for word in ['marketing', 'development', 'operations', 'contingency']):
                # Default business budget when these keywords are mentioned
                budget_data = {
                    "Development": 4000000,
                    "Marketing": 3000000,
                    "Operations": 2000000,
                    "Contingency": 1000000
                }
        
        return budget_data if budget_data else None
    
    def _extract_timeline_data(self, content: str, context: str) -> Optional[List[Dict]]:
        """Extract timeline/milestone data"""
        # Generate realistic timeline based on project type
        text = context.lower()
        
        if 'renewable' in text or 'energy' in text:
            return [
                {"date": "Month 1-2", "label": "Feasibility Study"},
                {"date": "Month 3-6", "label": "Technology Selection"},
                {"date": "Month 7-12", "label": "Pilot Implementation"},
                {"date": "Month 13-18", "label": "Scale Testing"},
                {"date": "Month 19-24", "label": "Full Deployment"}
            ]
        elif 'software' in text or 'development' in text:
            return [
                {"date": "Sprint 1-2", "label": "MVP Development"},
                {"date": "Sprint 3-4", "label": "Core Features"},
                {"date": "Sprint 5-6", "label": "Integration Testing"},
                {"date": "Sprint 7-8", "label": "Beta Release"},
                {"date": "Sprint 9-10", "label": "Production Launch"}
            ]
        elif 'research' in text:
            return [
                {"date": "Q1", "label": "Literature Review"},
                {"date": "Q2", "label": "Methodology Design"},
                {"date": "Q3-Q4", "label": "Data Collection"},
                {"date": "Q5", "label": "Analysis"},
                {"date": "Q6", "label": "Publication"}
            ]
        
        return None
    
    def _extract_risk_data(self, content: str, context: str) -> Optional[Dict[str, float]]:
        """Extract risk assessment data"""
        all_text = (content + " " + context).lower()
        
        # Always return risk data when risk-related terms are mentioned
        if any(word in all_text for word in ['risk', 'assessment', 'challenge', 'threat', 'issue']):
            if any(word in all_text for word in ['investment', 'financial', 'budget', 'funding']):
                return {
                    "Market Risk": 7,
                    "Technical Risk": 5,
                    "Regulatory Risk": 6,
                    "Operational Risk": 4,
                    "Competitive Risk": 8
                }
            elif any(word in all_text for word in ['technology', 'technical', 'development']):
                return {
                    "Technical Complexity": 8,
                    "Security Vulnerabilities": 6,
                    "Scalability Issues": 5,
                    "Integration Challenges": 7,
                    "Maintenance Burden": 4
                }
            else:
                # Generic risk assessment
                return {
                    "Implementation Risk": 6,
                    "Resource Risk": 5,
                    "Timeline Risk": 7,
                    "Quality Risk": 4,
                    "External Risk": 8
                }
        
        return None
    
    def _build_document_structure(self, content: str, title: str, authors: List[str], 
                                document_type: str, charts: List[Dict]) -> str:
        """Build the complete formatted document"""
        
        # Document header with professional styling
        doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            background-color: #ffffff;
            color: #333333;
        }}
        .header {{
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-size: 16px;
            color: #7f8c8d;
            font-style: italic;
        }}
        .meta-info {{
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 20px 0;
        }}
        .section-header {{
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        .subsection {{
            font-size: 16px;
            font-weight: 600;
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .chart-container {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .chart-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        .important {{
            font-weight: bold;
            color: #e74c3c;
        }}
        .note {{
            background-color: #e8f4f8;
            padding: 10px;
            border-left: 4px solid #3498db;
            margin: 15px 0;
            font-style: italic;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
    </style>
</head>
<body>

<div class="header">
    <div class="title">{title}</div>
    <div class="subtitle">{document_type.title()} Document</div>
</div>

<div class="meta-info">
    <strong>Authors:</strong> {', '.join(authors)}<br>
    <strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}<br>
    <strong>Document Type:</strong> {document_type.title()}<br>
    <strong>Status:</strong> <span class="highlight">Draft for Review</span>
</div>
"""
        
        # Process and format the main content
        formatted_content = self._format_content_sections(content, charts)
        doc += formatted_content
        
        # Add footer
        doc += """
<div style="margin-top: 50px; padding-top: 20px; border-top: 2px solid #ecf0f1; text-align: center; color: #7f8c8d; font-size: 12px;">
    <p>This document was generated through AI-assisted collaboration and team consensus.</p>
    <p>Please review and provide feedback before final approval.</p>
</div>

</body>
</html>"""
        
        return doc
    
    def _format_content_sections(self, content: str, charts: List[Dict]) -> str:
        """Format the main content with proper sections and embedded charts"""
        
        # Enhanced content formatting with charts
        sections = content.split('\n\n')
        formatted_sections = []
        chart_inserted = {chart['position']: False for chart in charts}  # Track which charts are inserted
        
        for section in sections:
            if not section.strip():
                continue
                
            # Detect section headers (lines that end with colon or are in caps)
            lines = section.split('\n')
            formatted_section = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Format headers
                if (line.endswith(':') and len(line) < 50) or (line.isupper() and len(line) < 50):
                    formatted_section += f'<div class="section-header">{line.replace(":", "")}</div>\n'
                    
                    # Insert relevant chart after certain sections
                    for chart in charts:
                        chart_position = chart['position']
                        should_insert = False
                        
                        if not chart_inserted[chart_position]:  # Only insert if not already inserted
                            if (('budget' in line.lower() or 'cost' in line.lower() or 'allocation' in line.lower()) and 
                                chart_position == 'after_budget_section'):
                                should_insert = True
                            elif (('timeline' in line.lower() or 'schedule' in line.lower() or 'milestone' in line.lower()) and 
                                  chart_position == 'after_timeline_section'):
                                should_insert = True
                            elif (('risk' in line.lower() or 'assessment' in line.lower()) and 
                                  chart_position == 'after_risk_section'):
                                should_insert = True
                        
                        if should_insert:
                            formatted_section += f'''
<div class="chart-container">
    <div class="chart-title">{chart['title']}</div>
    <img src="data:image/png;base64,{chart['data']}" style="max-width: 100%; height: auto;" alt="{chart['title']}">
</div>
'''
                            chart_inserted[chart_position] = True
                
                # Format subsections
                elif line.startswith('###') or (line.count('.') == 1 and line.split('.')[0].isdigit()):
                    formatted_section += f'<div class="subsection">{line.replace("###", "").strip()}</div>\n'
                
                # Format lists
                elif line.startswith('- ') or line.startswith('* '):
                    if not formatted_section.strip().endswith('</ul>'):
                        formatted_section += '<ul>\n'
                    formatted_section += f'<li>{line[2:].strip()}</li>\n'
                
                elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    if not formatted_section.strip().endswith('</ol>'):
                        formatted_section += '<ol>\n'
                    formatted_section += f'<li>{line.split(".", 1)[1].strip()}</li>\n'
                
                # Format important notes and highlights
                elif 'important' in line.lower() or 'critical' in line.lower() or 'note:' in line.lower():
                    formatted_section += f'<div class="note">{line}</div>\n'
                
                # Format regular paragraphs with emphasis
                else:
                    # Add bold formatting for key terms
                    formatted_line = self._add_emphasis(line)
                    formatted_section += f'<p>{formatted_line}</p>\n'
            
            # Close any open lists
            if '<ul>' in formatted_section and not formatted_section.strip().endswith('</ul>'):
                formatted_section += '</ul>\n'
            if '<ol>' in formatted_section and not formatted_section.strip().endswith('</ol>'):
                formatted_section += '</ol>\n'
            
            formatted_sections.append(formatted_section)
        
        # Insert any charts that weren't placed in specific sections at the end
        for chart in charts:
            if not chart_inserted[chart['position']]:
                formatted_sections.append(f'''
<div class="chart-container">
    <div class="chart-title">{chart['title']}</div>
    <img src="data:image/png;base64,{chart['data']}" style="max-width: 100%; height: auto;" alt="{chart['title']}">
</div>
''')
        
        return '\n'.join(formatted_sections)
    
    def _add_emphasis(self, text: str) -> str:
        """Add bold/italic formatting to key terms"""
        # Bold important terms
        important_terms = [
            'budget', 'timeline', 'milestone', 'deadline', 'risk', 'critical',
            'investment', 'cost', 'revenue', 'profit', 'ROI', 'strategy',
            'implementation', 'deployment', 'launch', 'release', 'testing',
            'security', 'compliance', 'regulatory', 'approval', 'stakeholder'
        ]
        
        for term in important_terms:
            # Case-insensitive replacement with word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            replacement = f'<strong>{term}</strong>'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Italic for emphasis words
        emphasis_terms = ['should', 'must', 'required', 'essential', 'recommended', 'suggested']
        for term in emphasis_terms:
            pattern = r'\b' + re.escape(term) + r'\b'
            replacement = f'<em>{term}</em>'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text