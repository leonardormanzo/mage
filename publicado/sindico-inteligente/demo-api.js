(function () {
  const data = {
    documents: [
      { id: 1, name: "Regimento-interno-demo.pdf", pages: 28, status: "indexado", indexed_at: "2026-07-27T09:30:00" },
      { id: 2, name: "Ata-assembleia-julho-demo.pdf", pages: 7, status: "indexado", indexed_at: "2026-07-26T17:10:00" }
    ],
    occurrences: [
      { id: 1, title: "Vazamento no 4º andar", category: "Manutenção", priority: "alta", status: "em andamento", due_date: "2026-07-29", responsible: "Carlos" },
      { id: 2, title: "Lâmpada da garagem", category: "Elétrica", priority: "média", status: "aberta", due_date: "2026-07-30", responsible: "Equipe predial" }
    ],
    tasks: [
      { id: 1, title: "Solicitar orçamento hidráulico", due_date: "2026-07-29", responsible: "Carlos", status: "em andamento" },
      { id: 2, title: "Revisar comunicado da garagem", due_date: "2026-07-30", responsible: "Síndico", status: "pendente" }
    ],
    announcements: [
      { id: 1, title: "Manutenção preventiva dos elevadores", body: "Serviço programado para sexta-feira.", status: "publicado" },
      { id: 2, title: "Orientações para descarte", body: "Rascunho para revisão.", status: "rascunho" }
    ],
    contacts: [
      { id: 1, name: "Carlos Mendes", kind: "prestador", phone: "(11) 99999-0001", email: "demo@example.com" },
      { id: 2, name: "Hidráulica Central", kind: "fornecedor", phone: "(11) 99999-0002", email: "demo2@example.com" }
    ],
    spaces: [
      { id: 1, name: "Salão de festas", rules: "Até 22h; máximo de 50 pessoas.", opens_at: "08:00", closes_at: "22:00" },
      { id: 2, name: "Churrasqueira", rules: "Reserva por período de quatro horas.", opens_at: "10:00", closes_at: "22:00" }
    ],
    reservations: [
      { id: 1, space_id: 1, space_name: "Salão de festas", title: "Aniversário — unidade 72", starts_at: "2026-08-01T18:00", ends_at: "2026-08-01T22:00" }
    ]
  };
  const ok = value => Promise.resolve({ ok: true, data: value });
  const fail = message => Promise.resolve({ ok: false, error: message });
  const dashboard = () => ({
    open_occurrences: data.occurrences.filter(item => !["resolvida", "cancelada"].includes(item.status)).length,
    overdue_tasks: 1,
    upcoming_reservations: data.reservations.length,
    documents: data.documents.length,
    recent_documents: data.documents.slice(0, 4),
    recent_occurrences: data.occurrences.slice(0, 5)
  });

  window.pywebview = { api: {
    bootstrap: () => ok({ dashboard: dashboard(), ...data }),
    list_entity: entity => ok(data[entity] || []),
    preview: (action, entity, payload) => ok({ action, entity, payload }),
    commit: (action, entity, payload) => {
      if (!data[entity]) return fail("Módulo indisponível na demonstração.");
      if (action === "delete") {
        const index = data[entity].findIndex(item => item.id === Number(payload.id));
        if (index >= 0) data[entity].splice(index, 1);
        return ok(null);
      }
      const record = { id: Date.now(), ...payload };
      if (entity === "reservations") {
        const space = data.spaces.find(item => item.id === Number(payload.space_id));
        record.space_name = space ? space.name : "Espaço";
      }
      data[entity].unshift(record);
      return ok(record.id);
    },
    choose_pdf: () => ok("Regimento-novo-demo.pdf"),
    import_pdf: () => {
      const document = { id: Date.now(), name: "Regimento-novo-demo.pdf", pages: 16, chunks: 24, status: "indexado" };
      data.documents.unshift(document);
      return ok(document);
    },
    delete_document: id => {
      const index = data.documents.findIndex(item => item.id === Number(id));
      if (index >= 0) data.documents.splice(index, 1);
      return ok(null);
    },
    ask_documents: question => ok({
      answer: "Obras com ruído são permitidas de segunda a sexta, das 8h às 17h, e aos sábados, das 9h às 13h.",
      confidence: "alta",
      mode: "Demonstração com dados fictícios",
      sources: [
        { document: "Regimento-interno-demo.pdf", page: 12, excerpt: `Trecho demonstrativo relacionado à pergunta “${question}”: respeitar os horários autorizados e comunicar previamente a administração.` },
        { document: "Ata-assembleia-julho-demo.pdf", page: 4, excerpt: "A assembleia manteve os horários de obras e reforçou a necessidade de cadastro dos prestadores." }
      ]
    }),
    backup: () => ok("backup-demo-simulado.db"),
    export_data: () => ok("exportacao-demo-simulada.json")
  }};
  setTimeout(() => window.dispatchEvent(new Event("pywebviewready")), 0);
})();
