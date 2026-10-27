/**
 * Cloudflare Worker do portfólio de Leonardo Manzo.
 *
 * /api/ask: assistente que responde perguntas sobre o portfólio usando a Gemini API.
 * A base de conhecimento é pequena (~22 documentos), então o modelo recebe a base
 * inteira a cada pergunta, em vez de só os trechos achados por busca de palavras.
 * Isso evita respostas ruins quando a pergunta usa palavras que não estão na base
 * (ex.: "como ele pode ajudar a minha empresa?").
 *
 * Fonte única dos dados: publicado/portfolio/kb.json (usada também pela página).
 */
import KB from './publicado/portfolio/kb.json';

const CONTACT = 'leonardo.r.manzo@gmail.com';

// Ordem de tentativa. thinkingLevel baixo: a resposta é curta e o "pensamento"
// conta dentro de maxOutputTokens; com nível alto a resposta pode vir vazia.
const MODELS = [
  { name: 'gemini-3.5-flash-lite', thinkingLevel: 'minimal' },
  { name: 'gemini-3.8-flash', thinkingLevel: 'low' },
];
const MAX_QUESTION_CHARS = 300;

const STOP_WORDS = new Set(['a','o','e','de','da','do','das','dos','em','no','na','nos','nas','um','uma','para','por','com','que','qual','quais','como','ele','ela','dele','dela','tem','ter','foi','ser','esta','estao','voce','seu','sua','sobre','mais','algum','alguma','ja','se','ou','os','as','ao','aos','me','fale','conte','quanto','quantos','onde','quando','leonardo','manzo','the','is','are','was','does','do','did','he','his','him','has','have','had','what','which','who','how','any','of','in','on','at','to','for','with','and','or','about','tell','an','it','this','that']);

function tokenize(text) {
  if (!text) return [];
  return text.toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9 ]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 1 && !STOP_WORDS.has(w))
    .map(w => w.replace(/(oes|ais|s)$/, '').slice(0, 6));
}

/** Busca léxica: só para escolher as fontes exibidas e para o modo sem IA. */
function searchContext(query, isEn) {
  const q = tokenize(query);
  if (!q.length) return [];
  return KB.map(doc => {
    const kw = tokenize(doc.k), title = tokenize(isEn ? doc.te : doc.t), body = tokenize(isEn ? doc.xe : doc.x);
    let score = 0;
    for (const t of q) {
      if (kw.includes(t)) score += 3;
      else if (title.includes(t)) score += 2;
      else if (body.includes(t)) score += 1;
    }
    return { doc, score };
  })
    .filter(r => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map(r => r.doc);
}

function systemPrompt(isEn) {
  return isEn
    ? `You answer questions from recruiters and companies about Leonardo Rabello Manzo, using ONLY the knowledge base below.

Rules:
1. Use only facts from the knowledge base. Never invent numbers, clients, results, employers or dates.
2. If the answer is not in the knowledge base, say so in one sentence and suggest contacting Leonardo at ${CONTACT}.
3. Answer the actual question first, in the first sentence. Prefer a concrete example from his projects over adjectives.
4. Be honest about maturity: his AI experience is recent and his projects are prototypes and MVPs; his seniority is in management and operations. Do not inflate.
5. Plain text, no markdown headers or bold. At most 4 short sentences, or up to 4 bullets starting with "•" when listing.
6. Professional and friendly tone. No sales pitch and no closing questions.
7. Reply in English.`
    : `Você responde perguntas de recrutadores e empresas sobre Leonardo Rabello Manzo usando SOMENTE a base de conhecimento abaixo.

Regras:
1. Use apenas fatos da base. Nunca invente números, clientes, resultados, empregadores ou datas.
2. Se a resposta não estiver na base, diga isso em uma frase e sugira o contato com o Leonardo: ${CONTACT}.
3. Responda a pergunta logo na primeira frase. Prefira um exemplo concreto dos projetos a adjetivos.
4. Seja honesto sobre a maturidade: a experiência em IA é recente e os projetos são protótipos e MVPs; a senioridade dele está em gestão e operações. Não exagere.
5. Texto simples, sem títulos ou negrito em markdown. No máximo 4 frases curtas, ou até 4 itens começando com "•" quando for listar.
6. Tom profissional e cordial. Sem discurso de vendas e sem pergunta de fechamento.
7. Responda em português do Brasil.`;
}

function knowledgeBase(isEn) {
  return KB.map(d => `### ${isEn ? d.te : d.t} [${d.id}]\n${isEn ? d.xe : d.x}`).join('\n\n');
}

async function askGemini(env, model, isEn, question) {
  const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model.name}:generateContent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-goog-api-key': env.GEMINI_API_KEY },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: `${systemPrompt(isEn)}\n\nBASE DE CONHECIMENTO:\n${knowledgeBase(isEn)}` }] },
      contents: [{ role: 'user', parts: [{ text: question }] }],
      generationConfig: {
        temperature: 0.2,
        maxOutputTokens: 1024,
        thinkingConfig: { thinkingLevel: model.thinkingLevel },
      },
    }),
  });

  if (!res.ok) {
    const detail = (await res.text()).slice(0, 300);
    throw new Error(`${model.name} HTTP ${res.status}: ${detail}`);
  }
  const data = await res.json();
  const cand = data.candidates?.[0];
  // Junta só as partes de texto da resposta, ignorando partes de "pensamento".
  const text = (cand?.content?.parts || [])
    .filter(p => p.text && !p.thought)
    .map(p => p.text)
    .join('')
    .trim();
  if (!text) {
    throw new Error(`${model.name} sem texto (finishReason=${cand?.finishReason}, blockReason=${data.promptFeedback?.blockReason})`);
  }
  return text;
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

async function handleAsk(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'JSON inválido' }, 400);
  }
  const isEn = body.lang === 'en';
  const question = String(body.question || '').trim().slice(0, MAX_QUESTION_CHARS);
  if (!question) return json({ error: isEn ? 'Empty question' : 'Pergunta vazia' }, 400);

  const docs = searchContext(question, isEn);
  const sources = docs.map(d => ({ title: isEn ? d.te : d.t, target: d.s }));

  if (env.GEMINI_API_KEY) {
    for (const model of MODELS) {
      try {
        const answer = await askGemini(env, model, isEn, question);
        return json({ answer, sources, mode: model.name });
      } catch (err) {
        // Aparece em `wrangler tail` e nos logs do Cloudflare. Antes o erro era engolido.
        console.error('[ask]', err.message);
      }
    }
  } else {
    console.error('[ask] GEMINI_API_KEY não configurada');
  }

  // Modo sem IA: mostra o trecho mais próximo, sem fingir que é uma resposta gerada.
  const lead = isEn
    ? `The AI assistant is unavailable right now. Here is the closest information I found. For anything else, contact ${CONTACT}.`
    : `O assistente de IA está indisponível agora. Segue a informação mais próxima que encontrei. Para outras dúvidas, fale com ${CONTACT}.`;
  const answer = docs.length ? `${lead}\n\n${isEn ? docs[0].xe : docs[0].x}` : lead;
  return json({ answer, sources: sources.slice(0, 1), mode: 'local' });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/ask' && request.method === 'POST') {
      try {
        return await handleAsk(request, env);
      } catch (err) {
        console.error('[ask] erro inesperado', err);
        return json({ error: 'Erro interno' }, 500);
      }
    }

    // Demais rotas: assets estáticos.
    let path = url.pathname;
    if (path === '/' || path === '' || path === '/publicado' || path === '/publicado/') {
      return Response.redirect(new URL('/portfolio/', request.url).toString(), 302);
    }
    if (path.startsWith('/publicado/')) path = path.substring('/publicado'.length);
    if (path.endsWith('/')) path += 'index.html';
    const assetUrl = new URL(request.url);
    assetUrl.pathname = path;
    const assetReq = new Request(assetUrl.toString(), request);
    return env.ASSETS ? env.ASSETS.fetch(assetReq) : fetch(request);
  },
};
