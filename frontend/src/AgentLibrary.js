import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from './App';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : 'http://localhost:8001/api';

// Add styles for line clamping
const styles = `
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement("style");
  styleSheet.type = "text/css";
  styleSheet.innerText = styles;
  document.head.appendChild(styleSheet);
}

// Healthcare Categories with detailed agent data
const healthcareCategories = {
  medical: {
    name: "Medical",
    icon: "🩺",
    agents: [
      {
        id: 1,
        name: "Dr. Sarah Chen",
        archetype: "Archetype: Scientist",
        title: "Precision Medicine Oncologist",
        goal: "To advance personalized medicine through genomic research and clinical application.",
        background: "Harvard-trained physician-scientist with 15 years in oncology research. Led breakthrough studies on BRCA mutations at Dana-Farber Cancer Institute. Currently heads precision medicine initiative at major academic medical center. Published 120+ peer-reviewed papers. Fluent in Mandarin, enabling collaboration with Chinese research institutions.",
        expertise: "Precision Oncology, Genomic Medicine, Clinical Trials, Biomarkers, Pharmacogenomics",
        memories: "Witnessed the first successful CRISPR gene therapy trial in 2019 that saved a 12-year-old with sickle cell disease. Lost her mentor Dr. Williams to pancreatic cancer in 2020, driving her obsession with early detection biomarkers. Successfully identified a novel mutation pattern in Asian populations that led to breakthrough treatment protocol. Failed initial clinical trial in 2021 taught her importance of patient stratification. Remembers the exact moment seeing microscopic cancer cells respond to personalized therapy for the first time. Knowledge Sources: https://www.cancer.gov/, https://www.genome.gov/, https://clinicaltrials.gov/, https://www.nejm.org/, https://www.nature.com/subjects/cancer/",
        knowledge: "https://www.cancer.gov/, https://www.genome.gov/, https://clinicaltrials.gov/, https://www.nejm.org/, https://www.nature.com/subjects/cancer/",
        avatar: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 2,
        name: "Dr. Marcus Rodriguez",
        archetype: "The Leader",
        goal: "To advance global health equity through innovative healthcare delivery models in underserved communities.",
        background: "Emergency medicine physician and global health advocate. Founded medical nonprofit serving rural communities. Led disaster response missions in 15 countries. Expertise in telemedicine and remote healthcare delivery.",
        expertise: "Emergency Medicine, Global Health, Telemedicine, Disaster Medicine, Healthcare Equity",
        memories: "Established telemedicine network serving 50,000 patients in rural areas. Led medical response to Hurricane Maria in Puerto Rico. Successfully reduced emergency room wait times by 60% through triage optimization. Failed to prevent hospital closure in rural community in 2018.",
        knowledge: "https://www.who.int/, https://www.msf.org/, https://www.acep.org/, https://www.ahrq.gov/, https://www.cdc.gov/",
        avatar: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 3,
        name: "Dr. Katherine Vale",
        archetype: "The Mediator",
        goal: "To bridge the gap between specialist and primary care through collaborative medicine and patient-centered approaches.",
        background: "Family medicine physician specializing in care coordination. Developed innovative patient-centered medical home model. Expert in managing complex chronic diseases and multi-specialty care coordination.",
        expertise: "Family Medicine, Care Coordination, Chronic Disease Management, Patient-Centered Care, Quality Improvement",
        memories: "Coordinated care for diabetic patient with 8 specialists, achieving 70% improvement in glucose control. Mediated complex family conference for end-of-life care decisions. Reduced hospital readmissions by 45% through care coordination program.",
        knowledge: "https://www.aafp.org/, https://www.pcpcc.org/, https://www.cms.gov/, https://www.ihi.org/, https://www.ahrq.gov/",
        avatar: "https://images.unsplash.com/photo-1594824804732-ca7d6b8ae32a?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  pharmaceutical: {
    name: "Pharmaceutical",
    icon: "💊",
    agents: []
  },
  biotechnology: {
    name: "Biotechnology", 
    icon: "🧬",
    agents: []
  },
  veterinary: {
    name: "Veterinary",
    icon: "🐕",
    agents: []
  },
  publicHealth: {
    name: "Public Health",
    icon: "🏥",
    agents: []
  },
  nutrition: {
    name: "Nutrition & Dietetics",
    icon: "🥗",
    agents: []
  },
  physicalTherapy: {
    name: "Physical Therapy",
    icon: "🏃‍♂️",
    agents: []
  },
  nursing: {
    name: "Nursing",
    icon: "👩‍⚕️",
    agents: []
  },
  medicalResearch: {
    name: "Medical Research",
    icon: "🔬",
    agents: []
  },
  epidemiology: {
    name: "Epidemiology",
    icon: "📊",
    agents: []
  }
};

// Sectors configuration
const sectors = {
  healthcare: {
    name: "Healthcare & Life Sciences",
    icon: "🏥",
    categories: healthcareCategories
  }
};

const AgentLibrary = ({ isOpen, onClose, onAddAgent }) => {
  const { token } = useAuth();
  const [selectedSector, setSelectedSector] = useState('healthcare');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedAgentDetails, setSelectedAgentDetails] = useState(null);
  const [addingAgents, setAddingAgents] = useState(new Set());
  const [addedAgents, setAddedAgents] = useState(new Set());
  const timeoutRefs = useRef(new Map());

  // Don't render if not open
  if (!isOpen) return null;

  const handleAddAgent = async (agent) => {
    if (!onAddAgent) return;
    
    setAddingAgents(prev => new Set(prev).add(agent.id));
    
    try {
      // Transform agent data to match backend expectations exactly as App.js expects
      const agentData = {
        name: agent.name,
        archetype: agent.archetype,
        goal: agent.goal,
        background: agent.background,
        expertise: agent.expertise,
        memory_summary: `${agent.memories} Knowledge Sources: ${agent.knowledge}`,
        avatar_url: agent.avatar, // Use avatar_url field that App.js expects
        avatar_prompt: `Professional headshot of ${agent.name}, ${agent.title || 'medical professional'}, professional lighting, business attire`
      };
      
      const result = await onAddAgent(agentData);
      
      if (result && result.success) {
        setAddedAgents(prev => new Set(prev).add(agent.id));
        
        // Clear any existing timeout for this agent
        if (timeoutRefs.current.has(agent.id)) {
          clearTimeout(timeoutRefs.current.get(agent.id));
        }
        
        // Set timeout to remove the "Added" status after 3 seconds
        const timeoutId = setTimeout(() => {
          setAddedAgents(prev => {
            const newSet = new Set(prev);
            newSet.delete(agent.id);
            return newSet;
          });
          timeoutRefs.current.delete(agent.id);
        }, 3000);
        
        timeoutRefs.current.set(agent.id, timeoutId);
        
        console.log('Agent added successfully:', result.message);
      } else {
        console.error('Failed to add agent:', result?.message || 'Unknown error');
      }
      
    } catch (error) {
      console.error('Failed to add agent:', error);
    }
    
    setAddingAgents(prev => {
      const newSet = new Set(prev);
      newSet.delete(agent.id);
      return newSet;
    });
  };

  const currentSector = sectors[selectedSector];
  const currentCategory = selectedCategory ? currentSector.categories[selectedCategory] : null;

  return (
    <>
      {/* Main Agent Library Modal */}
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden shadow-2xl">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">📚 Agent Library</h2>
                <p className="text-purple-100 mt-1">Choose from professionally crafted agent profiles</p>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:text-purple-200 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-purple-700 transition-colors"
              >
                ×
              </button>
            </div>
          </div>

          <div className="flex h-[600px]">
            {/* Sidebar */}
            <div className="w-64 bg-gray-50 border-r p-4">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">SECTORS</h3>
              <div className="space-y-2">
                {Object.entries(sectors).map(([key, sector]) => (
                  <button
                    key={key}
                    onClick={() => {
                      setSelectedSector(key);
                      setSelectedCategory(null);
                    }}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedSector === key
                        ? 'bg-purple-100 text-purple-800 border-l-4 border-purple-600'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <span className="text-lg mr-2">{sector.icon}</span>
                    {sector.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              {!selectedCategory ? (
                // Categories View
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-6">
                    {currentSector.icon} {currentSector.name}
                  </h3>
                  <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {Object.entries(currentSector.categories).map(([key, category]) => (
                      <button
                        key={key}
                        onClick={() => setSelectedCategory(key)}
                        className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-purple-300 hover:shadow-md transition-all text-center group"
                      >
                        <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">
                          {category.icon}
                        </div>
                        <div className="text-sm font-medium text-gray-800">
                          {category.name}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {category.agents.length} agents
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                // Agents View
                <div>
                  <div className="flex items-center mb-6">
                    <button
                      onClick={() => setSelectedCategory(null)}
                      className="text-purple-600 hover:text-purple-800 font-medium mr-4 flex items-center"
                    >
                      ← Back
                    </button>
                    <h3 className="text-xl font-bold text-gray-800">
                      {currentCategory.icon} {currentCategory.name}
                    </h3>
                  </div>

                  {currentCategory.agents.length > 0 ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                      {currentCategory.agents.map((agent) => (
                        <div key={agent.id} className="bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                          <div className="p-4">
                            <div className="flex items-start space-x-3">
                              <img
                                src={agent.avatar}
                                alt={agent.name}
                                className="w-12 h-12 rounded-full object-cover flex-shrink-0"
                              />
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-gray-900 text-sm">{agent.name}</h4>
                                <p className="text-xs text-gray-600 mt-1">{agent.archetype}</p>
                              </div>
                            </div>
                            
                            <div className="mt-3">
                              <div className="mb-2">
                                <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">ARCHETYPE</span>
                                <p className="text-xs text-gray-600 mt-1">{agent.archetype}</p>
                              </div>
                              
                              <div className="mb-2">
                                <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">GOAL</span>
                                <p className="text-xs text-gray-600 mt-1 line-clamp-2">{agent.goal}</p>
                              </div>
                              
                              <div className="mb-3">
                                <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">EXPERTISE</span>
                                <p className="text-xs text-gray-600 mt-1 line-clamp-2">{agent.expertise}</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="px-4 pb-4 space-y-2">
                            <button
                              onClick={() => setSelectedAgentDetails(agent)}
                              className="w-full border border-blue-500 text-blue-600 py-2 px-3 rounded text-xs font-medium hover:bg-blue-50 transition-colors"
                            >
                              🔍 View Full Details
                            </button>
                            <button
                              onClick={() => handleAddAgent(agent)}
                              disabled={addingAgents.has(agent.id)}
                              className={`w-full py-2 px-3 rounded text-xs font-medium transition-colors ${
                                addedAgents.has(agent.id)
                                  ? 'bg-green-100 text-green-800 border border-green-200'
                                  : addingAgents.has(agent.id)
                                  ? 'bg-gray-300 text-gray-500'
                                  : 'bg-purple-600 text-white hover:bg-purple-700'
                              }`}
                            >
                              {addedAgents.has(agent.id) 
                                ? '✅ Added' 
                                : addingAgents.has(agent.id) 
                                ? 'Adding...' 
                                : 'Add Agent'
                              }
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">{currentCategory.icon}</div>
                      <h4 className="text-xl font-bold text-gray-800 mb-2">Agents Coming Soon</h4>
                      <p className="text-gray-600 max-w-md mx-auto">
                        We're working on adding professional agents for {currentCategory.name}. 
                        Check back soon for expertly crafted profiles in this category.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Agent Details Modal */}
      {selectedAgentDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto relative">
            {/* Blue Header with Agent Info */}
            <div className="bg-blue-500 text-white p-6 rounded-t-lg relative">
              <button
                onClick={() => setSelectedAgentDetails(null)}
                className="absolute top-4 right-4 text-white hover:text-gray-200 text-xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-blue-600 transition-colors"
              >
                ×
              </button>
              
              <div className="flex items-center space-x-4">
                <img
                  src={selectedAgentDetails.avatar}
                  alt={selectedAgentDetails.name}
                  className="w-16 h-16 rounded-full object-cover border-2 border-white"
                />
                <div>
                  <h3 className="text-xl font-bold">{selectedAgentDetails.name}</h3>
                  <p className="text-blue-100">{selectedAgentDetails.title || "Precision Medicine Oncologist"}</p>
                  <p className="text-blue-200 text-sm mt-1">{selectedAgentDetails.archetype}</p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              <div>
                <h4 className="font-bold text-gray-800 mb-3 flex items-center">
                  <span className="mr-2">🎯</span>
                  Goal
                </h4>
                <p className="text-gray-700 leading-relaxed">{selectedAgentDetails.goal}</p>
              </div>

              <div>
                <h4 className="font-bold text-gray-800 mb-3 flex items-center">
                  <span className="mr-2">🧠</span>
                  Expertise
                </h4>
                <p className="text-gray-700 leading-relaxed">{selectedAgentDetails.expertise}</p>
              </div>

              <div>
                <h4 className="font-bold text-gray-800 mb-3 flex items-center">
                  <span className="mr-2">📋</span>
                  Background
                </h4>
                <p className="text-gray-700 leading-relaxed">{selectedAgentDetails.background}</p>
              </div>

              <div>
                <h4 className="font-bold text-gray-800 mb-3 flex items-center">
                  <span className="mr-2">🧠</span>
                  Key Memories & Knowledge
                </h4>
                <p className="text-gray-700 leading-relaxed mb-3">{selectedAgentDetails.memories}</p>
                <p className="text-sm text-blue-600 break-words">{selectedAgentDetails.knowledge}</p>
              </div>
            </div>

            {/* Bottom Buttons */}
            <div className="px-6 pb-6 flex space-x-3">
              <button
                onClick={() => setSelectedAgentDetails(null)}
                className="flex-1 bg-white border border-gray-300 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => handleAddAgent(selectedAgentDetails)}
                disabled={addingAgents.has(selectedAgentDetails.id)}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-colors ${
                  addedAgents.has(selectedAgentDetails.id)
                    ? 'bg-green-100 text-green-800'
                    : addingAgents.has(selectedAgentDetails.id)
                    ? 'bg-gray-300 text-gray-500'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
              >
                {addedAgents.has(selectedAgentDetails.id) 
                  ? '✅ Added' 
                  : addingAgents.has(selectedAgentDetails.id) 
                  ? 'Adding...' 
                  : 'Add Agent'
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AgentLibrary;