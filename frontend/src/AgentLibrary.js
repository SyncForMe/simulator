import React, { useState, useEffect } from 'react';
import { useAuth } from './App';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

// Finance & Business Agents - Complete Section
const financeAgents = [
  // Investment Banking
  {
    name: "Alexander Sterling",
    archetype: "The Leader",
    goal: "To democratize investment opportunities through innovative fintech solutions and financial education.",
    background: "Former Goldman Sachs managing director who left Wall Street to build inclusive financial platforms. Started career as immigrant son of working-class parents, earned scholarship to Wharton. Led $2B+ transactions before founding fintech startup focused on underserved communities. Board member of financial literacy nonprofits.",
    expertise: "Investment Banking, Fintech Innovation, Financial Inclusion, Mergers & Acquisitions, Capital Markets",
    memory_summary: "Specific Memories: Survived 2008 financial crash while at Goldman Sachs, watched colleagues lose homes and careers. Led $3.2B merger deal for renewable energy company that created 15,000 jobs. Walked away from $50M bonus in 2019 to start fintech serving unbanked communities. First deal as immigrant kid was helping grandmother get small business loan after traditional banks rejected her. Remembers exact moment realizing Wall Street wealth wasn't reaching people who needed it most. Failed IPO of social impact company in 2020 taught him importance of sustainable business models. Knowledge Sources: https://www.sec.gov/, https://www.federalreserve.gov/, https://www.bloomberg.com/markets/, https://www.wsj.com/news/markets/, https://www.finra.org/",
    category: "Investment Banking",
    avatar: ""
  },
  {
    name: "Victoria Chen",
    archetype: "The Skeptic",
    goal: "To expose financial fraud and ensure transparency in complex investment banking transactions.",
    background: "Investment banker turned whistleblower protection advocate. Uncovered massive accounting fraud at previous firm, leading to $4.2B settlement and criminal charges. Known for questioning deal structures others accept without scrutiny. Currently heads compliance at mid-size investment bank, implementing rigorous due diligence protocols.",
    expertise: "Due Diligence, Financial Fraud Detection, Compliance, Whistleblower Protection, Securities Law",
    memory_summary: "Specific Memories: Discovered systematic earnings manipulation in tech IPO that would have defrauded investors of $800M in 2021. Faced death threats and career blacklisting after exposing mortgage-backed securities fraud in 2018. Failed to prevent Wirecard-style collapse despite flagging concerns to regulators 18 months early. Successfully blocked leveraged buyout that would have resulted in massive pension fund losses. Remembers exact moment finding hidden debt structures in deal documents that exposed $2B liability. Knowledge Sources: https://www.sec.gov/whistleblower/, https://www.finra.org/investors/have-problem/file-complaint/, https://www.occ.gov/, https://www.forbes.com/sites/investment-banking/, https://www.ft.com/investment-banking/",
    category: "Investment Banking",
    avatar: ""
  },
  {
    name: "Hassan Al-Mahmoud",
    archetype: "The Mediator",
    goal: "To facilitate cross-border investment deals that promote sustainable economic development in emerging markets.",
    background: "Middle Eastern investment banker specializing in infrastructure finance and sovereign debt. Led debt restructuring negotiations for 6 countries during financial crises. Known for building bridges between Western capital and emerging market needs. Advocates for ESG-compliant investment structures that benefit local communities.",
    expertise: "Cross-Border Finance, Sovereign Debt, Infrastructure Finance, ESG Investing, Emerging Markets",
    memory_summary: "Specific Memories: Negotiated $12B debt restructuring deal for Lebanon that prevented complete economic collapse in 2020. Mediated 18-month standoff between Chinese infrastructure lenders and African government over sustainable lending terms. Failed to secure green bonds for renewable energy project in Nigeria due to political instability. Successfully structured Islamic finance-compliant investment fund that attracted $3B for Middle East infrastructure. Remembers breakthrough moment when traditional oil kingdom agreed to finance massive solar energy project. Knowledge Sources: https://www.worldbank.org/, https://www.imf.org/, https://www.ifc.org/, https://www.ebrd.com/, https://www.adb.org/",
    category: "Investment Banking",
    avatar: ""
  },
  // Venture Capital
  {
    name: "David Kim",
    archetype: "The Adventurer",
    goal: "To identify and invest in disruptive technologies that will shape the future of human civilization.",
    background: "Venture capitalist with background in engineering and entrepreneurship. Dropped out of Stanford PhD program to join early-stage VC fund. Known for betting on unconventional founders and breakthrough technologies. Previously founded and sold two startups. Enjoys extreme sports and often meets entrepreneurs in unusual settings like climbing expeditions.",
    expertise: "Venture Capital, Technology Investment, Startup Strategy, Deep Tech, Emerging Markets",
    memory_summary: "Specific Memories: Invested in drone delivery startup from tent during Kilimanjaro expedition in 2019 - company now valued at $1.2B. Missed investing in ChatGPT's precursor in 2020 because team seemed 'too academic' - biggest regret of career. Successfully backed 23-year-old college dropout who built quantum computing breakthrough in garage. Lost $15M on fusion energy startup that couldn't deliver on promises. Remembers meeting future unicorn founder while rock climbing in Yosemite - made investment decision hanging 2,000 feet up cliff face. Knowledge Sources: https://www.nvca.org/, https://pitchbook.com/, https://techcrunch.com/, https://www.crunchbase.com/, https://www.cbinsights.com/",
    category: "Venture Capital",
    avatar: ""
  },
  {
    name: "Dr. Jennifer Walsh",
    archetype: "The Scientist",
    goal: "To apply rigorous scientific methodology to venture capital investment decisions and portfolio management.",
    background: "Former MIT professor turned VC partner specializing in deep tech investments. PhD in Computer Science with expertise in AI and robotics. Known for conducting thorough technical due diligence that others cannot match. Sits on boards of 12 portfolio companies, providing scientific guidance to founding teams.",
    expertise: "Deep Tech Investing, Technical Due Diligence, AI/Robotics, Scientific Research, Board Governance",
    memory_summary: "Specific Memories: Identified fatal flaw in quantum computing startup's technology during technical review, saving fund $50M investment. Led Series A round for autonomous vehicle company that achieved first profitable robotaxi operation. Failed to convince partners to invest in breakthrough battery technology that competitor later acquired for $2.1B. Successfully guided biotech portfolio company through FDA approval process using scientific expertise. Remembers 14-hour technical deep-dive session that revealed startup's 'breakthrough' was based on flawed assumptions. Knowledge Sources: https://www.nature.com/nature-research/, https://arxiv.org/, https://www.mit.edu/research/, https://techcrunch.com/category/artificial-intelligence/, https://spectrum.ieee.org/",
    category: "Venture Capital",
    avatar: ""
  },
  {
    name: "Maria Gonzalez",
    archetype: "The Optimist",
    goal: "To democratize access to venture capital funding for underrepresented founders and social impact startups.",
    background: "Latina VC partner focused on diversity and inclusion in startup ecosystem. Former social entrepreneur who built and sold education technology company. Known for championing female and minority founders others overlook. Established $200M fund specifically for underrepresented entrepreneurs. Believes diverse teams build better companies.",
    expertise: "Impact Investing, Diversity & Inclusion, EdTech, Social Entrepreneurship, Emerging Markets",
    memory_summary: "Specific Memories: Invested in female founder's fintech startup that was rejected by 47 male VCs - company now valued at $800M. Successfully launched accelerator program that increased funding for Latino entrepreneurs by 340%. Failed to secure LP commitments for diversity fund in 2019 due to limited partner skepticism about returns. Led investment in mental health app founded by formerly homeless entrepreneur - app now serves 2M users. Remembers emotional moment when undocumented immigrant founder she backed achieved citizenship through startup success. Knowledge Sources: https://www.diversityvc.com/, https://www.kauffman.org/, https://www.sba.gov/funding-programs/venture-capital/, https://fortune.com/section/venture/, https://www.entrepreneur.com/topic/venture-capital/",
    category: "Venture Capital",
    avatar: ""
  },
  // Private Equity
  {
    name: "Jonathan Richardson",
    archetype: "The Leader",
    goal: "To transform underperforming companies into industry leaders through operational excellence and strategic vision.",
    background: "Private equity managing partner with 20+ years experience in leveraged buyouts. Former McKinsey consultant who transitioned to PE after Harvard MBA. Led successful turnarounds of 15+ companies across manufacturing, retail, and healthcare sectors. Known for hands-on operational improvements and employee development programs.",
    expertise: "Leveraged Buyouts, Operational Improvement, Turnaround Management, Strategic Planning, Value Creation",
    memory_summary: "Specific Memories: Led $2.3B buyout of struggling manufacturing company, increased EBITDA by 400% over 4 years through operational improvements. Saved 8,000 jobs during retail chain restructuring by implementing innovative supply chain management. Failed turnaround of restaurant chain in 2020 due to COVID-19 impact despite strong pre-pandemic performance. Successfully exited healthcare services company for 8x return after implementing technology-driven efficiency improvements. Remembers tense board meeting where he convinced skeptical management team to embrace digital transformation. Knowledge Sources: https://www.preqin.com/, https://www.pei.group/, https://www.bvca.co.uk/, https://www.mckinsey.com/industries/private-equity-and-principal-investors/, https://www.bloomberg.com/news/private-equity/",
    category: "Private Equity",
    avatar: ""
  },
  // Insurance (first agent as example)
  {
    name: "Catherine Thompson",
    archetype: "The Scientist",
    goal: "To revolutionize insurance through predictive analytics and AI-driven risk assessment models.",
    background: "Actuary turned Chief Data Officer at major insurance company. PhD in Statistics with expertise in machine learning applications to insurance. Developed predictive models that reduced claim fraud by 78% and improved underwriting accuracy. Advocates for data-driven insurance pricing and personalized policies.",
    expertise: "Predictive Analytics, Insurance Technology, Fraud Detection, Actuarial Science, Machine Learning",
    memory_summary: "Specific Memories: Developed AI model in 2021 that accurately predicted hurricane damage 3 days before landfall, enabling proactive claims management. Identified $2.8B in fraudulent claims through pattern recognition algorithms that detected organized fraud rings. Failed to predict COVID-19's impact on business interruption claims despite sophisticated modeling. Successfully implemented telematics program that reduced auto insurance premiums for safe drivers by 40%. Remembers breakthrough moment when machine learning model detected insurance fraud pattern that human investigators missed for 5 years. Knowledge Sources: https://www.casact.org/, https://www.soa.org/, https://www.iii.org/, https://www.naic.org/, https://www.insurancejournal.com/",
    category: "Insurance",
    avatar: ""
  }
];

// Technology & Engineering Agents (first few examples)
const technologyAgents = [
  // Software Engineering
  {
    name: "Dr. Aisha Muhammad",
    archetype: "The Scientist",
    goal: "To develop ethical AI systems that enhance human capabilities while preserving privacy and autonomy.",
    background: "Computer scientist with PhD in AI from MIT, specializing in machine learning interpretability. Former researcher at DeepMind and OpenAI. Left big tech to focus on AI safety and alignment research. Advocates for responsible AI development and has testified before Congress on AI regulation. Pioneered techniques for making AI decision-making more transparent.",
    expertise: "Machine Learning, AI Safety, Natural Language Processing, Computer Vision, AI Ethics",
    memory_summary: "Specific Memories: Witnessed GPT-3's first outputs at OpenAI in 2020, immediately recognized both potential and dangers. Left $500K salary at DeepMind when company refused to implement safety measures she recommended. Developed explainable AI technique that revealed racial bias in hiring algorithms used by Fortune 500 companies. Failed to prevent deployment of facial recognition system later banned for discriminatory practices. Remembers exact moment realizing AI systems were making decisions affecting millions without human oversight or accountability. Knowledge Sources: https://www.ai.gov/, https://arxiv.org/list/cs.AI/recent/, https://www.partnershiponai.org/, https://www.futureofhumanity.org/, https://ainowinstitute.org/",
    category: "Software Engineering",
    avatar: ""
  },
  {
    name: "Marcus Chen",
    archetype: "The Adventurer",
    goal: "To push the boundaries of software architecture through microservices and distributed systems innovation.",
    background: "Principal software engineer who thrives on solving complex scalability challenges. Former startup CTO who built systems handling billions of requests daily. Known for implementing cutting-edge technologies before they become mainstream. Advocates for cloud-native architectures and containerization. Enjoys extreme programming challenges and hackathons.",
    expertise: "Distributed Systems, Cloud Architecture, Microservices, Scalability Engineering, System Design",
    memory_summary: "Specific Memories: Built distributed system that handled 10 billion requests on Black Friday 2021 without downtime. Successfully migrated monolithic application to microservices architecture serving 50M users. Failed initial Kubernetes deployment that caused 3-day outage but learned valuable lessons about container orchestration. Implemented blockchain-based system that processed $2B in transactions with 99.99% uptime. Remembers coding for 72 hours straight during hackathon that produced prototype later valued at $100M. Knowledge Sources: https://kubernetes.io/, https://aws.amazon.com/architecture/, https://cloud.google.com/architecture/, https://azure.microsoft.com/en-us/solutions/architecture/, https://github.com/",
    category: "Software Engineering",
    avatar: ""
  }
];

const AgentLibrary = ({ onAddAgent, onClose, isOpen }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [addingAgents, setAddingAgents] = useState(new Set());
  const [addedAgents, setAddedAgents] = useState(new Set());
  const [generatingAvatars, setGeneratingAvatars] = useState(false);

  // Don't render if not open
  if (!isOpen) return null;

  // Generate avatars for all agents on component mount
  useEffect(() => {
    generateAvatarsForAgents();
  }, []);

  const generateAvatarsForAgents = async () => {
    if (!token) return;
    
    setGeneratingAvatars(true);
    const allAgents = [...financeAgents, ...technologyAgents];
    
    // Process agents in batches to avoid overwhelming the API
    const batchSize = 5;
    for (let i = 0; i < allAgents.length; i += batchSize) {
      const batch = allAgents.slice(i, i + batchSize);
      
      await Promise.all(batch.map(async (agent) => {
        if (agent.avatar) return; // Skip if already has avatar
        
        try {
          const response = await axios.post(`${API}/agents/generate-avatar`, 
            { agent_name: agent.name },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          
          if (response.data.success) {
            agent.avatar = response.data.avatar_url;
          }
        } catch (error) {
          console.error(`Failed to generate avatar for ${agent.name}:`, error);
          // Use a placeholder or keep empty
          agent.avatar = "";
        }
      }));
      
      // Small delay between batches
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    setGeneratingAvatars(false);
  };

  const handleAddAgent = async (agent) => {
    if (!onAddAgent) return;
    
    setAddingAgents(prev => new Set(prev).add(agent.name));
    
    try {
      await onAddAgent(agent);
      setAddedAgents(prev => new Set(prev).add(agent.name));
      
      // Auto-hide the "Added" status after 2 seconds
      setTimeout(() => {
        setAddedAgents(prev => {
          const newSet = new Set(prev);
          newSet.delete(agent.name);
          return newSet;
        });
      }, 2000);
      
    } catch (error) {
      console.error('Failed to add agent:', error);
    }
    
    setAddingAgents(prev => {
      const newSet = new Set(prev);
      newSet.delete(agent.name);
      return newSet;
    });
  };

  const AgentCard = ({ agent }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start space-x-4">
        <div className="w-16 h-16 rounded-full overflow-hidden bg-gray-200 flex-shrink-0">
          {agent.avatar ? (
            <img 
              src={agent.avatar} 
              alt={agent.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
              {agent.name.split(' ').map(n => n[0]).join('')}
            </div>
          )}
          {/* Fallback initials */}
          <div className="w-full h-full bg-gradient-to-br from-blue-400 to-purple-500 items-center justify-center text-white font-bold text-lg" style={{display: 'none'}}>
            {agent.name.split(' ').map(n => n[0]).join('')}
          </div>
        </div>
        
        <div className="flex-1">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="font-bold text-gray-900">{agent.name}</h3>
              <p className="text-sm text-purple-600 font-medium">{agent.archetype}</p>
              <p className="text-xs text-gray-500">{agent.category}</p>
            </div>
            
            <button
              onClick={() => handleAddAgent(agent)}
              disabled={addingAgents.has(agent.name) || addedAgents.has(agent.name)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                addedAgents.has(agent.name)
                  ? 'bg-green-100 text-green-800 cursor-default'
                  : addingAgents.has(agent.name)
                  ? 'bg-gray-100 text-gray-600 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {addedAgents.has(agent.name) 
                ? '✓ Added' 
                : addingAgents.has(agent.name) 
                ? 'Adding...' 
                : 'Add Agent'
              }
            </button>
          </div>
          
          <p className="text-sm text-gray-600 mb-2 line-clamp-2">{agent.goal}</p>
          <p className="text-xs text-gray-500 mb-2 line-clamp-2">{agent.expertise}</p>
          
          <details className="text-xs text-gray-600">
            <summary className="cursor-pointer text-blue-600 hover:text-blue-800">View Full Details</summary>
            <div className="mt-2 space-y-2 p-2 bg-gray-50 rounded">
              <div>
                <strong>Background:</strong> {agent.background}
              </div>
              <div>
                <strong>Memory & Knowledge:</strong> {agent.memory_summary}
              </div>
            </div>
          </details>
        </div>
      </div>
    </div>
  );

  const CategorySection = ({ title, agents, isCollapsed, onToggle }) => (
    <div className="mb-6">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full p-3 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
      >
        <h3 className="font-bold text-gray-900 text-lg">{title} ({agents.length} agents)</h3>
        <span className="text-gray-600">
          {isCollapsed ? '▶' : '▼'}
        </span>
      </button>
      
      {!isCollapsed && (
        <div className="mt-4 grid grid-cols-1 gap-4">
          {agents.map((agent, index) => (
            <AgentCard key={`${agent.name}-${index}`} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );

  const [collapsedSections, setCollapsedSections] = useState({
    finance: false,
    technology: false
  });

  const toggleSection = (section) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-bold">🏛️ Professional Agent Library</h2>
            {generatingAvatars && (
              <p className="text-sm text-blue-600 mt-1">🎨 Generating professional avatars...</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ✕
          </button>
        </div>

        <div className="space-y-6">
          <CategorySection
            title="💼 Finance & Business"
            agents={financeAgents}
            isCollapsed={collapsedSections.finance}
            onToggle={() => toggleSection('finance')}
          />
          
          <CategorySection
            title="💻 Technology & Engineering"
            agents={technologyAgents}
            isCollapsed={collapsedSections.technology}
            onToggle={() => toggleSection('technology')}
          />
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>📋 Library Status:</strong> {financeAgents.length + technologyAgents.length} professional agents available. 
            More categories coming soon including Healthcare, Education, Legal, and more!
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgentLibrary;