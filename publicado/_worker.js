/**
 * Cloudflare Worker para o Agente RAG do Portfólio de Leonardo Manzo.
 * Atua como um Agente de IA conversacional e fundamentado em conhecimento.
 * Intercepta /api/ask e responde usando a Gemini API (se GEMINI_API_KEY estiver configurada)
 * ou o motor de busca léxico contextual.
 */const KB = [
  {
    id: "como_funciona_agente",
    t: "Como Funciona o Agente RAG",
    te: "How the RAG Agent Works",
    s: "#sobre",
    k: "como funciona isso funciona agente rag assistente bot inteligente o que faz ajuda sistema duvida como usa responder",
    x: "Este é o Agente Virtual de IA do portfólio de Leonardo Rabello Manzo (Engenheiro de Soluções de IA e Automação). Ele analisa perguntas em linguagem natural, consulta a base de conhecimento oficial (10+ anos de experiência, pós em Engenharia de IA na Faculdade Impacta Digital, consultoria na Arquitetool, gestão na CH3 e projetos técnicos como Síndico Inteligente, Agenda Retrátil, Gerador de Cronograma Físico-Financeiro e Vigia Obra) e sintetiza respostas fundamentadas com fontes.",
    xe: "This is the Virtual AI Agent for Leonardo Rabello Manzo's portfolio (AI Solutions & Automation Engineer). It processes natural language questions, queries the official knowledge base (10+ years background, AI Engineering postgrad at Impacta Digital, consultancy at Arquitetool, management at CH3, and technical projects like Síndico Inteligente, Agenda Retrátil, Cost-Loaded Schedule Generator, and Vigia Obra), and synthesizes grounded answers with sources."
  },
  {
    id: "saudacao_apresentacao",
    t: "Apresentação do Agente",
    te: "Agent Introduction",
    s: "#sobre",
    k: "oi ola quem e voce sobre o que pode falar ajuda recursos capacidades funcionalidades hello hi agent who are you",
    x: "Sou o assistente inteligente do portfólio de Leonardo Rabello Manzo. Posso responder sobre sua experiência profissional em operações de construção e engenharia de IA, cargos atuais (Arquitetool e CH3 Incorporadora), projetos técnicos em Python, automação de processos, stack (LLMs, LangChain, APIs REST, SQL, FTS5, OpenCV) e preferências de contratação.",
    xe: "I am the intelligent assistant for Leonardo Rabello Manzo's portfolio. I can answer questions about his professional experience in construction operations and AI engineering, current roles (Arquitetool and CH3 Incorporadora), technical Python projects, process automation, stack (LLMs, LangChain, REST APIs, SQL, FTS5, OpenCV), and hiring preferences."
  },
  {
    id: "posicionamento",
    t: "Posicionamento e Resumo Profissional",
    te: "Positioning & Professional Summary",
    s: "#topo",
    k: "cargo posicao vaga perfil quem resumo objetivo busca procura role position job profile who summary goal looking",
    x: "Leonardo Rabello Manzo é Engenheiro de Soluções de IA e Automação (ConTech / PropTech), pós-graduado em Engenharia de IA, com mais de 10 anos de experiência em operações de construção, gestão de projetos e melhoria de processos. Desenvolve soluções em Python e IA generativa com APIs REST, OAuth, SQL/SQLite, busca documental, IA multimodal e structured outputs. Aderente a vagas de AI Solutions, AI Automation, Implementation, ConTech e PropTech.",
    xe: "Leonardo Rabello Manzo is an AI Solutions and Automation Engineer (ConTech / PropTech), post-graduated in AI Engineering, with over 10 years of experience in construction operations, project management, and process improvement. He develops solutions in Python and generative AI with REST APIs, OAuth, SQL/SQLite, document search, multimodal AI, and structured outputs. Ideal for AI Solutions, AI Automation, Implementation, ConTech, and PropTech roles."
  },
  {
    id: "experiencia_ia",
    t: "Experiência com IA e Automação",
    te: "AI & Automation Experience",
    s: "#projetos",
    k: "ia inteligencia artificial llm experiencia tempo anos senior pleno nivel senioridade machine learning ai experience years seniority level mid",
    x: "Pós-graduação em Engenharia de IA concluída em 2026 na Faculdade Impacta Digital. Atua na Arquitetool como Consultor de IA e Automação (temporário), traduzindo necessidades reais de campo em oportunidades de produto e automação. Desenvolveu múltiplos projetos práticos: Síndico Inteligente, Agenda Retrátil, Gerador de Cronograma Físico-Financeiro e Vigia Obra Segurança.",
    xe: "Postgraduate degree in AI Engineering completed in 2026 at Impacta Digital. Serves as AI & Automation Consultant (temporary) at Arquitetool, translating operational needs into product and automation opportunities. Developed practical projects: Síndico Inteligente, Agenda Retrátil, Cost-Loaded Schedule Generator, and Vigia Obra Safety."
  },
  {
    id: "maturidade_testes",
    t: "Maturidade e Testes Automatizados",
    te: "Maturity & Automated Tests",
    s: "#projetos",
    k: "producao usuarios clientes comercial saas escala real deploy testes test pytest unittest cobertura qualificacao quality tests automated",
    x: "Aplicações e MVPs com suíte automatizada validada: Síndico Inteligente (4 testes aprovados), Agenda Retrátil (4 testes aprovados com keyring e etag), RAG do Zero (11 testes), Arc Copilot (10 testes) e Prospecção de Leads CLI (5 testes). Todos os projetos contam com transparência de maturidade e cobertura de testes unitários.",
    xe: "Applications and MVPs with validated test suites: Síndico Inteligente (4 passed tests), Agenda Retrátil (4 passed tests with keyring and etag), RAG do Zero (11 tests), Arc Copilot (10 tests), and Lead Prospecting CLI (5 tests). All projects feature transparent maturity levels and unit test coverage."
  },
  {
    id: "stack",
    t: "Competências Técnicas & Stack",
    te: "Technical Skills & Stack",
    s: "#competencias",
    k: "stack tecnologias ferramentas linguagens python langchain langgraph sql sqlite postgresql api rest json git github testes programa codigo fastapi technologies tools languages tests code",
    x: "IA & LLMs: APIs de LLMs, LangChain, structured outputs, engenharia de prompts, APIs multimodais, busca documental, SQLite FTS5. Desenvolvimento & Integração: Python, SQL, SQLite, JavaScript, JSON, NDJSON, APIs REST, OAuth, Git, GitHub, testes unitários. Dados & Aplicações: Streamlit, Plotly, OpenCV, aplicações desktop locais, persistência local, armazenamento seguro de tokens (Keyring). Domínio: análise de requisitos, melhoria de processos, gestão de projetos, ConTech / PropTech.",
    xe: "AI & LLMs: LLM APIs, LangChain, structured outputs, prompt engineering, multimodal APIs, document search, SQLite FTS5. Development & Integration: Python, SQL, SQLite, JavaScript, JSON, NDJSON, REST APIs, OAuth, Git, GitHub, unit tests. Data & Apps: Streamlit, Plotly, OpenCV, local desktop apps, local persistence, token security (Keyring). Domain: requirements analysis, process improvement, project management, ConTech / PropTech."
  },
  {
    id: "sindico_inteligente",
    t: "Projeto: Síndico Inteligente",
    te: "Project: Síndico Inteligente",
    s: "#projetos",
    k: "sindico condominio condominios documentos pdf fts5 pywebview busca documental condo building documents",
    x: "Aplicação desktop local para gestão condominial (Python, SQLite FTS5, PDFs, JavaScript). Realiza importação e indexação de PDFs com busca textual por documento e página, regras de reserva, histórico, backup SQLite e exportação JSON. Implementou prévia antes de alterações e bloqueio de conflitos; suíte automatizada validada com 4 testes aprovados.",
    xe: "Local desktop app for condo management (Python, SQLite FTS5, PDFs, JavaScript). Features PDF import and indexing with page-level text search, reservation rules, history, SQLite backup, and JSON export. Implemented preview before changes and conflict blocking; automated suite validated with 4 passed tests."
  },
  {
    id: "agenda_retratil",
    t: "Projeto: Agenda Retrátil",
    te: "Project: Agenda Retrátil",
    s: "#projetos",
    k: "agenda retratil calendario calendar google oauth windows metas compromissos credential goals appointments keyring request_id etag",
    x: "Assistente desktop para leitura, criação, edição e exclusão de eventos no Google Calendar via OAuth (Python, Google Calendar API, OAuth, SQLite, Keyring). Executa ações somente após prévia e confirmação explícita. Implementou armazenamento seguro de token no Gerenciador de Credenciais do Windows, persistência local, proteção contra repetição por request_id e sobrescrita por etag; 4 testes automatizados aprovados.",
    xe: "Desktop assistant for reading, creating, updating, and deleting Google Calendar events via OAuth (Python, Google Calendar API, OAuth, SQLite, Keyring). Executes actions only after preview and explicit confirmation. Implemented secure token storage in Windows Credential Manager, local persistence, request_id replay protection, and etag overwrite protection; 4 passed automated tests."
  },
  {
    id: "gerador_cronograma",
    t: "Projeto: Gerador de Cronograma Físico-Financeiro",
    te: "Project: Cost-Loaded Schedule Generator",
    s: "#projetos",
    k: "gerador cronograma fisico financeiro gantt streamlit plotly llm json escopo obras schedule generator",
    x: "Aplicação em Python, Streamlit, API de LLM e Plotly. Transforma escopo de obra em texto livre em JSON estruturado, calcula datas e dependências e apresenta etapas, orçamento e gráfico de Gantt interativo, incluindo tratamento robusto de respostas incompletas e mensagens de erro.",
    xe: "Application built with Python, Streamlit, LLM API, and Plotly. Transforms free-text construction scope into structured JSON, calculates dates and dependencies, and displays stages, budget, and an interactive Gantt chart, including error handling for incomplete responses."
  },
  {
    id: "vigia_obra",
    t: "Projeto: Vigia Obra Segurança",
    te: "Project: Vigia Obra Safety",
    s: "#projetos",
    k: "vigia video videos canteiro seguranca opencv visao multimodal frames ndjson safety site vision",
    x: "Pipeline assistivo em Python, OpenCV, API Multimodal e NDJSON. Extrai frames de vídeos de canteiros de obra e sinaliza possíveis não conformidades de segurança, emitindo progresso em NDJSON. Exige revisão humana e não substitui inspeção presencial.",
    xe: "Assistive pipeline in Python, OpenCV, Multimodal API, and NDJSON. Extracts frames from site videos and flags potential safety non-conformities, emitting progress in NDJSON. Requires human review and does not replace onsite inspection."
  },
  {
    id: "historico",
    t: "Experiência Profissional Detalhada",
    te: "Detailed Work Experience",
    s: "#experiencia",
    k: "empresa empresas trabalhou trabalha emprego atual historico carreira trajetoria cargos arquitetool ch3 blink engconsult torao mazza arq lmanzo bougue obras arquiteto coordenador diretor consultor gestor company companies worked works current history career jobs construction architect",
    x: "• Arquitetool (ago/2026–atual): Consultor de IA e Automação (temporário) em SP. Atua na interseção entre construção, processos, produto e tecnologia.\n• CH3 Incorporadora (out/2025–atual): Gestor de Obras em SP. Idealizou e desenvolveu app de checklist para padronizar registros de campo; coordena equipes, planejamento executivo e suprimentos.\n• Blink Reformei (jun/2024–out/2025): Coordenador de Obras.\n• Torão Design (mar/2022–2024): Coordenador de Obras.\n• Engconsult (2023): Gestor de Obras (temporário - obras comerciais/Caedu/shoppings).\n• M. Mazza Arquitetura (mar/2021–mar/2022): Coordenador de Obras.\n• Arq. LManzo (jan/2016–mar/2021): Arquiteto Autônomo.\n• Experiência Anterior (2008–2015): Bougue (Arquiteto Projetista), Torão Design, e estágios na Construtora Bracoo, União Técnica, Nucleora e Monaco San Marzano.",
    xe: "• Arquitetool (Aug/2026–present): AI & Automation Consultant (temporary) in SP. Works at the intersection of construction, processes, product, and technology.\n• CH3 Incorporadora (Oct/2025–present): Construction Manager in SP. Built a site checklist app; manages teams, executive planning, and procurement.\n• Blink Reformei (Jun/2024–Oct/2025): Construction Coordinator.\n• Torão Design (Mar/2022–2024): Construction Coordinator.\n• Engconsult (2023): Construction Manager (temporary - commercial retail/malls).\n• M. Mazza Arquitetura (Mar/2021–Mar/2022): Construction Coordinator.\n• Arq. LManzo (Jan/2016–Mar/2021): Independent Architect.\n• Earlier Experience (2008–2015): Bougue, Torão Design, and internships at Bracoo, União Técnica, Nucleora, and Monaco San Marzano."
  },
  {
    id: "formacao",
    t: "Formação Acadêmica",
    te: "Education",
    s: "#formacao",
    k: "formacao faculdade graduacao pos estudou curso universidade diploma arquitetura impacta anhembi belas artes education degree studied university college architecture",
    x: "• Pós-graduação em Engenharia de IA: Faculdade Impacta Digital (Concluída em 2026).\n• Pós-graduação em Gestão de Projetos: Universidade Anhembi Morumbi (2023).\n• Arquitetura e Urbanismo: Centro Universitário Belas Artes de São Paulo (2007–2013).",
    xe: "• Postgraduate degree in AI Engineering: Faculdade Impacta Digital (Completed in 2026).\n• Postgraduate degree in Project Management: Universidade Anhembi Morumbi (2023).\n• Bachelor's degree in Architecture and Urbanism: Centro Universitário Belas Artes de São Paulo (2007–2013)."
  },
  {
    id: "certificacoes",
    t: "Certificações & Cursos Complementares",
    te: "Certifications & Courses",
    s: "#formacao",
    k: "certificacao certificacoes certificado certificados google anthropic claude dio lean scrum nr10 sebrae eletrica certification certifications certificate",
    x: "Certificações: Google AI Professional Certificate (Google / Coursera); Claude Platform 101 (Anthropic); Sistema de Interpretação de Gestos com Python e Machine Learning (DIO).\nCursos: Lean Construction (Udemy); Metodologia Scrum (Udemy); Finanças para pequenas empresas (Sebrae); Elétrica Residencial e NR 10 (Seal).",
    xe: "Certifications: Google AI Professional Certificate (Google / Coursera); Claude Platform 101 (Anthropic); Gesture Recognition System with Python & Machine Learning (DIO).\nCourses: Lean Construction (Udemy); Scrum Methodology (Udemy); Small Business Finance (Sebrae); Residential Electricity and NR 10 (Seal)."
  },
  {
    id: "competencias_negocio",
    t: "Competências de Negócio, Domínio & Ferramentas",
    te: "Business Competencies, Domain & Tools",
    s: "#competencias",
    k: "negocio dominio ferramentas powerbi excel ms project autocad sketchup lumion vray photoshop riscos planejamento lideranca business tools",
    x: "Negócio & Domínio: Gestão de projetos, Análise de requisitos, Planejamento e indicadores, Melhoria de processos, Gestão de riscos, Liderança multidisciplinar, Comunicação técnico-negócio, Documentação técnica, Operações de construção, ConTech / PropTech.\nFerramentas: Excel, Power BI, MS Project, Pacote Office, AutoCAD, SketchUp/Layout, Lumion, V-Ray, Twinmotion, Photoshop.",
    xe: "Business & Domain: Project management, Requirements analysis, Planning and KPIs, Process improvement, Risk management, Multidisciplinary leadership, Technical-business communication, Technical documentation, Construction operations, ConTech / PropTech.\nTools: Excel, Power BI, MS Project, Office Suite, AutoCAD, SketchUp/Layout, Lumion, V-Ray, Twinmotion, Photoshop."
  },
  {
    id: "trajetoria_historia_pessoal",
    t: "Trajetória e História de Carreira Detalhada",
    te: "Detailed Career History & Story",
    s: "#experiencia",
    k: "faculdade bolsa roberto monaco nucleora uniao tecnica bracco torao bougue loja material mazza engconsult blink ch3 champions league koji guedala buddha spa osasco historia inicio estagio",
    x: "Leonardo iniciou a faculdade aos 17 anos com bolsa integral. Seu primeiro estágio foi com o Prof. Roberto Monaco, atuando em processos jurídicos, laudos estruturais e perícias documentais. Em seguida, na Nucleora, elaborou projetos industriais de cozinhas. Na União Técnica de Engenharia, apoiou o engenheiro residente no canteiro, tirando dúvidas técnicas, realizando mapeamento de concreto e conferência de projetos. Na Construtora Bracoo, atendia clientes, desenhava projetos executivos de personalização/reforma e supervisionava a execução até a entrega das chaves. Trabalhou como projetista na Torão Design e na Bougue (onde atendia leads do Google, fazia visitas técnicas, projetos e orçamentos). Também empreendeu com loja de materiais de construção, unindo fornecimento a projetos/obras. Na M. Mazza Arquitetura, coordenou 5 obras residenciais simultâneas. Na Engconsult (temporário), geriu equipes em obras comerciais de shopping centers (lojas Caedu). Retornou à Torão Design para coordenar obras do escritório. Na Blink Reformei, geriu simultaneamente 8 reformas residenciais completas. Na CH3 Incorporadora, é Gestor de Obras de projetos de alto padrão e comerciais em shopping (como a Champions League Experience, Koji Guedala e Buddha Spa no Super Shopping Osasco), onde também desenvolveu o app interno de checklist de obra.",
    xe: "Leonardo entered university at age 17 on a full scholarship. His first internship was with Prof. Roberto Monaco, working on legal processes, structural reports, and document audits. Next, at Nucleora, he designed industrial kitchen projects. At União Técnica de Engenharia, he supported the resident engineer onsite with concrete mapping and project verification. At Construtora Bracoo, he met clients, designed customization plans, and supervised renovations through to key handover. Worked as designer at Torão Design and Bougue (handling Google leads, site visits, design, and budgeting). Also owned/managed a building material store, bridging materials to renovation execution. At M. Mazza Arquitetura, he coordinated 5 residential sites simultaneously. At Engconsult (temporary), he managed commercial mall builds (Caedu stores). Returned to Torão Design as coordinator. At Blink Reformei, managed 8 full residential renovations at once. At CH3 Incorporadora, serves as Construction Manager for flagship commercial mall builds (Champions League Exp, Koji Guedala, Buddha Spa Osasco) and built an internal site checklist app."
  },
  {
    id: "vagas_pretensao_contrato",
    t: "Pretensão Salarial, Formato de Contrato e Disponibilidade",
    te: "Salary Expectation, Contract Format & Availability",
    s: "#contato",
    k: "pretensao salario valores valor contratacao contrato pj clt inicio disponibilidade quando comecar arquitetool dezembro contrato",
    x: "• Pretensão Salarial: R$ 8.000 a R$ 12.000.\n• Formato de Contrato: Sem preferência entre PJ e CLT (já atua como PJ).\n• Disponibilidade: Início imediato, com preferência a partir de dezembro/2026 (contrato da Arquitetool encerra em 30/11/2026).\n• Nível/Cargo: Sem preferência por rótulos (aberto a posições de AI Solutions Engineer, AI Automation, Implementation, ConTech ou Gestão Técnica de IA).",
    xe: "• Salary Expectation: R$ 8,000 to R$ 12,000/month.\n• Contract Format: No preference between PJ and CLT (already works as PJ).\n• Availability: Immediate, with preference starting December/2026 (Arquitetool consultancy contract ends Nov 30, 2026).\n• Seniority/Role: Open to title formats (AI Solutions Engineer, AI Automation, Implementation, ConTech, Technical AI Management)."
  },
  {
    id: "diferencial_construcao_ia",
    t: "Diferencial Competitivo: Vivência Prática no Canteiro",
    te: "Competitive Advantage: Onsite Domain Expertise",
    s: "#sobre",
    k: "diferencial vantagem por que contratar visao campo canteiro pratica construcao civil operacao dores reais",
    x: "O grande diferencial de Leonardo em IA é a sua vivência prática de 10+ anos em obras, lojas de materiais e coordenação de canteiro. Com esse conhecimento de causa, ele enxerga e projeta soluções de IA e automação que realmente fazem diferença no campo, criando ferramentas úteis que resolvem dores operacionais reais.",
    xe: "Leonardo's key edge in AI is his 10+ years of hands-on experience in construction sites, material procurement, and team management. With deep domain knowledge, he identifies and builds AI and automation solutions that solve real field pain points."
  },
  {
    id: "arc_copilot_desafio",
    t: "Projeto Arc Copilot & Desafios Técnicos",
    te: "Arc Copilot Project & Technical Challenges",
    s: "#projetos",
    k: "arc copilot desafio tecnico mais desafiador fastapi sqlalchemy mensagens whatsapp permissões rdo estoque",
    x: "O Arc Copilot é um dos projetos mais completos e desafiadores: aplicação web em FastAPI/SQLAlchemy que converte mensagens de campo em registros estruturados, movimentações de estoque e Diário de Obra (RDO). Implementou controle de acesso refinado por função (trabalhador, mestre de obra, engenheiro), isolamento por obra e validação com 10 testes automatizados.",
    xe: "Arc Copilot is one of his most comprehensive technical projects: a FastAPI/SQLAlchemy web app converting field messages into confirmed records, inventory movements, and Daily Reports (RDO). Features role-based access control (worker, foreman, engineer), site isolation, and 10 automated tests."
  },
  {
    id: "decisoes_tecnicas_arquitetura",
    t: "Decisões Técnicas de Arquitetura (FTS5 & Keyring)",
    te: "Architectural Technical Decisions (FTS5 & Keyring)",
    s: "#projetos",
    k: "por que fts5 porque sqlite fts5 local privacidade keyring agenda retratil tokens oauth seguranca",
    x: "No Síndico Inteligente, a escolha do SQLite FTS5 foi feita para rodar 100% localmente: garante privacidade total dos documentos do condomínio, custo zero de infraestrutura e funcionamento em qualquer máquina sem dependência de nuvem. No Agenda Retrátil, o armazenamento de tokens OAuth utiliza o Gerenciador de Credenciais do Windows (Windows Keyring) para criptografia nativa no SO.",
    xe: "In Síndico Inteligente, SQLite FTS5 was selected to run 100% locally: ensuring document privacy, zero cloud infrastructure cost, and local execution. In Agenda Retrátil, OAuth tokens are stored via Windows Credential Manager (Keyring) for OS-level encryption."
  }
];

const STOP_WORDS = new Set(['a','o','e','de','da','do','das','dos','em','no','na','nos','nas','um','uma','para','por','com','que','qual','quais','como','ele','ela','dele','dela','tem','ter','foi','ser','esta','estao','voce','seu','sua','sobre','mais','algum','alguma','ja','se','ou','os','as','ao','aos','me','fale','conte','quanto','quantos','onde','quando','leonardo','manzo','the','is','are','was','does','do','did','he','his','him','has','have','had','what','which','who','how','any','of','in','on','at','to','for','with','and','or','about','tell','me','an','it','this','that']);

function tokenize(text) {
  if (!text) return [];
  return text.toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9 ]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 1 && !STOP_WORDS.has(w))
    .map(w => w.replace(/(oes|ais|s)$/, '').slice(0, 6));
}

function searchContext(query, isEn = false) {
  const qTokens = tokenize(query);
  if (!qTokens.length) return [];

  const scored = KB.map(doc => {
    const titleTokens = tokenize(isEn ? doc.te : doc.t);
    const kwTokens = tokenize(doc.k);
    const bodyTokens = tokenize(isEn ? doc.xe : doc.x);

    let score = 0;
    qTokens.forEach(token => {
      if (kwTokens.includes(token)) score += 3;
      else if (titleTokens.includes(token)) score += 2;
      else if (bodyTokens.includes(token)) score += 1;
    });

    return { doc, score };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored.filter(item => item.score > 0).slice(0, 4).map(item => item.doc);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/ask' && request.method === 'POST') {
      try {
        const body = await request.json();
        const question = (body.question || '').trim();
        const lang = body.lang || 'pt';
        const isEn = lang === 'en';

        if (!question) {
          return new Response(JSON.stringify({ error: isEn ? 'Empty question' : 'Pergunta vazia' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' }
          });
        }

        let relevantDocs = searchContext(question, isEn);

        // Se a busca léxica não encontrar termos exatos (ex.: perguntas genéricas como "como isso aqui funciona?"),
        // injeta os documentos institucionais principais (como funciona, posicionamento e stack) para o Agente responder fluentemente.
        if (!relevantDocs.length) {
          const defaultDocIds = ["como_funciona_agente", "saudacao_apresentacao", "posicionamento", "stack"];
          relevantDocs = KB.filter(d => defaultDocIds.includes(d.id));
        }

        // Se tiver a chave da Gemini API configurada no ambiente do Worker
        if (env.GEMINI_API_KEY) {
          const contextText = relevantDocs
            .map(d => `[${isEn ? d.te : d.t} (${d.s})]: ${isEn ? d.xe : d.x}`)
            .join('\n\n');

          const systemPrompt = isEn
            ? `You are the Virtual AI Assistant for Leonardo Rabello Manzo's Portfolio. Your mission is to act as a warm, persuasive, natural tech & business consultant. SELL Leonardo's profile to recruiters, clients, and engineering leaders.

CRITICAL FORMATTING AND STYLE RULES:
1. NEVER use markdown headers like ###, ##, # or hr dividers ---. Do NOT clutter the response with bold markdown (**). Write in clean, natural conversational paragraphs with simple bullet points (•) if listing items.
2. NATURAL PITCH TONE: Highlight Leonardo's unique edge — combining 10+ years of real-world construction site experience with applied AI Engineering (Python, LLMs, automation, REST APIs). He builds practical solutions that solve real operational pain points.
3. COMPELLING CLOSING: Always end every answer with an engaging, practical pitch question (e.g. 'Can you imagine a custom AI solution like this streamlining your site operations? Would you like to schedule a quick chat with Leonardo to see how this fits your team?').
4. Always answer in clear, friendly English.`
            : `Você é o Assistente Virtual de IA do Portfólio de Leonardo Rabello Manzo. Sua missão é atuar como um consultor humano de tecnologia e negócios, conversando de forma simples, fluida, acolhedora e altamente convincente. VENDA o perfil do Leonardo para recrutadores, clientes e gestores.

REGRAS RÍGIDAS DE ESTILO E FORMATAÇÃO (MUITO IMPORTANTE):
1. NUNCA use marcadores de cabeçalho como ###, ##, # ou divisores ---. NÃO polua o texto com excesso de negritos (**). Escreva em linguagem natural de conversa, com parágrafos bem espaçados, frases limpas e marcadores simples (•) se precisar listar itens.
2. TOM DE VENDAS E CONVENCIMENTO: Destaque o grande diferencial do Leonardo — a união de mais de 10 anos de vivência prática em canteiro de obras e gestão com a Engenharia de IA aplicada (Python, LLMs, automação de processos). Ele não cria teorias, ele projeta ferramentas úteis que resolvem dores operacionais reais do campo.
3. GANCHO FINAL PROVOCATIVO: Termine TODA resposta com uma pergunta envolvente de aplicação prática no negócio do cliente (ex.: 'Já imaginou um assistente desse nível acelerando a sua obra e eliminando erros operacionais? Quer agendar um papo rápido com o Leonardo para ver essa solução rodando na sua empresa?').
4. Sempre responda em português do Brasil de forma concisa, fluida e envolvente.`;

          const userPrompt = `Contexto do Portfólio:\n${contextText}\n\nPergunta do Usuário: ${question}`;

          const modelsToTry = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-flash'];
          for (const model of modelsToTry) {
            try {
              const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'x-goog-api-key': env.GEMINI_API_KEY
                },
                body: JSON.stringify({
                  contents: [{
                    role: 'user',
                    parts: [{ text: userPrompt }]
                  }],
                  systemInstruction: {
                    parts: [{ text: systemPrompt }]
                  },
                  generationConfig: {
                    temperature: 0.3,
                    maxOutputTokens: 450
                  }
                })
              });

              if (geminiRes.ok) {
                const data = await geminiRes.json();
                const answer = data.candidates?.[0]?.content?.parts?.[0]?.text;
                if (answer) {
                  return new Response(JSON.stringify({
                    answer: answer.trim(),
                    sources: relevantDocs.map(d => ({ title: isEn ? d.te : d.t, target: d.s })),
                    mode: model
                  }), {
                    headers: { 'Content-Type': 'application/json' }
                  });
                }
              }
            } catch (e) {
              // Tenta o próximo modelo
            }
          }
        }

        // Resposta inteligente do Agente em modo local (sem API key ou em caso de erro da API)
        const directAnswers = relevantDocs.map(d => isEn ? d.xe : d.x).join('\n\n');
        return new Response(JSON.stringify({
          answer: directAnswers,
          sources: relevantDocs.map(d => ({ title: isEn ? d.te : d.t, target: d.s })),
          mode: 'agente-rag-local'
        }), {
          headers: { 'Content-Type': 'application/json' }
        });

      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }

    // Para qualquer outra rota, serve os assets estáticos do Cloudflare Workers Assets
    let newPath = url.pathname;
    if (newPath === '/' || newPath === '' || newPath === '/publicado' || newPath === '/publicado/') {
      return Response.redirect(new URL('/portfolio/', request.url).toString(), 302);
    }
    if (newPath.startsWith('/publicado/')) {
      newPath = newPath.substring('/publicado'.length);
    }
    if (newPath.endsWith('/')) {
      newPath += 'index.html';
    }
    let newUrl = new URL(request.url);
    newUrl.pathname = newPath;
    let assetReq = new Request(newUrl.toString(), request);
    return env.ASSETS ? env.ASSETS.fetch(assetReq) : fetch(request);
  }
};
