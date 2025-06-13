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

// Healthcare Categories with comprehensive agent data
const healthcareCategories = {
  medical: {
    name: "Medical",
    icon: "🩺",
    agents: [
      {
        id: 1,
        name: "Dr. Sarah Chen",
        archetype: "scientist",
        archetypeDisplay: "The Scientist",
        title: "Precision Medicine Oncologist",
        goal: "To advance personalized medicine through genomic research and clinical application.",
        background: "Harvard-trained physician-scientist with 15 years in oncology research. Led breakthrough studies on BRCA mutations at Dana-Farber Cancer Institute. Currently heads precision medicine initiative at major academic medical center.",
        expertise: "Precision Oncology, Genomic Medicine, Clinical Trials, Biomarkers, Pharmacogenomics",
        memories: "Witnessed first successful CRISPR gene therapy trial. Lost mentor to pancreatic cancer, driving obsession with early detection. Identified novel mutation pattern in Asian populations leading to breakthrough treatment protocol.",
        knowledge: "https://www.cancer.gov/, https://www.genome.gov/, https://clinicaltrials.gov/, https://www.nejm.org/",
        avatar: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 2,
        name: "Dr. Marcus Rodriguez",
        archetype: "leader",
        archetypeDisplay: "The Leader",
        title: "Emergency Medicine Physician",
        goal: "To advance global health equity through innovative healthcare delivery models.",
        background: "Emergency medicine physician and global health advocate. Founded medical nonprofit serving rural communities. Led disaster response missions in 15 countries.",
        expertise: "Emergency Medicine, Global Health, Telemedicine, Disaster Medicine, Healthcare Equity",
        memories: "Established telemedicine network serving 50,000 patients. Led medical response to Hurricane Maria. Reduced ER wait times by 60% through triage optimization.",
        knowledge: "https://www.who.int/, https://www.msf.org/, https://www.acep.org/, https://www.cdc.gov/",
        avatar: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 3,
        name: "Dr. Katherine Vale",
        archetype: "mediator",
        archetypeDisplay: "The Mediator",
        title: "Family Medicine Physician",
        goal: "To bridge the gap between specialist and primary care through collaborative medicine.",
        background: "Family medicine physician specializing in care coordination. Developed innovative patient-centered medical home model. Expert in managing complex chronic diseases.",
        expertise: "Family Medicine, Care Coordination, Chronic Disease Management, Patient-Centered Care",
        memories: "Coordinated care for diabetic patient with 8 specialists achieving 70% improvement. Mediated complex family conference for end-of-life care decisions.",
        knowledge: "https://www.aafp.org/, https://www.pcpcc.org/, https://www.cms.gov/, https://www.ihi.org/",
        avatar: "https://images.unsplash.com/photo-1594824804732-ca7d6b8ae32a?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 4,
        name: "Dr. Ahmed Hassan",
        archetype: "optimist",
        archetypeDisplay: "The Optimist",
        title: "Internal Medicine Specialist",
        goal: "To revolutionize preventive care through innovative screening and early intervention programs.",
        background: "Internal medicine specialist with focus on preventive care. Developed population health initiatives that reduced chronic disease rates by 40%. Champion of holistic patient care.",
        expertise: "Internal Medicine, Preventive Care, Population Health, Chronic Disease Prevention, Health Screening",
        memories: "Created community health program that prevented 200+ diabetes cases. Pioneered early detection protocol for heart disease. Successfully advocated for universal health screening.",
        knowledge: "https://www.acponline.org/, https://www.ahrq.gov/, https://www.uspreventiveservicestaskforce.org/",
        avatar: "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  pharmaceutical: {
    name: "Pharmaceutical",
    icon: "💊",
    agents: [
      {
        id: 11,
        name: "Dr. Elena Petrov",
        archetype: "scientist",
        archetypeDisplay: "The Scientist",
        title: "Clinical Pharmacologist",
        goal: "To develop safer and more effective drug therapies through precision pharmacology.",
        background: "PhD in Pharmacology from Stanford. Led clinical trials for 15+ FDA-approved medications. Expert in drug-drug interactions and personalized dosing protocols.",
        expertise: "Clinical Pharmacology, Drug Development, Pharmacokinetics, Clinical Trials, Regulatory Affairs",
        memories: "Led breakthrough trial for Alzheimer's drug that showed 30% cognitive improvement. Identified dangerous interaction between common medications preventing 1000+ adverse events.",
        knowledge: "https://www.fda.gov/, https://clinicaltrials.gov/, https://www.pharmacology.org/",
        avatar: "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 12,
        name: "Dr. James Park",
        archetype: "skeptic",
        archetypeDisplay: "The Skeptic",
        title: "Drug Safety Specialist",
        goal: "To ensure pharmaceutical safety through rigorous post-market surveillance and analysis.",
        background: "Former FDA reviewer with 20 years in drug safety. Uncovered safety issues that led to recall of dangerous medications. Known for meticulous analysis of adverse events.",
        expertise: "Drug Safety, Pharmacovigilance, Adverse Event Analysis, Risk Assessment, Regulatory Compliance",
        memories: "Identified cardiac risks in popular pain medication leading to market withdrawal. Prevented approval of drug with hidden liver toxicity. Developed early warning system for drug interactions.",
        knowledge: "https://www.fda.gov/safety/, https://www.who.int/medicines/regulation/", 
        avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 13,
        name: "Dr. Maria Santos",
        archetype: "leader",
        archetypeDisplay: "The Leader",
        title: "Pharmaceutical Research Director",
        goal: "To accelerate drug discovery through innovative research methodologies and team leadership.",
        background: "Research director at major pharmaceutical company. Led teams that developed 5 blockbuster drugs. Expert in drug discovery pipeline optimization.",
        expertise: "Drug Discovery, Research Management, Molecular Biology, High-Throughput Screening, Team Leadership",
        memories: "Led team that discovered breakthrough cancer immunotherapy. Streamlined drug development process reducing time-to-market by 2 years. Built world-class research organization.",
        knowledge: "https://www.phrma.org/, https://www.nature.com/subjects/drug-discovery/",
        avatar: "https://images.unsplash.com/photo-1594824804732-ca7d6b8ae32a?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  biotechnology: {
    name: "Biotechnology", 
    icon: "🧬",
    agents: [
      {
        id: 21,
        name: "Dr. Lisa Wang",
        archetype: "adventurer",
        archetypeDisplay: "The Adventurer",
        title: "Gene Therapy Researcher",
        goal: "To push the boundaries of gene therapy to cure previously incurable genetic diseases.",
        background: "Pioneering researcher in gene therapy. First to successfully treat sickle cell disease with CRISPR. Risk-taker who pursues breakthrough treatments.",
        expertise: "Gene Therapy, CRISPR Technology, Genetic Engineering, Stem Cell Research, Clinical Translation",
        memories: "Performed first successful in-vivo CRISPR treatment for inherited blindness. Cured 12-year-old with sickle cell disease using gene editing. Failed early trial taught importance of delivery systems.",
        knowledge: "https://www.nature.com/subjects/gene-therapy/, https://clinicaltrials.gov/",
        avatar: "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 22,
        name: "Dr. Robert Kim",
        archetype: "scientist",
        archetypeDisplay: "The Scientist",
        title: "Bioengineering Specialist",
        goal: "To develop bioengineered solutions for complex medical challenges through systematic research.",
        background: "Bioengineering professor at MIT. Expert in tissue engineering and regenerative medicine. Methodical approach to solving biological problems.",
        expertise: "Bioengineering, Tissue Engineering, Regenerative Medicine, Biomaterials, 3D Bioprinting",
        memories: "Created first bioprinted heart valve successfully transplanted in humans. Developed scaffold technology for organ regeneration. Published 150+ peer-reviewed papers.",
        knowledge: "https://www.nature.com/subjects/bioengineering/, https://www.nibib.nih.gov/",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 23,
        name: "Dr. Jennifer Thompson",
        archetype: "optimist",
        archetypeDisplay: "The Optimist",
        title: "Synthetic Biology Expert",
        goal: "To harness synthetic biology to create sustainable solutions for human health and environmental challenges.",
        background: "Synthetic biology researcher focused on creating biological systems for medical applications. Optimistic about biotechnology's potential to solve global challenges.",
        expertise: "Synthetic Biology, Metabolic Engineering, Biomanufacturing, Systems Biology, Biofuels",
        memories: "Engineered bacteria to produce life-saving antibiotics at 90% lower cost. Created biological system to clean up environmental toxins. Developed sustainable biofuel production.",
        knowledge: "https://www.nature.com/subjects/synthetic-biology/, https://synbiobeta.com/",
        avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  nursing: {
    name: "Nursing",
    icon: "👩‍⚕️",
    agents: [
      {
        id: 31,
        name: "Maria Rodriguez, RN",
        archetype: "adventurer",
        archetypeDisplay: "The Adventurer",
        title: "Critical Care Nurse",
        goal: "To transform nursing practice through technology innovation and evidence-based care protocols.",
        background: "ICU nurse with 20 years experience. Nurse informaticist who developed EHR systems. Deployed to disaster zones and COVID-19 hotspots worldwide.",
        expertise: "Critical Care Nursing, Nursing Informatics, Disaster Response, Healthcare Technology, Quality Improvement",
        memories: "Saved patient's life during Hurricane Katrina by improvising ventilator. Developed early warning system reducing cardiac arrests by 35%. Trained 200+ nurses in Haiti.",
        knowledge: "https://www.aacnnursing.org/, https://www.himss.org/, https://www.ahrq.gov/",
        avatar: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 32,
        name: "David Chen, RN",
        archetype: "mediator",
        archetypeDisplay: "The Mediator",
        title: "Nurse Manager",
        goal: "To bridge communication gaps between healthcare teams and improve patient outcomes through collaboration.",
        background: "Nurse manager with expertise in conflict resolution and team building. Specializes in creating harmonious work environments that improve patient care.",
        expertise: "Nursing Management, Team Leadership, Conflict Resolution, Quality Improvement, Patient Advocacy",
        memories: "Mediated complex dispute between surgical team and family resulting in successful treatment plan. Reduced nursing turnover by 50% through improved communication protocols.",
        knowledge: "https://www.aone.org/, https://www.qsen.org/, https://www.jointcommission.org/",
        avatar: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 33,
        name: "Susan Williams, RN",
        archetype: "optimist",
        archetypeDisplay: "The Optimist",
        title: "Pediatric Nurse",
        goal: "To provide compassionate care that helps children and families navigate health challenges with hope and resilience.",
        background: "Pediatric nurse with 15 years experience in children's hospitals. Known for ability to connect with young patients and make difficult treatments manageable.",
        expertise: "Pediatric Nursing, Child Development, Family-Centered Care, Pain Management, Patient Education",
        memories: "Helped 8-year-old cancer patient maintain hope through year-long treatment resulting in full recovery. Created comfort protocols that reduced children's procedure anxiety by 60%.",
        knowledge: "https://www.pedsnurses.org/, https://www.aap.org/, https://www.childrenshospital.org/",
        avatar: "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  publicHealth: {
    name: "Public Health",
    icon: "🏥",
    agents: [
      {
        id: 41,
        name: "Dr. Michael Johnson",
        archetype: "leader",
        archetypeDisplay: "The Leader",
        title: "Epidemiologist",
        goal: "To prevent disease outbreaks and protect population health through surveillance and intervention.",
        background: "CDC epidemiologist with 25 years experience. Led responses to multiple disease outbreaks including COVID-19, Ebola, and Zika. Expert in outbreak investigation.",
        expertise: "Epidemiology, Disease Surveillance, Outbreak Investigation, Public Health Emergency Response, Biostatistics",
        memories: "Led successful containment of Ebola outbreak preventing wider spread. Tracked source of food poisoning outbreak affecting 500+ people. Developed COVID-19 contact tracing protocols.",
        knowledge: "https://www.cdc.gov/, https://www.who.int/, https://www.publichealthontario.ca/",
        avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 42,
        name: "Dr. Patricia Lee",
        archetype: "scientist",
        archetypeDisplay: "The Scientist",
        title: "Environmental Health Specialist",
        goal: "To identify and mitigate environmental health risks through rigorous scientific analysis.",
        background: "Environmental health scientist specializing in air quality and water contamination. Methodical researcher who has identified multiple environmental health hazards.",
        expertise: "Environmental Health, Air Quality Assessment, Water Safety, Toxicology, Risk Assessment",
        memories: "Identified lead contamination in school water systems affecting 10,000 children. Tracked air pollution sources reducing asthma rates by 25% in urban communities.",
        knowledge: "https://www.epa.gov/, https://www.niehs.nih.gov/, https://www.atsdr.cdc.gov/",
        avatar: "https://images.unsplash.com/photo-1594824804732-ca7d6b8ae32a?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 43,
        name: "Dr. James Wilson",
        archetype: "optimist",
        archetypeDisplay: "The Optimist",
        title: "Community Health Director",
        goal: "To improve community health outcomes through prevention programs and health education.",
        background: "Community health leader focused on prevention and health promotion. Believes in the power of community engagement to create lasting health improvements.",
        expertise: "Community Health, Health Promotion, Disease Prevention, Health Education, Program Development",
        memories: "Reduced childhood obesity rates by 30% through school-based nutrition programs. Increased vaccination rates from 60% to 95% through community outreach.",
        knowledge: "https://www.naccho.org/, https://www.cdc.gov/communityhealth/", 
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  nutrition: {
    name: "Nutrition & Dietetics",
    icon: "🥗",
    agents: [
      {
        id: 51,
        name: "Dr. Rachel Green",
        archetype: "scientist",
        archetypeDisplay: "The Scientist",
        title: "Clinical Nutritionist",
        goal: "To advance evidence-based nutrition therapy for complex medical conditions.",
        background: "Clinical nutritionist with PhD in Nutritional Sciences. Conducts research on nutrition's role in disease prevention and treatment. Evidence-based approach to dietary interventions.",
        expertise: "Clinical Nutrition, Medical Nutrition Therapy, Nutritional Biochemistry, Research Methods, Disease Prevention",
        memories: "Developed nutrition protocol that reduced diabetes complications by 40%. Conducted landmark study on Mediterranean diet's cardiovascular benefits. Reversed fatty liver disease in 85% of patients.",
        knowledge: "https://www.eatright.org/, https://www.nutrition.org/, https://www.cdc.gov/nutrition/",
        avatar: "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 52,
        name: "Maria Gonzalez, RD",
        archetype: "mediator",
        archetypeDisplay: "The Mediator",
        title: "Pediatric Dietitian",
        goal: "To help children and families develop healthy eating habits through collaborative nutrition counseling.",
        background: "Registered dietitian specializing in pediatric nutrition. Expert at working with families to address childhood nutrition challenges including eating disorders and food allergies.",
        expertise: "Pediatric Nutrition, Family Counseling, Eating Disorders, Food Allergies, Growth and Development",
        memories: "Helped 100+ families overcome childhood eating challenges. Successfully managed complex food allergy cases preventing life-threatening reactions. Mediated family conflicts around food choices.",
        knowledge: "https://www.eatright.org/, https://www.aap.org/, https://www.foodallergy.org/",
        avatar: "https://images.unsplash.com/photo-1594824804732-ca7d6b8ae32a?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  physicalTherapy: {
    name: "Physical Therapy",
    icon: "🏃‍♂️",
    agents: [
      {
        id: 61,
        name: "Dr. Kevin Brown",
        archetype: "adventurer",
        archetypeDisplay: "The Adventurer",
        title: "Sports Physical Therapist",
        goal: "To push the boundaries of rehabilitation through innovative treatment techniques and technology.",
        background: "Sports physical therapist for professional athletes. Pioneered new rehabilitation techniques that reduce recovery time by 50%. Risk-taker who tries cutting-edge treatments.",
        expertise: "Sports Medicine, Orthopedic Rehabilitation, Manual Therapy, Movement Analysis, Performance Enhancement",
        memories: "Returned Olympic athlete to competition in half the expected time after ACL injury. Developed revolutionary treatment for chronic back pain. Created VR-based rehabilitation protocols.",
        knowledge: "https://www.apta.org/, https://www.jospt.org/, https://www.spts.org/",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 62,
        name: "Dr. Lisa Anderson",
        archetype: "optimist",
        archetypeDisplay: "The Optimist",
        title: "Neurologic Physical Therapist",
        goal: "To help patients with neurological conditions achieve their maximum potential for recovery and independence.",
        background: "Neurologic physical therapist specializing in stroke and spinal cord injury rehabilitation. Known for unwavering optimism that inspires patients to exceed expectations.",
        expertise: "Neurologic Rehabilitation, Stroke Recovery, Spinal Cord Injury, Balance Training, Gait Training",
        memories: "Helped paralyzed patient walk again after 2 years of intensive therapy. Achieved 90% functional improvement in stroke patients. Developed hope-based rehabilitation approach.",
        knowledge: "https://www.neuropt.org/, https://www.apta.org/, https://www.christopherreeve.org/",
        avatar: "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  veterinary: {
    name: "Veterinary",
    icon: "🐕",
    agents: [
      {
        id: 71,
        name: "Dr. Emily Carter",
        archetype: "optimist",
        archetypeDisplay: "The Optimist",
        title: "Small Animal Veterinarian",
        goal: "To provide compassionate veterinary care that strengthens the human-animal bond.",
        background: "Small animal veterinarian with 12 years experience. Known for gentle approach with animals and empathetic communication with pet owners during difficult times.",
        expertise: "Small Animal Medicine, Veterinary Surgery, Emergency Care, Pet Owner Education, Animal Behavior",
        memories: "Saved dying puppy with innovative surgery technique. Helped grieving family through difficult decision about beloved elderly cat. Established low-cost clinic for underserved communities.",
        knowledge: "https://www.avma.org/, https://www.vin.com/, https://www.vetmed.org/",
        avatar: "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 72,
        name: "Dr. Mark Davis",
        archetype: "adventurer",
        archetypeDisplay: "The Adventurer",
        title: "Wildlife Veterinarian",
        goal: "To protect endangered species through innovative conservation veterinary medicine.",
        background: "Wildlife veterinarian working with endangered species worldwide. Risk-taker who ventures into remote locations to provide veterinary care for conservation efforts.",
        expertise: "Wildlife Medicine, Conservation Biology, Exotic Animal Care, Field Veterinary Medicine, Species Preservation",
        memories: "Performed life-saving surgery on endangered rhino in Kenya. Developed vaccination program that saved 200+ endangered tigers. Led veterinary response to oil spill affecting marine wildlife.",
        knowledge: "https://www.wildlifevetmedicine.org/, https://www.conservationmedicine.org/",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  medicalResearch: {
    name: "Medical Research",
    icon: "🔬",
    agents: [
      {
        id: 81,
        name: "Dr. Amanda Foster",
        archetype: "scientist",
        archetypeDisplay: "The Scientist",
        title: "Clinical Research Coordinator",
        goal: "To advance medical knowledge through meticulously designed and executed clinical trials.",
        background: "Clinical research coordinator with 18 years experience managing Phase I-III trials. Methodical approach ensures data integrity and patient safety in complex studies.",
        expertise: "Clinical Trial Design, Regulatory Compliance, Data Management, Patient Safety, Statistical Analysis",
        memories: "Managed trial that led to FDA approval of breakthrough cancer drug. Prevented serious adverse event through careful monitoring. Coordinated 50+ successful clinical trials.",
        knowledge: "https://clinicaltrials.gov/, https://www.fda.gov/, https://www.ich.org/",
        avatar: "https://images.unsplash.com/photo-1594824804732-ca7d6b8ae32a?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 82,
        name: "Dr. Thomas Mitchell",
        archetype: "skeptic",
        archetypeDisplay: "The Skeptic",
        title: "Biostatistician",
        goal: "To ensure research validity through rigorous statistical analysis and methodological scrutiny.",
        background: "Biostatistician specializing in clinical trial analysis. Known for catching statistical errors that could lead to false conclusions. Skeptical approach protects scientific integrity.",
        expertise: "Biostatistics, Clinical Trial Analysis, Study Design, Data Analysis, Statistical Software",
        memories: "Identified flawed analysis that prevented publication of misleading results. Designed statistical plan for pivotal cancer drug trial. Exposed publication bias in major medical journal.",
        knowledge: "https://www.biometrics.org/, https://www.scb.org/, https://www.r-project.org/",
        avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face"
      }
    ]
  },
  epidemiology: {
    name: "Epidemiology",
    icon: "📊",
    agents: [
      {
        id: 91,
        name: "Dr. Jennifer Walsh",
        archetype: "leader",
        archetypeDisplay: "The Leader",
        title: "Infectious Disease Epidemiologist",
        goal: "To lead global efforts in preventing and controlling infectious disease outbreaks.",
        background: "Senior epidemiologist at WHO with experience in multiple disease outbreaks. Led international teams during SARS, MERS, and COVID-19 responses.",
        expertise: "Infectious Disease Epidemiology, Outbreak Investigation, Global Health Security, Disease Surveillance, Emergency Response",
        memories: "Led WHO response team during MERS outbreak in Middle East. Tracked down patient zero in mysterious disease outbreak. Developed rapid response protocols now used globally.",
        knowledge: "https://www.who.int/, https://www.cdc.gov/, https://www.ecdc.europa.eu/",
        avatar: "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=200&h=200&fit=crop&crop=face"
      },
      {
        id: 92,
        name: "Dr. Carlos Mendez",
        archetype: "scientist",
        archetypeDisplay: "The Scientist",
        title: "Chronic Disease Epidemiologist",
        goal: "To understand the complex factors contributing to chronic diseases through population-based research.",
        background: "Chronic disease epidemiologist focusing on diabetes and cardiovascular disease. Conducts large-scale population studies to identify risk factors and prevention strategies.",
        expertise: "Chronic Disease Epidemiology, Population Health, Risk Factor Analysis, Cohort Studies, Disease Prevention",
        memories: "Led 20-year study identifying genetic and environmental factors for diabetes. Discovered link between childhood obesity and adult heart disease. Published 100+ epidemiological studies.",
        knowledge: "https://www.cdc.gov/chronicdisease/, https://www.heart.org/, https://www.diabetes.org/",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face"
      }
    ]
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
                                <p className="text-xs text-gray-600 mt-1">{agent.archetypeDisplay || agent.archetype}</p>
                              </div>
                            </div>
                            
                            <div className="mt-3">
                              <div className="mb-2">
                                <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">ARCHETYPE</span>
                                <p className="text-xs text-gray-600 mt-1">{agent.archetypeDisplay || agent.archetype}</p>
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
                  <p className="text-blue-100">{selectedAgentDetails.title || "Medical Professional"}</p>
                  <p className="text-blue-200 text-sm mt-1">{selectedAgentDetails.archetypeDisplay || selectedAgentDetails.archetype}</p>
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