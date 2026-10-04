(function () {
  const STORAGE_KEY = "sindico_inteligente_demo_v1";

  const defaultData = {
    documents: [
      { id: 1, name: "Regimento-interno-demo.pdf", pages: 28, status: "indexado", indexed_at: "2026-07-27T09:30:00" },
      { id: 2, name: "Ata-assembleia-julho-demo.pdf", pages: 7, status: "indexado", indexed_at: "2026-07-26T17:10:00" },
      { id: 3, name: "Convenção-condominial.pdf", pages: 45, status: "indexado", indexed_at: "2026-06-15T14:20:00" }
    ],
    occurrences: [
      { id: 1, title: "Vazamento no 4º andar", category: "Manutenção", priority: "alta", status: "em andamento", due_date: "2026-07-29", responsible: "Carlos Mendes" },
      { id: 2, title: "Lâmpada da garagem queimada", category: "Elétrica", priority: "média", status: "aberta", due_date: "2026-07-30", responsible: "Equipe predial" },
      { id: 3, title: "Ruído excessivo apto 82", category: "Convivência", priority: "alta", status: "resolvida", due_date: "2026-07-25", responsible: "Portaria" }
    ],
    tasks: [
      { id: 1, title: "Solicitar orçamento hidráulico", due_date: "2026-07-29", responsible: "Carlos Mendes", status: "em andamento" },
      { id: 2, title: "Revisar comunicado da garagem", due_date: "2026-07-30", responsible: "Síndico", status: "pendente" },
      { id: 3, title: "Inspeção mensal dos extintores", due_date: "2026-08-05", responsible: "Empresa de Segurança", status: "pendente" }
    ],
    announcements: [
      { id: 1, title: "Manutenção preventiva dos elevadores", body: "Serviço programado para sexta-feira das 9h às 12h.", status: "publicado" },
      { id: 2, title: "Orientações para descarte seletivo", body: "Lixo reciclável deve ser separado em sacos azuis no subsolo 1.", status: "publicado" },
      { id: 3, title: "Convocaçao Assembleia Extraordinaria", body: "Rascunho de pauta sobre reforma da fachada.", status: "rascunho" }
    ],
    contacts: [
      { id: 1, name: "Carlos Mendes", kind: "prestador", phone: "(11) 99999-0001", email: "carlos.mendes@prestador.com" },
      { id: 2, name: "Hidráulica Central", kind: "fornecedor", phone: "(11) 99999-0002", email: "comercial@hidraulica.com" },
      { id: 3, name: "Dra. Ana Paula (Jurídico)", kind: "prestador", phone: "(11) 98888-7766", email: "ana.paula@advocacia.com" }
    ],
    spaces: [
      { id: 1, name: "Salão de festas", rules: "Até 22h; máximo de 50 pessoas; taxa de limpeza R$ 120.", opens_at: "08:00", closes_at: "22:00" },
      { id: 2, name: "Churrasqueira Gourmet", rules: "Reserva por período de quatro horas. Manter limpo ao sair.", opens_at: "10:00", closes_at: "22:00" },
      { id: 3, name: "Espaço Coworking", rules: "Silêncio exigido. Acesso livre a moradores.", opens_at: "07:00", closes_at: "23:00" }
    ],
    reservations: [
      { id: 1, space_id: 1, space_name: "Salão de festas", title: "Aniversário — unidade 72", starts_at: "2026-08-01T18:00", ends_at: "2026-08-01T22:00" },
      { id: 2, space_id: 2, space_name: "Churrasqueira Gourmet", title: "Almoço em família — unidade 34", starts_at: "2026-08-02T12:00", ends_at: "2026-08-02T16:00" }
    ]
  };

  function loadData() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) {
      console.warn("Falha ao carregar dados salvos:", e);
    }
    return defaultData;
  }

  function saveData(current) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
    } catch (e) {
      console.warn("Falha ao salvar no localStorage:", e);
    }
  }

  const data = loadData();

  const ok = value => Promise.resolve({ ok: true, data: value });
  const fail = message => Promise.resolve({ ok: false, error: message });

  const dashboard = () => ({
    open_occurrences: data.occurrences.filter(item => !["resolvida", "cancelada"].includes(item.status)).length,
    overdue_tasks: data.tasks.filter(item => item.status !== "concluida").length,
    upcoming_reservations: data.reservations.length,
    documents: data.documents.length,
    recent_documents: data.documents.slice(0, 4),
    recent_occurrences: data.occurrences.slice(0, 5)
  });

  function downloadBlob(filename, text, mimeType = "application/json") {
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  window.pywebview = {
    api: {
      bootstrap: () => ok({ dashboard: dashboard(), ...data }),
      list_entity: entity => ok(data[entity] || []),
      preview: (action, entity, payload) => ok({ action, entity, payload }),
      commit: (action, entity, payload) => {
        if (!data[entity]) return fail("Módulo indisponível na demonstração.");
        if (action === "delete") {
          const index = data[entity].findIndex(item => item.id === Number(payload.id));
          if (index >= 0) data[entity].splice(index, 1);
          saveData(data);
          return ok(null);
        }
        const record = { id: Date.now(), ...payload };
        if (entity === "reservations") {
          const space = data.spaces.find(item => item.id === Number(payload.space_id));
          record.space_name = space ? space.name : "Espaço";
        }
        data[entity].unshift(record);
        saveData(data);
        return ok(record.id);
      },
      delete_entity_item: (entity, id) => {
        if (!data[entity]) return fail("Entidade não encontrada.");
        const index = data[entity].findIndex(item => item.id === Number(id));
        if (index >= 0) data[entity].splice(index, 1);
        saveData(data);
        return ok(null);
      },
      update_entity_item: (entity, id, updates) => {
        if (!data[entity]) return fail("Entidade não encontrada.");
        const item = data[entity].find(x => x.id === Number(id));
        if (item) {
          Object.assign(item, updates);
          saveData(data);
        }
        return ok(item);
      },
      choose_pdf: () => ok("Regimento-interno-atualizado-2026.pdf"),
      import_pdf: path => {
        const document = {
          id: Date.now(),
          name: path ? path.split(/[/\\]/).pop() : "Documento-novo.pdf",
          pages: Math.floor(Math.random() * 20) + 5,
          chunks: Math.floor(Math.random() * 30) + 10,
          status: "indexado",
          indexed_at: new Date().toISOString()
        };
        data.documents.unshift(document);
        saveData(data);
        return ok(document);
      },
      delete_document: id => {
        const index = data.documents.findIndex(item => item.id === Number(id));
        if (index >= 0) data.documents.splice(index, 1);
        saveData(data);
        return ok(null);
      },
      ask_documents: question => {
        const q = question.toLowerCase();
        let answer = "";
        let sources = [];
        let confidence = "alta";

        if (q.includes("obra") || q.includes("reforma") || q.includes("barulho") || q.includes("ruido")) {
          answer = "Obras com emissão de ruído são permitidas estritamente de segunda a sexta-feira, das 8h às 17h, e aos sábados, das 9h às 13h. É proibido qualquer ruído de obra aos domingos e feriados.";
          sources = [
            { document: "Regimento-interno-demo.pdf", page: 12, excerpt: "Art. 42: Obras e reformas que gerem ruídos deverão respeitar a janela das 8h às 17h nos dias úteis e 9h às 13h aos sábados." },
            { document: "Ata-assembleia-julho-demo.pdf", page: 4, excerpt: "Deliberação 3.1: Mantido o horário limite para ruídos de obras e aprovada a obrigatoriedade de comunicação prévia de 48h à portaria." }
          ];
        } else if (q.includes("silencio") || q.includes("som") || q.includes("festa") || q.includes("horario")) {
          answer = "O horário de silêncio vigora diariamente das 22h às 7h. As festas no Salão de Festas ou Churrasqueira devem encerrar a música e dispersar convidados no máximo às 22h.";
          sources = [
            { document: "Regimento-interno-demo.pdf", page: 15, excerpt: "Art. 55: O período de silêncio inicia-se pontualmente às 22:00h e estende-se até às 07:00h do dia seguinte." },
            { document: "Convenção-condominial.pdf", page: 22, excerpt: "Cláusula 18ª: O descumprimento do horário de silêncio sujeita a unidade a advertência formal e multa de 1 taxa condominial em caso de reincidência." }
          ];
        } else if (q.includes("pet") || q.includes("animal") || q.includes("cachorro") || q.includes("gato")) {
          answer = "Animais de estimação são permitidos desde que transportados no colo ou em caixas de transporte nos elevadores de serviço. É proibida a circulação sem guia pelas áreas sociais.";
          sources = [
            { document: "Regimento-interno-demo.pdf", page: 19, excerpt: "Art. 71: Os animais domésticos deverão utilizar exclusivamente o elevador de serviço e permanecer com coleira/guia curta nas áreas comuns." }
          ];
        } else if (q.includes("vaga") || q.includes("garagem") || q.includes("estacionar") || q.includes("carro")) {
          answer = "Cada unidade possui direito ao uso da vaga demarcada na convenção. É proibido estacionar veículos fora da faixa, utilizar a vaga alheia sem autorização por escrito ou armazenar entulho/móveis nas vagas.";
          sources = [
            { document: "Convenção-condominial.pdf", page: 11, excerpt: "Art. 34: As vagas de garagem destinam-se exclusivamente ao estacionamento de veículos automotores em bom estado de conservação." }
          ];
        } else if (q.includes("lixo") || q.includes("descarte") || q.includes("reciclagem")) {
          answer = "O lixo orgânico deve ser depositado devidamente ensacado na lixeira do andar até as 20h. O lixo reciclável (seco) deve ser levado ao depósito de recicláveis no Subsolo 1.";
          sources = [
            { document: "Regimento-interno-demo.pdf", page: 25, excerpt: "Art. 88: O descarte de materiais recicláveis deve seguir a separação correta dos recipientes localizados no subsolo 1." }
          ];
        } else {
          answer = `Com base nos documentos indexados do condomínio, a consulta sobre "${question}" requer observância às normas do Regimento Interno e Convenção. Recomenda-se verificar a convenção completa para casos específicos.`;
          confidence = "média";
          sources = [
            { document: "Regimento-interno-demo.pdf", page: 5, excerpt: `Disposição geral relativa ao tema "${question}": o morador deve zelar pelo sossego, segurança e conservação do patrimônio comum.` },
            { document: "Convenção-condominial.pdf", page: 14, excerpt: "Os casos omissos serão decididos pelo Síndico ad referendum da Assembleia Geral." }
          ];
        }

        return ok({ answer, confidence, mode: "RAG Local Ativo", sources });
      },
      backup: () => {
        const jsonStr = JSON.stringify(data, null, 2);
        const filename = `backup-sindico-${new Date().toISOString().slice(0, 10)}.json`;
        downloadBlob(filename, jsonStr);
        return ok(filename);
      },
      export_data: () => {
        const jsonStr = JSON.stringify(data, null, 2);
        const filename = `exportacao-condominio-${new Date().toISOString().slice(0, 10)}.json`;
        downloadBlob(filename, jsonStr);
        return ok(filename);
      }
    }
  };

  setTimeout(() => window.dispatchEvent(new Event("pywebviewready")), 0);
})();
